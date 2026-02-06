"""
Universal Distro Detector
Supports: Arch/CachyOS, Debian/Ubuntu, Fedora, Alpine, Void, Slackware
"""
import os
import re
import subprocess
from typing import Optional, Dict

class DistroInfo:
    def __init__(self, name: str, family: str, pkg_manager: str, install_cmd: str):
        self.name = name
        self.family = family
        self.pkg_manager = pkg_manager
        self.install_cmd = install_cmd

class DistroDetector:
    DISTRO_SIGNATURES = {
        'arch': {
            'keywords': ['arch', 'cachy', 'manjaro', 'endeavour'],
            'pkg_manager': 'pacman',
            'install_cmd': 'pacman -S --noconfirm --ask=4'
        },
        'debian': {
            'keywords': ['debian', 'ubuntu', 'mint', 'pop'],
            'pkg_manager': 'apt',
            'install_cmd': 'apt-get install -y'
        },
        'fedora': {
            'keywords': ['fedora', 'rhel', 'centos', 'rocky'],
            'pkg_manager': 'dnf',
            'install_cmd': 'dnf install -y'
        },
        'alpine': {
            'keywords': ['alpine'],
            'pkg_manager': 'apk',
            'install_cmd': 'apk add --no-cache'
        },
        'void': {
            'keywords': ['void'],
            'pkg_manager': 'xbps',
            'install_cmd': 'xbps-install -y'
        },
        'slackware': {
            'keywords': ['slackware'],
            'pkg_manager': 'slackpkg',
            'install_cmd': 'slackpkg install'
        }
    }

    @staticmethod
    def detect() -> Optional[DistroInfo]:
        """Detect the current Linux distribution."""
        # Method 1: /etc/os-release (Standard)
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                for family, sig in DistroDetector.DISTRO_SIGNATURES.items():
                    for keyword in sig['keywords']:
                        if keyword in content:
                            return DistroInfo(
                                name=keyword.capitalize(),
                                family=family,
                                pkg_manager=sig['pkg_manager'],
                                install_cmd=sig['install_cmd']
                            )
        
        # Method 2: Kernel signatures (fallback)
        try:
            uname = subprocess.check_output(['uname', '-r'], text=True).lower()
            if 'arch' in uname or 'cachy' in uname:
                return DistroInfo('Arch', 'arch', 'pacman', 'pacman -S --noconfirm')
        except:
            pass
        
        # Method 3: Package manager presence
        for family, sig in DistroDetector.DISTRO_SIGNATURES.items():
            if subprocess.run(['which', sig['pkg_manager']], capture_output=True).returncode == 0:
                return DistroInfo(family.capitalize(), family, sig['pkg_manager'], sig['install_cmd'])
        
        return None
