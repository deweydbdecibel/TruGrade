#!/usr/bin/env python3
"""
Revolutionary Card Grader Pro - Integrated Start System
Launches all services with proper dependency checking
"""

import subprocess
import time
import sys
import json
import signal
import os
from pathlib import Path
from typing import Dict, List

class RevolutionaryStartSystem:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.processes = {}
        self.config = self.load_config()

    def load_config(self):
        """Load configuration"""
        config_file = self.base_dir / "config" / "revolutionary_config.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)

        # Default config if file doesn't exist
        return {
            "database": {
                "postgresql": {"host": "localhost", "port": 5432, "database": "card_grading"}
            },
            "cache": {
                "valkey": {"host": "localhost", "port": 6380}
            },
            "services": {
                "pwa_backend": {"port": 5000, "script": "services/pwa_backend_api.py"},
                "annotation_server": {"port": 8000, "script": "services/annotation_server.py"},
                "training_system": {"port": 8003, "script": "services/training_system.py"},
                "augmentation_service": {"port": 8002, "script": "services/augmentation_service.py"}
            }
        }

    def check_system_requirements(self):
        """Check if PostgreSQL and Valkey are running"""
        print("🔍 Checking system requirements...")

        # Check PostgreSQL
        try:
            result = subprocess.run(['pg_isready', '-h', 'localhost', '-p', '5432'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ PostgreSQL is running")
            else:
                print("❌ PostgreSQL not running")
                return False
        except FileNotFoundError:
            print("⚠️  PostgreSQL tools not found")
            return False

        # Check Valkey/Redis
        try:
            result = subprocess.run(['valkey-cli', 'ping'], capture_output=True, text=True)
            if result.returncode == 0 and 'PONG' in result.stdout:
                print("✅ Valkey is running")
            else:
                # Try redis-cli as fallback
                result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
                if result.returncode == 0 and 'PONG' in result.stdout:
                    print("✅ Redis is running")
                else:
                    print("❌ Valkey/Redis not running")
                    return False
        except FileNotFoundError:
            print("⚠️  Valkey/Redis tools not found")
            return False

        return True

    def create_directories(self):
        """Create necessary directories"""
        dirs = ['logs', 'data', 'temp', 'models']
        for dir_name in dirs:
            dir_path = self.base_dir / dir_name
            dir_path.mkdir(exist_ok=True)
        print("✅ Created necessary directories")

    def start_service(self, name: str, script_path: str, port: int):
        """Start a single service"""
        script_full_path = self.base_dir / script_path

        if not script_full_path.exists():
            print(f"⚠️  {script_path} not found, skipping {name}")
            return None

        print(f"🚀 Starting {name}...")

        # Create log file
        log_file = self.base_dir / "logs" / f"{name.lower().replace(' ', '_')}.log"

        try:
            # Set up environment with PYTHONPATH
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.base_dir)

            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    [sys.executable, str(script_full_path)],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    cwd=self.base_dir,
                    env=env  # Add this line
                )

            self.processes[name] = {
                'process': process,
                'script': script_path,
                'port': port,
                'log_file': str(log_file)
            }

            print(f"   ✅ {name} started (PID: {process.pid}, Port: {port})")
            return process

        except Exception as e:
            print(f"   ❌ Failed to start {name}: {e}")
            return None

    def start_all_services(self):
        """Start all configured services"""
        print("\n🚀 Starting Revolutionary Card Grader services...")

        for name, config in self.config['services'].items():
            service_name = name.replace('_', ' ').title()
            self.start_service(
                service_name,
                config['script'],
                config['port']
            )
            time.sleep(2)  # Give each service time to start

    def check_service_health(self):
        """Check if services are responding"""
        print("\n🔍 Checking service health...")

        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        for name, info in self.processes.items():
            if info['process'].poll() is None:  # Process is running
                try:
                    # Different health check strategies per service
                    service_key = name.lower().replace(' ', '_')
                    
                    if service_key == 'pwa_backend':
                        response = requests.get(f"https://localhost:{info['port']}/api/health", timeout=5, verify=False)
                    elif service_key == 'annotation_server':
                        response = requests.get(f"http://localhost:{info['port']}/health", timeout=5)
                    elif service_key == 'training_system':
                        # Training system uses FastAPI - try root endpoint
                        response = requests.get(f"http://localhost:{info['port']}/", timeout=5)
                    elif service_key == 'augmentation_service':
                        # Background service - just check if process is alive
                        print(f"   ✅ {name}: Running (background service)")
                        continue
                    else:
                        response = requests.get(f"http://localhost:{info['port']}/health", timeout=5)
                    if response.status_code == 200:
                        print(f"   ✅ {name}: Healthy")
                    else:
                        print(f"   ⚠️  {name}: Running but not responding")
                except requests.exceptions.RequestException:
                    print(f"   ⚠️  {name}: Running but not responding to health check")
            else:
                print(f"   ❌ {name}: Process died")

    def stop_all_services(self):
        """Stop all running services"""
        print("\n🛑 Stopping all services...")

        for name, info in self.processes.items():
            try:
                process = info['process']
                if process.poll() is None:  # Process is still running
                    print(f"   Stopping {name}...")
                    process.terminate()

                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                        print(f"   ✅ {name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        print(f"   🔥 Force killing {name}...")
                        process.kill()
                        process.wait()
                        print(f"   ✅ {name} force stopped")
                else:
                    print(f"   ✅ {name} already stopped")

            except Exception as e:
                print(f"   ❌ Error stopping {name}: {e}")

    def show_status(self):
        """Show current service status"""
        print("\n📊 Service Status:")
        print("=" * 60)

        if not self.processes:
            print("   No services running")
            return

        for name, info in self.processes.items():
            if info['process'].poll() is None:
                print(f"   ✅ {name}")
                print(f"      PID: {info['process'].pid}")
                print(f"      Port: {info['port']}")
                print(f"      Log: {info['log_file']}")
            else:
                print(f"   ❌ {name} (stopped)")

        print(f"\n🎯 Access Points:")
        print(f"   Mobile PWA: http://localhost:{self.config['services']['pwa_backend']['port']}")
        print(f"   Admin Panel: http://localhost:{self.config['services']['annotation_server']['port']}")
        print(f"   Desktop UI: python src/ui/revolutionary_shell.py")

    def monitor_services(self):
        """Monitor running services"""
        print(f"\n🎉 Revolutionary Card Grader Pro is running!")
        self.show_status()
        print(f"\n💡 Commands:")
        print(f"   - View logs: tail -f logs/*.log")
        print(f"   - Check status: python services/start_system.py status")
        print(f"   - Stop all: python services/start_system.py stop")
        print(f"\nPress Ctrl+C to stop all services...")

        # Setup signal handlers
        def signal_handler(signum, frame):
            print(f"\n\n🛑 Received signal {signum}, shutting down...")
            self.stop_all_services()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            while True:
                time.sleep(5)

                # Check for dead processes
                for name, info in list(self.processes.items()):
                    if info['process'].poll() is not None:
                        print(f"\n⚠️  {name} has stopped unexpectedly!")

        except KeyboardInterrupt:
            pass

    def run(self, command=None):
        """Main run method"""
        if command == "stop":
            self.stop_all_services()
            return

        if command == "status":
            self.show_status()
            return

        # Full startup sequence
        print("🚀 Revolutionary Card Grader Pro - System Startup")
        print("=" * 55)

        # Check system requirements
        if not self.check_system_requirements():
            print("\n❌ System requirements not met!")
            print("💡 Run: python scripts/start_dev_services.py setup")
            sys.exit(1)

        # Create directories
        self.create_directories()

        # Start services
        self.start_all_services()

        # Wait a moment for services to initialize
        time.sleep(5)

        # Check health
        self.check_service_health()

        # Monitor
        self.monitor_services()

def main():
    """Main entry point"""
    system = RevolutionaryStartSystem()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        system.run(command)
    else:
        system.run()

if __name__ == "__main__":
    main()
