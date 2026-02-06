# Product Context

## Purpose
The project provides a robust, automated way to deploy `zapret` for users who need to bypass DPI (Deep Packet Inspection) censorship. It removes the complexity of manual configuration and ensures persistence via self-healing mechanisms.

## Problems Solved
-   **Manual Dependency Hell**: Automatically installs required system libraries and tools.
-   **Complex Configuration**: Abstracts `zapret` flags into modular strategies.
-   **Service Crashes**: Uses a Sentinel service to restart and reconfigure `zapret` if it fails.
-   **OS Compatibility**: Targeted support for multiple package managers and init systems.

## User Experience Goal
A one-command installation experience (`sudo python3 setup.py --mode=god`) that "just works" on any supported Linux machine.
