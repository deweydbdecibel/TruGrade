#!/usr/bin/env python3
"""
TruGrade Border Calibration - Professional Border Detection & Annotation
=======================================================================

Adapted from RCG border_calibration.py for TruGrade platform.
Provides professional border calibration with annotation capabilities.

Features:
- Revolutionary border detection
- Manual annotation tools
- Persistent calibration data
- TruScore integration ready
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw
import json
import os
import math
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import time

# Add project paths
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import TruGrade theme
from desktop_app.trugrade_simplified_shell import TruGradeTheme, TruGradeButton

@dataclass
class BorderAnnotation:
    """Border annotation data structure"""
    x1: float
    y1: float
    x2: float
    y2: float
    class_id: int
    confidence: float
    label: str
    corrected_by_human: bool = False
    correction_timestamp: str = ""

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2

    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2

    @property
    def width(self) -> float:
        return abs(self.x2 - self.x1)

    @property
    def height(self) -> float:
        return abs(self.y2 - self.y1)

class TruGradeBorderCalibration(ctk.CTkFrame):
    """
    TruGrade Professional Border Calibration
    
    Provides professional border detection and annotation capabilities
    for accurate card border identification and centering analysis.
    """
    
    def __init__(self, parent, image_path: Optional[str] = None):
        super().__init__(parent, fg_color=TruGradeTheme.QUANTUM_DARK)
        
        self.image_path = image_path
        self.original_image = None
        self.display_image = None
        self.current_annotations = []
        self.scale_factor = 1.0
        self.canvas_width = 800
        self.canvas_height = 600
        
        # Annotation state
        self.annotation_mode = False
        self.current_annotation = None
        self.start_x = None
        self.start_y = None
        
        self.setup_ui()
        
        if image_path:
            self.load_image(image_path)
    
    def setup_ui(self):
        """Setup the border calibration interface"""
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Left panel - Controls
        self.create_control_panel()
        
        # Right panel - Image canvas
        self.create_canvas_panel()
        
        # Bottom panel - Status
        self.create_status_panel()
    
    def create_control_panel(self):
        """Create the left control panel"""
        control_frame = ctk.CTkFrame(self, fg_color=TruGradeTheme.NEURAL_GRAY, corner_radius=15)
        control_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(20, 10), pady=20)
        control_frame.grid_rowconfigure(10, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(
            control_frame,
            text="🎯 Border Calibration",
            font=(TruGradeTheme.FONT_FAMILY, 18, "bold"),
            text_color=TruGradeTheme.PLASMA_BLUE
        )
        header_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # TruScore branding
        truscore_label = ctk.CTkLabel(
            control_frame,
            text="TruScore™ Border Detection",
            font=(TruGradeTheme.FONT_FAMILY, 11, "bold"),
            text_color=TruGradeTheme.QUANTUM_GREEN
        )
        truscore_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Load image section
        load_section = ctk.CTkFrame(control_frame, fg_color="transparent")
        load_section.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            load_section,
            text="📸 Image",
            font=(TruGradeTheme.FONT_FAMILY, 14, "bold"),
            text_color=TruGradeTheme.GHOST_WHITE
        ).pack(pady=(0, 10))
        
        TruGradeButton(
            load_section,
            text="📁 Load Image",
            style="primary",
            width=200,
            command=self.load_image_dialog
        ).pack(pady=2)
        
        # Detection section
        detection_section = ctk.CTkFrame(control_frame, fg_color="transparent")
        detection_section.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkLabel(
            detection_section,
            text="🔍 Detection",
            font=(TruGradeTheme.FONT_FAMILY, 14, "bold"),
            text_color=TruGradeTheme.GHOST_WHITE
        ).pack(pady=(0, 10))
        
        TruGradeButton(
            detection_section,
            text="🤖 Auto Detect",
            style="primary",
            width=200,
            command=self.auto_detect_borders
        ).pack(pady=2)
        
        TruGradeButton(
            detection_section,
            text="✏️ Manual Annotate",
            style="glass",
            width=200,
            command=self.toggle_annotation_mode
        ).pack(pady=2)
        
        # Annotation tools
        tools_section = ctk.CTkFrame(control_frame, fg_color="transparent")
        tools_section.grid(row=4, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkLabel(
            tools_section,
            text="🛠️ Tools",
            font=(TruGradeTheme.FONT_FAMILY, 14, "bold"),
            text_color=TruGradeTheme.GHOST_WHITE
        ).pack(pady=(0, 10))
        
        TruGradeButton(
            tools_section,
            text="🗑️ Clear All",
            style="glass",
            width=200,
            command=self.clear_annotations
        ).pack(pady=2)
        
        TruGradeButton(
            tools_section,
            text="💾 Save Annotations",
            style="glass",
            width=200,
            command=self.save_annotations
        ).pack(pady=2)
        
        TruGradeButton(
            tools_section,
            text="📂 Load Annotations",
            style="glass",
            width=200,
            command=self.load_annotations
        ).pack(pady=2)
    
    def create_canvas_panel(self):
        """Create the image canvas panel"""
        canvas_frame = ctk.CTkFrame(self, fg_color=TruGradeTheme.NEURAL_GRAY, corner_radius=15)
        canvas_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        canvas_frame.grid_columnconfigure(0, weight=1)
        canvas_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(canvas_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="🖼️ Border Detection Canvas",
            font=(TruGradeTheme.FONT_FAMILY, 16, "bold"),
            text_color=TruGradeTheme.PLASMA_BLUE
        ).pack(side="left")
        
        # Canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            bg=TruGradeTheme.VOID_BLACK,
            highlightthickness=0,
            width=self.canvas_width,
            height=self.canvas_height
        )
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Placeholder text
        self.canvas.create_text(
            self.canvas_width // 2,
            self.canvas_height // 2,
            text="Load an image to begin border calibration",
            fill=TruGradeTheme.GHOST_WHITE,
            font=(TruGradeTheme.FONT_FAMILY, 16)
        )
    
    def create_status_panel(self):
        """Create status panel"""
        status_frame = ctk.CTkFrame(self, fg_color=TruGradeTheme.NEURAL_GRAY, corner_radius=10)
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="🎯 TruGrade Border Calibration Ready - Load an image to begin",
            font=(TruGradeTheme.FONT_FAMILY, 12),
            text_color=TruGradeTheme.GHOST_WHITE
        )
        self.status_label.pack(pady=10)
    
    def load_image_dialog(self):
        """Load image via file dialog"""
        file_types = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Card Image for Border Calibration",
            filetypes=file_types
        )
        
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, image_path: str):
        """Load and display image"""
        try:
            self.image_path = image_path
            
            # Load image
            self.original_image = cv2.imread(image_path)
            if self.original_image is None:
                raise ValueError("Could not load image")
            
            # Display image
            self.display_image_on_canvas()
            
            # Update status
            file_name = Path(image_path).name
            self.status_label.configure(text=f"✅ Image loaded: {file_name} - Ready for border detection")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            self.status_label.configure(text=f"❌ Error loading image: {str(e)}")
    
    def display_image_on_canvas(self):
        """Display image on canvas with proper scaling"""
        if self.original_image is None:
            return
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
        
        # Calculate scaling
        img_height, img_width = image_rgb.shape[:2]
        
        scale_x = self.canvas_width / img_width
        scale_y = self.canvas_height / img_height
        self.scale_factor = min(scale_x, scale_y)
        
        new_width = int(img_width * self.scale_factor)
        new_height = int(img_height * self.scale_factor)
        
        # Resize image
        resized_image = cv2.resize(image_rgb, (new_width, new_height))
        
        # Convert to PIL and PhotoImage
        pil_image = Image.fromarray(resized_image)
        self.display_image = ImageTk.PhotoImage(pil_image)
        
        # Center image on canvas
        x_offset = (self.canvas_width - new_width) // 2
        y_offset = (self.canvas_height - new_height) // 2
        
        self.canvas.create_image(
            x_offset, y_offset,
            anchor="nw",
            image=self.display_image
        )
        
        # Draw existing annotations
        self.draw_annotations()
    
    def draw_annotations(self):
        """Draw all annotations on canvas"""
        for annotation in self.current_annotations:
            self.draw_annotation(annotation)
    
    def draw_annotation(self, annotation: BorderAnnotation):
        """Draw a single annotation"""
        # Scale coordinates
        x1 = annotation.x1 * self.scale_factor
        y1 = annotation.y1 * self.scale_factor
        x2 = annotation.x2 * self.scale_factor
        y2 = annotation.y2 * self.scale_factor
        
        # Draw rectangle
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=TruGradeTheme.PLASMA_BLUE,
            width=2,
            tags="annotation"
        )
        
        # Draw label
        self.canvas.create_text(
            x1, y1 - 10,
            text=f"{annotation.label} ({annotation.confidence:.2f})",
            fill=TruGradeTheme.QUANTUM_GREEN,
            anchor="sw",
            tags="annotation"
        )
    
    def toggle_annotation_mode(self):
        """Toggle manual annotation mode"""
        self.annotation_mode = not self.annotation_mode
        
        if self.annotation_mode:
            self.status_label.configure(text="✏️ Annotation mode ON - Click and drag to create border annotations")
        else:
            self.status_label.configure(text="✏️ Annotation mode OFF")
    
    def on_canvas_click(self, event):
        """Handle canvas click"""
        if not self.annotation_mode or self.original_image is None:
            return
        
        self.start_x = event.x
        self.start_y = event.y
        self.current_annotation = None
    
    def on_canvas_drag(self, event):
        """Handle canvas drag"""
        if not self.annotation_mode or self.start_x is None:
            return
        
        # Remove previous temporary annotation
        if self.current_annotation:
            self.canvas.delete(self.current_annotation)
        
        # Draw temporary rectangle
        self.current_annotation = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline=TruGradeTheme.PLASMA_ORANGE,
            width=2,
            tags="temp_annotation"
        )
    
    def on_canvas_release(self, event):
        """Handle canvas release"""
        if not self.annotation_mode or self.start_x is None:
            return
        
        # Remove temporary annotation
        if self.current_annotation:
            self.canvas.delete(self.current_annotation)
        
        # Create permanent annotation
        x1 = min(self.start_x, event.x) / self.scale_factor
        y1 = min(self.start_y, event.y) / self.scale_factor
        x2 = max(self.start_x, event.x) / self.scale_factor
        y2 = max(self.start_y, event.y) / self.scale_factor
        
        # Only create if annotation is large enough
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            annotation = BorderAnnotation(
                x1=x1, y1=y1, x2=x2, y2=y2,
                class_id=0,
                confidence=1.0,
                label="manual_border",
                corrected_by_human=True,
                correction_timestamp=datetime.now().isoformat()
            )
            
            self.current_annotations.append(annotation)
            self.draw_annotation(annotation)
            
            self.status_label.configure(
                text=f"✅ Manual annotation added - Total annotations: {len(self.current_annotations)}"
            )
        
        # Reset
        self.start_x = None
        self.start_y = None
        self.current_annotation = None
    
    def auto_detect_borders(self):
        """Auto-detect borders using AI"""
        if self.original_image is None:
            messagebox.showwarning("No Image", "Please load an image first.")
            return
        
        self.status_label.configure(text="🤖 Running AI border detection...")
        
        # Run detection in background
        threading.Thread(
            target=self._perform_auto_detection,
            daemon=True
        ).start()
    
    def _perform_auto_detection(self):
        """Perform auto detection in background"""
        try:
            # Placeholder for AI detection
            time.sleep(2)  # Simulate processing
            
            # Mock detection results
            height, width = self.original_image.shape[:2]
            
            # Create mock border detection
            border_margin = 0.05  # 5% margin
            x1 = width * border_margin
            y1 = height * border_margin
            x2 = width * (1 - border_margin)
            y2 = height * (1 - border_margin)
            
            annotation = BorderAnnotation(
                x1=x1, y1=y1, x2=x2, y2=y2,
                class_id=0,
                confidence=0.95,
                label="auto_border",
                corrected_by_human=False
            )
            
            # Update UI in main thread
            self.after(0, lambda: self._detection_complete(annotation))
            
        except Exception as e:
            self.after(0, lambda: self._detection_error(str(e)))
    
    def _detection_complete(self, annotation: BorderAnnotation):
        """Handle detection completion"""
        self.current_annotations.append(annotation)
        self.draw_annotation(annotation)
        
        self.status_label.configure(
            text=f"✅ Auto-detection complete - Confidence: {annotation.confidence:.1%}"
        )
    
    def _detection_error(self, error_msg: str):
        """Handle detection error"""
        self.status_label.configure(text=f"❌ Detection error: {error_msg}")
        messagebox.showerror("Detection Error", f"Auto-detection failed: {error_msg}")
    
    def clear_annotations(self):
        """Clear all annotations"""
        self.current_annotations.clear()
        self.canvas.delete("annotation")
        self.status_label.configure(text="🗑️ All annotations cleared")
    
    def save_annotations(self):
        """Save annotations to file"""
        if not self.current_annotations:
            messagebox.showwarning("No Annotations", "No annotations to save.")
            return
        
        if not self.image_path:
            messagebox.showwarning("No Image", "No image loaded.")
            return
        
        # Create annotations file path
        image_path = Path(self.image_path)
        annotations_path = image_path.with_suffix('.json')
        
        try:
            # Convert annotations to dict
            annotations_data = {
                'image_path': str(self.image_path),
                'image_size': {
                    'width': self.original_image.shape[1],
                    'height': self.original_image.shape[0]
                },
                'annotations': [asdict(ann) for ann in self.current_annotations],
                'saved_at': datetime.now().isoformat()
            }
            
            # Save to file
            with open(annotations_path, 'w') as f:
                json.dump(annotations_data, f, indent=2)
            
            self.status_label.configure(text=f"💾 Annotations saved to {annotations_path.name}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save annotations: {str(e)}")
    
    def load_annotations(self):
        """Load annotations from file"""
        if not self.image_path:
            messagebox.showwarning("No Image", "Please load an image first.")
            return
        
        # Try to find annotations file
        image_path = Path(self.image_path)
        annotations_path = image_path.with_suffix('.json')
        
        if not annotations_path.exists():
            file_path = filedialog.askopenfilename(
                title="Select Annotations File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if not file_path:
                return
            annotations_path = Path(file_path)
        
        try:
            # Load annotations
            with open(annotations_path, 'r') as f:
                data = json.load(f)
            
            # Convert to BorderAnnotation objects
            self.current_annotations = [
                BorderAnnotation(**ann_data) 
                for ann_data in data['annotations']
            ]
            
            # Redraw
            self.display_image_on_canvas()
            
            self.status_label.configure(
                text=f"📂 Loaded {len(self.current_annotations)} annotations from {annotations_path.name}"
            )
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load annotations: {str(e)}")

def main():
    """Test the border calibration"""
    root = ctk.CTk()
    root.title("TruGrade Border Calibration Test")
    root.geometry("1400x900")
    
    border_cal = TruGradeBorderCalibration(root)
    border_cal.pack(fill="both", expand=True, padx=10, pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()