import argparse
import sys
from app_scanner import scan_apps
from mode_controller import apply_mode
import shutil
from logger import get_logger

log = get_logger()

def check_health():
    log.info("=== Running System Health Check ===")
    deps = [
        ('pactl', 'OK', 'WARN'),
        ('amixer', 'OK', 'WARN'),
        ('brightnessctl', 'OK', 'WARN'),
        ('xrandr', 'OK', 'WARN'),
        ('redshift', 'OK', 'WARN'),
    ]
    
    for dep, success, fail in deps:
        if shutil.which(dep):
            log.info(f"[{success}] {dep} found")
        else:
            log.info(f"[{fail}] {dep} not installed")
    log.info("=== Health Check Complete ===")

def fix_permissions():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    targets = [os.path.join(base_dir, "data"), os.path.join(base_dir, "logs")]
    
    log.info("=== Fixing Directory Permissions ===")
    for target in targets:
        if os.path.exists(target):
            log.info(f"Fixing permissions on {target}...")
            try:
                os.chmod(target, 0o777)
                for root, dirs, files in os.walk(target):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), 0o777)
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o666)
                log.info(f"[OK] Fixed permissions for {target}")
            except Exception as e:
                log.error(f"[ERROR] Failed to fix permissions on {target}: {e}")
    log.info("=== Permission Fix Complete ===")

def main():
    parser = argparse.ArgumentParser(description="ModeOS - Adaptive OS Mode Manager")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to run")
    
    # 'scan' command
    scan_parser = subparsers.add_parser("scan", help="Scan installed applications")
    
    # 'mode' command
    mode_parser = subparsers.add_parser("mode", help="Switch system mode")
    mode_parser.add_argument("mode_name", help="Name of the mode to activate (e.g., focus, gaming)")
    mode_parser.add_argument("--dry-run", action="store_true", help="Print what would happen without executing commands")
    
    # 'reset' command
    reset_parser = subparsers.add_parser("reset", help="Reset system to default state")
    reset_parser.add_argument("--dry-run", action="store_true", help="Print what would happen without executing commands")
    
    # 'revert' command
    revert_parser = subparsers.add_parser("revert", help="Revert system to previous state before last mode")
    revert_parser.add_argument("--dry-run", action="store_true", help="Print what would happen without executing commands")
    
    # 'health' command
    health_parser = subparsers.add_parser("health", help="Check system application backend dependencies")
    
    # 'fix-permissions' command
    fix_perms_parser = subparsers.add_parser("fix-permissions", help="Fix data and log directory permissions recursively")
    
    args = parser.parse_args()
    
    if args.command == "health":
        check_health()
    elif args.command == "fix-permissions":
        fix_permissions()
    elif args.command == "scan":
        scan_apps()
    elif args.command == "mode":
        from state_manager import save_state
        if not args.dry_run:
            save_state()
        success = apply_mode(args.mode_name, args.dry_run)
        if not success:
            sys.exit(1)
    elif args.command == "reset":
        from mode_controller import reset_system
        success = reset_system(args.dry_run)
        if not success:
            sys.exit(1)
    elif args.command == "revert":
        from state_manager import restore_state
        success = restore_state(args.dry_run)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
