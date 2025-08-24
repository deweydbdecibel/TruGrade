#!/usr/bin/env python3
"""
TruGrade Professional Platform - Quick Launcher
==============================================

Quick launcher for the TruGrade Professional Platform.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch TruGrade Professional Platform"""
    print("🚀 TruGrade Professional Platform Launcher")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found. Please run from project root.")
        return 1
    
    try:
        # Launch the main application
        result = subprocess.run([sys.executable, "main.py"], check=True)
        return result.returncode
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching TruGrade: {e}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n👋 TruGrade Professional Platform closed by user")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())