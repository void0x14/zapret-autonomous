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

PROBE_TIMEOUT = 5.0
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
        
        # TurkNet + NextDNS kullanıcısı için:
        # Önce sistem DNS'ine güven, sadece zehirlenme varsa DoH yap.
        self._resolved_ip = self._resolve_domain()

    def _resolve_domain(self) -> str:
        """Sistem DNS'ini kullan. Sadece 0.0.0.0 dönerse Cloudflare DoH dene."""
        try:
            # 1. Sistem DNS (NextDNS DoT)
            ip = socket.gethostbyname(self.target_domain)
            if not ip.startswith("0.") and ip != "127.0.0.1":
                logging.info(f"[DNS] Sistem Çözümü: {self.target_domain} -> {ip}")
                return ip
        except Exception as e:
            logging.debug(f"[DNS] Sistem hatası: {e}")
        
        # 2. Zehirlenme varsa DoH Fallback
        logging.warning("[DNS] Sistem başarısız/zehirli, DoH deneniyor...")
        try:
            resp = requests.get(
                "https://cloudflare-dns.com/dns-query",
                params={"name": self.target_domain, "type": "A"},
                headers={"Accept": "application/dns-json"},
                timeout=5, verify=False
            )
            for ans in resp.json().get("Answer", []):
                if ans.get("type") == 1:
                    return ans.get("data")
        except:
            pass
            
        return self.target_domain

    def _test_strategy(self, strategy_key: str, queue_num: int):
        if self.stop_event.is_set(): return
        
        # IP kontrolü
        if not self._resolved_ip or self._resolved_ip.startswith("0."):
            return
            
        nfqws_proc = None
        rules_added = False
        
        try:
            strategy_cmd = STRATEGIES[strategy_key]["cmd"]
            start_time = time.time()
            
            # iptables
            add_rule = [
                'iptables', '-t', 'mangle', '-I', 'OUTPUT',
                '-p', 'tcp', '--dport', '443', '-d', self._resolved_ip,
                '-j', 'NFQUEUE', '--queue-num', str(queue_num), '--queue-bypass'
            ]
            
            if subprocess.run(add_rule, capture_output=True).returncode == 0:
                rules_added = True
            else:
                return

            # nfqws start
            cmd = [NFQWS_PATH, f'--qnum={queue_num}'] + shlex.split(strategy_cmd)
            nfqws_proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                start_new_session=True
            )
            time.sleep(0.4) # Faster check
            
            if nfqws_proc.poll() is not None:
                return
            
            # Request
            if self._make_request_with_ip(self._resolved_ip):
                duration = time.time() - start_time
                logging.info(f"[{strategy_key}] ✓ BAŞARILI ({duration:.2f}s)")
                with self.lock:
                    if not self.winner_strategy:
                        self.winner_strategy = strategy_key
                        self.stop_event.set()
            else:
                logging.debug(f"[{strategy_key}] ✗ Request failed")
                
        except Exception as e:
            logging.debug(f"[{strategy_key}] Exception: {e}")
        finally:
            if nfqws_proc:
                nfqws_proc.terminate()
                try: nfqws_proc.wait(timeout=1)
                except: nfqws_proc.kill()
            if rules_added:
                del_rule = [
                    'iptables', '-t', 'mangle', '-D', 'OUTPUT',
                    '-p', 'tcp', '--dport', '443', '-d', self._resolved_ip,
                    '-j', 'NFQUEUE', '--queue-num', str(queue_num), '--queue-bypass'
                ]
                subprocess.run(del_rule, capture_output=True)

    def _make_request_with_ip(self, ip: str) -> bool:
        try:
            # TurkNet bazen User-Agent filtering yapabilir mi? Sanmam ama standart tutalım.
            resp = requests.get(
                f"https://{ip}",
                headers={"Host": self.target_domain, "User-Agent": "curl/7.68.0"},
                timeout=PROBE_TIMEOUT, verify=False, allow_redirects=True
            )
            # 403 Forbidden bile olsa, bağlantı kuruldu demektir (Cloudflare block page)
            # Bu yüzden status code kontrolünü esnetiyoruz.
            # TCP bağlantısı kurulduysa ve SSL handshake bittiyse bypass çalışmıştır.
            return True
        except requests.exceptions.SSLError:
            # SSL hatası = DPI Araya girdi (Fail)
            return False
        except requests.exceptions.ConnectionError:
            # Bağlantı koptu = Fail
            return False
        except:
            return False

    def solve(self) -> Optional[str]:
        logging.info(f"[PROBER] TurkNet/NextDNS Modu: {self.target_domain}")
        logging.info(f"[DNS] Hedef IP: {self._resolved_ip}")
        
        threads = []
        for idx, strategy in enumerate(PRIORITY_LIST):
            queue_num = TEST_QUEUE_BASE + idx
            t = threading.Thread(target=self._test_strategy, args=(strategy, queue_num))
            t.start()
            threads.append(t)
            
        for t in threads:
            t.join(timeout=PROBE_TIMEOUT + 1)
            
        logging.info(f"[PROBER] Kazanan: {self.winner_strategy}")
        return self.winner_strategy
