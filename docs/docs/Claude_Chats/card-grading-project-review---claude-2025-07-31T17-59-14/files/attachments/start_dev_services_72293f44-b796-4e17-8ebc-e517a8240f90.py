#!/usr/bin/env python3
"""
🚀 DEVELOPMENT SERVICES STARTER
==============================

Starts PostgreSQL and Valkey services for development, then launches the card grading system.
For Arch Linux development environment.
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def run_command(command, description, check_output=False):
    """Run a system command with error handling"""
    try:
        print(f"🔧 {description}...")

        if check_output:
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            return result.returncode == 0, result.stdout.strip()
        else:
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print(f"✅ {description} - Success")
                return True
            else:
                print(f"❌ {description} - Failed: {result.stderr}")
                return False

    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def check_service_status(service_name):
    """Check if a systemd service is active"""
    success, output = run_command(
        f"systemctl is-active {service_name}",
        f"Checking {service_name} status",
        check_output=True
    )
    return success and output == "active"

def start_service(service_name):
    """Start a systemd service"""
    if check_service_status(service_name):
        print(f"✅ {service_name} already running")
        return True

    print(f"🚀 Starting {service_name}...")
    success = run_command(
        f"sudo systemctl start {service_name}",
        f"Starting {service_name}"
    )

    if success:
        # Wait a moment for service to fully start
        time.sleep(2)

        # Verify it's running
        if check_service_status(service_name):
            print(f"✅ {service_name} started successfully")
            return True
        else:
            print(f"⚠️ {service_name} started but not yet active, waiting...")
            time.sleep(3)
            return check_service_status(service_name)

    return False

def enable_service(service_name):
    """Enable a systemd service to start on boot (optional)"""
    return run_command(
        f"sudo systemctl enable {service_name}",
        f"Enabling {service_name} for auto-start"
    )

def check_postgresql_ready():
    """Check if PostgreSQL is ready to accept connections"""
    for attempt in range(5):
        success, _ = run_command(
            "pg_isready -h localhost -p 5432",
            f"Testing PostgreSQL connection (attempt {attempt + 1})",
            check_output=True
        )
        if success:
            print("✅ PostgreSQL ready for connections")
            return True
        time.sleep(2)

    print("⚠️ PostgreSQL may not be ready for connections")
    return False

def check_valkey_ready():
    """Check if Valkey is ready to accept connections"""
    for attempt in range(5):
        try:
            result = subprocess.run(
                ["valkey-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0 and "PONG" in result.stdout:
                print("✅ Valkey ready for connections")
                return True
        except:
            pass
        time.sleep(2)

    print("⚠️ Valkey may not be ready for connections")
    return False

def main():
    """Main function to start all development services"""

    print("🚀 REVOLUTIONARY CARD GRADER - DEV SERVICES STARTER")
    print("=" * 60)
    print("🐧 Starting services for Arch Linux development environment")
    print()

    # Check if running as regular user (sudo will be called when needed)
    if os.geteuid() == 0:
        print("⚠️ Don't run this script as root - it will call sudo when needed")
        return False

    success_count = 0
    total_services = 2

    # Start PostgreSQL
    print("📊 Starting PostgreSQL...")
    if start_service("postgresql.service"):
        if check_postgresql_ready():
            success_count += 1
        else:
            print("⚠️ PostgreSQL started but connection test failed")
    else:
        print("❌ Failed to start PostgreSQL")

    print()

    # Start Valkey
    print("🔴 Starting Valkey...")
    if start_service("valkey.service"):
        if check_valkey_ready():
            success_count += 1
        else:
            print("⚠️ Valkey started but connection test failed")
    else:
        print("❌ Failed to start Valkey")

    print()
    print("=" * 60)

    if success_count == total_services:
        print("🎉 ALL SERVICES STARTED SUCCESSFULLY!")
        print("✅ PostgreSQL: Ready")
        print("✅ Valkey: Ready")
        print()

        # Ask if user wants to launch the main system
        try:
            launch = input("🚀 Launch start_system.py now? (y/n): ").lower().strip()
            if launch in ['y', 'yes', '']:
                print("\n🎯 Launching Revolutionary Card Grader System...")

                # Check if start_system.py exists
                if Path("start_system.py").exists():
                    try:
                        subprocess.run([sys.executable, "start_system.py"])
                    except KeyboardInterrupt:
                        print("\n👋 System startup cancelled")
                else:
                    print("❌ start_system.py not found in current directory")
                    print("💡 You can run it manually: python start_system.py")
            else:
                print("👍 Services are running - you can now run start_system.py manually")

        except KeyboardInterrupt:
            print("\n👍 Services started successfully")

    else:
        print(f"⚠️ Only {success_count}/{total_services} services started successfully")
        print("\n🔧 Troubleshooting tips:")
        print("   • Make sure PostgreSQL is installed: sudo pacman -S postgresql")
        print("   • Make sure Valkey is installed: sudo pacman -S valkey")
        print("   • Initialize PostgreSQL if first time: sudo -u postgres initdb -D /var/lib/postgres/data")
        print("   • Check service logs: sudo journalctl -u postgresql.service")
        print("   • Check service logs: sudo journalctl -u valkey.service")
        return False

    return True

def quick_status():
    """Quick status check of all services"""
    print("🔍 SERVICES STATUS CHECK")
    print("=" * 30)

    services = ["postgresql.service", "valkey.service"]

    for service in services:
        if check_service_status(service):
            print(f"✅ {service}: Active")
        else:
            print(f"❌ {service}: Inactive")

    print()

def stop_services():
    """Stop all services (cleanup function)"""
    print("🛑 STOPPING DEVELOPMENT SERVICES")
    print("=" * 40)

    services = ["postgresql.service", "valkey.service"]

    for service in services:
        run_command(
            f"sudo systemctl stop {service}",
            f"Stopping {service}"
        )

    print("👋 All services stopped")

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            quick_status()
        elif sys.argv[1] == "stop":
            stop_services()
        elif sys.argv[1] == "help":
            print("🚀 Revolutionary Card Grader - Dev Services")
            print("Usage:")
            print("  python start_dev_services.py        - Start all services")
            print("  python start_dev_services.py status - Check service status")
            print("  python start_dev_services.py stop   - Stop all services")
            print("  python start_dev_services.py help   - Show this help")
        else:
            print("❌ Unknown command. Use 'help' for usage information.")
    else:
        # Default: start services
        success = main()
        if not success:
            sys.exit(1)
