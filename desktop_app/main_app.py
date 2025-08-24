#!/usr/bin/env python3
"""
TruGrade Professional Desktop Application - Main Launcher
Revolutionary card grading platform - Zero web dependencies!

COPY TO: /home/dewster/TruGrade/desktop_app/main_app.py
"""

import sys
import os
import logging
from pathlib import Path

# Add desktop_app to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter")
    
    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow")
    
    try:
        import aiohttp
    except ImportError:
        missing_deps.append("aiohttp")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\n💡 Install with: pip install Pillow aiohttp")
        return False
    
    return True

def check_backend():
    """Check if TruGrade backend is running"""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def main():
    """Main application entry point"""
    print("🚀 TruGrade Professional Desktop Application")
    print("=" * 60)
    print("Revolutionary Card Grading - Zero Web Dependencies!")
    print()
    
    # Check dependencies
    logger.info("🔍 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        sys.exit(1)
    
    print("✅ All dependencies satisfied")
    
    # Check backend connection
    logger.info("🔍 Checking TruGrade backend...")
    if not check_backend():
        print("⚠️  TruGrade backend not detected")
        print("💡 Start backend with: python start_trugrade_system.py")
        print("   The desktop app will still launch, but some features may be limited.")
        print()
    else:
        print("✅ TruGrade backend connected")
    
    # Import and start desktop app
    try:
        logger.info("🚀 Starting TruGrade Desktop Application...")
        from trugrade_desktop import TruGradeDesktop
        
        app = TruGradeDesktop()
        app.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()