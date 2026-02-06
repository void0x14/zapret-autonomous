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
from typing import Optional, List
from solver.heuristics import STRATEGIES

# Configuration
NFQUEUE_NUM = 200
NFQWS_PATH = shutil.which('nfqws') or '/usr/bin/nfqws'

class StrategyApplicator:
    """Manages iptables rules and nfqws process for actual DPI bypass."""
    
    def __init__(self):
        self.nfqws_process: Optional[subprocess.Popen] = None
        self.active_strategy: Optional[str] = None
        self.rules_applied = False
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logging.info("Signal received, cleaning up...")
        self.cleanup()
    
    def _run_cmd(self, cmd: List[str], check: bool = True) -> bool:
        """Run a shell command."""
        try:
            logging.debug(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=check, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {' '.join(cmd)}\n{e.stderr}")
            return False
    
    def _add_iptables_rules(self, ports: List[int] = [80, 443]) -> bool:
        """Add iptables mangle rules to redirect traffic to NFQUEUE."""
        logging.info("Adding iptables rules for NFQUEUE...")
        
        ports_str = ','.join(map(str, ports))
        
        # TCP rule for HTTP/HTTPS
        tcp_rule = [
            'iptables', '-t', 'mangle', '-I', 'POSTROUTING',
            '-p', 'tcp', '-m', 'multiport', '--dports', ports_str,
            '-m', 'connbytes', '--connbytes-dir=original', '--connbytes-mode=packets', '--connbytes', '1:6',
            '-m', 'mark', '!', '--mark', '0x40000000/0x40000000',
            '-j', 'NFQUEUE', '--queue-num', str(NFQUEUE_NUM), '--queue-bypass'
        ]
        
        # UDP rule for QUIC (port 443)
        udp_rule = [
            'iptables', '-t', 'mangle', '-I', 'POSTROUTING',
            '-p', 'udp', '--dport', '443',
            '-m', 'mark', '!', '--mark', '0x40000000/0x40000000',
            '-j', 'NFQUEUE', '--queue-num', str(NFQUEUE_NUM), '--queue-bypass'
        ]
        
        success = self._run_cmd(tcp_rule) and self._run_cmd(udp_rule)
        if success:
            self.rules_applied = True
            logging.info("✓ IPTables rules applied")
        return success
    
    def _remove_iptables_rules(self) -> bool:
        """Remove the NFQUEUE rules we added."""
        if not self.rules_applied:
            return True
            
        logging.info("Removing iptables rules...")
        
        # Delete TCP rule
        tcp_del = [
            'iptables', '-t', 'mangle', '-D', 'POSTROUTING',
            '-p', 'tcp', '-m', 'multiport', '--dports', '80,443',
            '-m', 'connbytes', '--connbytes-dir=original', '--connbytes-mode=packets', '--connbytes', '1:6',
            '-m', 'mark', '!', '--mark', '0x40000000/0x40000000',
            '-j', 'NFQUEUE', '--queue-num', str(NFQUEUE_NUM), '--queue-bypass'
        ]
        
        # Delete UDP rule
        udp_del = [
            'iptables', '-t', 'mangle', '-D', 'POSTROUTING',
            '-p', 'udp', '--dport', '443',
            '-m', 'mark', '!', '--mark', '0x40000000/0x40000000',
            '-j', 'NFQUEUE', '--queue-num', str(NFQUEUE_NUM), '--queue-bypass'
        ]
        
        # Try to delete, ignore errors (rule might not exist)
        self._run_cmd(tcp_del, check=False)
        self._run_cmd(udp_del, check=False)
        self.rules_applied = False
        logging.info("✓ IPTables rules removed")
        return True
    
    def _start_nfqws(self, strategy_key: str) -> bool:
        """Start nfqws process with the given strategy."""
        if strategy_key not in STRATEGIES:
            logging.error(f"Unknown strategy: {strategy_key}")
            return False
        
        if not os.path.exists(NFQWS_PATH):
            logging.error(f"nfqws binary not found at {NFQWS_PATH}")
            return False
        
        strategy_cmd = STRATEGIES[strategy_key]["cmd"]
        
        # Build nfqws command
        cmd = [
            NFQWS_PATH,
            f'--qnum={NFQUEUE_NUM}',
            strategy_cmd
        ]
        
        logging.info(f"Starting nfqws with strategy '{strategy_key}': {' '.join(cmd)}")
        
        try:
            self.nfqws_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.active_strategy = strategy_key
            logging.info(f"✓ nfqws started (PID: {self.nfqws_process.pid})")
            return True
        except Exception as e:
            logging.error(f"Failed to start nfqws: {e}")
            return False
    
    def _stop_nfqws(self) -> bool:
        """Stop the nfqws process."""
        if self.nfqws_process:
            logging.info("Stopping nfqws...")
            try:
                self.nfqws_process.terminate()
                self.nfqws_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.nfqws_process.kill()
            self.nfqws_process = None
            self.active_strategy = None
            logging.info("✓ nfqws stopped")
        return True
    
    def apply(self, strategy_key: str) -> bool:
        """Apply a bypass strategy to the system."""
        logging.info(f"Applying strategy: {strategy_key}")
        
        # Stop any existing process
        self._stop_nfqws()
        
        # Add iptables rules (if not already)
        if not self.rules_applied:
            if not self._add_iptables_rules():
                return False
        
        # Start nfqws
        return self._start_nfqws(strategy_key)
    
    def is_active(self) -> bool:
        """Check if bypass is currently active."""
        if self.nfqws_process:
            return self.nfqws_process.poll() is None
        return False
    
    def get_status(self) -> dict:
        """Get current bypass status."""
        return {
            "active": self.is_active(),
            "strategy": self.active_strategy,
            "nfqws_pid": self.nfqws_process.pid if self.nfqws_process else None,
            "rules_applied": self.rules_applied
        }
    
    def cleanup(self):
        """Clean up all resources."""
        self._stop_nfqws()
        self._remove_iptables_rules()


# Singleton instance
_applicator: Optional[StrategyApplicator] = None

def get_applicator() -> StrategyApplicator:
    global _applicator
    if _applicator is None:
        _applicator = StrategyApplicator()
    return _applicator
