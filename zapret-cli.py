#!/usr/bin/env python3
"""
Zapret CLI - Simple command-line interface for DPI bypass
Usage:
    sudo python3 zapret-cli.py turbo.cr jpg6.su        # Bypass & daemonize
    sudo python3 zapret-cli.py status
    sudo python3 zapret-cli.py stop
"""
import sys
import os
import logging
import argparse
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
    
    final_strategy = None
    
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
        
        final_strategy = strategy
        
        # Apply the strategy
        print(f"[APPLY] Activating bypass with strategy: {strategy}")
        if applicator.apply(strategy):
            print(f"✓ Bypass ACTIVE for {domain}")
        else:
            print(f"✗ Failed to apply bypass")
    
    if not applicator.is_active():
        print("\n❌ No bypass is active. Check the logs above.")
        return
    
    print(f"\n{'='*50}")
    print("  ✓ Bypass is now ACTIVE!")
    print("  Terminal will be released. nfqws runs in background.")
    print(f"{'='*50}")
    print("\nCommands:")
    print("  sudo python3 zapret-cli.py status  - Check status")
    print("  sudo python3 zapret-cli.py stop    - Stop bypass")
    
    # DON'T block terminal! Just detach and exit.
    # The nfqws process is already running in background via Popen

def cmd_status():
    """Show current bypass status."""
    from core.db import StrategyDB
    import subprocess
    
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
        conn.close()
    except:
        print("    (none)")
    
    print(f"{'='*50}\n")

def cmd_stop():
    """Stop running bypass."""
    import subprocess
    
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
    
    for domain in domains:
        try:
            url = f"https://{domain}"
            response = requests.get(url, timeout=10, verify=False)
            print(f"✓ {domain}: Accessible (HTTP {response.status_code})")
        except requests.exceptions.Timeout:
            print(f"✗ {domain}: TIMEOUT - Likely blocked")
        except requests.exceptions.SSLError as e:
            print(f"✗ {domain}: SSL Error - {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"✗ {domain}: Connection Error - Blocked or down")
        except Exception as e:
            print(f"? {domain}: {e}")

def cmd_clear():
    """Clear all saved strategies from database."""
    import os
    try:
        os.remove('strategies.db')
        print("✓ Strategy database cleared")
    except FileNotFoundError:
        print("Database already empty")

def is_domain(arg: str) -> bool:
    """Check if argument looks like a domain name."""
    return '.' in arg and not arg.startswith('-')

def main():
    # Smart argument handling: if first arg looks like a domain, assume 'bypass'
    if len(sys.argv) > 1 and is_domain(sys.argv[1]):
        sys.argv.insert(1, 'bypass')
    
    parser = argparse.ArgumentParser(
        description='Zapret Autonomous - DPI Bypass Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo python3 zapret-cli.py twitter.com youtube.com   # Bypass (detached)
  sudo python3 zapret-cli.py bypass --fresh site.com   # Re-probe strategies
  sudo python3 zapret-cli.py status
  sudo python3 zapret-cli.py stop
  python3 zapret-cli.py test twitter.com
  sudo python3 zapret-cli.py clear                     # Clear saved strategies
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # bypass command
    bypass_parser = subparsers.add_parser('bypass', help='Find and apply bypass for domains')
    bypass_parser.add_argument('domains', nargs='+', help='Domains to bypass')
    bypass_parser.add_argument('--fresh', '-f', action='store_true', help='Ignore cache and re-probe strategies')
    
    # status command
    subparsers.add_parser('status', help='Show current bypass status')
    
    # stop command
    subparsers.add_parser('stop', help='Stop running bypass')
    
    # test command
    test_parser = subparsers.add_parser('test', help='Test if domains are accessible')
    test_parser.add_argument('domains', nargs='+', help='Domains to test')
    
    # clear command
    subparsers.add_parser('clear', help='Clear saved strategy database')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'test':
        cmd_test(args.domains)
    elif args.command == 'clear':
        cmd_clear()
    elif args.command in ['bypass', 'status', 'stop']:
        check_root()
        if args.command == 'bypass':
            cmd_bypass(args.domains, fresh=args.fresh)
        elif args.command == 'status':
            cmd_status()
        elif args.command == 'stop':
            cmd_stop()

if __name__ == '__main__':
    main()
