# Zapret Autonomous - Project Brief

## Project Overview
Zapret Autonomous is a self-healing, multi-distro setup system for the `zapret` DPI bypass tool. It aims to automate the installation and configuration of `zapret` and its dependencies across various Linux distributions, providing a "God Mode" installer that handles system-level requirements and sets up watchdog services.

## Core Objectives
1.  **Autonomous Installation**: Multi-distro support (Arch, Debian, Fedora, Alpine, etc.).
2.  **Self-Healing**: Sentinel watchdog services to ensure the bypass stays active.
3.  **Simplified UI**: Easy-to-use modes (God, Safe, Ask).
4.  **Global Bypass**: Generalized from country-specific blocks to global intelligence.

## Current State
Implementation of the core bootstrapper (`setup.py`) is complete, but it fails on Arch Linux due to a package conflict between `iptables` and `iptables-nft`.

## Tech Stack
-   **Language**: Python 3
-   **Core Tool**: Zapret (C-based DPI bypass)
-   **Networking**: iptables/nftables, ipset, libnetfilter_queue
-   **Service Management**: systemd
