"""
The Sentinel - Self-Healing Watchdog
Monitors system health and auto-repairs issues
"""
import os
import subprocess
import logging
import time
from pathlib import Path

class Sentinel:
    def __init__(self):
        self.check_interval = 3600  # 1 hour
        self.kernel_version_file = '/tmp/zapret_kernel_version'
    
    def check_kernel_update(self) -> bool:
        """Detect if kernel was updated."""
        current_kernel = subprocess.check_output(['uname', '-r'], text=True).strip()
        
        if os.path.exists(self.kernel_version_file):
            with open(self.kernel_version_file, 'r') as f:
                old_kernel = f.read().strip()
            
            if old_kernel != current_kernel:
                logging.warning(f"Kernel updated: {old_kernel} -> {current_kernel}")
                return True
        
        # Save current kernel
        with open(self.kernel_version_file, 'w') as f:
            f.write(current_kernel)
        
        return False
    
    def check_dependencies(self) -> bool:
        """Verify critical dependencies are present."""
        try:
            import netfilterqueue
            import scapy
            return True
        except ImportError as e:
            logging.error(f"Missing dependency: {e}")
            return False
    
    def check_service_health(self) -> bool:
        """Check if main service is running."""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'zapret-autonomous'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def check_internet(self) -> bool:
        """Basic internet connectivity check."""
        try:
            subprocess.run(
                ['ping', '-c', '1', '-W', '2', '8.8.8.8'],
                capture_output=True,
                timeout=3,
                check=True
            )
            return True
        except:
            return False
    
    def repair_dependencies(self):
        """Auto-reinstall missing dependencies."""
        logging.warning("Attempting to repair dependencies...")
        try:
            subprocess.run([
                'pip3', 'install', '-r', 'requirements.txt'
            ], check=True)
            logging.info("✓ Dependencies repaired")
        except Exception as e:
            logging.error(f"Failed to repair: {e}")
    
    def restart_service(self):
        """Restart the main service."""
        logging.warning("Restarting zapret-autonomous service...")
        try:
            subprocess.run(['systemctl', 'restart', 'zapret-autonomous'], check=True)
            logging.info("✓ Service restarted")
        except Exception as e:
            logging.error(f"Failed to restart: {e}")
    
    def patrol(self):
        """Main watchdog loop."""
        logging.info("Sentinel watchdog started. Patrol interval: 1 hour")
        
        while True:
            try:
                # Check 1: Kernel update
                if self.check_kernel_update():
                    logging.warning("Kernel change detected. May need nfqueue rebuild.")
                
                # Check 2: Dependencies
                if not self.check_dependencies():
                    self.repair_dependencies()
                
                # Check 3: Service health
                if not self.check_service_health():
                    logging.warning("Service is down!")
                    self.restart_service()
                
                # Check 4: Internet connectivity
                if not self.check_internet():
                    logging.warning("No internet connectivity. Skipping checks.")
                
                time.sleep(self.check_interval)
            
            except KeyboardInterrupt:
                logging.info("Sentinel shutdown")
                break
            except Exception as e:
                logging.error(f"Sentinel error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [SENTINEL] - %(levelname)s - %(message)s'
    )
    
    sentinel = Sentinel()
    sentinel.patrol()
