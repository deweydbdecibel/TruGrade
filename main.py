#!/usr/bin/env python3
"""
TruGrade Professional Card Grading Platform
Main Application Entry Point

The revolutionary platform that will overthrow traditional card grading
through superior AI technology, speed, and accuracy.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional

# Add TruGrade to Python path
TRUGRADE_ROOT = Path(__file__).parent
sys.path.insert(0, str(TRUGRADE_ROOT))

from core.trugrade_platform import TruGradePlatform
from core.system.logging_config import setup_logging
from core.system.config_manager import ConfigManager
from core.system.startup_checks import perform_startup_checks

class TruGradeApplication:
    """
    TruGrade Professional Platform Application
    
    The main application class that orchestrates the entire TruGrade ecosystem,
    including the TruScore grading engine and all professional suites.
    """
    
    def __init__(self):
        self.platform: Optional[TruGradePlatform] = None
        self.config_manager = ConfigManager()
        self.logger = None
        
    async def initialize(self) -> bool:
        """
        Initialize the TruGrade platform
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Setup logging
            self.logger = setup_logging()
            self.logger.info("🚀 TruGrade Platform Starting...")
            
            # Load configuration
            config = await self.config_manager.load_config()
            self.logger.info("⚙️ Configuration loaded successfully")
            
            # Perform startup checks
            startup_success = await perform_startup_checks()
            if not startup_success:
                self.logger.error("❌ Startup checks failed")
                return False
                
            # Initialize TruGrade Platform
            self.platform = TruGradePlatform(config)
            await self.platform.initialize()
            
            self.logger.info("✅ TruGrade Platform initialized successfully")
            self.logger.info("🎯 TruScore Engine ready for revolutionary grading")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Platform initialization failed: {e}")
            else:
                print(f"❌ Critical error during startup: {e}")
            return False
            
    async def run(self):
        """Run the TruGrade platform"""
        try:
            if not self.platform:
                raise RuntimeError("Platform not initialized")
                
            self.logger.info("🔥 Launching TruGrade Professional Interface...")
            await self.platform.run()
            
        except KeyboardInterrupt:
            self.logger.info("🛑 Shutdown requested by user")
        except Exception as e:
            self.logger.error(f"❌ Runtime error: {e}")
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Gracefully shutdown the platform"""
        try:
            if self.platform:
                self.logger.info("🔄 Shutting down TruGrade Platform...")
                await self.platform.shutdown()
                
            self.logger.info("✅ TruGrade Platform shutdown complete")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")

def print_banner():
    """Print the TruGrade startup banner"""
    banner = """
    ████████╗██████╗ ██╗   ██╗ ██████╗ ██████╗  █████╗ ██████╗ ███████╗
    ╚══██╔══╝██╔══██╗██║   ██║██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██╔════╝
       ██║   ██████╔╝██║   ██║██║  ███╗██████╔╝███████║██║  ██║█████╗  
       ██║   ██╔══██╗██║   ██║██║   ██║██╔══██╗██╔══██║██║  ██║██╔══╝  
       ██║   ██║  ██║╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝███████╗
       ╚═╝   ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝
                                                                        
    ████████╗██████╗ ██╗   ██╗███████╗ ██████╗ ██████╗ ██████╗ ███████╗
    ╚══██╔══╝██╔══██╗██║   ██║██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
       ██║   ██████╔╝██║   ██║███████╗██║     ██║   ██║██████╔╝█████╗  
       ██║   ██╔══██╗██║   ██║╚════██║██║     ██║   ██║██╔══██╗██╔══╝  
       ██║   ██║  ██║╚██████╔╝███████║╚██████╗╚██████╔╝██║  ██║███████╗
       ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝
    
    🔥 PROFESSIONAL CARD GRADING PLATFORM 🔥
    Powered by TruScore AI Engine
    
    🎯 Mission: Revolutionize card grading through superior AI technology
    ⚡ Speed: Sub-second professional grading
    🎯 Accuracy: 98.5%+ grading precision
    🔬 Technology: Photometric stereo + 24-point centering + Phoenix AI
    
    Ready to overthrow PSA, BGS, and SGC? Let's make history! 🚀
    """
    print(banner)

async def main():
    """Main application entry point"""
    # Print startup banner
    print_banner()
    
    # Create and run application
    app = TruGradeApplication()
    
    # Initialize platform
    if await app.initialize():
        # Run the platform
        await app.run()
    else:
        print("❌ Failed to initialize TruGrade Platform")
        sys.exit(1)

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ TruGrade requires Python 3.8 or higher")
        sys.exit(1)
        
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 TruGrade Platform stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)