# ModeOS (Adaptive OS Mode Manager)

ModeOS is a customizable, terminal-based system utility that transforms your Linux environment based on predefined states called **Modes**. Think of it as a supercharged "Do Not Disturb" combined with a performance optimizer.

Whether you are jumping into a deep work session, gaming, or giving a presentation, ModeOS automatically adjusts your system brightness, volume, night light (blue light filter), and dynamically manages your running applications (prioritizing what you need and killing distractions).

---

## ⚡ Features

- **Hardware Control:** Automatically adjust Brightness, Volume, and Night Light based on the active mode.
- **Distraction Blocking & Focusing:** Kill distracting apps instantly while prioritizing your active tasks by intelligently adjusting process priority (nice values).
- **Graceful Reversions:** Before a mode is applied, ModeOS safely saves your exact setup. Use `revert` to jump backwards perfectly when you're done.
- **YAML Configurable:** Modes are completely customizable using simple, human-readable YAML files.
- **Self-Healing & Fault Tolerant:** Includes dynamic system fallbacks. If an application backend isn't present to adjust audio or video, ModeOS reacts organically without crashing.

---

## 🛠️ Prerequisites Dependencies

ModeOS requires the following dependencies installed on your Linux system to work completely. The system won't crash if they are missing, but features will dynamically disable.

Make sure you have installed:
- `python3`
- `python3-pip` (Install dependencies with: `pip install -r requirements.txt`)
- `pactl` (For Audio control)
- `brightnessctl` (For Display brightness)

*Note: Changing process priorities below zero will likely require ModeOS to be executed as root (`sudo`).*

---

## 🚀 Getting Started

### 1. Initial Setup (Scan Your Apps)
Before applying any modes, ModeOS needs to index the graphical applications installed on your system.
```bash
python3 main.py scan
```
This builds a local database of your applications so that you can simply type application names (like `discord` or `vscode`) in your YAML mode configurations without tracking their exact executable names.

### 2. Configure Your Modes
Navigate to the `modes/` directory. You will find several YAML files (e.g., `deep_work.yaml`, `music.yaml`, `gaming.yaml`).
You can edit these to tweak how your setup behaves:
- **`brightness` / `volume`**: Target percentage (`0` - `100`).
- **`kill_all_except_allow`**: A strict focus mode that eliminates all user-facing apps except those whitelisted.
- **`boost_apps` / `reduce_apps`**: Adjust CPU availability by giving specific utilities priority across the hardware stack.

### 3. Check System Health
You can instantly visualize if your machine has the right background services hooked up:
```bash
python3 main.py health
```

---

## 💻 Commands Summary

**Apply a Mode**
```bash
# Safely apply a mode via its YAML filename (without the extension)
python3 main.py mode deep_work
```

**Dry Run Mode (Safe Preview)**
Want to see what a mode does before actually shutting down processes or blinding your screen? Append `--dry-run`:
```bash
python3 main.py mode gaming --dry-run
```

**Revert System State**
Instantly shift back to the hardware settings present *before* you launched your last mode.
```bash
python3 main.py revert
```

**Reset to Defaults**
Forcibly jump back to standardized system defaults (100% brightness, 100% volume, 0 Process Priority).
```bash
python3 main.py reset
```

**Fix Log/Data Permissions**
Occasionally Linux can cross permission wires when shifting between `sudo` process commands. Run this to recursively fix standard R/W operations natively.
```bash
python3 main.py fix-permissions
```
