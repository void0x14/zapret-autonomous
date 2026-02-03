# Project Plan: Autonomous Zapret Installer (The "God Mode" Update)

## 1. Executive Summary
**Goal:** Create a fire-and-forget, self-healing, high-performance anti-censorship system that works on **ANY** Linux distribution (CachyOS, Alpine, Void, etc.).
**Philosophy:** "Speed is King, Autonomy is God."
**Performance:** Zero-Overhead Data Plane. Traffic flows through `nfqws` (C binary). Python only acts as the "General" giving orders, never touching the actual data packets after the initial decision.

## 2. Architecture

### A. The "Universal" Bootstrapper (`setup.py`)
A single Python script acting as a universal adapter.
- **Distro Agnostic:** Detects OS via `/etc/os-release` or kernel signatures.
- **Package Manager Abstraction:**
  - `Pacman` (Arch/Cachy)
  - `Apt` (Debian/Ubuntu)
  - `Apk` (Alpine)
  - `Xbps` (Void)
  - `Slackpkg` (Slackware)
  - *Fallback:* Compile from source (Make/GCC) if no package found.
- **Three Modes of Autonomy:**
  1.  `--mode=god` (Full Auto): Deletes lock files, kills conflicting processes, force-installs.
  2.  `--mode=safe` (Safe Auto): Retries standard installs, fails if system repair needed.
  3.  `--mode=ask` (Interactive): Asks for permission before every major change.

### B. The Core Daemon (`autonomous_zapret.py`)
- **Language:** Python (Control Plane) / C (Data Plane).
- **Function:** Listens to NFQueue *only* for blocked packets (TCP RST/Timeouts).
- **Optimization:** Once a strategy is found, it injects a rule into `ipset`. The Kernel + `nfqws` handles the traffic. **Python CPU usage drops to 0%.**

### C. The Sentinel (Self-Healing Watchdog)
A separate persistent process or cron job.
- **Kernel Watch:** Did the kernel update? Recompile `nfqws` if needed.
- **Dependency Watch:** Is `libnetfilter_queue` gone? Reinstall it immediately.
- **Sanity Check:** Can't reach Google? Restart the service.

### D. The "Sensei" (Educational Logger)
- Logs actions with "WHY" explanations to `learn_log.md`.
- *Example:* "Action: Deleted `/var/lib/pacman/db.lck`. **Reason:** Pacman was locked for >5 mins. learn about Lock Files here: [Link]"

## 3. Implementation Phases

### Phase 1: universal-bootstrapper
- [ ] Implement `DistroDetector` class (signatures for Alpine, Void, etc.).
- [ ] Implement `PackageManager` abstract base class with retries.
- [ ] Implement `GodMode` logic (lock removal, conflict resolution).

### Phase 2: high-performance-core
- [ ] Optimization: Ensure Python only intercepts SYN/RST, never Payload.
- [ ] Logic: "Parallel Probing" finalized (C-speed resolution).

### Phase 3: the-sentinel
- [ ] Create systemd service (auto-restart on failure).
- [ ] Create cron/timer for daily integrity checks.
- [ ] Kernel header auto-detection.

### Phase 4: education-layer
- [ ] Implement `SenseiLogger`.
- [ ] Create Mind Map generator (text-based tree view of what system is doing).

## 4. Verification Checklist
- [ ] **Speed Test:** `iperf3` throughput with and without Zapret (Must be identical).
- [ ] **Latency Test:** Time-to-First-Byte on blocked site < 2s.
- [ ] **Distro Test:** Run on Docker containers (Alpine, Arch, Ubuntu) and verify install.
- [ ] **Healing Test:** Manually kill `nfqws`, watch it resurrect.

## 5. Security Note
- **God Mode Risk:** Running in God Mode grants the script permission to modify system files aggressively.
- **Mitigation:** Logic includes "Sanity Checks" (e.g., won't delete `/etc/passwd`).

---
**File:** `docs/PLAN-autonomous-installer.md`
