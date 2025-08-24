#!/usr/bin/env python3
"""
TruGrade Professional Platform
The main orchestrator for the revolutionary card grading ecosystem
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .truscore_engine import TruScoreEngine
from .system.suite_manager import SuiteManager
from .system.api_gateway import APIGateway
from .ui.platform_interface import PlatformInterface

class TruGradePlatform:
    """
    TruGrade Professional Platform
    
    The central orchestrator that manages all suites, the TruScore engine,
    and provides the unified interface for the revolutionary grading platform.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.truscore_engine: Optional[TruScoreEngine] = None
        self.suite_manager: Optional[SuiteManager] = None
        self.api_gateway: Optional[APIGateway] = None
        self.platform_interface: Optional[PlatformInterface] = None
        
        # Platform state
        self.is_initialized = False
        self.is_running = False
        
    async def initialize(self):
        """Initialize the TruGrade platform"""
        try:
            self.logger.info("🔥 Initializing TruGrade Platform...")
            
            # Initialize TruScore Engine
            self.logger.info("🎯 Initializing TruScore Engine...")
            self.truscore_engine = TruScoreEngine(self.config.get('truscore', {}))
            await self.truscore_engine.initialize()
            
            # Initialize Suite Manager
            self.logger.info("📊 Initializing Suite Manager...")
            self.suite_manager = SuiteManager(self.config.get('suites', {}))
            await self.suite_manager.initialize()
            
            # Initialize API Gateway
            self.logger.info("🌐 Initializing API Gateway...")
            self.api_gateway = APIGateway(
                self.config.get('api', {}),
                self.truscore_engine
            )
            await self.api_gateway.initialize()
            
            # Initialize Platform Interface
            self.logger.info("🖥️ Initializing Platform Interface...")
            self.platform_interface = PlatformInterface(
                self.config.get('ui', {}),
                self.suite_manager,
                self.truscore_engine,
                self.api_gateway
            )
            await self.platform_interface.initialize()
            
            self.is_initialized = True
            self.logger.info("✅ TruGrade Platform initialization complete")
            
        except Exception as e:
            self.logger.error(f"❌ Platform initialization failed: {e}")
            raise
            
    async def run(self):
        """Run the TruGrade platform"""
        if not self.is_initialized:
            raise RuntimeError("Platform not initialized")
            
        try:
            self.is_running = True
            self.logger.info("🚀 TruGrade Platform running...")
            
            # Start all services
            await asyncio.gather(
                self.api_gateway.start(),
                self.platform_interface.run(),
                return_exceptions=True
            )
            
        except Exception as e:
            self.logger.error(f"❌ Platform runtime error: {e}")
            raise
        finally:
            self.is_running = False
            
    async def shutdown(self):
        """Gracefully shutdown the platform"""
        try:
            self.logger.info("🔄 Shutting down TruGrade Platform...")
            
            # Shutdown components in reverse order
            if self.platform_interface:
                await self.platform_interface.shutdown()
                
            if self.api_gateway:
                await self.api_gateway.shutdown()
                
            if self.suite_manager:
                await self.suite_manager.shutdown()
                
            if self.truscore_engine:
                await self.truscore_engine.shutdown()
                
            self.is_initialized = False
            self.is_running = False
            
            self.logger.info("✅ TruGrade Platform shutdown complete")
            
        except Exception as e:
            self.logger.error(f"❌ Error during platform shutdown: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get platform status"""
        return {
            "platform": {
                "initialized": self.is_initialized,
                "running": self.is_running,
                "version": "1.0.0"
            },
            "truscore_engine": self.truscore_engine.get_status() if self.truscore_engine else None,
            "suite_manager": self.suite_manager.get_status() if self.suite_manager else None,
            "api_gateway": self.api_gateway.get_status() if self.api_gateway else None
        }