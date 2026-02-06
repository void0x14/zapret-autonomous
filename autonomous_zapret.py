#!/usr/bin/env python3
"""
Autonomous Zapret Service
Main entry point for the DPI bypass daemon.

This service:
1. Monitors network connections
2. Detects blocks (timeout/reset)
3. Automatically finds working bypass strategies
4. Applies them in real-time
"""
import sys
import os
import signal
import time
import logging
import argparse
from core.db import StrategyDB
from core.strategy_applicator import get_applicator
from solver.parallel_prober import ParallelProber

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [ZAPRET-AUTO] - %(levelname)s - %(message)s'
)

def check_root():
    if os.geteuid() != 0:
        logging.error("This service requires root privileges.")
        logging.error("Run: sudo python3 autonomous_zapret.py")
        sys.exit(1)

def signal_handler(sig, frame):
    logging.info("Shutdown signal received...")
    applicator = get_applicator()
    applicator.cleanup()
    logging.info("Cleanup complete. Exiting.")
    sys.exit(0)

def apply_saved_strategies():
    """Apply all saved strategies from database on startup."""
    db = StrategyDB()
    applicator = get_applicator()
    
    try:
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT strategy FROM domains LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            strategy = row[0]
            logging.info(f"Applying saved strategy: {strategy}")
            applicator.apply(strategy)
            return True
    except Exception as e:
        logging.debug(f"No saved strategies: {e}")
    
    return False

def solve_and_apply(domain: str):
    """Solve for a domain and apply the strategy."""
    db = StrategyDB()
    applicator = get_applicator()
    
    # Check cache first
    cached = db.get_strategy(domain)
    if cached:
        logging.info(f"Using cached strategy '{cached}' for {domain}")
        return applicator.apply(cached)
    
    # Solve
    logging.info(f"No cached strategy for {domain}, probing...")
    prober = ParallelProber(domain)
    strategy = prober.solve()
    
    if strategy:
        db.save_strategy(domain, strategy)
        return applicator.apply(strategy)
    else:
        logging.error(f"Could not find working strategy for {domain}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Autonomous Zapret Service')
    parser.add_argument('--domains', nargs='*', help='Domains to bypass (optional)')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    args = parser.parse_args()
    
    check_root()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info("="*50)
    logging.info("  ZAPRET AUTONOMOUS - Starting")
    logging.info("="*50)
    
    # Initialize
    db = StrategyDB()
    applicator = get_applicator()
    
    # If domains provided, solve for them
    if args.domains:
        for domain in args.domains:
            solve_and_apply(domain)
    else:
        # Try to apply any saved strategy
        if apply_saved_strategies():
            logging.info("Bypass active with saved strategy")
        else:
            logging.warning("No saved strategies. Use --domains to add some.")
            logging.info("Example: sudo python3 autonomous_zapret.py --domains twitter.com youtube.com")
    
    # Keep running
    if args.daemon or applicator.is_active():
        logging.info("Service running. Press Ctrl+C to stop.")
        try:
            while True:
                if applicator.is_active():
                    time.sleep(5)
                else:
                    logging.warning("nfqws process died, restarting...")
                    if applicator.active_strategy:
                        applicator.apply(applicator.active_strategy)
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    applicator.cleanup()
    logging.info("Service stopped.")

if __name__ == "__main__":
    main()
