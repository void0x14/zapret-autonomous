import threading
import socket
import logging
import time
import requests
import subprocess
import shutil
import shlex
from typing import Optional
from .heuristics import STRATEGIES, PRIORITY_LIST
from telemetry.stats_tracker import StatsTracker

# Configuration
PROBE_TIMEOUT = 8.0  # Increased timeout
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
NFQWS_PATH = shutil.which('nfqws') or '/usr/bin/nfqws'
TEST_QUEUE_BASE = 210  # Use different queue numbers for testing


class ParallelProber:
    """
    Probes a domain with different DPI bypass strategies in parallel.
    Uses REAL network requests to determine which strategy works.
    """
    
    def __init__(self, target_domain: str, enable_telemetry: bool = True):
        self.target_domain = target_domain
        self.stop_event = threading.Event()
        self.winner_strategy = None
        self.lock = threading.Lock()
        self.enable_telemetry = enable_telemetry
        self.tracker = StatsTracker() if enable_telemetry else None
        self._resolved_ip = None

    def _test_strategy(self, strategy_key: str, queue_num: int):
        """
        Test a single strategy by:
        1. Setting up a temporary iptables rule
        2. Starting nfqws with that strategy
        3. Making a real HTTP request
        4. Cleaning up
        """
        if self.stop_event.is_set():
            return
        
        nfqws_proc = None
        rules_added = False
        target_ip = self._resolve_domain()
        
        try:
            logging.info(f"[{strategy_key}] Testing against {self.target_domain} ({target_ip})...")
            
            strategy_cmd = STRATEGIES[strategy_key]["cmd"]
            start_time = time.time()
            
            # Add temporary iptables rule for this test
            add_rule = [
                'iptables', '-t', 'mangle', '-I', 'OUTPUT',
                '-p', 'tcp', '--dport', '443',
                '-d', target_ip,
                '-j', 'NFQUEUE', '--queue-num', str(queue_num), '--queue-bypass'
            ]
            
            result = subprocess.run(add_rule, capture_output=True, text=True)
            if result.returncode != 0:
                logging.debug(f"[{strategy_key}] iptables failed: {result.stderr}")
                return
            rules_added = True
            
            # Start nfqws for this test - PROPERLY PARSE THE COMMAND
            base_cmd = [NFQWS_PATH, f'--qnum={queue_num}']
            strategy_args = shlex.split(strategy_cmd)
            nfqws_cmd = base_cmd + strategy_args
            
            logging.debug(f"[{strategy_key}] Running: {' '.join(nfqws_cmd)}")
            nfqws_proc = subprocess.Popen(
                nfqws_cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Give nfqws time to initialize and bind to queue
            time.sleep(0.5)
            
            # Check if nfqws is still running
            if nfqws_proc.poll() is not None:
                logging.debug(f"[{strategy_key}] nfqws died immediately")
                return
            
            # Make REAL request
            success = self._make_request()
            duration = time.time() - start_time
            
            if success:
                logging.info(f"[{strategy_key}] ✓ SUCCESS in {duration:.2f}s")
                with self.lock:
                    if not self.winner_strategy:
                        self.winner_strategy = strategy_key
                        self.stop_event.set()
            else:
                logging.info(f"[{strategy_key}] ✗ Failed in {duration:.2f}s")
                
        except Exception as e:
            logging.error(f"[{strategy_key}] Error: {e}")
        finally:
            # Cleanup
            if nfqws_proc:
                nfqws_proc.terminate()
                try:
                    nfqws_proc.wait(timeout=2)
                except:
                    nfqws_proc.kill()
            
            if rules_added:
                del_rule = [
                    'iptables', '-t', 'mangle', '-D', 'OUTPUT',
                    '-p', 'tcp', '--dport', '443',
                    '-d', target_ip,
                    '-j', 'NFQUEUE', '--queue-num', str(queue_num), '--queue-bypass'
                ]
                subprocess.run(del_rule, capture_output=True)
    
    def _resolve_domain(self) -> str:
        """Resolve domain to IP address (cached)."""
        if self._resolved_ip:
            return self._resolved_ip
        try:
            self._resolved_ip = socket.gethostbyname(self.target_domain)
            return self._resolved_ip
        except:
            return self.target_domain
    
    def _make_request(self) -> bool:
        """Make a real HTTPS request to test connectivity."""
        import urllib3
        urllib3.disable_warnings()
        
        try:
            url = f"https://{self.target_domain}"
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=PROBE_TIMEOUT,
                allow_redirects=True,
                verify=False  # Ignore SSL errors for testing
            )
            # Any 2xx or 3xx is success
            return response.status_code < 400
        except requests.exceptions.Timeout:
            logging.debug(f"Request timeout")
            return False
        except requests.exceptions.SSLError as e:
            logging.debug(f"SSL error: {e}")
            return False
        except requests.exceptions.ConnectionError as e:
            logging.debug(f"Connection error: {e}")
            return False
        except Exception as e:
            logging.debug(f"Request error: {e}")
            return False

    def solve(self) -> Optional[str]:
        """
        Launch all strategies in parallel and return the first one that works.
        """
        threads = []
        logging.info(f"Starting parallel probe for {self.target_domain} with {len(PRIORITY_LIST)} strategies...")
        
        # Pre-resolve domain
        ip = self._resolve_domain()
        logging.info(f"Resolved {self.target_domain} -> {ip}")
        
        for idx, strategy in enumerate(PRIORITY_LIST):
            queue_num = TEST_QUEUE_BASE + idx
            t = threading.Thread(target=self._test_strategy, args=(strategy, queue_num))
            t.start()
            threads.append(t)
        
        # Wait for completion
        start = time.time()
        for t in threads:
            t.join(timeout=PROBE_TIMEOUT + 3)
        
        total_time = time.time() - start
        logging.info(f"Probe finished in {total_time:.2f}s. Winner: {self.winner_strategy}")
        
        # Log telemetry
        if self.enable_telemetry and self.tracker:
            success = self.winner_strategy is not None
            strategy = self.winner_strategy or "none"
            latency_ms = int(total_time * 1000)
            self.tracker.log_bypass(self.target_domain, strategy, success, latency_ms)
        
        return self.winner_strategy
