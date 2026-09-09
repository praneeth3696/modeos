# ModeOS (Adaptive OS Mode Manager)

ModeOS is a customizable, terminal-based system utility that transforms your Linux environment based on predefined states called **Modes**. Think of it as a supercharged "Do Not Disturb" combined with an intelligent hardware and process orchestrator.

Whether you are jumping into a deep work session, gaming, reading, or giving a presentation, ModeOS automatically adjusts your system brightness, volume, night light (blue light filter), and dynamically manages your running applications (prioritizing what you need, reducing background hogs, and gracefully closing distractions).

---

## ⚡ Key Features

- **Hardware Control:** Automatically adjusts Brightness, Volume, and Night Light based on the active mode profile.
- **Pluggable Architecture:**
  - **Audio:** WirePlumber (`wpctl` / modern PipeWire), PulseAudio (`pactl`), ALSA (`amixer`), and Mock simulation.
  - **Display:** Direct Linux sysfs backlight (`/sys/class/backlight/*`), `brightnessctl`, `xrandr`, and Mock simulation.
  - **Night Light:** GNOME GSettings, KDE Plasma D-Bus, Gammastep/Wlsunset (Wayland), Redshift (X11), and Mock simulation.
- **Graceful & Safe Process Management:**
  - Two-stage process termination (`SIGTERM` with clean 2s grace period before escalating to `SIGKILL`).
  - Strict system daemon whitelist protecting shells, terminal multiplexers (`tmux`, `screen`), audio servers, compositors, and IDEs.
  - Process priority tracking: stores original nice values and cleanly restores them upon revert.
- **100% Guaranteed Dry-Run Engine:** Running `--dry-run` guarantees zero destructive actions (no killed processes, no modified nice values, no hardware writes).
- **Cross-Platform Controlled Testing:** Includes built-in Mock Backends (`--mock` or `MODEOS_MOCK=1`) and a Docker sandbox for testing Linux modes safely anywhere (macOS, Linux, CI/CD).
- **XDG Specification Compliance:** Cleanly stores configuration in `~/.config/modeos`, session states in `~/.local/state/modeos`, and caches in `~/.cache/modeos`.

---

## 🛠️ Installation & Prerequisites

### 1. Install Dependencies
ModeOS requires `python3` (>= 3.8), `psutil`, and `PyYAML`.

```bash
# Clone the repository
git clone https://github.com/modeos/modeos.git
cd modeos

# Install ModeOS CLI in editable mode
pip install -e .
```

### 2. Supported Linux Subsystems
ModeOS includes automatic detection and fallbacks for:
- **Audio:** `wpctl` (PipeWire / WirePlumber), `pactl` (PulseAudio), or `amixer` (ALSA)
- **Display:** `/sys/class/backlight` (native laptop backlight), `brightnessctl`, or `xrandr`
- **Night Light:** GNOME Shell (`gsettings`), KDE Plasma (`qdbus`), `gammastep` (Wayland), or `redshift` (X11)

To check your machine's connected backends at any time:
```bash
modeos doctor
```

---

## 🚀 Getting Started

### 1. Scan Installed Applications
Index installed desktop applications across system, user, Flatpak, and Snap directories:
```bash
modeos scan
```
This allows you to reference friendly application names (e.g. `code`, `discord`, `steam`) in YAML profiles without needing full executable paths.

### 2. View Available Modes
List all configured modes and their hardware/focus rules:
```bash
modeos list
```

### 3. Switch Mode
```bash
# Apply a mode
modeos mode deep_work

# Safe preview (no processes killed, no hardware changed)
modeos mode gaming --dry-run
```

### 4. Check Active Status
```bash
modeos current
```

### 5. Revert System State
Instantly restore hardware settings and process priorities back to their exact state before the mode was activated:
```bash
modeos revert
```

### 6. Reset System to Defaults
Reset brightness to 100%, volume to 100%, night light to OFF, and all user process priorities to 0:
```bash
modeos reset
```

---

## 💻 Command Reference

| Command | Description | Example |
|---|---|---|
| `modeos list` | List all discovered modes in formatted table | `modeos list` |
| `modeos mode <name>` | Activate a mode | `modeos mode deep_work` |
| `modeos mode <name> --dry-run` | Preview actions without executing | `modeos mode gaming --dry-run` |
| `modeos revert` | Rollback hardware & process priorities | `modeos revert` |
| `modeos reset` | Reset hardware & priorities to defaults | `modeos reset` |
| `modeos current` | Display active session telemetry | `modeos current` |
| `modeos doctor` | Diagnostic report on Linux subsystems | `modeos doctor` |
| `modeos scan` | Index system, user, Flatpak, & Snap apps | `modeos scan` |
| `modeos validate <name>` | Check mode YAML syntax and schema | `modeos validate coding` |

*(Note: `python3 main.py <command>` remains fully supported for backward compatibility.)*

---

## 🧪 Controlled Environment & Container Testing

### Running Unit & Integration Tests
ModeOS includes a comprehensive test suite covering hardware backends, process managers, state reversions, and YAML schemas:
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

### Running with Mock Backends
You can test ModeOS on any machine (including macOS or headless servers) without native Linux hardware:
```bash
modeos mode deep_work --mock --dry-run
modeos doctor
```

### Dockerized Sandbox
To run inside an isolated Ubuntu 24.04 LTS container:
```bash
docker compose run modeos-test
```
or interactively:
```bash
docker compose run modeos-cli
```

---

## 📝 Customizing Modes

Mode profiles are simple YAML files located in `modes/` or `~/.config/modeos/modes/`:

```yaml
description: Deep focus session for coding
brightness: 80              # Target display brightness percentage (0-100)
volume: 10                  # Target audio volume percentage (0-100)
night_light: true           # Enable or disable blue light filter
cpu_limit: 100              # Target CPU scheduling budget (%)

# Focus rules
kill_all_except_allow: true # Strict focus: close everything except allowed apps
allow_apps:
  - code
  - terminal
  - nvim

# Priority tuning
boost_apps:
  code: -10                 # Priority boost (nice value)
reduce_apps:
  slack: 10                 # Priority reduction (nice value)
```

---

## 🔒 Security & Rootless Design

- ModeOS runs **completely in user space**.
- Relative CPU prioritization is achieved without requiring `sudo` or root privileges.
- Permissions follow standard XDG directory security standards (no `chmod 777` anti-patterns).
