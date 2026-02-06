## Active Context - Zapret Autonomous

## Latest Session: 2026-02-06

### Major Architectural Overhaul COMPLETE

**Problem**: Tool was a non-functional prototype. Simulation worked but actual bypass didn't.

**Root Causes Fixed**:
1. `parallel_prober.py` was using MOCK tests instead of real network requests
2. `autonomous_zapret.py` had the interceptor commented out
3. No mechanism existed to actually apply iptables rules or spawn nfqws
4. README was misleading - didn't explain how to actually use the tool

### Files Created/Modified

| File | Action | Purpose |
|------|--------|--------|
| `core/strategy_applicator.py` | **CREATED** | Applies iptables rules + spawns nfqws |
| `solver/parallel_prober.py` | **REWRITTEN** | Real network tests instead of mock |
| `autonomous_zapret.py` | **REWRITTEN** | Working daemon with cleanup |
| `zapret-cli.py` | **CREATED** | User-friendly CLI |
| `README.md` | **REWRITTEN** | Clear step-by-step usage guide |

### How It Works Now

1. User runs: `sudo python3 zapret-cli.py bypass twitter.com`
2. System checks database for cached strategy
3. If not cached, ParallelProber tests 5 strategies in parallel
4. Each strategy test:
   - Adds temporary iptables rule
   - Spawns nfqws with that strategy
   - Makes real HTTPS request
   - Cleans up
5. First working strategy wins
6. StrategyApplicator applies permanent iptables rules
7. nfqws runs in background
8. User can now access the site

### Key Technical Details

**IPTables Rule Applied**:
```bash
iptables -t mangle -I POSTROUTING -p tcp -m multiport --dports 80,443 \
  -m connbytes --connbytes-dir=original --connbytes-mode=packets --connbytes 1:6 \
  -m mark ! --mark 0x40000000/0x40000000 \
  -j NFQUEUE --queue-num 200 --queue-bypass
```

**nfqws Command**:
```bash
/usr/bin/nfqws --qnum=200 --dpi-desync=fake
```

### Next Steps for User
1. Run: `sudo python3 zapret-cli.py bypass <blocked-site>`
2. Verify with: `sudo python3 zapret-cli.py status`
3. Test access in browser
