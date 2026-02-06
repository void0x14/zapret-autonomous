# System Patterns & Architecture

## Core Components
1.  **`setup.py`**: The entry point. Orchestrates the installation workflow.
2.  **`installer/`**: Modular logic for OS detection and package management.
    -   `distro_detector.py`: Uses `/etc/os-release` or similar to identify the family.
    -   `package_manager.py`: Abstraction layer over `pacman`, `apt`, `dnf`, etc.
3.  **`autonomous_zapret.py`**: The main logic that runs the bypass.
4.  **`sentinel.py`**: The self-healing watchdog.

## Architecture
-   **State Machine**: Installation moves from Detection -> Dependency Check -> Service Setup.
-   **Abstraction**: Package manager logic is separated from the distro family definitions.
-   **Persistence**: Uses systemd units for continuous operation.

## Key Files
-   `installer/distro_detector.py`
-   `installer/package_manager.py`
-   `setup.py`
-   `sentinel.py`
