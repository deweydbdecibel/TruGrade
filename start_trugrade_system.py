#!/usr/bin/env python3
"""
TruGrade Professional System Startup
Revolutionary card grading platform system orchestration

Adapted from original services/start_system.py with TruGrade architecture
Includes PWA backend with mobile phone scanning capabilities
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import threading
import time

# Add TruGrade to path
sys.path.append(str(Path(__file__).parent))

# Import TruGrade suites
from suites import (
    DataManagementSuite,
    AIDevelopmentSuite, 
    ProfessionalGradingSuite,
    ConsumerConnectionSuite,
    BusinessIntelligenceSuite,
    SystemAdministrationSuite
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TruGradeSystemOrchestrator:
    """
    Professional system orchestrator for TruGrade platform
    Manages all suites and provides unified API
    """
    
    def __init__(self, config_path: str = "config/trugrade_config.json"):
        self.config_path = config_path
        self.config = {}
        self.app = FastAPI(
            title="TruGrade Professional Platform",
            description="Revolutionary Card Grading System",
            version="1.0.0"
        )
        
        # Initialize suites
        self.data_management = None
        self.ai_development = None
        self.professional_grading = None
        self.consumer_connection = None
        self.business_intelligence = None
        self.system_administration = None
        
        self.is_running = False
        
        # Load configuration
        self.load_configuration()
        
        # Setup FastAPI app
        self.setup_fastapi()
    
    def load_configuration(self):
        """Load TruGrade system configuration"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                self.create_default_config()
            
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            
            logger.info(f"🚀 TruGrade system configuration loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            # Use minimal default config
            self.config = self.get_minimal_config()
    
    def create_default_config(self):
        """Create default TruGrade system configuration"""
        default_config = {
            "system": {
                "name": "TruGrade Professional Platform",
                "version": "1.0.0",
                "environment": "development"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "ssl_enabled": False,
                "cors_origins": ["*"]
            },
            "pwa": {
                "enabled": True,
                "mobile_scanning": True,
                "offline_support": True,
                "push_notifications": True
            },
            "suites": {
                "data_management": {"enabled": True, "priority": 1},
                "ai_development": {"enabled": True, "priority": 2},
                "professional_grading": {"enabled": True, "priority": 3},
                "consumer_connection": {"enabled": True, "priority": 4},
                "business_intelligence": {"enabled": True, "priority": 5},
                "system_administration": {"enabled": True, "priority": 6}
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
                },
                "mobile_scanning": {
                    "enabled": True,
                    "supported_formats": ["jpg", "png", "webp"],
                    "max_file_size": "10MB",
                    "auto_enhancement": True
                }
            },
            "security": {
                "api_rate_limiting": {
                    "enabled": True,
                    "requests_per_minute": 100
                },
                "cors_origins": ["*"],
                "ssl_certificates": {
                    "cert_path": "certificates/localhost+2.pem",
                    "key_path": "certificates/localhost+2-key.pem"
                }
            }
        }
        
        # Ensure config directory exists
        os.makedirs("config", exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"📝 Created default TruGrade system configuration")
    
    def get_minimal_config(self):
        """Get minimal configuration for fallback"""
        return {
            "server": {"host": "0.0.0.0", "port": 8000},
            "suites": {
                "consumer_connection": {"enabled": True, "priority": 1}
            },
            "revolutionary_features": {
                "mobile_scanning": {"enabled": True}
            }
        }
    
    def setup_fastapi(self):
        """Setup FastAPI application with all routes"""
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get("security", {}).get("cors_origins", ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Static files for PWA
        static_dir = Path("static")
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory="static"), name="static")
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "platform": "TruGrade Professional",
                "version": "1.0.0",
                "suites_running": self.is_running
            }
        
        # System status endpoint
        @self.app.get("/api/system/status")
        async def system_status():
            return await self.get_system_status()
        
        # Consumer grading endpoint (preserves mobile scanning)
        @self.app.post("/api/grade/card")
        async def grade_card(card_data: dict):
            """
            Grade card endpoint - preserves mobile phone scanning capability
            """
            if self.consumer_connection:
                return await self.consumer_connection.grade_card_consumer(
                    card_data.get("image_data", b""),
                    card_data.get("metadata", {})
                )
            else:
                raise HTTPException(status_code=503, detail="Consumer connection not available")
        
        # Load card interface endpoint (preserves existing functionality)
        @self.app.post("/api/card/load")
        async def load_card(card_data: dict):
            """
            Load card interface - preserves revolutionary_card_manager.py functionality
            """
            if self.consumer_connection:
                return await self.consumer_connection.load_card_interface(**card_data)
            else:
                raise HTTPException(status_code=503, detail="Consumer connection not available")
        
        # Border calibration endpoint (preserves existing functionality)
        @self.app.post("/api/calibration/border")
        async def calibrate_border(calibration_data: dict):
            """
            Border calibration - preserves revolutionary_border_calibration.py functionality
            """
            if self.consumer_connection:
                return await self.consumer_connection.border_calibration_interface(**calibration_data)
            else:
                raise HTTPException(status_code=503, detail="Consumer connection not available")
        
        # Full analysis endpoint (preserves existing functionality)
        @self.app.post("/api/analysis/full")
        async def full_analysis(analysis_data: dict):
            """
            Full analysis - preserves enhanced_revo_card_manager.py functionality
            """
            if self.consumer_connection:
                return await self.consumer_connection.full_analysis_interface(
                    analysis_data.get("card_data"),
                    **analysis_data.get("options", {})
                )
            else:
                raise HTTPException(status_code=503, detail="Consumer connection not available")
        
        # Business intelligence endpoints
        @self.app.get("/api/business/dashboard")
        async def business_dashboard():
            if self.business_intelligence:
                return await self.business_intelligence.generate_executive_dashboard()
            else:
                raise HTTPException(status_code=503, detail="Business intelligence not available")
        
        logger.info("🌐 FastAPI application configured with TruGrade endpoints")
    
    async def initialize_suites(self):
        """Initialize all TruGrade suites"""
        logger.info("🚀 Initializing TruGrade Professional Suites...")
        
        suite_configs = self.config.get("suites", {})
        
        try:
            # Initialize suites in priority order
            if suite_configs.get("data_management", {}).get("enabled", True):
                self.data_management = DataManagementSuite({})
                await self.data_management.initialize()
                logger.info("📊 Data Management Suite initialized")
            
            if suite_configs.get("ai_development", {}).get("enabled", True):
                self.ai_development = AIDevelopmentSuite({})
                await self.ai_development.initialize()
                logger.info("🔥 AI Development Suite initialized")
            
            if suite_configs.get("professional_grading", {}).get("enabled", True):
                self.professional_grading = ProfessionalGradingSuite({})
                await self.professional_grading.initialize()
                logger.info("💎 Professional Grading Suite initialized")
            
            if suite_configs.get("consumer_connection", {}).get("enabled", True):
                self.consumer_connection = ConsumerConnectionSuite({})
                await self.consumer_connection.initialize()
                logger.info("🌐 Consumer Connection Suite initialized (preserves Load Card, Border Calibration, Full Analysis)")
            
            if suite_configs.get("business_intelligence", {}).get("enabled", True):
                self.business_intelligence = BusinessIntelligenceSuite({})
                await self.business_intelligence.initialize()
                logger.info("📈 Business Intelligence Suite initialized")
            
            if suite_configs.get("system_administration", {}).get("enabled", True):
                self.system_administration = SystemAdministrationSuite({})
                await self.system_administration.initialize()
                logger.info("⚙ System Administration Suite initialized")
            
            self.is_running = True
            logger.info("✅ All TruGrade suites initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Suite initialization failed: {e}")
            raise
    
    async def get_system_status(self):
        """Get comprehensive system status"""
        return {
            "platform": "TruGrade Professional",
            "status": "running" if self.is_running else "initializing",
            "suites": {
                "data_management": "running" if self.data_management else "disabled",
                "ai_development": "running" if self.ai_development else "disabled",
                "professional_grading": "running" if self.professional_grading else "disabled",
                "consumer_connection": "running" if self.consumer_connection else "disabled",
                "business_intelligence": "running" if self.business_intelligence else "disabled",
                "system_administration": "running" if self.system_administration else "disabled"
            },
            "features": {
                "mobile_scanning": self.config.get("revolutionary_features", {}).get("mobile_scanning", {}).get("enabled", False),
                "photometric_stereo": self.config.get("revolutionary_features", {}).get("photometric_stereo", {}).get("enabled", False),
                "24_point_centering": self.config.get("revolutionary_features", {}).get("24_point_centering", {}).get("enabled", False),
                "continuous_learning": self.config.get("revolutionary_features", {}).get("continuous_learning", {}).get("enabled", False)
            }
        }
    
    async def shutdown(self):
        """Graceful shutdown of all suites"""
        logger.info("🛑 Shutting down TruGrade system...")
        
        try:
            if self.system_administration:
                await self.system_administration.shutdown()
            if self.business_intelligence:
                await self.business_intelligence.shutdown()
            if self.consumer_connection:
                await self.consumer_connection.shutdown()
            if self.professional_grading:
                await self.professional_grading.shutdown()
            if self.ai_development:
                await self.ai_development.shutdown()
            if self.data_management:
                await self.data_management.shutdown()
            
            self.is_running = False
            logger.info("✅ TruGrade system shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

async def main():
    """Main system startup"""
    print("🚀 TruGrade Professional Platform System Startup")
    print("=" * 60)
    
    orchestrator = TruGradeSystemOrchestrator()
    
    try:
        # Initialize all suites
        await orchestrator.initialize_suites()
        
        # Get server configuration
        server_config = orchestrator.config.get("server", {})
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 8000)
        
        logger.info(f"🌍 Starting TruGrade server on {host}:{port}")
        logger.info("📱 Mobile scanning enabled - PWA ready")
        logger.info("💎 Load Card, Border Calibration, Full Analysis preserved")
        logger.info("🚀 Revolutionary grading technology active")
        
        # Start the server
        config = uvicorn.Config(
            orchestrator.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested by user")
        await orchestrator.shutdown()
    except Exception as e:
        logger.error(f"❌ System startup failed: {e}")
        await orchestrator.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())