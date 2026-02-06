## Active Context - Project Maintenance & Enhancement

## Current Focus
Post-installation verification and fixing the hardcoded simulation domain.

## Debug Session: 2026-02-06
-   **Environment**: Laptop (CachyOS/Arch).
-   **Issue**: `simulate_block.py` was ignoring command-line arguments and only testing `blocked-site.com`.
-   **Root Cause**: Hardcoded `target` variable in the script.
-   **Solution**: Refactored script to iterate over `sys.argv[1:]`.

## Progress
1.  **Installation**: Successfully bypassed Arch `iptables-nft` conflicts and PEP 668 Python restrictions.
2.  **Tooling Improvement**: `simulate_block.py` is now dynamic and supports multiple domains in one run.
3.  **Sync**: All changes pushed to GitHub for desktop machine synchronization.

## Next Steps
-   User to run `git pull` on the desktop machine.
-   Verify real-world bypass with `systemctl start zapret-autonomous`.
