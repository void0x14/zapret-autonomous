"""
Universal Bootstrapper - The "God Mode" Installer
Autonomous, self-healing, multi-distro setup system
"""
import sys
import os
import logging
import argparse
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
        'arch': ['libnetfilter_queue', 'iptables', 'ipset'],
        'debian': ['libnetfilter-queue-dev', 'libnetfilter-queue1', 'iptables', 'ipset'],
        'fedora': ['libnetfilter_queue-devel', 'iptables', 'ipset'],
        'alpine': ['libnetfilter_queue-dev', 'iptables', 'ipset'],
        'void': ['libnetfilter_queue-devel', 'iptables', 'ipset'],
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
    
    def install_system_dependencies(self):
        """Install system-level dependencies."""
        deps = self.SYSTEM_DEPS.get(self.distro.family, self.SYSTEM_DEPS['arch'])
        
        logging.info(f"Installing system dependencies: {', '.join(deps)}")
        
        for dep in deps:
            self.sensei.log_package_install(
                package=dep,
                purpose=f"Required for packet manipulation and DPI bypass"
            )
        
        if self.mode == 'ask':
            response = input(f"Install {len(deps)} packages? [Y/n]: ")
            if response.lower() == 'n':
                logging.info("Installation cancelled by user")
                sys.exit(0)
        
        success = self.pkg_mgr.install(deps)
        if not success:
            logging.error("Failed to install system dependencies")
            sys.exit(1)
    
    def install_python_dependencies(self):
        """Install Python dependencies."""
        logging.info("Installing Python dependencies...")
        
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            logging.info("✓ Python dependencies installed")
        except Exception as e:
            logging.error(f"Failed to install Python deps: {e}")
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
        self.install_system_dependencies()
        self.install_python_dependencies()
        self.setup_service()
        
        print()
        print("=" * 60)
        print("  ✓ Installation Complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Test: python3 simulate_block.py")
        print("  2. Start: sudo systemctl start zapret-autonomous")
        print("  3. Check: sudo systemctl status zapret-autonomous")
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
