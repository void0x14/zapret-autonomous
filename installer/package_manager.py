"""
Package Manager Abstraction Layer
Handles retries, lock resolution, and error recovery
"""
import subprocess
import time
import os
import logging
from typing import List, Optional

class PackageManager:
    def __init__(self, install_cmd: str, mode: str = 'safe'):
        self.install_cmd = install_cmd
        self.mode = mode  # 'god', 'safe', 'ask'
        self.max_retries = 3
        self.backoff_base = 2  # seconds
    
    def install(self, packages: List[str]) -> bool:
        """Install packages with retry logic."""
        for package in packages:
            success = self._install_single(package)
            if not success:
                logging.error(f"Failed to install {package} after {self.max_retries} attempts")
                return False
        return True
    
    def _install_single(self, package: str) -> bool:
        """Install a single package with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                logging.info(f"Installing {package} (attempt {attempt + 1}/{self.max_retries})...")
                
                # God mode: Try to fix locks before running
                if self.mode == 'god' and attempt > 0:
                    self._god_mode_fixes()
                
                cmd = f"{self.install_cmd} {package}"
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    logging.info(f"✓ {package} installed successfully")
                    return True
                else:
                    logging.warning(f"Install failed: {result.stderr}")
                    
                    # Exponential backoff
                    if attempt < self.max_retries - 1:
                        wait_time = self.backoff_base ** attempt
                        logging.info(f"Retrying in {wait_time}s...")
                        time.sleep(wait_time)
            
            except subprocess.TimeoutExpired:
                logging.error(f"Timeout installing {package}")
            except Exception as e:
                logging.error(f"Exception: {e}")
        
        return False
    
    def _god_mode_fixes(self):
        """Aggressive system fixes (God Mode only)."""
        if 'pacman' in self.install_cmd:
            # Remove pacman lock
            lock_file = '/var/lib/pacman/db.lck'
            if os.path.exists(lock_file):
                logging.warning(f"[GOD MODE] Removing {lock_file}")
                try:
                    os.remove(lock_file)
                except:
                    pass
        
        elif 'apt' in self.install_cmd:
            # Kill dpkg/apt processes
            logging.warning("[GOD MODE] Killing apt locks")
            subprocess.run("killall -9 apt apt-get dpkg", shell=True, capture_output=True)
            subprocess.run("rm -f /var/lib/dpkg/lock*", shell=True, capture_output=True)
