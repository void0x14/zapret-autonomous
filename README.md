# Zapret Autonomous

**Zero-Config, Self-Healing Anti-Censorship System**

A fire-and-forget autonomous wrapper for `zapret` that automatically detects blocked domains and negotiates bypass strategies without user intervention.

## Features

- 🚀 **Fast Parallel Probing**: Resolves blocks in <5 seconds
- 🤖 **Fully Autonomous**: Auto-detects OS, installs dependencies, self-heals
- 🌍 **Universal**: Works on any Linux distro (Arch, Debian, Alpine, Void, etc.)
- 🕵️ **Proactive Intelligence**: Auto-scrapes BTK/community blocklists
- 📊 **Built-in Telemetry**: Track bypass stats with CLI dashboard
- 📚 **Educational**: Logs every action with explanations
- 🛡️ **Secure**: No external ports, kernel-level performance

## Quick Start

### Installation (God Mode - Full Auto)
```bash
sudo python3 setup.py --mode=god
```

### Installation (Safe Mode - Interactive)
```bash
sudo python3 setup.py --mode=ask
```

### Verify
```bash
python3 simulate_block.py
```

### Check Statistics
```bash
./zapret-stats today
```

## Architecture

- **Control Plane**: Python (Decision making, strategy database)
- **Data Plane**: C (nfqws binary, zero-overhead packet manipulation)
- **Intelligence**: Multi-source blocklist scraper (BTK, USOM, GitHub)
- **Telemetry**: Local SQLite tracking with CLI dashboard
- **Autonomy**: Self-healing watchdog monitors kernel updates and dependencies

## Performance

- **CPU Impact**: <0.1% (Ryzen 5 3600 / i5 13500H tested)
- **Latency**: Time-to-bypass <5s on first detection
- **Throughput**: Native speed (no VPN overhead)

## Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `--mode=god` | Full autonomous. Deletes locks, kills conflicts | "I trust this, do whatever it takes" |
| `--mode=safe` | Auto-retry, no system modifications | Default, safe for production |
| `--mode=ask` | Interactive confirmation for each step | Learning/debugging |

## Advanced Features

### BTK Scraper
Automatically fetches blocked domain lists from multiple sources:
```bash
python3 intelligence/btk_scraper.py
```

### Telemetry Dashboard
View bypass statistics:
```bash
./zapret-stats today      # Today's stats
./zapret-stats week       # Last 7 days
./zapret-stats --range 30d  # Custom range
```

## License

MIT (Wrapper) / Original zapret license applies to C binaries

---

Built with obsessive attention to autonomy and speed.
