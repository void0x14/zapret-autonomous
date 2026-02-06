"""
Universal Bootstrapper - The "God Mode" Installer
Autonomous, self-healing, multi-distro setup system
"""
import sys
import os
import logging
import argparse
import time
import shutil
from installer.distro_detector import DistroDetector
from installer.package_manager import PackageManager
from installer.sensei_logger import SenseiLogger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SETUP] - %(levelname)s - %(message)s'
)

class UniversalBootstrapper:
    SYSTEM_DEPS = {
        'arch': ['base-devel', 'libnetfilter_queue', 'libmnl', 'zlib', 'libcap', 'iptables-nft', 'ipset'],
        'debian': ['build-essential', 'libnetfilter-queue-dev', 'libnetfilter-queue1', 'libmnl-dev', 'zlib1g-dev', 'libcap-dev', 'iptables', 'ipset'],
        'fedora': ['gcc', 'make', 'libnetfilter_queue-devel', 'libmnl-devel', 'zlib-devel', 'libcap-devel', 'iptables', 'ipset'],
        'alpine': ['build-base', 'libnetfilter_queue-dev', 'libmnl-dev', 'zlib-dev', 'libcap-dev', 'iptables', 'ipset'],
        'void': ['base-devel', 'libnetfilter_queue-devel', 'libmnl-devel', 'zlib-devel', 'libcap-devel', 'iptables', 'ipset'],
        'slackware': ['libnetfilter_queue', 'iptables', 'ipset']
    }

    def __init__(self, mode: str = 'safe'):
        self.mode = mode
        self.sensei = SenseiLogger()
        self.distro = None
        self.pkg_mgr = None
    
    def check_root(self):
        """Verify root privileges."""
        if os.geteuid() != 0:
            logging.error("This installer requires root privileges")
            logging.info("Please run: sudo python3 setup.py")
            sys.exit(1)
    
    def detect_distro(self):
        """Detect Linux distribution."""
        logging.info("Detecting your Linux distribution...")
        self.distro = DistroDetector.detect()
        
        if not self.distro:
            logging.error("Could not detect your distribution!")
            logging.error("Supported: Arch, Debian, Fedora, Alpine, Void, Slackware")
            sys.exit(1)
        
        logging.info(f"✓ Detected: {self.distro.name} ({self.distro.family})")
        self.sensei.log_distro_detection(self.distro.name, "/etc/os-release")
        
        self.pkg_mgr = PackageManager(self.distro.install_cmd, self.mode)
    
    def backup_firewall(self):
        """Backup existing firewall rules."""
        logging.info("Backing up existing firewall rules...")
        backup_dir = 'tmp/firewall_backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = int(time.time())
        try:
            # iptables backup
            if shutil.which('iptables-save'):
                with open(f"{backup_dir}/iptables_{timestamp}.bak", "w") as f:
                    import subprocess
                    subprocess.run(["iptables-save"], stdout=f)
            # nftables backup
            if shutil.which('nft'):
                with open(f"{backup_dir}/nftables_{timestamp}.bak", "w") as f:
                    import subprocess
                    subprocess.run(["nft", "list", "ruleset"], stdout=f)
            logging.info(f"✓ Firewall rules backed up to {backup_dir}")
        except Exception as e:
            logging.warning(f"Could not backup firewall rules: {e}")
    
    def install_system_dependencies(self):
        """Install system-level dependencies with smart detection."""
        deps = self.SYSTEM_DEPS.get(self.distro.family, self.SYSTEM_DEPS['arch'])
        
        # Smart detection: Check if binary exists before trying to install package
        filtered_deps = []
        for dep in deps:
            is_satisfied = False
            # Map packages to binary commands
            if dep in ['iptables', 'iptables-nft'] and shutil.which('iptables'):
                is_satisfied = True
            elif dep == 'ipset' and shutil.which('ipset'):
                is_satisfied = True
            elif dep in ['base-devel', 'build-essential', 'build-base']:
                # Check for gcc and make
                if shutil.which('gcc') and shutil.which('make'):
                    is_satisfied = True
            elif 'libnetfilter' in dep or 'libmnl' in dep or 'zlib' in dep or 'libcap' in dep:
                # Keep libraries as they are usually needed for building/linking
                is_satisfied = False
                
            if is_satisfied:
                logging.info(f"✓ Requirement '{dep}' already satisfied by existing system binary")
            else:
                filtered_deps.append(dep)
        
        if not filtered_deps:
            logging.info("✓ All system dependencies are already satisfied")
            return

        logging.info(f"Installing missing system dependencies: {', '.join(filtered_deps)}")
        
        for dep in filtered_deps:
            self.sensei.log_package_install(
                package=dep,
                purpose=f"Required for packet manipulation and DPI bypass"
            )
        
        if self.mode == 'ask':
            response = input(f"Install {len(filtered_deps)} packages? [Y/n]: ")
            if response.lower() == 'n':
                logging.info("Installation cancelled by user")
                sys.exit(0)
        
        success = self.pkg_mgr.install(filtered_deps)
        if not success:
            logging.error("Failed to install system dependencies")
            sys.exit(1)
    
    def install_python_dependencies(self):
        """Install Python dependencies with PEP 668 handling."""
        logging.info("Installing Python dependencies...")
        
        base_cmd = [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt']
        
        try:
            import subprocess
            # Try standard installation first
            subprocess.check_output(base_cmd, stderr=subprocess.STDOUT)
            logging.info("✓ Python dependencies installed")
        except subprocess.CalledProcessError as e:
            output = e.output.decode() if e.output else ""
            
            # Check for PEP 668: externally-managed-environment
            if "externally-managed-environment" in output or "PEP 668" in output:
                logging.warning("Detected externally managed Python environment (PEP 668)")
                
                if self.mode in ['god', 'ask']:
                    if self.mode == 'ask':
                        response = input("System blocks pip install. Override with --break-system-packages? [y/N]: ")
                        if response.lower() != 'y':
                            logging.error("Installation aborted by user due to PEP 668")
                            sys.exit(1)
                    
                    logging.info("Retrying with --break-system-packages...")
                    try:
                        subprocess.check_call(base_cmd + ['--break-system-packages'])
                        logging.info("✓ Python dependencies installed (overridden)")
                        return
                    except Exception as err:
                        logging.error(f"Failed even with override: {err}")
                        sys.exit(1)
                else:
                    logging.error("System blocks pip install. Run in --mode=god or --mode=ask to override.")
                    sys.exit(1)
            
            logging.error(f"Failed to install Python deps: {output}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error installing Python deps: {e}")
    
    def compile_nfqws(self):
        """Compile nfqws from source and install to /usr/bin."""
        import subprocess
        
        # Check if already installed
        if shutil.which('nfqws'):
            logging.info("✓ nfqws binary already installed")
            return
        
        logging.info("Compiling nfqws from source...")
        
        # Check if nfq directory exists
        nfq_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nfq')
        if not os.path.exists(nfq_dir):
            logging.error("nfq source directory not found!")
            sys.exit(1)
        
        try:
            # Clean and compile
            subprocess.run(['make', 'clean'], cwd=nfq_dir, capture_output=True)
            result = subprocess.run(['make'], cwd=nfq_dir, capture_output=True, text=True)
            
            if result.returncode != 0:
                logging.error(f"Compilation failed: {result.stderr}")
                sys.exit(1)
            
            # Find compiled binary
            binaries_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'binaries', 'my')
            nfqws_path = os.path.join(binaries_dir, 'nfqws')
            
            # Also check directly in nfq folder
            if not os.path.exists(nfqws_path):
                nfqws_path = os.path.join(nfq_dir, 'nfqws')
            
            if not os.path.exists(nfqws_path):
                logging.error("nfqws binary not found after compilation!")
                logging.error("Try running manually: cd nfq && make")
                sys.exit(1)
            
            # Install to /usr/bin
            target_path = '/usr/bin/nfqws'
            shutil.copy2(nfqws_path, target_path)
            os.chmod(target_path, 0o755)
            
            logging.info(f"✓ nfqws installed to {target_path}")
            self.sensei.log_action(
                action="Compiled and installed nfqws binary",
                reason="Required for packet manipulation and DPI bypass",
                learn_more="nfqws uses NFQUEUE to intercept and modify packets"
            )
        except FileNotFoundError:
            logging.error("'make' not found. Install build tools first.")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Failed to compile nfqws: {e}")
            sys.exit(1)
    
    def setup_service(self):
        """Create systemd service for auto-start."""
        logging.info("Setting up systemd services...")
        
        # Main service
        service_content = f"""[Unit]
Description=Zapret Autonomous Anti-Censorship Service
After=network.target

[Service]
Type=simple
ExecStart={sys.executable} {os.path.abspath('autonomous_zapret.py')}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        # Sentinel service
        sentinel_content = f"""[Unit]
Description=Zapret Sentinel (Self-Healing Watchdog)
After=network.target zapret-autonomous.service

[Service]
Type=simple
ExecStart={sys.executable} {os.path.abspath('sentinel.py')}
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
"""
        
        try:
            # Install main service
            with open('/etc/systemd/system/zapret-autonomous.service', 'w') as f:
                f.write(service_content)
            
            # Install sentinel service
            with open('/etc/systemd/system/zapret-sentinel.service', 'w') as f:
                f.write(sentinel_content)
            
            import subprocess
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', 'zapret-autonomous'], check=True)
            subprocess.run(['systemctl', 'enable', 'zapret-sentinel'], check=True)
            
            logging.info("✓ Services installed and enabled")
            self.sensei.log_action(
                action="Created systemd services (main + sentinel)",
                reason="Ensures Zapret starts automatically on boot and the Sentinel monitors system health",
                learn_more="systemd is the init system used by most modern Linux distributions"
            )
        except Exception as e:
            logging.warning(f"Could not setup services: {e}")
    
    def run(self):
        """Main installation workflow."""
        print("=" * 60)
        print("  ZAPRET AUTONOMOUS - Universal Installer")
        print(f"  Mode: {self.mode.upper()}")
        print("=" * 60)
        print()
        
        self.check_root()
        self.detect_distro()
        self.backup_firewall()
        self.install_system_dependencies()
        self.compile_nfqws()
        self.install_python_dependencies()
        self.setup_service()
        
        print()
        print("=" * 60)
        print("  ✓ Installation Complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Bypass: sudo python3 zapret-cli.py twitter.com youtube.com")
        print("  2. Status: sudo python3 zapret-cli.py status")
        print("  3. Service: sudo systemctl start zapret-autonomous")
        print()
        print(f"Learn more: Check {self.sensei.log_file}")

def main():
    parser = argparse.ArgumentParser(description='Zapret Autonomous Installer')
    parser.add_argument(
        '--mode',
        choices=['god', 'safe', 'ask'],
        default='safe',
        help='Installation mode (god=full auto, safe=retry only, ask=interactive)'
    )
    
    args = parser.parse_args()
    
    installer = UniversalBootstrapper(mode=args.mode)
    installer.run()

if __name__ == '__main__':
    main()
