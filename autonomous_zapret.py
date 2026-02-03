import sys
import os
import signal
import time
import logging
from core.db import StrategyDB
from core.interceptor import PacketInterceptor
from solver.parallel_prober import ParallelProber

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [AUTO-ZAPRET] - %(levelname)s - %(message)s'
)

def check_root():
    if os.geteuid() != 0:
        logging.error("This service requires root privileges to manipulate NFQueue/IPtables.")
        sys.exit(1)

def on_new_domain_detected(domain):
    """
    Called when the interceptor sees a new execution.
    1. Check DB.
    2. If unknown, trigger Solver?
    Actually, usually we wait for a BLOCK.
    But for this prototype "Fast Solver", let's simulate a trigger.
    """
    db = StrategyDB()
    strategy = db.get_strategy(domain)
    
    if strategy:
        logging.info(f"Known domain {domain} -> Using {strategy}")
        # Here we would add to ipset: `ipset add zapret_set domain_ip`
    else:
        logging.info(f"New domain {domain}. Assuming okay, but watching...")
        # In a real app, we would have a separate thread watching for RST/Timeout 
        # for this specific domain connection. 
        # If that fires -> trigger `solve_domain(domain)`

def solve_domain(domain):
    logging.warning(f"BLOCK DETECTED for {domain}! Initiating Fast Solver...")
    prober = ParallelProber(domain)
    result = prober.solve()
    
    if result:
        db = StrategyDB()
        db.save_strategy(domain, result)
        logging.info(f"RESOLVED: {domain} needs {result}. Applied to system.")
    else:
        logging.error(f"FAILED: Could not find a working strategy for {domain}.")

def signal_handler(sig, frame):
    logging.info("Shutting down...")
    sys.exit(0)

def main():
    check_root()
    signal.signal(signal.SIGINT, signal_handler)

    logging.info("Initializing Autonomous Zapret Service...")
    
    # 1. Init DB
    db = StrategyDB()
    
    # 2. Start Interceptor (Threaded)
    interceptor = PacketInterceptor(db, on_new_domain_detected)
    # interceptor.start_threaded() # Commented out for now as we don't have real NFQueue set up in env
    
    logging.info("Service Running. Waiting for triggers...")
    
    # Simulation Loop for User Demo
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
