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
PROBE_TIMEOUT = 10.0
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
NFQWS_PATH = shutil.which('nfqws') or '/usr/bin/nfqws'
TEST_QUEUE_BASE = 210

# DoH servers to bypass DNS poisoning
DOH_SERVERS = [
    "https://cloudflare-dns.com/dns-query",
    "https://dns.google/resolve",
    "https://dns.quad9.net/dns-query"
]


class ParallelProber:
    """
    Probes a domain with different DPI bypass strategies in parallel.
    Uses DoH to bypass DNS poisoning first, then tests DPI bypass strategies.
    """
    
    def __init__(self, target_domain: str, enable_telemetry: bool = True):
        self.target_domain = target_domain
        self.stop_event = threading.Event()
        self.winner_strategy = None
        self.lock = threading.Lock()
        self.enable_telemetry = enable_telemetry
        self.tracker = StatsTracker() if enable_telemetry else None
        self._resolved_ip = None

    def _resolve_via_doh(self, domain: str) -> Optional[str]:
        """Resolve domain using DNS over HTTPS to bypass DNS poisoning."""
        import urllib3
        urllib3.disable_warnings()
        
        for doh_server in DOH_SERVERS:
            try:
                if "cloudflare" in doh_server:
                    # Cloudflare DoH format
                    response = requests.get(
                        doh_server,
                        params={"name": domain, "type": "A"},
                        headers={"Accept": "application/dns-json"},
                        timeout=5,
                        verify=False
                    )
                    data = response.json()
                    if "Answer" in data:
                        for answer in data["Answer"]:
                            if answer.get("type") == 1:  # A record
                                ip = answer.get("data")
                                if ip and not ip.startswith("0."):
                                    logging.info(f"DoH resolved {domain} -> {ip} (via Cloudflare)")
                                    return ip
                elif "google" in doh_server:
                    # Google DoH format
                    response = requests.get(
                        doh_server,
                        params={"name": domain, "type": "A"},
                        timeout=5,
                        verify=False
                    )
                    data = response.json()
                    if "Answer" in data:
                        for answer in data["Answer"]:
                            if answer.get("type") == 1:
                                ip = answer.get("data")
                                if ip and not ip.startswith("0."):
                                    logging.info(f"DoH resolved {domain} -> {ip} (via Google)")
                                    return ip
                else:
                    # Generic DoH
                    response = requests.get(
                        doh_server,
                        params={"name": domain, "type": "A"},
                        headers={"Accept": "application/dns-json"},
                        timeout=5,
                        verify=False
                    )
                    data = response.json()
                    if "Answer" in data:
                        for answer in data["Answer"]:
                            if answer.get("type") == 1:
                                ip = answer.get("data")
                                if ip and not ip.startswith("0."):
                                    logging.info(f"DoH resolved {domain} -> {ip}")
                                    return ip
            except Exception as e:
                logging.debug(f"DoH server {doh_server} failed: {e}")
                continue
        
        return None

    def _resolve_domain(self) -> str:
        """Resolve domain - try DoH first to bypass DNS poisoning."""
        if self._resolved_ip:
            return self._resolved_ip
        
        # First try normal DNS
        try:
            ip = socket.gethostbyname(self.target_domain)
            # Check if DNS is poisoned (returns 0.0.0.0 or similar)
            if ip.startswith("0.") or ip == "127.0.0.1":
                logging.warning(f"DNS poisoning detected! {self.target_domain} -> {ip}")
                logging.info("Trying DoH to get real IP...")
                real_ip = self._resolve_via_doh(self.target_domain)
                if real_ip:
                    self._resolved_ip = real_ip
                    return real_ip
                else:
                    logging.error("DoH also failed. Domain may be blocked at IP level.")
                    return ip
            else:
                self._resolved_ip = ip
                return ip
        except socket.gaierror as e:
            logging.warning(f"Normal DNS failed: {e}, trying DoH...")
            real_ip = self._resolve_via_doh(self.target_domain)
            if real_ip:
                self._resolved_ip = real_ip
                return real_ip
            return self.target_domain

    def _test_strategy(self, strategy_key: str, queue_num: int):
        """Test a single strategy with proper nfqws setup."""
        if self.stop_event.is_set():
            return
        
        nfqws_proc = None
        rules_added = False
        target_ip = self._resolve_domain()
        
        # Skip if IP is poisoned
        if target_ip.startswith("0.") or target_ip == "127.0.0.1":
            logging.debug(f"[{strategy_key}] Skipping - poisoned IP")
            return
        
        try:
            logging.info(f"[{strategy_key}] Testing against {self.target_domain} ({target_ip})...")
            
            strategy_cmd = STRATEGIES[strategy_key]["cmd"]
            start_time = time.time()
            
            # Add temporary iptables rule
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
            
            # Start nfqws with properly parsed args
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
            
            time.sleep(0.5)
            
            if nfqws_proc.poll() is not None:
                logging.debug(f"[{strategy_key}] nfqws died immediately")
                return
            
            # Make request using the resolved IP directly
            success = self._make_request_with_ip(target_ip)
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

    def _make_request_with_ip(self, ip: str) -> bool:
        """Make HTTPS request directly to IP with Host header."""
        import urllib3
        urllib3.disable_warnings()
        
        try:
            # Connect directly to IP, set Host header
            url = f"https://{ip}"
            response = requests.get(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Host": self.target_domain
                },
                timeout=PROBE_TIMEOUT,
                allow_redirects=True,
                verify=False
            )
            return response.status_code < 400
        except Exception as e:
            logging.debug(f"Request to {ip} failed: {e}")
            return False

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
                verify=False
            )
            return response.status_code < 400
        except:
            return False

    def solve(self) -> Optional[str]:
        """Launch all strategies in parallel and return the first one that works."""
        logging.info(f"Starting parallel probe for {self.target_domain} with {len(PRIORITY_LIST)} strategies...")
        
        # Pre-resolve domain with DoH
        ip = self._resolve_domain()
        logging.info(f"Resolved {self.target_domain} -> {ip}")
        
        if ip.startswith("0.") or ip == "127.0.0.1":
            logging.error("Cannot proceed - DNS is poisoned and DoH failed")
            return None
        
        threads = []
        for idx, strategy in enumerate(PRIORITY_LIST):
            queue_num = TEST_QUEUE_BASE + idx
            t = threading.Thread(target=self._test_strategy, args=(strategy, queue_num))
            t.start()
            threads.append(t)
        
        start = time.time()
        for t in threads:
            t.join(timeout=PROBE_TIMEOUT + 3)
        
        total_time = time.time() - start
        logging.info(f"Probe finished in {total_time:.2f}s. Winner: {self.winner_strategy}")
        
        if self.enable_telemetry and self.tracker:
            success = self.winner_strategy is not None
            strategy = self.winner_strategy or "none"
            latency_ms = int(total_time * 1000)
            self.tracker.log_bypass(self.target_domain, strategy, success, latency_ms)
        
        return self.winner_strategy
