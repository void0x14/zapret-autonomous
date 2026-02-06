# Active Context - Debugging Arch Linux Installation

## Current Focus
Debugging and fixing the `iptables` installation failure on Arch Linux.

## Debug Session: 2026-02-06
-   **Issue**: `pacman` fails to install `iptables` because it conflicts with `iptables-nft` already on the system (or vice versa).
-   **Symptom**: `error: unresolvable package conflicts detected`.
-   **Hypothesis**: `iptables-nft` should be used instead of `iptables` on Arch, or the installer should handle the replacement prompt.

## Progress
1.  **Analysis**: Identified that `setup.py` specifically requests `iptables` for Arch, causing conflicts with `iptables-nft`.
2.  **Research**: Confirmed `iptables-nft` is the modern standard on Arch and provides compatibility for `iptables` syntax.
3.  **Memory Bank**: Initialized `memory-bank/` with project context and current issue.
4.  **Fix Applied (Iteration 2)**: 
    - **Smart Dependency Check**: `setup.py` now checks if `iptables` or `ipset` binaries are already functional before attempting package installation. This makes it agnostic to specific package names like `iptables` vs `iptables-nft`.
    - **Firewall Backup**: Added a `backup_firewall` method to `setup.py` that exports current rules to `tmp/firewall_backups` before any installation or changes occur.
    - **Pacman Robustness**: Kept `--ask=4` in `distro_detector.py` for cases where package replacement is still necessary.

## Next Steps
-   Verify if the user is satisfied with the "God Mode" improvements.
-   Conduct a full code review of `autonomous_zapret.py` to ensure it uses the detected firewall tools correctly.
