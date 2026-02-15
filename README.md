# ZAPRET AUTONOMOUS

> **Intelligent, Zero-Configuration DPI Bypass for Linux**  
> *Autonomous detection. Real-time strategy selection. Seamless connectivity.*

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.txt)
[![Platform](https://img.shields.io/badge/Platform-Linux-green.svg)](#requirements)
[![Status](https://img.shields.io/badge/Status-Alpha-orange.svg)](#roadmap)

---

## 🚀 Quick Start

### 1. Install
```bash
git clone https://github.com/void0x14/zapret-autonomous.git
cd zapret-autonomous
sudo python3 setup.py --mode=god
```

### 2. Bypass a Blocked Site
```bash
# Test strategies and apply bypass
sudo python3 zapret-cli.py bypass twitter.com youtube.com

# The tool will:
# 1. Test 5 different DPI bypass strategies in parallel
# 2. Find the one that works
# 3. Apply iptables rules + start nfqws
# 4. Save the strategy for future use
```

### 3. Check Status
```bash
sudo python3 zapret-cli.py status
```

### 4. Stop Bypass
```bash
sudo python3 zapret-cli.py stop
```

---

## 📖 How It Works

### The Problem
Your ISP uses **Deep Packet Inspection (DPI)** to detect and block certain websites. When you try to access a blocked site, the DPI system sees the domain name in your TLS handshake and drops the connection.

### The Solution
Zapret Autonomous:

1. **Detects blocks** - Identifies when a connection times out or is reset
2. **Tests strategies** - Tries 5 different packet manipulation techniques in parallel
3. **Finds what works** - Uses the first successful strategy
4. **Applies bypass** - Sets up iptables + nfqws to manipulate your traffic
5. **Remembers** - Saves working strategies to a database for instant reuse

### Bypass Strategies

| Strategy | Description |
|----------|-------------|
| `fake` | Send fake packet with bad checksum |
| `disorder2` | Send packets out of order |
| `split2` | Split TCP packet into two |
| `combo_1` | Fake + Disorder combined |
| `combo_2` | Fake + Split combined |

---

## 🔧 Commands

### `bypass` - Find and apply bypass
```bash
sudo python3 zapret-cli.py bypass site1.com site2.com site3.com
```
- Tests strategies against each domain
- Saves working strategies to database
- Applies IPTables rules
- Starts nfqws process
- Runs until you press Ctrl+C

### `status` - Show current state
```bash
sudo python3 zapret-cli.py status
```
Shows:
- Whether bypass is active
- Current strategy
- nfqws process ID
- Saved domains

### `stop` - Stop bypass
```bash
sudo python3 zapret-cli.py stop
```
- Stops nfqws process
- Removes IPTables rules

### `test` - Test connectivity (no bypass)
```bash
python3 zapret-cli.py test twitter.com youtube.com
```
Tests if sites are accessible WITHOUT bypass (useful for debugging).

---

## 🖥️ System Service (Optional)

To run bypass on boot:

```bash
# Enable service
sudo systemctl enable zapret-autonomous

# Start service
sudo systemctl start zapret-autonomous

# Check logs
sudo journalctl -u zapret-autonomous -f
```

---

## 📁 File Structure

```
zapret-autonomous/
├── zapret-cli.py          # Main CLI tool (USE THIS)
├── autonomous_zapret.py   # Daemon service
├── setup.py               # Installer
├── core/
│   ├── db.py              # Strategy database
│   └── strategy_applicator.py  # IPTables + nfqws manager
├── solver/
│   ├── parallel_prober.py # Strategy tester
│   └── heuristics.py      # Strategy definitions
└── strategies.db          # SQLite database with saved strategies
```

---

## ⚠️ Requirements

- **OS**: Linux (Arch, Debian/Ubuntu, Fedora, OpenWrt)
- **Privileges**: Root access (required for `iptables` and NFQUEUE manipulation)
- **Kernel**: Version 4.19+ with `netfilter` support
- **Dependencies**: 
  - `nfqws` / `tpws` binaries (provisioned by `setup.py`)
  - Python 3.8+
  - Modules: `requests`, `netfilterqueue`, `scapy`

---

## 🔍 Troubleshooting & Verification

### Common Failure Points

1.  **`nfqws` Path Errors**:
    The prober expects `nfqws` to be in the `../bin` directory relative to the core or in your system `PATH`. If `setup.py` was interrupted, verify binary existence in the `files` directory.
    
2.  **Database Locking (`sqlite3.OperationalError`)**:
    High-concurrency probing can occasionally cause database locks. The system implements a retry mechanism, but if persistent errors occur, manually clear the database:
    ```bash
    rm strategies.db
    # The system will recreate it on next run
    ```

3.  **NFQUEUE Conflict**:
    By default, this tool uses NFQUEUE number `1`. If another firewall service is using queue `1`, packets will be dropped or ignored. Ensure no other `zapret` or concurrent bypass tools are active.

4.  **ISP IP-Level Blocking**:
    If a site is blocked by IP address rather than hostname (SNI), packet manipulation alone will not work. In these cases, a VPN or Proxy is required.

---

## 🗺️ Roadmap

### Phase 1: Stability & Core (Current)
- [x] Autonomous strategy probing and persistence.
- [x] Systemd integration for persistent operation.
- [x] Multi-distro support (Arch, Debian, Fedora).

### Phase 2: Intelligence & Optimization
- [ ] **Heuristic Refinement**: Improve detection of "fake" HTTP responses and TLS resets.
- [ ] **Asynchronous Strategy Engine**: Transition from threaded probing to `asyncio` for lower resource overhead.
- [ ] **DB Resilience**: Replace raw SQLite with a more robust connection pooling or WAL mode for high concurrency.

### Phase 3: Observability & Scaling
- [ ] **Web Dashboard**: Real-time visualization of bypassed domains and strategy effectiveness.
- [ ] **Prometheus Exporter**: Export metrics for Grafana monitoring.
- [ ] **Cloud-Sync Strategies**: Share anonymized working strategies across nodes to reduce per-client probing time.

---

## 📜 License

- **Wrapper Code**: MIT License
- **Zapret Core (nfqws)**: GPL License

---

<p align="center">
  <i>Made for a free and open internet.</i>
</p>
