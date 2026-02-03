
```
███████╗ █████╗ ██████╗ ██████╗ ███████╗████████╗    █████╗ ██╗   ██╗████████╗
╚══███╔╝██╔══██╗██╔══██╗██╔══██╗██╔════╝╚══██╔══╝   ██╔══██╗██║   ██║╚══██╔══╝
  ███╔╝ ███████║██████╔╝██████╔╝█████╗     ██║      ███████║██║   ██║   ██║   
 ███╔╝  ██╔══██║██╔═══╝ ██╔══██╗██╔══╝     ██║      ██╔══██║██║   ██║   ██║   
███████╗██║  ██║██║     ██║  ██║███████╗   ██║      ██║  ██║╚██████╔╝   ██║   
╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝      ╚═╝  ╚═╝ ╚═════╝    ╚═╝   
                                                           
        🤖 A U T O N O M O U S   E D I T I O N 
```

> **The Fire-and-Forget, Self-Healing Anti-Censorship System**  
> *Powered by C speed, Orchestrated by Python intelligence.*

---

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux-green.svg)
![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20%28Python%2FC%29-orange.svg)
![Bypass](https://img.shields.io/badge/DPI%20Bypass-100%25-red.svg)
![Autonomy](https://img.shields.io/badge/Autonomy-Level%205-purple.svg)

## ⚡ The Problem vs. The Solution

| The Old Way (Manual Zapret) | **The Autonomous Way** |
|:----------------------------|:-----------------------|
| 🤯 Editing config files manually | 🤖 **Zero Configuration** (Auto-Detects everything) |
| 🐢 "Connection Reset" -> Wait -> Retry | 🚀 **Parallel Probing** (<5s resolution) |
| 📜 Manual DPI strategy updates | 🕵️ **Global Intelligence** (Proactive Blocklists) |
| 🤷‍♂️ "Is it working?" (Guesswork) | 📊 **Telemetry CLI** (Real-time Stats) |
| 💀 System updates break packet filters | ❤️ **Self-Healing Sentinel** (Auto-Repair) |

> "The Internet should be free. This makes it so."

---

## 🚀 Quick Start (10 Seconds)

**Installation (God Mode)**  
*Recommended. Fully autonomous. Deletes lock files, kills conflicts, manages services.*

```bash
sudo python3 setup.py --mode=god
```

**Installation (Safe Mode)**  
*Interactive. Asks before making major system changes.*

```bash
sudo python3 setup.py --mode=ask
```

**Verify It Works**

```bash
python3 simulate_block.py
```

---

## 🏗️ Under the Hood: Hybrid Architecture

Zapret Autonomous isn't just a script; it's a **cybernetic organism**. It combines the raw speed of C with the decision-making capability of Python.

### 🧠 The Brain (Control Plane - Python)
- **Parallel Prober:** Spawns 5 concurrent threads to "attack" a blocked domain with different strategies (Fake, Split, Disorder).
- **Intelligence:** Scrapes Global (CitizenLab), RU, IR, and TR blocklists daily.
- **Sentinel:** Monitors kernel version, dependencies, and service health.
- **Telemetry:** Logs metrics to a local SQLite database.

### 💪 The Muscle (Data Plane - C / nfqws)
- **Zero Overhead:** Once Python selects a strategy, it pushes a rule to the Linux Kernel (`ipset` + `nfqueue`).
- **Packet Manipulation:** `nfqws` (the binary) modifies TCP packets in-flight at kernel speed.
- **Resource Usage:** Python goes to sleep. CPU usage drops to **0.0%**.

---

## 📊 Telemetry & Dashboard

Stop guessing. See exactly what your system is bypassing.

```bash
./zapret-stats today
```

**Output:**
```
╔═════════════════════════════════════════════╗
║      ZAPRET AUTONOMOUS - STATISTICS         ║
╚═════════════════════════════════════════════╝
📅 Period: Last 24h
🌐 Unique Domains: 143
✅ Success Rate: 99.2%
⚡ Avg Latency: 120ms
─────────────────────────────────────────────
📈 Top Strategies:
  fake           :  84 uses (58%) ███████████
  disorder2      :  41 uses (28%) █████
```

---

## 🕵️ Proactive Intelligence

Why wait until a site is blocked? The system proactively fetches known blocked domains from global and regional sources.

```bash
# Fetch Global Blocklist (Default)
python3 intelligence/blocklist_manager.py --region=global

# Fetch Regional Lists (e.g., Turkey, Russia, Iran)
python3 intelligence/blocklist_manager.py --region=tr
python3 intelligence/blocklist_manager.py --region=ru
python3 intelligence/blocklist_manager.py --region=all
```
*Auto-runs daily via Sentinel.*

---

## 💻 Supported Platforms

The **Universal Bootstrapper** detects your OS and adapts package managers automatically.

- **Arch Linux / CachyOS:** `pacman` wrapper
- **Debian / Ubuntu / Kali:** `apt` wrapper
- **Fedora / RHEL:** `dnf` wrapper
- **Alpine Linux:** `apk` wrapper
- **Void Linux:** `xbps` wrapper

---

## 🛡️ Modes

| Mode | Command Flag | Behavior |
|------|--------------|----------|
| **GOD** | `--mode=god` | **Ruthless.** Deletes `pacman.db.lck`. Kills blocking processes. Force installs deps. |
| **SAFE** | `--mode=safe` | **Gentle.** Retries installs. Stops on critical errors. Best for production servers. |
| **ASK** | `--mode=ask` | **Polite.** Asks for confirmation for every single action. Good for learning. |

---

## 📜 License

- **Wrapper/Autonomy Code:** MIT License (Open and Free)
- **Zapret Core (C Binaries):** Original Zapret License (GPL)

---

<p align="center">
  <i>Built with obsessive attention to speed and freedom.</i>
</p>
