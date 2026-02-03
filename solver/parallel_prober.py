import threading
import socket
import logging
import time
import requests
from typing import Optional
from .heuristics import STRATEGIES, PRIORITY_LIST
from telemetry.stats_tracker import StatsTracker

# Timeout for each probe (aggressive)
PROBE_TIMEOUT = 3.0 
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class ParallelProber:
    def __init__(self, target_domain: str, enable_telemetry: bool = True):
        self.target_domain = target_domain
        self.stop_event = threading.Event()
        self.winner_strategy = None
        self.lock = threading.Lock()
        self.enable_telemetry = enable_telemetry
        self.tracker = StatsTracker() if enable_telemetry else None

    def _test_strategy(self, strategy_key: str):
        """
        Actually runs a test connection using a specific strategy.
        In a real scenario, this would spin up a local proxy instance of 'nfqws' with that specific config,
        and try to curl through it.
        
        For this prototype, we simulate the 'check' logic.
        """
        if self.stop_event.is_set():
            return

        cmd = STRATEGIES[strategy_key]["cmd"]
        logging.info(f"[{strategy_key}] probing {self.target_domain}...")

        # TO-DO: Here we would actually spawn a subprocess of nfqws
        # listening on a unique local port (e.g. 10001, 10002...)
        # and try requests.get(..., proxies={"https": "socks5://localhost:10001"})
        
        # Simulating latency and success probability
        # In real code, this connects to the real site via the proxy.
        try:
            # Simulation placeholder
            # Real impl needs: subprocess.Popen(['nfqws', ...])
            start_time = time.time()
            
            # Simulated check (replace with real curl)
            if self._mock_check_connection(strategy_key):
                duration = time.time() - start_time
                logging.info(f"SUCCESS: {strategy_key} worked in {duration:.2f}s")
                
                with self.lock:
                    if not self.winner_strategy:
                        self.winner_strategy = strategy_key
                        self.stop_event.set() # Stop other threads
            else:
                logging.debug(f"FAIL: {strategy_key} failed")

        except Exception as e:
            logging.debug(f"Error in {strategy_key}: {e}")

    def _mock_check_connection(self, key):
        # MOCK: Pretend "fake" and "disorder2" work for "twitter.com"
        time.sleep(1) # Network delay simulation
        if key in ["fake", "disorder2"]:
            return True
        return False

    def solve(self) -> Optional[str]:
        """
        Launches all strategies in parallel.
        Returns the key of the winning strategy.
        """
        threads = []
        logging.info(f"Starting parallel probe for {self.target_domain} with {len(PRIORITY_LIST)} check(s)...")

        for strategy in PRIORITY_LIST:
            t = threading.Thread(target=self._test_strategy, args=(strategy,))
            t.start()
            threads.append(t)

        # Wait for all (or until prompt stop)
        start = time.time()
        for t in threads:
            t.join(timeout=PROBE_TIMEOUT + 1)
        
        total_time = time.time() - start
        logging.info(f"Probe finished in {total_time:.2f}s. Winner: {self.winner_strategy}")
        
        # Log telemetry
        if self.enable_telemetry and self.tracker:
            success = self.winner_strategy is not None
            strategy = self.winner_strategy or "none"
            latency_ms = int(total_time * 1000)
            self.tracker.log_bypass(self.target_domain, strategy, success, latency_ms)
        
        return self.winner_strategy
