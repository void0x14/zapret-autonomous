#!/usr/bin/env python3
"""
Zapret CLI - Simple command-line interface for DPI bypass
Usage:
    sudo python3 zapret-cli.py turbo.cr jpg6.su        # Auto-bypass
    sudo python3 zapret-cli.py bypass site1.com        # Explicit bypass
    sudo python3 zapret-cli.py status
    sudo python3 zapret-cli.py stop
"""
import sys
import os
import logging
import argparse

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

def cmd_bypass(domains: list):
    """Find working strategy and apply bypass for given domains."""
    from core.db import StrategyDB
    from core.strategy_applicator import get_applicator
    from solver.parallel_prober import ParallelProber
    
    db = StrategyDB()
    applicator = get_applicator()
    
    for domain in domains:
        print(f"\n{'='*50}")
        print(f"  Processing: {domain}")
        print(f"{'='*50}")
        
        # Check DB first
        cached_strategy = db.get_strategy(domain)
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
        if applicator.apply(strategy):
            print(f"✓ Bypass ACTIVE for {domain}")
        else:
            print(f"✗ Failed to apply bypass")
    
    print(f"\n{'='*50}")
    print("  Bypass is now running in background")
    print("  Press Ctrl+C to stop")
    print(f"{'='*50}")
    
    # Keep running
    try:
        import time
        while applicator.is_active():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")
        applicator.cleanup()
        print("✓ Bypass stopped")

def cmd_status():
    """Show current bypass status."""
    from core.strategy_applicator import get_applicator
    from core.db import StrategyDB
    
    applicator = get_applicator()
    status = applicator.get_status()
    db = StrategyDB()
    
    print(f"\n{'='*50}")
    print("  ZAPRET AUTONOMOUS - STATUS")
    print(f"{'='*50}")
    print(f"  Active: {'✓ YES' if status['active'] else '✗ NO'}")
    print(f"  Strategy: {status['strategy'] or 'None'}")
    print(f"  nfqws PID: {status['nfqws_pid'] or 'Not running'}")
    print(f"  IPTables Rules: {'Applied' if status['rules_applied'] else 'Not applied'}")
    
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
    from core.strategy_applicator import get_applicator
    
    applicator = get_applicator()
    applicator.cleanup()
    print("✓ Bypass stopped and rules cleaned up")

def cmd_test(domains: list):
    """Test if domains are accessible (without bypass)."""
    import requests
    
    for domain in domains:
        try:
            url = f"https://{domain}"
            response = requests.get(url, timeout=5)
            print(f"✓ {domain}: Accessible (HTTP {response.status_code})")
        except requests.exceptions.Timeout:
            print(f"✗ {domain}: TIMEOUT - Likely blocked")
        except requests.exceptions.ConnectionError as e:
            print(f"✗ {domain}: Connection Error - {e}")
        except Exception as e:
            print(f"? {domain}: {e}")

def is_domain(arg: str) -> bool:
    """Check if argument looks like a domain name."""
    # If it contains a dot and doesn't start with - it's probably a domain
    return '.' in arg and not arg.startswith('-')

def main():
    # Smart argument handling: if first arg looks like a domain, assume 'bypass'
    if len(sys.argv) > 1 and is_domain(sys.argv[1]):
        # User typed: zapret-cli.py site.com -> convert to: zapret-cli.py bypass site.com
        sys.argv.insert(1, 'bypass')
    
    parser = argparse.ArgumentParser(
        description='Zapret Autonomous - DPI Bypass Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo python3 zapret-cli.py twitter.com youtube.com   # Auto-bypass
  sudo python3 zapret-cli.py bypass twitter.com        # Explicit bypass
  sudo python3 zapret-cli.py status
  sudo python3 zapret-cli.py stop
  python3 zapret-cli.py test twitter.com
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # bypass command
    bypass_parser = subparsers.add_parser('bypass', help='Find and apply bypass for domains')
    bypass_parser.add_argument('domains', nargs='+', help='Domains to bypass')
    
    # status command
    subparsers.add_parser('status', help='Show current bypass status')
    
    # stop command
    subparsers.add_parser('stop', help='Stop running bypass')
    
    # test command
    test_parser = subparsers.add_parser('test', help='Test if domains are accessible')
    test_parser.add_argument('domains', nargs='+', help='Domains to test')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'test':
        cmd_test(args.domains)
    elif args.command in ['bypass', 'status', 'stop']:
        check_root()
        if args.command == 'bypass':
            cmd_bypass(args.domains)
        elif args.command == 'status':
            cmd_status()
        elif args.command == 'stop':
            cmd_stop()

if __name__ == '__main__':
    main()
