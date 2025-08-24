#!/usr/bin/env python3
"""
TruGrade Professional Services Launcher
Revolutionary card grading platform service orchestration

Adapted from original start_dev_services.py with TruGrade architecture
"""

import asyncio
import subprocess
import sys
import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import signal
import psutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TruGradeServiceLauncher:
    """
    Professional service launcher for TruGrade platform
    Orchestrates all revolutionary grading services
    """
    
    def __init__(self, config_path: str = "config/trugrade_config.json"):
        self.config_path = config_path
        self.config = {}
        self.running_services = {}
        self.service_processes = {}
        
        # Load configuration
        self.load_configuration()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def load_configuration(self):
        """Load TruGrade service configuration"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                # Create default config if not exists
                self.create_default_config()
            
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            
            logger.info(f"🚀 TruGrade configuration loaded from {self.config_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            sys.exit(1)
    
    def create_default_config(self):
        """Create default TruGrade configuration"""
        default_config = {
            "database": {
                "postgresql": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "trugrade_professional",
                    "user": "trugrade_user",
                    "password": "trugrade_pass"
                }
            },
            "cache": {
                "redis": {
                    "host": "localhost",
                    "port": 6379
                }
            },
            "services": {
                "trugrade_platform": {
                    "port": 8000,
                    "script": "main.py",
                    "description": "TruGrade Professional Platform Main Service",
                    "priority": "critical"
                },
                "truscore_engine": {
                    "port": 8001,
                    "script": "core/truscore_engine.py",
                    "description": "TruScore Revolutionary Grading Engine",
                    "priority": "critical"
                },
                "consumer_api": {
                    "port": 8002,
                    "script": "suites/consumer_connection.py",
                    "description": "Consumer API Gateway (CardGradeX Integration)",
                    "priority": "high"
                },
                "data_management": {
                    "port": 8003,
                    "script": "suites/data_management.py",
                    "description": "Data Management Suite",
                    "priority": "high"
                },
                "ai_development": {
                    "port": 8004,
                    "script": "suites/ai_development.py",
                    "description": "AI Development Suite",
                    "priority": "high"
                },
                "business_intelligence": {
                    "port": 8005,
                    "script": "suites/business_intelligence.py",
                    "description": "Business Intelligence Suite",
                    "priority": "medium"
                }
            },
            "revolutionary_features": {
                "photometric_stereo": {
                    "enabled": True,
                    "processing_timeout": 30,
                    "max_concurrent_analyses": 4
                },
                "continuous_learning": {
                    "enabled": True,
                    "feedback_collection": True,
                    "model_update_frequency": "realtime"
                },
                "24_point_centering": {
                    "enabled": True,
                    "precision_level": "microscopic",
                    "confidence_threshold": 0.95
                }
            }
        }
        
        # Ensure config directory exists
        os.makedirs("config", exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"📝 Created default TruGrade configuration at {self.config_path}")
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        logger.info("🔍 Checking TruGrade dependencies...")
        
        required_packages = [
            'fastapi', 'uvicorn', 'torch', 'cv2', 
            'ultralytics', 'numpy', 'PIL'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"❌ Missing required packages: {missing_packages}")
            logger.info("💡 Install with: pip install -r requirements.txt")
            return False
        
        logger.info("✅ All dependencies satisfied")
        return True
    
    def start_service(self, service_name: str, service_config: Dict) -> bool:
        """Start a TruGrade service"""
        try:
            script_path = service_config.get('script', f'{service_name}.py')
            port = service_config.get('port', 8000)
            description = service_config.get('description', service_name)
            
            logger.info(f"🚀 Starting {description} on port {port}...")
            
            # Check if port is available
            if self.is_port_in_use(port):
                logger.warning(f"⚠️ Port {port} already in use for {service_name}")
                return False
            
            # Start the service
            cmd = [sys.executable, script_path]
            if 'port' in service_config:
                cmd.extend(['--port', str(port)])
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.service_processes[service_name] = process
            self.running_services[service_name] = {
                'port': port,
                'pid': process.pid,
                'description': description,
                'status': 'starting'
            }
            
            # Give service time to start
            time.sleep(2)
            
            # Check if service started successfully
            if process.poll() is None:
                self.running_services[service_name]['status'] = 'running'
                logger.info(f"✅ {description} started successfully (PID: {process.pid})")
                return True
            else:
                logger.error(f"❌ {description} failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start {service_name}: {e}")
            return False
    
    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return True
        return False
    
    def start_all_services(self):
        """Start all TruGrade services"""
        logger.info("🚀 Starting TruGrade Professional Platform...")
        
        if not self.check_dependencies():
            return False
        
        services = self.config.get('services', {})
        
        # Start services by priority
        priority_order = ['critical', 'high', 'medium', 'low']
        
        for priority in priority_order:
            for service_name, service_config in services.items():
                if service_config.get('priority', 'medium') == priority:
                    self.start_service(service_name, service_config)
                    time.sleep(1)  # Brief delay between services
        
        self.display_service_status()
        return True
    
    def display_service_status(self):
        """Display status of all running services"""
        logger.info("📊 TruGrade Service Status:")
        logger.info("=" * 80)
        
        for service_name, service_info in self.running_services.items():
            status_emoji = "✅" if service_info['status'] == 'running' else "❌"
            logger.info(f"{status_emoji} {service_info['description']}")
            logger.info(f"   Port: {service_info['port']} | PID: {service_info['pid']} | Status: {service_info['status']}")
        
        logger.info("=" * 80)
        logger.info("🌍 TruGrade Platform Ready for Industry Disruption!")
    
    def stop_all_services(self):
        """Stop all running services"""
        logger.info("🛑 Stopping TruGrade services...")
        
        for service_name, process in self.service_processes.items():
            try:
                if process.poll() is None:
                    logger.info(f"🛑 Stopping {service_name}...")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"⚠️ Force killing {service_name}...")
                        process.kill()
                        process.wait()
                    
                    logger.info(f"✅ {service_name} stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping {service_name}: {e}")
        
        logger.info("✅ All TruGrade services stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        self.stop_all_services()
        sys.exit(0)
    
    def monitor_services(self):
        """Monitor running services and restart if needed"""
        logger.info("👁️ Monitoring TruGrade services...")
        
        try:
            while True:
                for service_name, process in list(self.service_processes.items()):
                    if process.poll() is not None:
                        logger.warning(f"⚠️ Service {service_name} has stopped unexpectedly")
                        
                        if self.config.get('deployment', {}).get('auto_restart', True):
                            logger.info(f"🔄 Restarting {service_name}...")
                            service_config = self.config['services'][service_name]
                            self.start_service(service_name, service_config)
                
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
            self.stop_all_services()

def main():
    """Main entry point"""
    print("🚀 TruGrade Professional Platform Service Launcher")
    print("=" * 60)
    
    launcher = TruGradeServiceLauncher()
    
    if launcher.start_all_services():
        try:
            launcher.monitor_services()
        except KeyboardInterrupt:
            launcher.stop_all_services()
    else:
        logger.error("❌ Failed to start TruGrade services")
        sys.exit(1)

if __name__ == "__main__":
    main()