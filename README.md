
```
███████╗ █████╗ ██████╗ ██████╗ ███████╗████████╗    █████╗ ██╗   ██╗████████╗
╚══███╔╝██╔══██╗██╔══██╗██╔══██╗██╔════╝╚══██╔══╝   ██╔══██╗██║   ██║╚══██╔══╝
  ███╔╝ ███████║██████╔╝██████╔╝█████╗     ██║      ███████║██║   ██║   ██║   
 ███╔╝  ██╔══██║██╔═══╝ ██╔══██╗██╔══╝     ██║      ██╔══██║██║   ██║   ██║   
███████╗██║  ██║██║     ██║  ██║███████╗   ██║      ██║  ██║╚██████╔╝   ██║   
╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝      ╚═╝  ╚═╝ ╚═════╝    ╚═╝   
                                                           
        🤖 A U T O N O M O U S   E D I T I O N 
```

> **Autonomous DPI Bypass for Linux**  
> *Zero configuration. Auto-detection. Real bypass.*

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux-green.svg)

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

- Linux (Debian/Ubuntu/Arch/Fedora)
- Root access (for iptables)
- `nfqws` binary (installed by setup.py)
- Python 3.8+
- `requests`, `netfilterqueue`, `scapy` (installed by setup.py)

---

## 🔍 Troubleshooting

### "nfqws not found"
```bash
sudo python3 setup.py --mode=god
```

### "Permission denied"
Run with sudo:
```bash
sudo python3 zapret-cli.py bypass twitter.com
```

### "No working strategy found"
The site might use a different blocking method. Try:
1. Check if the domain resolves: `dig twitter.com`
2. Try different DNS: `1.1.1.1` or `8.8.8.8`
3. The block might be IP-based (zapret can't help with that)

### "Connection still times out"
After running bypass, if the site still doesn't work:
1. Check status: `sudo python3 zapret-cli.py status`
2. Clear browser cache
3. Try a different browser/incognito mode

---

## 📜 License

- **Wrapper Code**: MIT License
- **Zapret Core (nfqws)**: GPL License

---

<p align="center">
  <i>Made for a free and open internet.</i>
</p>
