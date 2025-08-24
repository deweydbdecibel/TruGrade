#!/usr/bin/env python3
"""
TruGrade Professional Service Manager
Advanced service orchestration for the revolutionary platform

TRANSFERRED FROM: scripts/service_manager.py
ENHANCED FOR: TruGrade professional architecture
"""

import subprocess
import time
import sys
import json
import signal
import psutil
from pathlib import Path
from typing import Dict, List, Optional
import logging
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TruGradeServiceManager:
    """
    Professional service manager for TruGrade platform
    Manages all revolutionary grading services with dependency handling
    """
    
    def __init__(self, config_path: str = "config/trugrade_config.json"):
        self.base_dir = Path(__file__).parent.parent
        self.config_path = config_path
        self.config = self.load_config()
        self.processes = {}
        self.service_status = {}
        
        logger.info("🚀 TruGrade Service Manager initialized")
    
    def load_config(self) -> Dict:
        """Load TruGrade configuration"""
        try:
            config_file = self.base_dir / self.config_path
            if config_file.exists():
                with open(config_file) as f:
                    return json.load(f)
            else:
                logger.warning(f"⚠️ Config file not found: {config_file}")
                return self.get_default_config()
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default service configuration"""
        return {
            "services": {
                "trugrade_platform": {"port": 8000, "script": "main.py"},
                "mobile_pwa": {"port": 5000, "script": "mobile_pwa_backend.py"},
                "truscore_engine": {"port": 8001, "script": "core/truscore_engine.py"},
                "consumer_api": {"port": 8002, "script": "suites/consumer_connection.py"}
            },
            "system_services": {
                "postgresql": {"required": False, "port": 5432},
                "redis": {"required": False, "port": 6379}
            }
        }
    
    def check_system_services(self):
        """Check system services (PostgreSQL, Redis, etc.)"""
        logger.info("🔍 Checking system services...")
        
        system_services = self.config.get("system_services", {})
        
        # Check PostgreSQL
        if "postgresql" in system_services:
            try:
                result = subprocess.run(['pg_isready', '-h', 'localhost', '-p', '5432'],
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    logger.info("✅ PostgreSQL running")
                    self.service_status["postgresql"] = "running"
                else:
                    logger.warning("❌ PostgreSQL not running")
                    self.service_status["postgresql"] = "stopped"
                    if system_services["postgresql"].get("required", False):
                        self.start_system_service('postgresql')
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.warning("⚠️ PostgreSQL tools not found or timeout")
                self.service_status["postgresql"] = "unavailable"
        
        # Check Redis
        if "redis" in system_services:
            try:
                result = subprocess.run(['redis-cli', 'ping'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0 and b'PONG' in result.stdout:
                    logger.info("✅ Redis running")
                    self.service_status["redis"] = "running"
                else:
                    logger.warning("❌ Redis not running")
                    self.service_status["redis"] = "stopped"
                    if system_services["redis"].get("required", False):
                        self.start_system_service('redis')
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.warning("⚠️ Redis tools not found or timeout")
                self.service_status["redis"] = "unavailable"
    
    def start_system_service(self, service: str):
        """Start system service"""
        try:
            if sys.platform.startswith('linux'):
                subprocess.run(['sudo', 'systemctl', 'start', f'{service}.service'], 
                             check=True, timeout=30)
                logger.info(f"✅ Started {service}")
            elif sys.platform == 'darwin':  # macOS
                if service == 'postgresql':
                    subprocess.run(['brew', 'services', 'start', 'postgresql'], 
                                 check=True, timeout=30)
                elif service == 'redis':
                    subprocess.run(['brew', 'services', 'start', 'redis'], 
                                 check=True, timeout=30)
                logger.info(f"✅ Started {service}")
            else:
                logger.warning(f"⚠️ Manual start required for {service} on {sys.platform}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to start {service}: {e}")
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout starting {service}")
    
    def check_port_available(self, port: int) -> bool:
        """Check if port is available"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return False
        return True
    
    def start_application_services(self):
        """Start all TruGrade application services"""
        services = self.config.get("services", {})
        
        logger.info("🚀 Starting TruGrade application services...")
        
        # Start services in priority order
        service_order = [
            "trugrade_platform",
            "truscore_engine", 
            "mobile_pwa",
            "consumer_api"
        ]
        
        for service_name in service_order:
            if service_name in services:
                service_config = services[service_name]
                self.start_service(service_name, service_config)
                time.sleep(2)  # Brief delay between services
    
    def start_service(self, name: str, config: Dict):
        """Start individual service"""
        script = config.get("script", f"{name}.py")
        port = config.get("port", 8000)
        
        script_path = self.base_dir / script
        
        if not script_path.exists():
            logger.warning(f"⚠️ Script not found: {script_path}")
            self.service_status[name] = "script_missing"
            return
        
        # Check if port is available
        if not self.check_port_available(port):
            logger.warning(f"⚠️ Port {port} already in use for {name}")
            self.service_status[name] = "port_conflict"
            return
        
        logger.info(f"   Starting {name} on port {port}...")
        
        # Create logs directory
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"{name}.log"
        
        try:
            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    [sys.executable, str(script_path), "--port", str(port)],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    cwd=self.base_dir
                )
            
            self.processes[name] = process
            self.service_status[name] = "running"
            logger.info(f"   ✅ {name} started (PID: {process.pid})")
            
        except Exception as e:
            logger.error(f"   ❌ Failed to start {name}: {e}")
            self.service_status[name] = "failed"
    
    def stop_services(self):
        """Stop all running services"""
        logger.info("🛑 Stopping TruGrade services...")
        
        for name, process in self.processes.items():
            try:
                if process.poll() is None:  # Process is still running
                    logger.info(f"   Stopping {name}...")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                        logger.info(f"   ✅ Stopped {name}")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"   🔥 Force killing {name}...")
                        process.kill()
                        process.wait()
                        logger.info(f"   🔥 Force killed {name}")
                    
                    self.service_status[name] = "stopped"
                else:
                    logger.info(f"   ✅ {name} already stopped")
                    
            except Exception as e:
                logger.error(f"   ❌ Error stopping {name}: {e}")
    
    def status(self):
        """Show comprehensive service status"""
        logger.info("📊 TruGrade Service Status:")
        logger.info("=" * 50)
        
        # System services
        logger.info("🔧 System Services:")
        for service, status in self.service_status.items():
            if service in ["postgresql", "redis"]:
                status_emoji = "✅" if status == "running" else "❌" if status == "stopped" else "⚠️"
                logger.info(f"   {status_emoji} {service}: {status}")
        
        # Application services
        logger.info("\n🚀 Application Services:")
        for name, process in self.processes.items():
            if process.poll() is None:
                logger.info(f"   ✅ {name}: Running (PID: {process.pid})")
            else:
                logger.info(f"   ❌ {name}: Stopped")
        
        # Service status summary
        logger.info(f"\n📈 Status Summary:")
        for name, status in self.service_status.items():
            status_emoji = "✅" if status == "running" else "❌"
            logger.info(f"   {status_emoji} {name}: {status}")
    
    def start(self):
        """Start all services"""
        logger.info("🚀 Starting TruGrade Professional Platform...")
        
        # Check system services first
        self.check_system_services()
        
        # Start application services
        self.start_application_services()
        
        # Display access points
        self.display_access_points()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, lambda s, f: self.shutdown_handler())
        signal.signal(signal.SIGTERM, lambda s, f: self.shutdown_handler())
        
        # Monitor services
        self.monitor_services()
    
    def display_access_points(self):
        """Display service access points"""
        logger.info("\n🎯 TruGrade Platform Access Points:")
        logger.info("=" * 50)
        
        services = self.config.get("services", {})
        for name, config in services.items():
            port = config.get("port", 8000)
            if name in self.processes and self.processes[name].poll() is None:
                logger.info(f"🌐 {name}: http://localhost:{port}")
        
        logger.info("\n📱 Mobile PWA: Add to home screen for best experience")
        logger.info("🎯 Revolutionary grading technology active!")
    
    def monitor_services(self):
        """Monitor running services"""
        logger.info("\n👁️ Monitoring services... (Ctrl+C to stop)")
        
        try:
            while True:
                time.sleep(30)  # Check every 30 seconds
                
                # Check for dead processes
                dead_services = []
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        dead_services.append(name)
                        logger.warning(f"⚠️ {name} has stopped unexpectedly!")
                        self.service_status[name] = "crashed"
                
                # Optionally restart dead services
                restart_on_failure = self.config.get("restart_on_failure", True)
                if restart_on_failure and dead_services:
                    for service_name in dead_services:
                        if service_name in self.config.get("services", {}):
                            logger.info(f"🔄 Restarting {service_name}...")
                            service_config = self.config["services"][service_name]
                            self.start_service(service_name, service_config)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown_handler()
    
    def shutdown_handler(self):
        """Handle graceful shutdown"""
        logger.info("\n🛑 Shutting down TruGrade Platform...")
        self.stop_services()
        logger.info("✅ TruGrade Platform shutdown complete")
        sys.exit(0)

def main():
    """Main entry point"""
    manager = TruGradeServiceManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "start":
            manager.start()
        elif command == "stop":
            manager.stop_services()
        elif command == "status":
            manager.status()
        elif command == "restart":
            manager.stop_services()
            time.sleep(2)
            manager.start()
        else:
            print("Usage: python trugrade_service_manager.py [start|stop|status|restart]")
    else:
        manager.start()

if __name__ == "__main__":
    main()