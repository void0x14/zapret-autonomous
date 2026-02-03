
# ⚠️ Windows Support Status

**Zapret Autonomous is a Linux-First System.**

The "Autonomous" features (Sentinel, Parallel Prober, God Mode Installer) rely heavily on the **Linux Kernel** features:
- `NFQUEUE` (Netfilter Queue)
- `ipset`
- `iptables` / `nftables`
- `systemd`

These features do not exist natively on Windows.

---

## 🛠️ How to run on Windows?

### Option 1: WSL 2 (Recommended)
You can run Zapret Autonomous inside **Windows Subsystem for Linux 2 (WSL 2)**.
1. Install WSL 2 (Ubuntu or Arch).
2. Follow the standard Linux installation instructions.
3. *Note: Intercepting Windows traffic from WSL requires advanced networking configuration.*

### Option 2: Original Zapret (WinDivert)
For native Windows support, please use the original **Zapret** build which uses `WinDivert`.
- Go to the implementation of `bol-van/zapret`.
- Use the `install_easy.cmd` script provided there.

> **Note:** The "Autonomous" Python wrapper (God Mode, Telemetry, Scraper) is not currently ported to Windows native.

---

<p align="center">
  <i>We recommend Linux for maximum freedom and control.</i>
</p>
