#!/usr/bin/env python3
"""
TruGrade Professional Shell - Direct Launcher
============================================

Direct launcher for the professional desktop shell with all menu options.
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "desktop_app"))

def main():
    """Launch the professional shell directly"""
    print("🚀 TruGrade Professional Platform")
    print("📋 Complete Desktop Shell with All Menu Options")
    print("=" * 60)
    
    try:
        # Import and launch the professional shell
        from trugrade_professional_shell import TruGradeProfessionalShell
        
        print("✅ Launching Professional Desktop Shell...")
        app = TruGradeProfessionalShell()
        app.mainloop()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure to activate the environment: source trugrade_env/bin/activate")
        return 1
    except Exception as e:
        print(f"❌ Error launching shell: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("👋 TruGrade Professional Shell closed")
    return 0

if __name__ == "__main__":
    exit(main())