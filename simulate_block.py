import sys
import time
import logging
from solver.parallel_prober import ParallelProber
from core.db import StrategyDB

# Mock Logging config
logging.basicConfig(level=logging.INFO, format='%(message)s')

def simulate_site(target: str, db: StrategyDB):
    """Perform simulation for a single domain."""
    print(f"\n--- SIMULATION: Visiting {target} ---")
    
    # 1. Check if we already have a strategy in DB
    strategy = db.get_strategy(target)
    
    if strategy:
        print(f"[CACHE] Found defined strategy: {strategy}")
        return

    print(f"[!] Connection Timeout detected for {target}! (Simulated)")
    print(f"[*] Triggering Fast Solver for {target} (Parallel Mode)...")
    
    # 2. Solve using the Prober
    start = time.time()
    prober = ParallelProber(target)
    
    # The prober will test different zapret strategies
    winner = prober.solve()
    end = time.time()
    
    if winner:
        print(f"[+] SUCCESS! Found strategy for {target}: '{winner}' in {end-start:.2f} seconds.")
        print(f"[*] Saving {winner} to Database...")
        db.save_strategy(target, winner)
    else:
        print(f"[-] Failed to find bypass for {target}.")

def main():
    db = StrategyDB()
    
    # Get targets from command line arguments
    # Skip script name (index 0)
    targets = sys.argv[1:]
    
    # Fallback if no targets provided
    if not targets:
        print("[INFO] No domains provided. Use: python3 simulate_block.py site1.com site2.com")
        print("[INFO] Running with default test domain...")
        targets = ["blocked-site.com"]

    for site in targets:
        try:
            simulate_site(site, db)
        except Exception as e:
            print(f"[ERROR] Simulation failed for {site}: {e}")

if __name__ == "__main__":
    main()
