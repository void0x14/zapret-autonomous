"""
Strategy Applicator - The Real Deal
Applies iptables rules and spawns nfqws process to actually bypass DPI
"""
import subprocess
import shutil
import logging
import os
import signal
import atexit
import shlex
import socket
import requests
from typing import Optional, List
from solver.heuristics import STRATEGIES

# Configuration
NFQUEUE_NUM = 200
NFQWS_PATH = shutil.which('nfqws') or '/usr/bin/nfqws'

class StrategyApplicator:
    """Manages iptables rules and nfqws process for actual DPI bypass."""
    
    def __init__(self):
        self.current_process = None
        self.applied_rules = []
        # Cleanup on exit
        atexit.register(self.stop)
    
    def apply(self, strategy_key: str, domains: List[str]) -> bool:
        """Apply a specific strategy for the given domains."""
        self.stop()  # Clean up existing
        
        logging.info(f"Applying strategy: {strategy_key} for {len(domains)} domains")
        
        if not self._apply_iptables(domains):
            logging.error("Failed to apply iptables rules")
            return False
            
        if not self._start_nfqws(strategy_key):
            logging.error("Failed to start nfqws")
            self._cleanup_iptables()
            return False
            
        return True
    
    def stop(self):
        """Stop current bypass (kill nfqws, remove rules)."""
        if self.current_process:
            logging.info("Stopping nfqws...")
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=2)
            except:
                self.current_process.kill()
            self.current_process = None
            logging.info("✓ nfqws stopped")
            
        self._cleanup_iptables()

    def _cleanup_iptables(self):
        """Remove all applied iptables rules."""
        if self.applied_rules:
            logging.info("Removing iptables rules...")
            for rule in reversed(self.applied_rules):
                subprocess.run(['iptables', '-t', 'mangle', '-D'] + rule, capture_output=True)
            self.applied_rules = []
            
            # Flush queue just in case
            subprocess.run(['iptables', '-t', 'mangle', '-D', 'POSTROUTING', 
                          '-p', 'tcp', '-m', 'multiport', '--dports', '80,443',
                          '-m', 'connbytes', '--connbytes-dir=original', '--connbytes-mode=packets', '--connbytes', '1:6',
                          '-m', 'mark', '!', '--mark', '0x40000000/0x40000000',
                          '-j', 'NFQUEUE', '--queue-num', str(NFQUEUE_NUM), '--queue-bypass'], 
                          capture_output=True)
            logging.info("✓ IPTables rules removed")

    def _resolve_ip(self, domain: str) -> Optional[str]:
        """Resolve IP with DoH fallback."""
        try:
            ip = socket.gethostbyname(domain)
            if not ip.startswith("0.") and ip != "127.0.0.1":
                return ip
        except:
            pass
            
        # DoH Fallback (Cloudflare)
        try:
            resp = requests.get(
                "https://cloudflare-dns.com/dns-query",
                params={"name": domain, "type": "A"},
                headers={"Accept": "application/dns-json"},
                timeout=5, verify=False
            )
            for ans in resp.json().get("Answer", []):
                if ans.get("type") == 1:
                    return ans.get("data")
        except:
            pass
        return None

    def _apply_iptables(self, domains: List[str]) -> bool:
        """Apply NFQUEUE rules for target domains."""
        try:
            # 1. Genel kural (POSTROUTING)
            # Bu kural tüm 80/443 trafiğini yakalamaz, sadece OUTPUT kurallarıyla eşleşenleri yakalamak için
            # Ancak zapret genellikle POSTROUTING'de genel bir hook ister.
            # Biz spesifik domain çalıştığımız için OUTPUT chain kullanacağız.
            
            # Öncelikle nfqws'in kendisine loop yapmasını engellemek için MARK kontrolü ekliyoruz.
            
            for domain in domains:
                # Resolve IP (DoH supported)
                ip = self._resolve_ip(domain)
                if not ip:
                    logging.warning(f"Could not resolve {domain}, skipping iptables rule")
                    continue
                
                logging.info(f"Adding rule for {domain} -> {ip}")
                
                # Rule: OUTPUT chain for specific destination IP
                # -p tcp --dport 443 -d <IP> -j NFQUEUE --queue-num 200
                rule = [
                    'OUTPUT',
                    '-p', 'tcp', '--dport', '443',
                    '-d', ip,
                    '-j', 'NFQUEUE', '--queue-num', str(NFQUEUE_NUM), '--queue-bypass'
                ]
                
                subprocess.run(['iptables', '-t', 'mangle', '-I'] + rule, check=True)
                self.applied_rules.append(rule)
                
            return len(self.applied_rules) > 0
            
        except subprocess.CalledProcessError as e:
            logging.error(f"IPTables error: {e}")
            return False

    def _start_nfqws(self, strategy_key: str) -> bool:
        """Start nfqws process with the given strategy."""
        if strategy_key not in STRATEGIES:
            logging.error(f"Unknown strategy: {strategy_key}")
            return False
            
        strategy_cmd = STRATEGIES[strategy_key]["cmd"]
        
        # Build nfqws command - properly parse strategy_cmd with shlex
        cmd = [NFQWS_PATH, f'--qnum={NFQUEUE_NUM}'] + shlex.split(strategy_cmd)
        
        logging.info(f"Starting nfqws: {' '.join(cmd)}")
        
        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True # Detach from terminal
            )
            return True
        except Exception as e:
            logging.error(f"Failed to start nfqws: {e}")
            return False
