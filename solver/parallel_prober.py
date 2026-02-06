import threading
import socket
import logging
import time
import requests
import subprocess
import shutil
import shlex
import urllib3
from typing import Optional

urllib3.disable_warnings()

from .heuristics import STRATEGIES, PRIORITY_LIST
from telemetry.stats_tracker import StatsTracker

PROBE_TIMEOUT = 10.0
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
NFQWS_PATH = shutil.which('nfqws') or '/usr/bin/nfqws'
TEST_QUEUE_BASE = 210


class ParallelProber:
    def __init__(self, target_domain: str, enable_telemetry: bool = True):
        self.target_domain = target_domain
        self.stop_event = threading.Event()
        self.winner_strategy = None
        self.lock = threading.Lock()
        self.enable_telemetry = enable_telemetry
        self.tracker = StatsTracker() if enable_telemetry else None
        self._resolved_ip = None

    def _resolve_via_doh(self, domain: str) -> Optional[str]:
        """DNS over HTTPS ile gerçek IP al."""
        # Cloudflare
        try:
            logging.info(f"[DoH] Cloudflare sorgulanıyor: {domain}")
            resp = requests.get(
                "https://cloudflare-dns.com/dns-query",
                params={"name": domain, "type": "A"},
                headers={"Accept": "application/dns-json"},
                timeout=10, verify=False
            )
            data = resp.json()
            if "Answer" in data:
                for ans in data["Answer"]:
                    if ans.get("type") == 1:
                        ip = ans.get("data")
                        if ip and not ip.startswith("0.") and ip != "127.0.0.1":
                            logging.info(f"[DoH] Cloudflare başarılı: {domain} -> {ip}")
                            return ip
        except Exception as e:
            logging.warning(f"[DoH] Cloudflare hata: {e}")
        
        # Google
        try:
            logging.info(f"[DoH] Google sorgulanıyor: {domain}")
            resp = requests.get(
                "https://dns.google/resolve",
                params={"name": domain, "type": "A"},
                timeout=10, verify=False
            )
            data = resp.json()
            if "Answer" in data:
                for ans in data["Answer"]:
                    if ans.get("type") == 1:
                        ip = ans.get("data")
                        if ip and not ip.startswith("0.") and ip != "127.0.0.1":
                            logging.info(f"[DoH] Google başarılı: {domain} -> {ip}")
                            return ip
        except Exception as e:
            logging.warning(f"[DoH] Google hata: {e}")
        
        return None

    def _resolve_domain(self) -> str:
        """Domain çöz - DNS zehirlenmesini atlamak için DoH kullan."""
        if self._resolved_ip:
            return self._resolved_ip
        
        # Normal DNS dene
        normal_ip = None
        try:
            normal_ip = socket.gethostbyname(self.target_domain)
        except:
            pass
        
        # Zehirlenme kontrolü
        if normal_ip and (normal_ip.startswith("0.") or normal_ip == "127.0.0.1"):
            logging.warning(f"[DNS] ZEHİRLENME TESPİT: {self.target_domain} -> {normal_ip}")
            real_ip = self._resolve_via_doh(self.target_domain)
            if real_ip:
                self._resolved_ip = real_ip
                return real_ip
            logging.error("[DNS] DoH de başarısız!")
            return normal_ip
        elif normal_ip:
            self._resolved_ip = normal_ip
            return normal_ip
        else:
            real_ip = self._resolve_via_doh(self.target_domain)
            if real_ip:
                self._resolved_ip = real_ip
                return real_ip
            return self.target_domain

    def _test_strategy(self, strategy_key: str, queue_num: int):
        if self.stop_event.is_set():
            return
        
        target_ip = self._resolved_ip
        if not target_ip or target_ip.startswith("0.") or target_ip == "127.0.0.1":
            return
        
        nfqws_proc = None
        rules_added = False
        
        try:
            logging.info(f"[{strategy_key}] Test: {self.target_domain} ({target_ip})")
            strategy_cmd = STRATEGIES[strategy_key]["cmd"]
            start_time = time.time()
            
            add_rule = [
                'iptables', '-t', 'mangle', '-I', 'OUTPUT',
                '-p', 'tcp', '--dport', '443', '-d', target_ip,
                '-j', 'NFQUEUE', '--queue-num', str(queue_num), '--queue-bypass'
            ]
            result = subprocess.run(add_rule, capture_output=True, text=True)
            if result.returncode != 0:
                return
            rules_added = True
            
            base_cmd = [NFQWS_PATH, f'--qnum={queue_num}']
            strategy_args = shlex.split(strategy_cmd)
            nfqws_cmd = base_cmd + strategy_args
            
            nfqws_proc = subprocess.Popen(
                nfqws_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            time.sleep(0.5)
            
            if nfqws_proc.poll() is not None:
                return
            
            success = self._make_request_with_ip(target_ip)
            duration = time.time() - start_time
            
            if success:
                logging.info(f"[{strategy_key}] ✓ BAŞARILI ({duration:.2f}s)")
                with self.lock:
                    if not self.winner_strategy:
                        self.winner_strategy = strategy_key
                        self.stop_event.set()
            else:
                logging.info(f"[{strategy_key}] ✗ Başarısız ({duration:.2f}s)")
                
        except Exception as e:
            logging.error(f"[{strategy_key}] Hata: {e}")
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
                    '-p', 'tcp', '--dport', '443', '-d', target_ip,
                    '-j', 'NFQUEUE', '--queue-num', str(queue_num), '--queue-bypass'
                ]
                subprocess.run(del_rule, capture_output=True)

    def _make_request_with_ip(self, ip: str) -> bool:
        try:
            resp = requests.get(
                f"https://{ip}",
                headers={"Host": self.target_domain, "User-Agent": USER_AGENT},
                timeout=PROBE_TIMEOUT, verify=False, allow_redirects=True
            )
            return resp.status_code < 400
        except:
            return False

    def solve(self) -> Optional[str]:
        logging.info(f"[PROBER] {len(PRIORITY_LIST)} strateji test ediliyor: {self.target_domain}")
        
        ip = self._resolve_domain()
        logging.info(f"[PROBER] Resolved: {self.target_domain} -> {ip}")
        
        if ip.startswith("0.") or ip == "127.0.0.1":
            logging.error("[PROBER] DNS zehirlenmesi atlanamadı!")
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
        logging.info(f"[PROBER] Bitti: {total_time:.2f}s, Kazanan: {self.winner_strategy}")
        
        if self.enable_telemetry and self.tracker:
            success = self.winner_strategy is not None
            strategy = self.winner_strategy or "none"
            latency_ms = int(total_time * 1000)
            self.tracker.log_bypass(self.target_domain, strategy, success, latency_ms)
        
        return self.winner_strategy
