"""
Educational Logger - "The Sensei"
Logs every action with WHY explanations and learning resources
"""
import logging
from datetime import datetime

class SenseiLogger:
    def __init__(self, log_file: str = "learn_log.md"):
        self.log_file = log_file
        self._init_log()
    
    def _init_log(self):
        """Initialize the learning log."""
        with open(self.log_file, 'w') as f:
            f.write(f"# Zapret Learning Log\n")
            f.write(f"**Started:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("This log explains every action the system takes and why.\n\n")
            f.write("---\n\n")
    
    def log_action(self, action: str, reason: str, learn_more: str = ""):
        """Log an action with educational context."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        entry = f"## [{timestamp}] {action}\n\n"
        entry += f"**Why:** {reason}\n\n"
        
        if learn_more:
            entry += f"**Learn More:** {learn_more}\n\n"
        
        entry += "---\n\n"
        
        with open(self.log_file, 'a') as f:
            f.write(entry)
        
        # Also log to console
        logging.info(f"[SENSEI] {action}")
    
    def log_distro_detection(self, distro_name: str, method: str):
        """Log distribution detection."""
        self.log_action(
            action=f"Detected Distribution: {distro_name}",
            reason=f"Used {method} to identify your Linux distribution. This helps choose the correct package manager.",
            learn_more="Linux distributions use different package managers (pacman, apt, dnf, etc.). Auto-detection ensures compatibility."
        )
    
    def log_package_install(self, package: str, purpose: str):
        """Log package installation."""
        self.log_action(
            action=f"Installing: {package}",
            reason=purpose,
            learn_more=f"Package '{package}' provides system libraries needed for packet manipulation."
        )
    
    def log_god_mode_action(self, action: str, risk: str):
        """Log risky God Mode actions."""
        self.log_action(
            action=f"[GOD MODE] {action}",
            reason=f"System was locked/blocked. Took aggressive action to proceed. Risk: {risk}",
            learn_more="God Mode bypasses safety checks. Use only when you understand the implications."
        )
