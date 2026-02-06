#!/usr/bin/env python3
"""
Zapret CLI - Simple command-line interface for DPI bypass
Usage:
    sudo python3 zapret-cli.py turbo.cr jpg6.su        # Bypass (auto-detect)
    sudo python3 zapret-cli.py -f turbo.cr             # Fresh probe
    sudo python3 zapret-cli.py status
    sudo python3 zapret-cli.py stop
"""
import sys
import os
import logging
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [ZAPRET] - %(levelname)s - %(message)s'
)

def check_root():
    if os.geteuid() != 0:
        print("❌ This tool requires root privileges.")
        print("   Run: sudo python3 zapret-cli.py <command>")
        sys.exit(1)

def is_domain(arg: str) -> bool:
    """Check if argument looks like a domain name."""
    return '.' in arg and not arg.startswith('-') and arg not in ['status', 'stop', 'test', 'clear', 'bypass']

def cmd_bypass(domains: list, fresh: bool = False):
    """Find working strategy and apply bypass for given domains."""
    from core.db import StrategyDB
    from core.strategy_applicator import get_applicator
    from solver.parallel_prober import ParallelProber
    
    db = StrategyDB()
    applicator = get_applicator()
    
    # If fresh mode, clear old strategies for these domains
    if fresh:
        print("[FRESH] Clearing cached strategies and re-probing...")
        for domain in domains:
            db.delete_strategy(domain)
    
    for domain in domains:
        print(f"\n{'='*50}")
        print(f"  Processing: {domain}")
        print(f"{'='*50}")
        
        # Check DB first (unless fresh mode)
        cached_strategy = None if fresh else db.get_strategy(domain)
        
        if cached_strategy:
            print(f"[CACHE] Found saved strategy: {cached_strategy}")
            strategy = cached_strategy
        else:
            print(f"[PROBE] Testing strategies for {domain}...")
            prober = ParallelProber(domain)
            strategy = prober.solve()
            
            if strategy:
                db.save_strategy(domain, strategy)
                print(f"[SAVE] Strategy '{strategy}' saved to database")
            else:
                print(f"[FAIL] No working strategy found for {domain}")
                continue
        
        # Apply the strategy
        print(f"[APPLY] Activating bypass with strategy: {strategy}")
        if applicator.apply(strategy, [domain]):
            print(f"✓ Bypass ACTIVE for {domain}")
        else:
            print(f"✗ Failed to apply bypass")
    
    if not applicator.is_active():
        print("\n❌ No bypass is active. Check the logs above.")
        return
    
    print(f"\n{'='*50}")
    print("  ✓ Bypass is now ACTIVE!")
    print("  nfqws runs in background. Terminal released.")
    print(f"{'='*50}")
    print("\nCommands:")
    print("  sudo python3 zapret-cli.py status  - Check status")
    print("  sudo python3 zapret-cli.py stop    - Stop bypass")

def cmd_status():
    """Show current bypass status."""
    print(f"\n{'='*50}")
    print("  ZAPRET AUTONOMOUS - STATUS")
    print(f"{'='*50}")
    
    # Check nfqws process directly
    result = subprocess.run(['pgrep', '-a', 'nfqws'], capture_output=True, text=True)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        print(f"  Active: ✓ YES")
        print(f"  nfqws Processes: {len(lines)}")
        for line in lines:
            print(f"    {line}")
    else:
        print(f"  Active: ✗ NO")
        print(f"  nfqws: Not running")
    
    # Check iptables rules
    result = subprocess.run(
        ['iptables', '-t', 'mangle', '-L', 'POSTROUTING', '-n'],
        capture_output=True, text=True
    )
    has_rules = 'NFQUEUE' in result.stdout
    print(f"  IPTables Rules: {'Applied' if has_rules else 'Not applied'}")
    
    # Show saved domains
    print(f"\n  Saved Strategies:")
    try:
        import sqlite3
        conn = sqlite3.connect('strategies.db')
        cursor = conn.cursor()
        cursor.execute("SELECT domain, strategy FROM domains LIMIT 10")
        rows = cursor.fetchall()
        for domain, strategy in rows:
            print(f"    - {domain}: {strategy}")
        if not rows:
            print("    (none)")
        conn.close()
    except:
        print("    (none)")
    
    print(f"{'='*50}\n")

def cmd_stop():
    """Stop running bypass."""
    print("[STOP] Stopping nfqws processes...")
    
    # Kill all nfqws processes
    subprocess.run(['pkill', '-9', 'nfqws'], capture_output=True)
    
    # Remove iptables rules
    print("[STOP] Removing iptables rules...")
    subprocess.run([
        'iptables', '-t', 'mangle', '-D', 'POSTROUTING',
        '-p', 'tcp', '-m', 'multiport', '--dports', '80,443',
        '-m', 'connbytes', '--connbytes-dir=original', '--connbytes-mode=packets', '--connbytes', '1:6',
        '-m', 'mark', '!', '--mark', '0x40000000/0x40000000',
        '-j', 'NFQUEUE', '--queue-num', '200', '--queue-bypass'
    ], capture_output=True)
    
    subprocess.run([
        'iptables', '-t', 'mangle', '-D', 'POSTROUTING',
        '-p', 'udp', '--dport', '443',
        '-m', 'mark', '!', '--mark', '0x40000000/0x40000000',
        '-j', 'NFQUEUE', '--queue-num', '200', '--queue-bypass'
    ], capture_output=True)
    
    print("✓ Bypass stopped and rules cleaned up")

def cmd_test(domains: list):
    """Test if domains are accessible (without bypass)."""
    import requests
    import urllib3
    urllib3.disable_warnings()
    
    for domain in domains:
        try:
            url = f"https://{domain}"
            response = requests.get(url, timeout=10, verify=False)
            print(f"✓ {domain}: Accessible (HTTP {response.status_code})")
        except requests.exceptions.Timeout:
            print(f"✗ {domain}: TIMEOUT - Likely blocked")
        except requests.exceptions.SSLError as e:
            print(f"✗ {domain}: SSL Error - Possibly blocked")
        except requests.exceptions.ConnectionError:
            print(f"✗ {domain}: Connection Error - Blocked or down")
        except Exception as e:
            print(f"? {domain}: {e}")

def cmd_clear():
    """Clear all saved strategies from database."""
    try:
        os.remove('strategies.db')
        print("✓ Strategy database cleared")
    except FileNotFoundError:
        print("Database already empty")

def main():
    args = sys.argv[1:]
    
    if not args:
        print("""
Zapret Autonomous - DPI Bypass Tool

Usage:
  sudo python3 zapret-cli.py DOMAIN [DOMAIN...]     Bypass domains
  sudo python3 zapret-cli.py -f DOMAIN [DOMAIN...]  Bypass with fresh probe
  sudo python3 zapret-cli.py status                 Show status
  sudo python3 zapret-cli.py stop                   Stop bypass
  sudo python3 zapret-cli.py test DOMAIN            Test accessibility
  sudo python3 zapret-cli.py clear                  Clear saved strategies

Examples:
  sudo python3 zapret-cli.py turbo.cr jpg6.su
  sudo python3 zapret-cli.py -f twitter.com
  sudo python3 zapret-cli.py status
""")
        sys.exit(0)
    
    # Handle commands
    cmd = args[0]
    
    if cmd == 'status':
        check_root()
        cmd_status()
    elif cmd == 'stop':
        check_root()
        cmd_stop()
    elif cmd == 'clear':
        cmd_clear()
    elif cmd == 'test':
        if len(args) < 2:
            print("Usage: python3 zapret-cli.py test DOMAIN")
            sys.exit(1)
        cmd_test(args[1:])
    elif cmd == '-f' or cmd == '--fresh':
        # Fresh mode: -f domain1 domain2
        check_root()
        domains = [a for a in args[1:] if is_domain(a)]
        if not domains:
            print("Usage: sudo python3 zapret-cli.py -f DOMAIN [DOMAIN...]")
            sys.exit(1)
        cmd_bypass(domains, fresh=True)
    elif cmd == 'bypass':
        # Explicit bypass command
        check_root()
        fresh = '-f' in args or '--fresh' in args
        domains = [a for a in args[1:] if is_domain(a)]
        if not domains:
            print("Usage: sudo python3 zapret-cli.py bypass DOMAIN [DOMAIN...]")
            sys.exit(1)
        cmd_bypass(domains, fresh=fresh)
    elif is_domain(cmd):
        # Auto-detect: first arg is domain
        check_root()
        domains = [a for a in args if is_domain(a)]
        cmd_bypass(domains, fresh=False)
    else:
        print(f"Unknown command: {cmd}")
        print("Run without arguments for help.")
        sys.exit(1)

if __name__ == '__main__':
    main()
