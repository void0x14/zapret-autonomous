# ⚡ Quick Start Guide

> **Get up and running in less than 60 seconds.**

---

## 1. Zero-Config Installation

The system auto-detects your OS and installs everything needed.

```bash
git clone https://github.com/void0x14/zapret-autonomous.git
cd zapret-autonomous
sudo python3 setup.py --mode=god
```
*(Use `--mode=ask` if you want to confirm each step)*

---

## 2. Verify Your Freedom

Run the simulation tool. This tests the bypass engine without visiting real sites.

```bash
python3 simulate_block.py
```

Expected Output:
```
[PARALLEL PROBER] Starting probe for blocked-site.com...
[...Success...] Strategy 'fake' worked in 0.8s!
```

---

## 3. Check the Dashboard

See what the system is doing.

```bash
./zapret-stats today
```

---

## 4. Troubleshooting

**"Service failed to start?"**
Let the Sentinel fix it:
```bash
sudo systemctl restart zapret-sentinel
```

**"New site blocked?"**
Manually trigger the scraper to fetch latest updates:
```bash
python3 intelligence/btk_scraper.py
```

---

**That's it.** The system runs in the background. You don't need to do anything else.
