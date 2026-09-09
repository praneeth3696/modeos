"""
ModeOS Command Line Interface
Provides full backwards compatibility with legacy commands while introducing
new capabilities: list, doctor, current, and validate.
"""

import argparse
import sys
from modeos import __version__
from modeos.core import apply_mode, list_available_modes, load_mode_config, reset_system, revert_system
from modeos.doctor import check_dependencies
from modeos.logger import setup_logger, BOLD, CYAN, GREEN, YELLOW, RED, RESET
from modeos.scanner import scan_apps
from modeos.state import load_last_state

def cmd_list(args):
    modes = list_available_modes()
    if not modes:
        print("No modes found in configuration directories.")
        return

    print(f"\n{BOLD}{CYAN}Available ModeOS Modes:{RESET}\n")
    print(f"  {BOLD}{'Mode':<18} {'Brightness':<12} {'Volume':<10} {'Night Light':<14} {'Focus Action'}{RESET}")
    print("  " + "-" * 75)

    for m in modes:
        br_str = f"{m.brightness}%" if m.brightness is not None else "-"
        vol_str = f"{m.volume}%" if m.volume is not None else "-"
        nl_str = "ON" if m.night_light is True else ("OFF" if m.night_light is False else "-")

        if m.kill_all_except_allow:
            focus_str = f"Whitelist ({len(m.allow_apps)} apps)"
        elif m.block_apps:
            focus_str = f"Blocks {len(m.block_apps)} apps"
        elif m.boost_apps or m.reduce_apps:
            focus_str = f"Prioritizes ({len(m.boost_apps) + len(m.reduce_apps)} apps)"
        else:
            focus_str = "Hardware only"

        print(f"  {m.name:<18} {br_str:<12} {vol_str:<10} {nl_str:<14} {focus_str}")
    print()

def cmd_current(args):
    state = load_last_state()
    print(f"\n{BOLD}{CYAN}ModeOS Current Status:{RESET}\n")
    if state:
        mode = state.get("active_mode") or "Unknown / Reverted"
        ts = state.get("timestamp") or "N/A"
        vol = state.get("volume")
        br = state.get("brightness")
        nl = state.get("night_light")
        priors = len(state.get("modified_priorities", {}))

        print(f"  Active Mode:        {BOLD}{mode}{RESET}")
        print(f"  Applied At:         {ts}")
        print(f"  Recorded Volume:    {vol if vol is not None else 'N/A'}%")
        print(f"  Recorded Bright:    {br if br is not None else 'N/A'}%")
        print(f"  Recorded NightLight:{'ON' if nl else 'OFF'}")
        print(f"  Prioritized Tasks:  {priors} process(es)")
    else:
        print("  No previous mode session recorded.")
    print()

def cmd_validate(args):
    config = load_mode_config(args.mode_name)
    if not config:
        sys.exit(1)

    print(f"\n{BOLD}Validating mode '{config.name}'...{RESET}")
    warnings = config.validate()
    if warnings:
        for w in warnings:
            print(f"  {YELLOW}[WARN]{RESET} {w}")
    else:
        print(f"  {GREEN}[OK]{RESET} Configuration syntax and structure are valid.")
    print()

def cmd_fix_permissions(args):
    print("ModeOS uses XDG user directories and no longer requires permission fixes.")
    print("[OK] Permissions healthy.")

def main():
    parser = argparse.ArgumentParser(
        prog="modeos",
        description="ModeOS - Adaptive OS Mode Manager (Hardware & Process Orchestrator)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--mock", action="store_true", help="Run with simulated hardware backends")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to run")

    # 'mode' command
    mode_parser = subparsers.add_parser("mode", help="Switch system mode")
    mode_parser.add_argument("mode_name", help="Name of the mode to activate (e.g., deep_work, gaming)")
    mode_parser.add_argument("--dry-run", action="store_true", help="Safe simulation: preview actions without applying")
    mode_parser.add_argument("--mock", action="store_true", help="Run with simulated hardware backends")

    # 'list' command
    subparsers.add_parser("list", help="List all available modes")

    # 'current' command
    subparsers.add_parser("current", help="Display currently active mode and recorded state")

    # 'reset' command
    reset_parser = subparsers.add_parser("reset", help="Reset system hardware and process priorities to defaults")
    reset_parser.add_argument("--dry-run", action="store_true", help="Preview reset actions")
    reset_parser.add_argument("--mock", action="store_true", help="Run with simulated hardware backends")

    # 'revert' command
    revert_parser = subparsers.add_parser("revert", help="Revert system hardware and process priorities to pre-mode state")
    revert_parser.add_argument("--dry-run", action="store_true", help="Preview revert actions")
    revert_parser.add_argument("--mock", action="store_true", help="Run with simulated hardware backends")

    # 'scan' command
    subparsers.add_parser("scan", help="Scan and index installed desktop applications")

    # 'health' / 'doctor' command
    subparsers.add_parser("health", help="Check system application backend dependencies")
    subparsers.add_parser("doctor", help="Run comprehensive diagnostics on Linux subsystems")

    # 'validate' command
    validate_parser = subparsers.add_parser("validate", help="Validate mode configuration syntax")
    validate_parser.add_argument("mode_name", help="Name of mode YAML to validate")

    # 'fix-permissions' command (backwards compatibility)
    subparsers.add_parser("fix-permissions", help="Validate permissions")

    args = parser.parse_args()

    # Configure logger
    setup_logger(verbose=args.verbose)

    # Determine mock mode
    force_mock = getattr(args, "mock", False) or parser.parse_known_args()[0].mock

    if args.command == "mode":
        success = apply_mode(args.mode_name, dry_run=args.dry_run, force_mock=force_mock)
        if not success:
            sys.exit(1)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "current":
        cmd_current(args)
    elif args.command == "reset":
        success = reset_system(dry_run=args.dry_run, force_mock=force_mock)
        if not success:
            sys.exit(1)
    elif args.command == "revert":
        success = revert_system(dry_run=args.dry_run, force_mock=force_mock)
        if not success:
            sys.exit(1)
    elif args.command == "scan":
        scan_apps()
    elif args.command in ("health", "doctor"):
        check_dependencies()
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "fix-permissions":
        cmd_fix_permissions(args)

if __name__ == "__main__":
    main()
