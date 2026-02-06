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

PROBE_TIMEOUT = 8.0
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
        """DoH ile IP çöz (Cloudflare & Google)."""
        providers = [
            ("Cloudflare", "https://cloudflare-dns.com/dns-query"),
            ("Google", "https://dns.google/resolve")
        ]
        
        for name, url in providers:
            try:
                logging.debug(f"[DoH] {name} ile çözülüyor: {domain}")
                resp = requests.get(
                    url,
                    params={"name": domain, "type": "A"},
                    headers={"Accept": "application/dns-json"},
                    timeout=5, verify=False
                )
                data = resp.json()
                if "Answer" in data:
                    for ans in data["Answer"]:
                        if ans.get("type") == 1:
                            ip = ans.get("data")
                            if ip and not ip.startswith("0.") and ip != "127.0.0.1":
                                logging.info(f"[DoH] ✓ {name}: {domain} -> {ip}")
                                return ip
            except Exception as e:
                logging.debug(f"[DoH] {name} hata: {e}")
        return None

    def _resolve_domain(self) -> str:
        """Domain çözümle - Zehirlenme kontrolü yap."""
        if self._resolved_ip: return self._resolved_ip
        
        # 1. Normal DNS
        try:
            ip = socket.gethostbyname(self.target_domain)
            if not ip.startswith("0.") and ip != "127.0.0.1":
                self._resolved_ip = ip
                return ip
            logging.warning(f"[DNS] Zehirlenme: {self.target_domain} -> {ip}")
        except:
            pass
            
        # 2. DoH Fallback
        real_ip = self._resolve_via_doh(self.target_domain)
        if real_ip:
            self._resolved_ip = real_ip
            return real_ip
            
        return self.target_domain

    def _test_strategy(self, strategy_key: str, queue_num: int):
        if self.stop_event.is_set(): return
        
        target_ip = self._resolve_domain()
        if not target_ip or target_ip.startswith("0."): return
        
        nfqws_proc = None
        rules_added = False
        
        try:
            strategy_cmd = STRATEGIES[strategy_key]["cmd"]
            start_time = time.time()
            
            # iptables
            add_rule = [
                'iptables', '-t', 'mangle', '-I', 'OUTPUT',
                '-p', 'tcp', '--dport', '443', '-d', target_ip,
                '-j', 'NFQUEUE', '--queue-num', str(queue_num), '--queue-bypass'
            ]
            if subprocess.run(add_rule, capture_output=True).returncode == 0:
                rules_added = True
            else:
                return

            # nfqws (SHLEX FIX)
            cmd = [NFQWS_PATH, f'--qnum={queue_num}'] + shlex.split(strategy_cmd)
            nfqws_proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
            )
            time.sleep(0.5)
            
            # Test Connection
            if self._make_request_with_ip(target_ip):
                duration = time.time() - start_time
                logging.info(f"[{strategy_key}] ✓ BAŞARILI ({duration:.2f}s)")
                with self.lock:
                    if not self.winner_strategy:
                        self.winner_strategy = strategy_key
                        self.stop_event.set()
            else:
                pass
                
        except Exception:
            pass
        finally:
            if nfqws_proc:
                nfqws_proc.terminate()
                try: nfqws_proc.wait(timeout=1)
                except: nfqws_proc.kill()
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
        logging.info(f"[PROBER] {self.target_domain} için test başlıyor...")
        if not self._resolve_domain():
            logging.error("[PROBER] IP çözülemedi!")
            return None
            
        threads = []
        for idx, strategy in enumerate(PRIORITY_LIST):
            queue_num = TEST_QUEUE_BASE + idx
            t = threading.Thread(target=self._test_strategy, args=(strategy, queue_num))
            t.start()
            threads.append(t)
            
        for t in threads:
            t.join(timeout=PROBE_TIMEOUT + 2)
            
        logging.info(f"[PROBER] Sonuç: {self.winner_strategy}")
        return self.winner_strategy
