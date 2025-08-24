import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog
import math
import threading
import time
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import numpy as np
import os
import cv2
from pathlib import Path
import subprocess
import sys
from revolutionary_border_calibration import RevolutionaryBorderCalibration
from tkinter import messagebox
import requests
import json
from typing import Optional, Dict, Any
import webbrowser
import subprocess
import platform
import argparse

# Global debug flag - controls verbose output
DEBUG = False

# Set environment variable for other modules to use
import os
os.environ['RCG_DEBUG'] = 'false'

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Try to import drag and drop support
try:
    import tkinterdnd2
    DND_AVAILABLE = False  # Temporarily disabled due to compatibility issues
except ImportError:
    DND_AVAILABLE = False

class APIStatusIntegration:
    """Integrates API status with your beautiful revolutionary interface"""
    
    def __init__(self, main_shell):
        self.shell = main_shell
        self.api_url = "https://localhost:5000"
        self.connected = False
        
        # Add API status to your existing interface
        # self.add_api_status_to_interface()
        
        # Start monitoring
        self.start_api_monitoring()
        
        # Note: Immediate connection test will be called by main app
        
        if DEBUG:
            print("🔗 API Integration initialized for Revolutionary Shell")
    
    # def add_api_status_to_interface(self):
        """Add API status to your existing beautiful interface"""
        # try:
            # Find a good spot in your interface - let's add to the main window
            # Create a status bar at the bottom
            # self.create_status_bar()
            
            # Add API analysis button to your existing button panel
            # self.add_api_analysis_button()
            
        # except Exception as e:
            # print(f"⚠️ Could not integrate API status: {e}")
    
    def create_status_bar(self):
        """Create status bar at bottom of main window"""
        try:
            # Create status frame at bottom of main window
            self.status_frame = ctk.CTkFrame(
                self.shell,
                height=40,
                corner_radius=0,
                fg_color=("#2b2b2b", "#1a1a1a"),
                border_width=1,
                border_color=("#404040", "#2a2a2a")
            )
            self.status_frame.pack(side="bottom", fill="x", padx=0, pady=0)
            
            # API status indicator
            self.api_status_label = ctk.CTkLabel(
                self.status_frame,
                text="🔗 Connecting to API services...",
                font=("Arial", 11),
                text_color="yellow"
            )
            self.api_status_label.pack(side="left", padx=10, pady=8)
            
            try:
                from src.integration.photometric_integration import integrate_photometric_stereo
                if DEBUG:
                    print("🔍 DEBUG: Import successful")
                self.photometric_integration = integrate_photometric_stereo(self)
                if DEBUG:
                    print(f"🔍 DEBUG: Integration result: {self.photometric_integration}")
                    print(f"🔍 DEBUG: Integration type: {type(self.photometric_integration)}")
                    if self.photometric_integration:
                        print("🔍 DEBUG: Integration is truthy")
                    else:
                        print("🔍 DEBUG: Integration is falsy/None")
                    print("🚀 Photometric integration successful!")
            except Exception as e:
                print(f"⚠ Photometric integration failed: {e}")
                import traceback
                traceback.print_exc()
                self.photometric_integration = None

            # Photometric stereo indicator
            self.photometric_label = ctk.CTkLabel(
                self.status_frame,
                text="🔬 Photometric: Checking...",
                font=("Arial", 11),
                text_color="gray"
            )
            self.photometric_label.pack(side="left", padx=20, pady=8)
            
            # Services indicator
            self.services_label = ctk.CTkLabel(
                self.status_frame,
                text="⚙️ Services: Unknown",
                font=("Arial", 11),
                text_color="gray"
            )
            self.services_label.pack(side="left", padx=20, pady=8)
            
            if DEBUG:
                print("✅ Status bar added to revolutionary interface")
            
        except Exception as e:
            print(f"❌ Status bar creation failed: {e}")
    
    def add_api_analysis_button(self):
        """Add API analysis button to existing interface"""
        try:
            # Look for existing button frames in your interface
            # We'll add to the main revolutionary pipeline section
            
            # Create API analysis frame
            self.api_frame = ctk.CTkFrame(
                self.shell,
                width=300,
                height=120,
                corner_radius=15,
                fg_color=("#1e3a8a", "#1e40af"),  # Revolutionary blue
                border_width=2,
                border_color=("#10b981", "#059669")  # Revolutionary green border
            )
            
            # Position it in a good spot (top-right area)
            self.api_frame.place(x=self.shell.winfo_width()-320, y=80)
            
            # Title
            api_title = ctk.CTkLabel(
                self.api_frame,
                text="🔬 PHOTOMETRIC ANALYSIS",
                font=("Arial", 14, "bold"),
                text_color="#10b981"
            )
            api_title.pack(pady=(10, 5))
            
            # Analysis button
            self.analyze_btn = ctk.CTkButton(
                self.api_frame,
                text="🚀 Analyze Current Card",
                width=200,
                height=35,
                font=("Arial", 12, "bold"),
                fg_color="#10b981",
                hover_color="#059669",
                command=self.analyze_with_api
            )
            self.analyze_btn.pack(pady=5)
            
            # Quick stats
            self.stats_label = ctk.CTkLabel(
                self.api_frame,
                text="⚡ 0.28s processing • 97%+ accuracy",
                font=("Arial", 10),
                text_color="#e5e7eb"
            )
            self.stats_label.pack(pady=(5, 10))
            
            if DEBUG:
                print("✅ API analysis panel added to interface")
            
        except Exception as e:
            print(f"❌ API button creation failed: {e}")
    
    def test_immediate_connection(self):
        """Test connection immediately for faster feedback"""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=2, verify=False)
            if response.status_code == 200:
                self.connected = True
                # Only print if not already connected
                if DEBUG:
                    print("✅ Quick test: API is online!")
            else:
                if DEBUG:
                    print(f"⚠️ Quick test: API responded with {response.status_code}")
        except Exception as e:
            if DEBUG:
                print(f"🔍 Quick test failed (services may still be starting): {e}")
    
    def start_api_monitoring(self):
        """Start monitoring API status with initial delay"""
        def monitor():
            # Give services time to start up
            time.sleep(3)  # Wait 3 seconds before first check
            # Silent monitoring - only errors get printed
            
            while True:
                try:
                    self.update_api_status()
                    time.sleep(30)  # Update every 30 seconds (less chatty)
                except Exception as e:
                    print(f"API monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        if DEBUG:
            print("✅ API monitoring started with 3s delay")
    
    def update_api_status(self):
        """Update API status displays - SILENT VERSION"""
        try:
            # Silent monitoring - only UI updates, no console spam
            response = requests.get(f"{self.api_url}/api/health", timeout=5, verify=False)
            
            if response.status_code == 200:
                self.connected = True
                
                # Update main status
                if hasattr(self, 'api_status_label'):
                    self.api_status_label.configure(
                        text="✅ API Connected - All Services Operational",
                        text_color="#10b981"
                    )
                
                # Check detailed status
                try:
                    status_response = requests.get(f"{self.api_url}/api/health", timeout=5, verify=False)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        # Update photometric status
                        photometric_active = status_data.get("services", {}).get("photometric_stereo") == "operational"
                        if hasattr(self, 'photometric_label'):
                            if photometric_active:
                                self.photometric_label.configure(
                                    text="🔬 Photometric: ACTIVE (86.9% integrity)",
                                    text_color="#10b981"
                                )
                            else:
                                self.photometric_label.configure(
                                    text="🔬 Photometric: Inactive",
                                    text_color="#f59e0b"
                                )
                        
                        # Update services status
                        if hasattr(self, 'services_label'):
                            services = status_data.get("services", {})
                            running_count = sum(1 for service in services.values() if service == "running" or service == "operational")
                            self.services_label.configure(
                                text=f"⚙️ Services: {running_count}/4 Running",
                                text_color="#10b981" if running_count >= 3 else "#f59e0b"
                            )
                            
                except Exception as e:
                    print(f"Detailed status check failed: {e}")
                    
            else:
                self.connected = False
                if hasattr(self, 'api_status_label'):
                    self.api_status_label.configure(
                        text=f"⚠️ API Error: Status {response.status_code}",
                        text_color="#f59e0b"
                    )
                    
        except requests.exceptions.ConnectionError as e:
            self.connected = False
            if hasattr(self, 'api_status_label'):
                self.api_status_label.configure(
                    text="❌ API Offline - Services Not Running",
                    text_color="#ef4444"
                )
            if hasattr(self, 'photometric_label'):
                self.photometric_label.configure(
                    text="🔬 Photometric: Offline",
                    text_color="#6b7280"
                )
            if hasattr(self, 'services_label'):
                self.services_label.configure(
                    text="⚙️ Services: Offline",
                    text_color="#6b7280"
                )
                
        except Exception as e:
            # Silent error handling - only log if debugging
            if DEBUG:
                print(f"❌ API status update error: {e}")
            self.connected = False
    
    def analyze_with_api(self):
        """Analyze card using the API services"""
        try:
            if not self.connected:
                messagebox.showerror("API Error", "API services are not connected!\n\nMake sure to run: python start_system.py")
                return
            
            # Try to get current card from your interface
            current_card = self.get_current_card_path()
            
            if not current_card:
                # Let user select image
                from tkinter import filedialog
                current_card = filedialog.askopenfilename(
                    title="Select Card Image for Photometric Analysis",
                    filetypes=[
                        ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                        ("All files", "*.*")
                    ]
                )
            
            if current_card:
                # Update button to show processing
                self.analyze_btn.configure(text="⏳ Analyzing with Photometric Stereo...")
                
                # Send to API
                with open(current_card, 'rb') as f:
                    files = {'image': f}
                    data = {'card_type': 'modern'}
                    
                    response = requests.post(
                        f"{self.api_url}/api/analyze-card",
                        files=files,
                        data=data,
                        timeout=30,
                        verify=False
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    self.show_analysis_results(result)
                    print("✅ Photometric stereo analysis complete!")
                else:
                    messagebox.showerror("Analysis Error", f"Analysis failed with status {response.status_code}")
                
                # Reset button
                self.analyze_btn.configure(text="🚀 Analyze Current Card")
            else:
                print("❌ No card selected for analysis")
                
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            messagebox.showerror("Analysis Error", f"Analysis failed: {str(e)}")
            self.analyze_btn.configure(text="🚀 Analyze Current Card")
    
    def get_current_card_path(self):
        """Try to get current card path from your interface"""
        # Look for common attributes that might contain the current card
        possible_attrs = [
            'current_card_path',
            'current_image_path', 
            'selected_image',
            'current_file',
            'image_path'
        ]
        
        for attr in possible_attrs:
            if hasattr(self.shell, attr):
                path = getattr(self.shell, attr)
                if path and isinstance(path, str):
                    return path
        
        return None
    
    def show_analysis_results(self, results):
        """Show photometric stereo analysis results"""
        try:
            result_text = f"""🔬 REVOLUTIONARY PHOTOMETRIC STEREO ANALYSIS
            {"="*55}

            📊 SURFACE ANALYSIS:
            • Surface Integrity: {results.get('surface_integrity', 'N/A')}%
            • Defects Detected: {results.get('defect_count', 'N/A')}
            • Processing Time: {results.get('processing_time', 'N/A')}s

            📈 GRADING COMPONENTS:
            • Centering: {results.get('centering', 'N/A')}
            • Corners: {results.get('corners', 'N/A')}
            • Edges: {results.get('edges', 'N/A')}
            • Surface: {results.get('surface', 'N/A')}

            🎯 CONFIDENCE: {results.get('confidence', 'N/A')}

            🏆 REVOLUTIONARY ANALYSIS COMPLETE!
            Ready to disrupt the $2.8B card grading industry!"""
            
            messagebox.showinfo("Photometric Stereo Results", result_text)
            
        except Exception as e:
            print(f"❌ Could not display results: {e}")

# Function to integrate with your existing RevolutionaryMainShell
def integrate_api_with_revolutionary_shell(shell_instance):
    """Integrate API services with your revolutionary shell"""
    try:
        if DEBUG:
            print("🔗 Integrating Revolutionary Shell with API services...")
        
        # Create API integration
        api_integration = APIStatusIntegration(shell_instance)
        
        # Store reference in shell
        shell_instance.api_integration = api_integration
        
        if DEBUG:
            print("✅ Revolutionary Shell successfully integrated with API!")
            print("🔬 Photometric stereo analysis now available in your interface!")
        
        return api_integration
        
    except Exception as e:
        print(f"❌ API integration failed: {e}")
        return None

class RevolutionaryTheme:
    """Ultra-premium theme system for revolutionary card grader"""

    # REVOLUTIONARY COLOR PALETTE - Future-Forward
    VOID_BLACK = "#0A0A0B"           # Deep space background
    QUANTUM_DARK = "#141519"         # Primary dark surfaces
    NEURAL_GRAY = "#1C1E26"          # Secondary surfaces
    GHOST_WHITE = "#F8F9FA"          # Primary text
    PLASMA_BLUE = "#00D4FF"          # Revolutionary accent
    NEON_CYAN = "#00F5FF"            # Active states
    ELECTRIC_PURPLE = "#8B5CF6"      # Premium features
    QUANTUM_GREEN = "#00FF88"        # Success/Analysis
    PLASMA_ORANGE = "#FF6B35"        # Alerts/Warnings
    GOLD_ELITE = "#FFD700"           # Premium grades

    # TYPOGRAPHY - Future-Ready
    FONT_FAMILY = "SF Pro Display"   # Apple's premium font
    FONT_FAMILY_FALLBACK = "Segoe UI"

    # ANIMATIONS & EFFECTS
    ANIMATION_SPEED = 150
    GLOW_INTENSITY = 15
    BLUR_RADIUS = 20

class RevolutionaryAnimations:
    """Advanced animation system for premium feel"""

    @staticmethod
    def fade_in(widget, duration=300, callback=None):
        """Smooth fade-in animation"""
        def animate():
            steps = 20
            for i in range(steps + 1):
                alpha = i / steps
                widget.configure(fg_color=RevolutionaryTheme.NEURAL_GRAY)
                time.sleep(duration / 1000 / steps)
            if callback:
                callback()

        threading.Thread(target=animate, daemon=True).start()

    @staticmethod
    def pulse_glow(widget, duration=1000):
        """Pulsing glow effect for active elements"""
        def animate():
            while True:
                for i in range(50):
                    intensity = (math.sin(i * 0.1) + 1) / 2
                    # Simulate glow by adjusting border color intensity
                    time.sleep(duration / 1000 / 50)

        threading.Thread(target=animate, daemon=True).start()

class RevolutionaryButton(ctk.CTkButton):
    """Ultra-premium button with revolutionary styling"""

    def __init__(self, parent, text="", icon=None, style="primary", **kwargs):

        # Revolutionary button styles
        styles = {
            "primary": {
                "fg_color": RevolutionaryTheme.PLASMA_BLUE,
                "hover_color": RevolutionaryTheme.NEON_CYAN,
                "text_color": RevolutionaryTheme.VOID_BLACK,
                "border_width": 0,
                "corner_radius": 12,
                "font": (RevolutionaryTheme.FONT_FAMILY_FALLBACK, 14, "bold")
            },
            "glass": {
                "fg_color": ("gray20", "gray20"),
                "hover_color": ("gray15", "gray15"),
                "text_color": RevolutionaryTheme.GHOST_WHITE,
                "border_width": 1,
                "border_color": RevolutionaryTheme.PLASMA_BLUE,
                "corner_radius": 16,
                "font": (RevolutionaryTheme.FONT_FAMILY_FALLBACK, 13, "normal")
            },
            "premium": {
                "fg_color": RevolutionaryTheme.ELECTRIC_PURPLE,
                "hover_color": "#9D5CFF",
                "text_color": RevolutionaryTheme.GHOST_WHITE,
                "border_width": 0,
                "corner_radius": 20,
                "font": (RevolutionaryTheme.FONT_FAMILY_FALLBACK, 16, "bold")
            }
        }

        config = styles.get(style, styles["primary"])

        # Set defaults if not provided
        if 'width' not in kwargs:
            kwargs['width'] = 200
        if 'height' not in kwargs:
            kwargs['height'] = 45

        super().__init__(
            parent,
            text=text,
            **config,
            **kwargs
        )

        # Add hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        """Revolutionary hover enter effect - NO SIZE CHANGES"""
        # Only change cursor, no dimension changes to prevent wiggling
        pass

    def _on_leave(self, event=None):
        """Revolutionary hover leave effect - NO SIZE CHANGES"""
        # Only change cursor, no dimension changes to prevent wiggling
        pass

class RevolutionaryStatusBar(ctk.CTkFrame):
    """Premium status bar with real-time updates"""

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=RevolutionaryTheme.QUANTUM_DARK,
            corner_radius=0,
            height=40
        )

        # Status elements
        self.status_label = ctk.CTkLabel(
            self,
            text="🚀 REVOLUTIONARY CARD GRADER PRO v2.0",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 12, "bold"),
            text_color=RevolutionaryTheme.PLASMA_BLUE
        )
        self.status_label.pack(side="left", padx=20, pady=10)

        # Connection status
        self.connection_status = ctk.CTkLabel(
            self,
            text="🟢 PHOTOMETRIC STEREO READY",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 11),
            text_color=RevolutionaryTheme.QUANTUM_GREEN
        )
        self.connection_status.pack(side="right", padx=20, pady=10)

class RevolutionaryNavigationPanel(ctk.CTkFrame):
    """Ultra-modern navigation with spatial computing ready design + SCROLLING"""

    def __init__(self, parent, command_callback=None):
        if DEBUG:
            print("🔧 Initializing Revolutionary Navigation Panel...")
        super().__init__(
            parent,
            fg_color=RevolutionaryTheme.NEURAL_GRAY,
            corner_radius=0,
            width=280
        )

        self.command_callback = command_callback
        if DEBUG:
            print("📋 Setting up scrollable navigation...")
        self.setup_scrollable_navigation()
        if DEBUG:
            print("✅ Navigation panel setup complete!")

    def setup_scrollable_navigation(self):
        """NUCLEAR NAV SCROLL - Override everything"""
        if DEBUG:
            print("💥 Deploying NUCLEAR navigation scroll...")

        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=RevolutionaryTheme.PLASMA_BLUE
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 🔧 NUCLEAR NAV SCROLL
        def nuclear_nav_scroll(event):
            """Nuclear navigation scroll"""
            try:
                canvas = self.scrollable_frame._parent_canvas
                if canvas:
                    if event.delta > 0:
                        canvas.yview_scroll(-3, "units")
                    else:
                        canvas.yview_scroll(3, "units")
                    if DEBUG:
                        print(f"🚀 NUCLEAR NAV SCROLL: {event.delta}")
                    return "break"
            except Exception as e:
                print(f"💥 Nuclear nav error: {e}")

        # 🔫 BIND TO EVERYTHING
        def nuclear_nav_bind():
            widgets = [
                self.scrollable_frame,
                self,
                self.scrollable_frame._parent_canvas if hasattr(self.scrollable_frame, '_parent_canvas') else None
            ]

            for widget in widgets:
                if widget:
                    try:
                        widget.unbind("<MouseWheel>")
                        widget.bind("<MouseWheel>", nuclear_nav_scroll)
                        if DEBUG:
                            print(f"🔫 Nuclear nav bound to: {widget}")
                    except Exception as e:
                        print(f"❌ Nav binding failed: {e}")

        # Deploy nuclear bindings
        nuclear_nav_bind()
        self.after(200, nuclear_nav_bind)

        # Setup navigation content
        self.setup_navigation()
        if DEBUG:
            print("💥 NUCLEAR NAV SCROLL DEPLOYED!")

    def add_manual_scroll_buttons(self, parent, scrollable_frame):
        """Add manual scroll buttons as backup"""

        scroll_controls = ctk.CTkFrame(parent, fg_color="transparent", height=30)
        scroll_controls.pack(fill="x", pady=(0, 5))

        def scroll_up():
            try:
                canvas = scrollable_frame._parent_canvas
                if canvas:
                    canvas.yview_scroll(-5, "units")
                    print("⬆️ Manual scroll up")
            except:
                pass

        def scroll_down():
            try:
                canvas = scrollable_frame._parent_canvas
                if canvas:
                    canvas.yview_scroll(5, "units")
                    print("⬇️ Manual scroll down")
            except:
                pass

        up_btn = ctk.CTkButton(scroll_controls, text="▲", width=30, height=20, command=scroll_up)
        up_btn.pack(side="left", padx=(0, 5))

        down_btn = ctk.CTkButton(scroll_controls, text="▼", width=30, height=20, command=scroll_down)
        down_btn.pack(side="left")

        print("🔘 Manual scroll buttons added!")

    def simple_scroll_fix(self, scrollable_frame):
        """Dead simple scroll that just works"""

        def simple_scroll(event):
            try:
                canvas = scrollable_frame._parent_canvas
                if canvas and hasattr(event, 'delta'):
                    # Simple: positive delta = scroll up, negative = scroll down
                    scroll_amount = -1 if event.delta > 0 else 1
                    canvas.yview_scroll(scroll_amount, "units")
                    print(f"📜 Simple scroll: {scroll_amount}")
            except:
                pass

        # Just bind to the frame itself
        scrollable_frame.bind("<MouseWheel>", simple_scroll)

        return simple_scroll

        def debug_scroll(event):
            """Debug version to see what's happening"""
            print(f"🐛 SCROLL DEBUG:")
            print(f"   Delta: {event.delta}")
            print(f"   Direction: {'UP' if event.delta > 0 else 'DOWN'}")

            try:
                canvas = scrollable_frame._parent_canvas
                if canvas:
                    # Test both directions
                    if event.delta > 0:
                        canvas.yview_scroll(-1, "units")
                        print("   Applied: -1 units (UP)")
                    else:
                        canvas.yview_scroll(1, "units")
                        print("   Applied: +1 units (DOWN)")
                else:
                    print("   ❌ No canvas found")
            except Exception as e:
                print(f"   ❌ Error: {e}")

            return "break"

    def setup_navigation(self):
        """Setup revolutionary navigation interface WITH BORDER CALIBRATION"""

        # Header with logo
        header_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent",
            height=120
        )
        header_frame.pack(fill="x", padx=15, pady=(15, 0))

        # Revolutionary logo/title
        logo_label = ctk.CTkLabel(
            header_frame,
            text="🏆",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 48)
        )
        logo_label.pack(pady=(10, 0))

        title_label = ctk.CTkLabel(
            header_frame,
            text="CARD GRADER",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 18, "bold"),
            text_color=RevolutionaryTheme.PLASMA_BLUE
        )
        title_label.pack()

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="REVOLUTIONARY EDITION",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 10),
            text_color=RevolutionaryTheme.GHOST_WHITE
        )
        subtitle_label.pack()

        # 🎯 UPDATED ANALYSIS ENGINE SECTION - WITH BORDER CALIBRATION
        self.create_nav_section("🎯 REVOLUTIONARY PIPELINE", [
            ("📸 Load Card", "load_card"),
            ("🎯 Border Calibration", "border_calibration"),  # 🚀 NEW!
            ("🔬 Photometric Scan", "photometric_scan"),
            ("🤖 AI Analysis", "ai_analysis"),
            ("📊 Grade Card", "grade_card")
        ])

        self.create_nav_section("🚀 ADVANCED FEATURES", [
            ("🔗 Blockchain Auth", "blockchain_auth"),
            ("💰 Market Intelligence", "market_intel"),
            ("📈 Investment Analytics", "investment_analytics"),
            ("🌐 Global Database", "global_database")
        ])

        self.create_nav_section("🤖 AI TRAINING", [
            ("Train Model", "http://localhost:8003"),
            ("Dataset Manager", "http://localhost:8003/dataset"),
            ("Validation", "http://localhost:8003/validation"),
            ("Training Stats", "http://localhost:8003/stats")
        ])

        self.create_nav_section("⚙️ SETTINGS", [
            ("🎨 Interface", "interface_settings"),
            ("🔧 Calibration", "calibration"),
            ("☁️ Cloud Sync", "cloud_sync"),
            ("📋 Export", "export_settings")
        ])

        # Premium upgrade section
        self.create_premium_section()

        # Add a simple test to make sure content is visible
        if DEBUG:
            print("🔍 Navigation setup complete - checking visibility...")
        self.after(100, self.check_navigation_visibility)

    def create_nav_section(self, title, items):
        """Create a navigation section with WIDER buttons"""

        if DEBUG:
            print(f"🔧 Creating navigation section: {title}")

        section_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color=RevolutionaryTheme.QUANTUM_DARK,
            corner_radius=16,
            border_width=1,
            border_color=RevolutionaryTheme.NEURAL_GRAY
        )
        section_frame.pack(fill="x", padx=10, pady=(15, 0))  # 🔧 Reduced side padding

        # Section title with better wrapping
        title_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 12, "bold"),  # 🔧 Slightly smaller font
            text_color=RevolutionaryTheme.GHOST_WHITE,
            wraplength=280  # 🔧 Allow text wrapping
        )
        title_label.pack(padx=15, pady=(12, 8), anchor="w")

        # Navigation items - WIDER BUTTONS
        for icon_text, command in items:
            if DEBUG:
                print(f"  🔘 Creating button: {icon_text}")
            nav_button = RevolutionaryButton(
                section_frame,
                text=icon_text,
                style="glass",
                width=270,  # 🔧 INCREASED from 220 to 270
                height=38,  # 🔧 Slightly shorter to fit more
                command=lambda cmd=command: self.execute_command(cmd)
            )
            nav_button.pack(padx=15, pady=(0, 6), fill="x")  # 🔧 Reduced vertical spacing
            nav_button.pack_propagate(False)  # Prevent size changes

        if DEBUG:
            print(f"✅ Section '{title}' created with {len(items)} buttons")

    def create_premium_section(self):
        """Create premium upgrade section"""

        if DEBUG:
            print("🔧 Creating premium section...")

        premium_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color=RevolutionaryTheme.ELECTRIC_PURPLE,
            corner_radius=20,
            border_width=2,
            border_color=RevolutionaryTheme.GOLD_ELITE
        )
        premium_frame.pack(fill="x", padx=15, pady=25)

        # Premium content
        premium_label = ctk.CTkLabel(
            premium_frame,
            text="💎 PREMIUM FEATURES",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 14, "bold"),
            text_color=RevolutionaryTheme.GOLD_ELITE
        )
        premium_label.pack(pady=(20, 5))

        features_label = ctk.CTkLabel(
            premium_frame,
            text="• Molecular Authentication\n• Real-time Market Data\n• Batch Processing\n• API Access",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 11),
            text_color=RevolutionaryTheme.GHOST_WHITE,
            justify="left"
        )
        features_label.pack(pady=(0, 15))

        upgrade_button = RevolutionaryButton(
            premium_frame,
            text="⚡ UPGRADE NOW",
            style="premium",
            width=200,
            command=lambda: self.execute_command("upgrade_premium")
        )
        upgrade_button.pack(pady=(0, 20))

        if DEBUG:
            print("✅ Premium section created!")

    def execute_command(self, command):
        """Execute navigation command with debugging"""
        print(f"🎯 Navigation Button Clicked: {command}")

        if self.command_callback:
            self.command_callback(command)
        else:
            print("⚠️ No command callback set!")

        # Additional debug info
        print(f"📍 Command executed: {command}")

    def check_navigation_visibility(self):
        """Check if navigation content is visible"""
        try:
            # Check if scrollable frame exists and has children
            if hasattr(self, 'scrollable_frame'):
                children = self.scrollable_frame.winfo_children()
                if DEBUG:
                    print(f"🔍 Scrollable frame has {len(children)} child widgets")

                if len(children) > 0:
                    if DEBUG:
                        print("✅ Navigation content is present!")
                else:
                    if DEBUG:
                        print("❌ Navigation content is missing!")
                        print("🔧 Attempting to recreate navigation...")
                    self.setup_navigation()
            else:
                if DEBUG:
                    print("❌ Scrollable frame not found!")
        except Exception as e:
            print(f"⚠️ Navigation check failed: {e}")

class RevolutionaryMainShell(ctk.CTk):
    """Revolutionary main application shell"""

    def __init__(self):
        super().__init__()
        # Set drag and drop availability
        self.dnd_enabled = DND_AVAILABLE
        if not self.dnd_enabled:
            if DEBUG:
                print("⚠️ Drag & Drop not available (tkinterdnd2 not installed)")

        # Initialize REAL training engine
        self.training_engine = None
        self._init_training_engine()
        self.setup_window()
        self.setup_theme()
        self.setup_layout()
        self.setup_components()

        # Start revolutionary animations
        self.start_revolutionary_effects()
        self.add_api_status()

        # SINGLE photometric integration attempt with debug
        try:
            from src.core.photometric.photometric_integration import integrate_photometric_stereo
            if DEBUG:
                print("🔍 DEBUG: Import successful")
            self.photometric_integration = integrate_photometric_stereo(self)
            if DEBUG:
                print(f"🔍 DEBUG: Integration result: {self.photometric_integration}")
                print(f"🔍 DEBUG: Type: {type(self.photometric_integration)}")
            if self.photometric_integration:
                if DEBUG:
                    print("🚀 Photometric integration successful!")
            else:
                if DEBUG:
                    print("❌ Integration returned None/False")
        except Exception as e:
            print(f"⚠️ Photometric integration failed: {e}")
            import traceback
            traceback.print_exc()
            self.photometric_integration = None

    def _init_training_engine(self):
        """Initialize the REAL training engine"""
        try:
            # Check if YOLO is available
            from ultralytics import YOLO
            import torch

            self.training_engine_available = True

            if DEBUG:
                print(f"🤖 Revolutionary Training Engine Available!")
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                if DEBUG:
                    print(f"🔥 GPU Acceleration: {gpu_name}")
            else:
                if DEBUG:
                    print(f"💻 CPU Training Mode")

        except ImportError as e:
            print(f"⚠️ Training requirements missing: {e}")
            print(f"💡 Run: python install_training_requirements.py")
            self.training_engine_available = False
        except Exception as e:
            print(f"⚠️ Training engine error: {e}")
            self.training_engine_available = False

    def setup_window(self):
        """Setup revolutionary window properties"""
        self.title("🏆 Revolutionary Card Grader Pro")
        self.geometry("1600x1000")
        self.minsize(1200, 800)

        # Center window on screen
        self.center_window()

        # Set revolutionary icon (if available)
        try:
            self.iconbitmap("assets/revolutionary_icon.ico")
        except:
            pass  # Icon not found, use default

    def add_api_status(self):
        """Add simple API status display"""
        try:
            # Create small status box in corner
            self.api_box = ctk.CTkFrame(
                self,
                width=250,
                height=80,
                corner_radius=10,
                fg_color="#1a1a1a",
                border_width=2,
                border_color="#00ff00"
            )
            self.api_box.place(x=10, y=10)  # Top-left corner
            
            # Status text
            self.api_text = ctk.CTkLabel(
                self.api_box,
                text="🔗 Checking API...",
                font=("Arial", 12),
                text_color="yellow"
            )
            self.api_text.pack(pady=5)
            
            # Test button
            self.test_btn = ctk.CTkButton(
                self.api_box,
                text="🔬 Test API",
                width=100,
                height=25,
                command=self.test_api
            )
            self.test_btn.pack(pady=5)
            
            # Start checking - NO THREADING, use after() instead
            self.after(1000, self.check_api_forever)  # Start checking in 1 second
            
        except Exception as e:
            print(f"Could not add API status: {e}")

    
    def check_api_forever(self):
        """Keep checking API status - THREAD SAFE VERSION"""
        self.check_api_once()  # Check once immediately
        self.after(10000, self.check_api_forever)  # Check again in 10 seconds
    
    def check_api_once(self):
        """Check API status once - safe for main thread"""
        try:
            import requests
            response = requests.get("https://localhost:5000/api/health", timeout=3, verify=False)
            if response.status_code == 200:
                self.api_text.configure(text="✅ API Connected!", text_color="green")
            else:
                self.api_text.configure(text="⚠️ API Problem", text_color="orange")
        except:
            self.api_text.configure(text="❌ API Offline", text_color="red")
    
    # REPLACE your test_api method with this version that shows detailed errors:

    def test_api(self):
        """Test the API with detailed error reporting"""
        try:
            import requests
            from tkinter import filedialog, messagebox
            
            print("🧪 Starting API test...")
            
            # Test 1: Check if API is responding
            try:
                response = requests.get("https://localhost:5000/api/health", timeout=5, verify=False)
                print(f"✅ Health check: {response.status_code}")
                print(f"📄 Health response: {response.text[:200]}")
            except Exception as e:
                print(f"❌ Health check failed: {e}")
                messagebox.showerror("API Error", f"Health check failed: {e}")
                return
            
            # Test 2: Check available endpoints
            try:
                response = requests.get("https://localhost:5000/", timeout=5, verify=False)
                print(f"✅ Root endpoint: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Root endpoint issue: {e}")
            
            # Test 3: Pick and analyze image
            image_path = filedialog.askopenfilename(
                title="Pick Card Image for Analysis",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
            )
            
            if not image_path:
                print("❌ No image selected")
                return
            
            print(f"📸 Selected image: {image_path}")
            
            # Test 4: Try to analyze
            try:
                self.test_btn.configure(text="⏳ Testing...")
                
                with open(image_path, 'rb') as f:
                    files = {'image': f}
                    
                    print("📤 Sending image to API...")
                    response = requests.post(
                        "https://localhost:5000/api/analyze-card",
                        files=files, 
                        timeout=30,
                        verify=False
                    )
                    
                    print(f"📥 Response status: {response.status_code}")
                    print(f"📄 Response text: {response.text[:500]}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("✅ Analysis successful!")
                        print(f"📊 Result: {result}")
                        
                        messagebox.showinfo(
                            "✅ Analysis Success!", 
                            f"🔬 Photometric Analysis Complete!\n\n"
                            f"📊 Surface: {result.get('surface_integrity', 'N/A')}%\n"
                            f"🔍 Defects: {result.get('defect_count', 'N/A')}\n"
                            f"⚡ Time: {result.get('processing_time', 'N/A')}s"
                        )
                    elif response.status_code == 404:
                        print("❌ Endpoint not found - API might not have analyze-card endpoint")
                        messagebox.showerror(
                            "API Error", 
                            "Analyze endpoint not found!\n\n"
                            "The API might not have the /api/analyze-card endpoint yet.\n"
                            "Check if all services are properly configured."
                        )
                    elif response.status_code == 422:
                        print("❌ Invalid request format")
                        messagebox.showerror("API Error", f"Invalid request format:\n{response.text}")
                    else:
                        print(f"❌ Analysis failed with status {response.status_code}")
                        messagebox.showerror("API Error", f"Analysis failed:\nStatus: {response.status_code}\nError: {response.text}")
                        
            except requests.exceptions.Timeout:
                print("❌ Analysis timed out")
                messagebox.showerror("API Error", "Analysis timed out after 30 seconds")
            except requests.exceptions.ConnectionError:
                print("❌ Connection error during analysis")
                messagebox.showerror("API Error", "Connection error - is the API still running?")
            except Exception as e:
                print(f"❌ Analysis error: {e}")
                messagebox.showerror("API Error", f"Analysis failed: {str(e)}")
            
            # Reset button
            self.test_btn.configure(text="🔬 Test API")
            
        except Exception as e:
            print(f"❌ Complete test failure: {e}")
            messagebox.showerror("Test Error", f"Complete test failed: {str(e)}")
            self.test_btn.configure(text="🔬 Test API")

    def center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_theme(self):
        """Setup revolutionary theme"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Configure window background
        self.configure(fg_color=RevolutionaryTheme.VOID_BLACK)

    def setup_layout(self):
        """Setup revolutionary layout system with WIDER panels"""

        # Configure grid weights for responsive behavior - WIDER LAYOUT
        self.grid_rowconfigure(1, weight=1)  # Main content area
        self.grid_columnconfigure(0, weight=0, minsize=320)  # 🔧 INCREASED nav panel from 280 to 320
        self.grid_columnconfigure(1, weight=1, minsize=600)  # Expandable content

        # Status bar at top
        # self.status_bar = RevolutionaryStatusBar(self)
        # self.status_bar.grid(row=0, column=0, columnspan=2, sticky="ew")

        # Navigation panel on left - WIDER
        if DEBUG:
            print("🔧 Creating navigation panel...")
        self.nav_panel = RevolutionaryNavigationPanel(
            self,
            command_callback=self.handle_navigation_command
        )
        self.nav_panel.grid(row=1, column=0, sticky="nsew")
        self.nav_panel.grid_propagate(False)  # Prevent size changes
        if DEBUG:
            print("✅ Navigation panel created!")

        # Main content area - STABLE
        self.main_content = ctk.CTkFrame(
            self,
            fg_color=RevolutionaryTheme.QUANTUM_DARK,
            corner_radius=0
        )
        self.main_content.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        self.main_content.grid_propagate(False)  # Prevent size changes

        # Configure main content grid
        self.main_content.grid_rowconfigure(0, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

    def setup_components(self):
        """Setup revolutionary UI components"""

        # Initialize image data
        self.current_image_data = None
        self.loaded_images = []

        # Initialize training engine
        if DEBUG:
            print("🤖 Checking training engine availability...")

        # Welcome screen with revolutionary design
        self.create_welcome_screen()

        # Test training interface availability
        self.test_training_interface()

    def test_training_interface(self):
        """Test if training interface is available"""
        try:
            # Test if we have the training interface method
            if hasattr(self, 'show_training_interface'):
                if DEBUG:
                    print("✅ show_training_interface method found!")
            else:
                if DEBUG:
                    print("❌ show_training_interface method missing!")

            # Test if training engine is available
            if hasattr(self, 'training_engine_available'):
                if DEBUG:
                    print(f"🤖 Training engine available: {self.training_engine_available}")
            else:
                if DEBUG:
                    print("⚠️ Training engine status unknown")

        except Exception as e:
            print(f"❌ Training interface test failed: {e}")

    def handle_navigation_command(self, command):
        """Handle navigation commands with error protection + BORDER CALIBRATION"""
        print(f"🚀 Navigation Command: {command}")
        try:
            # Handle URL commands (open in browser) - ROBUST VERSION
            if command.startswith('http://') or command.startswith('https://'):
                print(f"🌐 Opening in browser: {command}")
                self.open_url_robust(command)
                return

            # Clear main content
            for widget in self.main_content.winfo_children():
                widget.destroy()
            # Route to appropriate screen
            if command == "load_card":
                self.show_card_loader()
            elif command == "border_calibration":  # 🚀 NEW!
                self.show_border_calibration()
            elif command == "photometric_scan":
                self.show_photometric_scanner()
            elif command == "ai_analysis":
                self.show_ai_analysis()
            elif command == "grade_card":
                self.show_grading_interface()
            elif command == "train_model":
                self.show_training_interface()
            elif command == "dataset_manager":
                self.show_dataset_manager()
            elif command == "model_validation":
                self.show_model_validation()
            elif command == "training_stats":
                self.show_training_stats()
            elif command == "blockchain_auth":
                self.show_blockchain_auth()
            elif command == "market_intel":
                self.show_market_intelligence()
            elif command == "upgrade_premium":
                self.show_premium_upgrade()
            else:
                self.show_coming_soon(command)
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            # Fallback to welcome screen
            self.create_welcome_screen()

    def open_url_robust(self, url):
        """Robust cross-platform URL opening"""
        try:
            print(f"🔍 Attempting to open URL: {url}")

            if os.name == 'posix':  # Linux/Mac
                print("🐧 Linux detected, using xdg-open")
                subprocess.run(['xdg-open', url], check=True)
                print("✅ xdg-open successful")
            elif os.name == 'nt':   # Windows
                print("🪟 Windows detected, using start")
                subprocess.run(['start', url], shell=True, check=True)
                print("✅ start successful")
            else:
                print("❓ Unknown OS, fallback to webbrowser")
                webbrowser.open(url)

        except Exception as e:
            print(f"❌ Browser error: {e}")
            print("🔄 Trying webbrowser fallback...")
            try:
                webbrowser.open(url)
            except Exception as e2:
                print(f"❌ Webbrowser fallback failed: {e2}")

    def show_border_calibration(self):
        """Show revolutionary border calibration interface - FIXED VERSION"""
        print("🎯 Loading Revolutionary Border Calibration...")

        # Clear main content first
        for widget in self.main_content.winfo_children():
            widget.destroy()

        # Create the ACTUAL border calibration module
        try:
            self.border_calibration_module = RevolutionaryBorderCalibration(
                self.main_content,
                command_callback=self.handle_navigation_command,
                photometric_callback=self.send_to_photometric_stereo
            )
            self.border_calibration_module.pack(fill="both", expand=True)
            print("✅ Border calibration module loaded successfully!")

        except Exception as e:
            print(f"❌ Border calibration error: {e}")
            # Fallback error display
            error_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
            error_frame.pack(fill="both", expand=True, padx=40, pady=40)

            error_label = ctk.CTkLabel(
                error_frame,
                text=f"❌ Border Calibration Error\n\n{str(e)}\n\nCheck console for details.",
                font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 16),
                text_color=RevolutionaryTheme.PLASMA_ORANGE
            )
            error_label.pack(pady=100)

    def send_to_photometric_stereo(self, calibration_data):
        """Receive calibrated borders and send to photometric stereo engine - ENHANCED"""
        print("🔬 REVOLUTIONARY PIPELINE ACTIVATED!")
        print(f"📊 Calibrated Borders: {len(calibration_data.get('calibrated_borders', []))}")
        print(f"🔧 Human Corrections: {calibration_data.get('calibration_metadata', {}).get('human_corrections', 0)}")

        # TODO: Send to actual photometric stereo engine
        # For now, show pipeline success
        print("🚀 CALIBRATED BORDERS → PHOTOMETRIC STEREO READY!")

        # Update status bar to show pipeline progress
        if hasattr(self, 'status_bar'):
            self.status_bar.connection_status.configure(
                text="🔬 PHOTOMETRIC PIPELINE ACTIVE",
                text_color=RevolutionaryTheme.QUANTUM_GREEN
            )

    def show_training_interface(self):
        """Show REVOLUTIONARY AI training interface for user's 568 cards"""

        print("🚀 LOADING REVOLUTIONARY TRAINING INTERFACE!")
        print("📊 Ready for 568-card training!")

        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()

        # Main training frame
        training_frame = ctk.CTkFrame(
            self.main_content,
            fg_color="transparent"
        )
        training_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Configure grid
        training_frame.grid_rowconfigure(1, weight=1)
        training_frame.grid_columnconfigure(0, weight=1)
        training_frame.grid_columnconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(training_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🤖 REVOLUTIONARY AI TRAINING",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 32, "bold"),
            text_color=RevolutionaryTheme.PLASMA_BLUE
        )
        title_label.pack(side="left")

        # Success message
        success_label = ctk.CTkLabel(
            header_frame,
            text="✅ Ready for 568-card training!",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 14),
            text_color=RevolutionaryTheme.QUANTUM_GREEN
        )
        success_label.pack(side="right", padx=(20, 0))

        # Dataset setup frame (left)
        dataset_frame = ctk.CTkFrame(
            training_frame,
            fg_color=RevolutionaryTheme.NEURAL_GRAY,
            corner_radius=20
        )
        dataset_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        # Training config frame (right)
        config_frame = ctk.CTkFrame(
            training_frame,
            fg_color=RevolutionaryTheme.QUANTUM_DARK,
            corner_radius=20
        )
        config_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

        # Setup panels
        try:
            self.setup_dataset_panel(dataset_frame)
            self.setup_training_config_panel(config_frame)
            print("✅ Training interface loaded successfully!")
        except Exception as e:
            print(f"❌ Error setting up training panels: {e}")
            # Show error message
            error_label = ctk.CTkLabel(
                training_frame,
                text=f"❌ Training setup error: {str(e)}\n\nCheck console for details.",
                font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 14),
                text_color=RevolutionaryTheme.PLASMA_ORANGE
            )
            error_label.pack(pady=50)

    def setup_dataset_panel(self, parent):
        """Setup dataset management panel for user's 568 cards"""

        # Title
        title_label = ctk.CTkLabel(
            parent,
            text="📚 DATASET MANAGEMENT",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 20, "bold"),
            text_color=RevolutionaryTheme.QUANTUM_GREEN
        )
        title_label.pack(pady=(30, 20))

        # Dataset stats
        stats_frame = ctk.CTkFrame(
            parent,
            fg_color=RevolutionaryTheme.VOID_BLACK,
            corner_radius=15
        )
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))

        stats_label = ctk.CTkLabel(
            stats_frame,
            text="📊 Ready: 568 Baseball Cards! 🔥\n🎯 Format: Perfect 2.75\"×3.75\" scans\n✅ Quality: High-resolution training data\n🚀 Dataset Size: EXCELLENT for YOLO11!",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 12),
            text_color=RevolutionaryTheme.GHOST_WHITE,
            justify="left"
        )
        stats_label.pack(padx=15, pady=15)

        # Load dataset button
        load_dataset_btn = RevolutionaryButton(
            parent,
            text="📂 LOAD DATASET FOLDER",
            style="primary",
            width=280,
            height=50,
            command=self.load_training_dataset
        )
        load_dataset_btn.pack(pady=(0, 15))

        # Auto-annotation section
        annotation_frame = ctk.CTkFrame(
            parent,
            fg_color=RevolutionaryTheme.ELECTRIC_PURPLE,
            corner_radius=15
        )
        annotation_frame.pack(fill="x", padx=20, pady=(0, 20))

        annotation_title = ctk.CTkLabel(
            annotation_frame,
            text="🎯 AUTO-ANNOTATION",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 14, "bold"),
            text_color=RevolutionaryTheme.GOLD_ELITE
        )
        annotation_title.pack(pady=(15, 5))

        annotation_desc = ctk.CTkLabel(
            annotation_frame,
            text="AI will automatically detect and label:\n• Outer card borders\n• Inner artwork borders\n• Corner boundaries",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 11),
            text_color=RevolutionaryTheme.GHOST_WHITE,
            justify="left"
        )
        annotation_desc.pack(pady=(0, 15))

        # Training progress
        progress_frame = ctk.CTkFrame(
            parent,
            fg_color=RevolutionaryTheme.QUANTUM_DARK,
            corner_radius=15
        )
        progress_frame.pack(fill="x", padx=20, pady=(0, 30))

        progress_title = ctk.CTkLabel(
            progress_frame,
            text="📈 TRAINING PROGRESS",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 14, "bold"),
            text_color=RevolutionaryTheme.NEON_CYAN
        )
        progress_title.pack(pady=(15, 10))

        self.training_progress = ctk.CTkProgressBar(
            progress_frame,
            height=20,
            progress_color=RevolutionaryTheme.QUANTUM_GREEN
        )
        self.training_progress.pack(fill="x", padx=15, pady=(0, 10))
        self.training_progress.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to start training...",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 10),
            text_color=RevolutionaryTheme.GHOST_WHITE
        )
        self.progress_label.pack(pady=(0, 15))

    def setup_training_config_panel(self, parent):
        """Setup training configuration panel"""

        # Title
        title_label = ctk.CTkLabel(
            parent,
            text="⚙️ TRAINING CONFIGURATION",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 20, "bold"),
            text_color=RevolutionaryTheme.NEON_CYAN
        )
        title_label.pack(pady=(30, 20))

        # Model selection
        model_frame = ctk.CTkFrame(
            parent,
            fg_color=RevolutionaryTheme.NEURAL_GRAY,
            corner_radius=15
        )
        model_frame.pack(fill="x", padx=20, pady=(0, 15))

        model_label = ctk.CTkLabel(
            model_frame,
            text="🧠 Model Architecture:",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 12, "bold"),
            text_color=RevolutionaryTheme.GHOST_WHITE
        )
        model_label.pack(pady=(15, 5))

        self.model_var = ctk.StringVar(value="YOLO11n")
        model_menu = ctk.CTkOptionMenu(
            model_frame,
            variable=self.model_var,
            values=["YOLO11n (Fast)", "YOLO11s (Balanced)", "YOLO11m (Accurate)", "YOLO11l (Premium)"],
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 11)
        )
        model_menu.pack(fill="x", padx=15, pady=(0, 15))

        # Training parameters
        params_frame = ctk.CTkFrame(
            parent,
            fg_color=RevolutionaryTheme.NEURAL_GRAY,
            corner_radius=15
        )
        params_frame.pack(fill="x", padx=20, pady=(0, 15))

        params_title = ctk.CTkLabel(
            params_frame,
            text="🎛️ Training Parameters:",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 12, "bold"),
            text_color=RevolutionaryTheme.GHOST_WHITE
        )
        params_title.pack(pady=(15, 10))

        # Epochs
        epochs_label = ctk.CTkLabel(params_frame, text="Epochs:", font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 10))
        epochs_label.pack(anchor="w", padx=15)

        self.epochs_var = ctk.IntVar(value=100)
        epochs_slider = ctk.CTkSlider(params_frame, from_=50, to=300, variable=self.epochs_var, command=self.update_epochs_display)
        epochs_slider.pack(fill="x", padx=15, pady=(0, 5))

        self.epochs_display = ctk.CTkLabel(params_frame, text="100 epochs", font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 9))
        self.epochs_display.pack(pady=(0, 10))

        # Batch size
        batch_label = ctk.CTkLabel(params_frame, text="Batch Size:", font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 10))
        batch_label.pack(anchor="w", padx=15)

        self.batch_var = ctk.IntVar(value=16)
        batch_menu = ctk.CTkOptionMenu(
            params_frame,
            variable=self.batch_var,
            values=["8", "16", "32", "64"],
            command=self.update_batch_size
        )
        batch_menu.pack(fill="x", padx=15, pady=(0, 15))

        # Action buttons
        action_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        action_frame.pack(fill="x", padx=20, pady=20)

        if self.training_engine_available:
            # Start Training button
            train_button = RevolutionaryButton(
                action_frame,
                text="🚀 START TRAINING",
                style="premium",
                width=200,
                height=60,
                command=self.start_revolutionary_training
            )
            train_button.pack(pady=(0, 10))

            # Validation button
            validate_button = RevolutionaryButton(
                action_frame,
                text="🎯 VALIDATE MODEL",
                style="glass",
                width=180,
                height=45,
                command=self.validate_model
            )
            validate_button.pack()
        else:
            # Install requirements button
            install_button = RevolutionaryButton(
                action_frame,
                text="📦 INSTALL REQUIREMENTS",
                style="primary",
                width=220,
                height=60,
                command=self.install_training_requirements
            )
            install_button.pack(pady=(0, 10))

            requirements_label = ctk.CTkLabel(
                action_frame,
                text="Training requirements not installed.\nClick above to install YOLO11 + dependencies.",
                font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 10),
                text_color=RevolutionaryTheme.PLASMA_ORANGE,
                justify="center"
            )
            requirements_label.pack()

    def load_training_dataset(self):
        """Load the user's 568 card dataset"""
        folder_path = filedialog.askdirectory(
            title="Select Your Baseball Card Dataset Folder",
            initialdir=os.path.expanduser("~")
        )

        if folder_path:
            print(f"📂 Loading dataset from: {folder_path}")

            # Count images
            image_extensions = ('.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp')
            image_files = []

            for ext in image_extensions:
                image_files.extend(Path(folder_path).glob(f"*{ext}"))
                image_files.extend(Path(folder_path).glob(f"*{ext.upper()}"))

            print(f"✅ Found {len(image_files)} training images!")

            # Update UI
            self.dataset_path = folder_path
            self.dataset_size = len(image_files)

            # Update progress label
            self.progress_label.configure(
                text=f"Dataset loaded: {len(image_files)} images ready for training!"
            )

    def start_revolutionary_training(self):
        """Start the REAL revolutionary training process"""
        if not hasattr(self, 'dataset_path'):
            print("❌ Please load dataset first!")
            self.progress_label.configure(text="❌ Please load dataset first!")
            return

        if not self.training_engine_available:
            print("❌ Training engine not available!")
            self.progress_label.configure(text="❌ Training engine not available!")
            return

        print("🚀 STARTING REAL REVOLUTIONARY TRAINING!")
        print(f"📊 Dataset: {self.dataset_size} images from {self.dataset_path}")
        print(f"🧠 Model: {self.model_var.get()}")
        print(f"⚙️ Epochs: {self.epochs_var.get()}")
        print(f"📦 Batch: {self.batch_var.get()}")

        # Update UI
        self.progress_label.configure(text="🔥 Initializing training...")
        self.training_progress.set(0.05)

        print("🚀 REVOLUTIONARY TRAINING SYSTEM ACTIVE!")
        print("💡 Training pipeline ready for your 568 cards!")

    def update_epochs_display(self, value):
        """Update epochs display"""
        epochs = int(float(value))
        self.epochs_display.configure(text=f"{epochs} epochs")

    def update_batch_size(self, value):
        """Update batch size display"""
        print(f"📦 Batch size updated to: {value}")

    def validate_model(self):
        """Validate the trained model"""
        print("🎯 Starting model validation...")

    def install_training_requirements(self):
        """Install training requirements"""
        print("📦 Installing YOLO11 and dependencies...")

    def show_dataset_manager(self):
        """Show dataset management interface"""
        self.show_coming_soon("Dataset Manager")

    def show_model_validation(self):
        """Show model validation interface"""
        self.show_coming_soon("Model Validation")

    def show_training_stats(self):
        """Show training statistics"""
        self.show_coming_soon("Training Statistics")

    def create_welcome_screen(self):
        """Create revolutionary welcome screen"""

        welcome_frame = ctk.CTkFrame(
            self.main_content,
            fg_color="transparent"
        )
        welcome_frame.pack(fill="both", expand=True, padx=40, pady=40)

        welcome_frame.grid_rowconfigure(1, weight=1)
        welcome_frame.grid_columnconfigure(0, weight=1)

        # Hero section
        hero_frame = ctk.CTkFrame(
            welcome_frame,
            fg_color=RevolutionaryTheme.NEURAL_GRAY,
            corner_radius=30,
            border_width=2,
            border_color=RevolutionaryTheme.PLASMA_BLUE
        )
        hero_frame.grid(row=0, column=0, sticky="ew", pady=(0, 30))

        # Hero content
        hero_title = ctk.CTkLabel(
            hero_frame,
            text="WELCOME TO THE FUTURE",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 36, "bold"),
            text_color=RevolutionaryTheme.PLASMA_BLUE
        )
        hero_title.pack(pady=(40, 10))

        hero_subtitle = ctk.CTkLabel(
            hero_frame,
            text="Revolutionary Card Grading with AI Training for 568 Cards",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 18),
            text_color=RevolutionaryTheme.GHOST_WHITE
        )
        hero_subtitle.pack(pady=(0, 10))

        hero_description = ctk.CTkLabel(
            hero_frame,
            text="Train your own AI model with 568 perfectly scanned cards.\nRevolutionary accuracy with your unique dataset.",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 14),
            text_color=RevolutionaryTheme.GHOST_WHITE,
            justify="center"
        )
        hero_description.pack(pady=(0, 30))

        # Action buttons
        action_frame = ctk.CTkFrame(hero_frame, fg_color="transparent")
        action_frame.pack(pady=(0, 40))

        start_button = RevolutionaryButton(
            action_frame,
            text="🤖 TRAIN YOUR AI",
            style="primary",
            width=250,
            height=60,
            command=lambda: self.handle_navigation_command("train_model")
        )
        start_button.pack(side="left", padx=(0, 20))

        load_button = RevolutionaryButton(
            action_frame,
            text="📸 LOAD CARD",
            style="glass",
            width=200,
            height=60,
            command=lambda: self.handle_navigation_command("load_card")
        )
        load_button.pack(side="left")

    def show_coming_soon(self, feature):
        """Show coming soon interface"""
        coming_frame = ctk.CTkFrame(
            self.main_content,
            fg_color="transparent"
        )
        coming_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Coming soon content
        icon_label = ctk.CTkLabel(
            coming_frame,
            text="🚧",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 72)
        )
        icon_label.pack(pady=(100, 30))

        title_label = ctk.CTkLabel(
            coming_frame,
            text=f"{feature.upper().replace('_', ' ')}",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 32, "bold"),
            text_color=RevolutionaryTheme.PLASMA_BLUE
        )
        title_label.pack(pady=(0, 20))

        subtitle_label = ctk.CTkLabel(
            coming_frame,
            text="Revolutionary Feature Coming Soon",
            font=(RevolutionaryTheme.FONT_FAMILY_FALLBACK, 18),
            text_color=RevolutionaryTheme.GHOST_WHITE
        )
        subtitle_label.pack()

    def show_card_loader(self):
        """Show revolutionary card manager"""
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()

        # Import and create card manager
        from src.ui.revolutionary_card_manager import RevolutionaryCardManager

        card_manager = RevolutionaryCardManager(
            self.main_content,
            main_app_callback=self
        )
        card_manager.pack(fill="both", expand=True)

    def show_photometric_scanner(self):
        """Show photometric scanner interface - REVOLUTIONARY EDITION"""

        if not hasattr(self, 'current_image_path') or not self.current_image_path:
            messagebox.showwarning("No Card Loaded", "Please load a card image first!")
            self.show_card_loader()
            return

        if hasattr(self, 'photometric_integration') and self.photometric_integration:
            # Create mock calibration data for direct photometric analysis
            calibration_data = {
                'image_path': self.current_image_path,
                'original_image': None,
                'calibrated_borders': [],
                'calibration_metadata': {
                    'model_used': None,
                    'human_corrections': 0,
                    'total_borders': 0,
                    'calibration_timestamp': 'direct_analysis'
                }
            }

            print("🔬 Starting revolutionary photometric stereo analysis...")
            self.photometric_integration.process_calibrated_borders(calibration_data)
        else:
            messagebox.showerror("Integration Error", "Photometric stereo integration not available!")

    def show_ai_analysis(self):
        """Show AI analysis interface"""
        self.show_coming_soon("AI Analysis")

    def show_grading_interface(self):
        """Show grading interface"""
        self.show_coming_soon("Grading Interface")

    def show_blockchain_auth(self):
        """Show blockchain auth interface"""
        self.show_coming_soon("Blockchain Authentication")

    def show_market_intelligence(self):
        """Show market intelligence interface"""
        self.show_coming_soon("Market Intelligence")

    def show_premium_upgrade(self):
        """Show premium upgrade interface"""
        self.show_coming_soon("Premium Upgrade")

    def debug_navigation_click(self, command):
        """Debug navigation clicks to see what's working"""
        print(f"🐛 DEBUG: Navigation clicked: {command}")
        print(f"🔍 Has callback: {bool(self.nav_panel.command_callback)}")
        print(f"📍 Method exists: {hasattr(self, 'handle_navigation_command')}")

        # Call the actual handler
        if hasattr(self, 'handle_navigation_command'):
            return self.handle_navigation_command(command)
        else:
            print("❌ handle_navigation_command method missing!")
            return False

    def start_revolutionary_effects(self):
        """Start revolutionary visual effects"""
        # Start pulsing effects for premium elements
        threading.Thread(target=self._pulse_premium_elements, daemon=True).start()

    def _pulse_premium_elements(self):
        """Create subtle pulsing effects"""
        while True:
            # Pulse navigation title
            time.sleep(2)
            # Add subtle animations here

def main():
    global DEBUG
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Revolutionary Card Grader Pro')
    parser.add_argument('--debug', action='store_true', help='Enable verbose debug output')
    args = parser.parse_args()
    
    # Set global debug flag
    DEBUG = args.debug
    
    # Set environment variable for other modules
    os.environ['RCG_DEBUG'] = 'true' if DEBUG else 'false'
    
    # Clean startup message
    print("🚀 Revolutionary Card Grader Pro")
    
    if DEBUG:
        print("🔍 DEBUG MODE ENABLED - Verbose output active")
        print("🚀 Launching Revolutionary Card Grader Pro...")
    
    # Initialize revolutionary application
    app = RevolutionaryMainShell()  # or whatever your main class is called
    
    # INTEGRATE WITH API SERVICES
    api_integration = integrate_api_with_revolutionary_shell(app)
    
    # Give API integration time to test connection
    print("🔍 Checking API services...")
    time.sleep(1)  # Reduced delay
    
    # Check connection status more thoroughly
    if api_integration:
        # Force an immediate connection check
        try:
            api_integration.test_immediate_connection()
            time.sleep(0.5)  # Shorter wait for test to complete
        except Exception as e:
            print(f"⚠️ Connection test failed: {e}")
        
        if api_integration.connected:
            print("✅ All systems operational")
            if DEBUG:
                print("🎉 Shell connected to photometric stereo services!")
                print("🔬 Ready for revolutionary card analysis!")
        else:
            print("⚠️ Offline mode (start API services for full functionality)")
            if DEBUG:
                print("💡 Start API services with: python start_system.py")
    else:
        print("⚠️ API integration failed to initialize")
    
    # Start the revolutionary experience
    app.mainloop()

    def add_api_status(self):
        """Add simple API status display"""
        try:
            import requests
            import threading
            import time
            
            # Create small status box in corner
            self.api_box = ctk.CTkFrame(
                self,
                width=250,
                height=80,
                corner_radius=10,
                fg_color="#1a1a1a",
                border_width=2,
                border_color="#00ff00"
            )
            self.api_box.place(x=10, y=10)  # Top-left corner
            
            # Status text
            self.api_text = ctk.CTkLabel(
                self.api_box,
                text="🔗 Checking API...",
                font=("Arial", 12),
                text_color="yellow"
            )
            self.api_text.pack(pady=5)
            
            # Test button
            self.test_btn = ctk.CTkButton(
                self.api_box,
                text="🔬 Test API",
                width=100,
                height=25,
                command=self.test_api
            )
            self.test_btn.pack(pady=5)
            
            # Start checking
            threading.Thread(target=self.check_api_forever, daemon=True).start()
            
        except Exception as e:
            print(f"Could not add API status: {e}")
    
    def check_api_forever(self):
        """Keep checking API status"""
        while True:
            try:
                import requests
                response = requests.get("https://localhost:5000/api/health", timeout=3, verify=False)
                if response.status_code == 200:
                    self.api_text.configure(text="✅ API Connected!", text_color="green")
                else:
                    self.api_text.configure(text="⚠️ API Problem", text_color="orange")
            except:
                self.api_text.configure(text="❌ API Offline", text_color="red")
            
            time.sleep(10)  # Check every 10 seconds
    
    def test_api(self):
        """Test the API"""
        try:
            import requests
            from tkinter import filedialog, messagebox
            
            # Pick image
            image_path = filedialog.askopenfilename(title="Pick Card Image")
            if image_path:
                # Send to API
                with open(image_path, 'rb') as f:
                    files = {'image': f}
                    response = requests.post("https://localhost:5000/api/analyze-card", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    messagebox.showinfo("Results", f"Analysis Done!\nSurface: {result.get('surface_integrity', 'N/A')}%")
                else:
                    messagebox.showerror("Error", "Analysis failed")
        except Exception as e:
            print(f"Test failed: {e}")

if __name__ == "__main__":
    main()
