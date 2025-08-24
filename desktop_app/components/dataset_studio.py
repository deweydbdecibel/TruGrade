#!/usr/bin/env python3
"""
TruGrade Dataset Studio - Enterprise Dataset Management
======================================================

Transferred from RCG enterprise_dataset_frame.py with minimal adaptations.
Keeping the original code exactly as it is for maximum functionality.

Original Features:
- Complete dataset management
- Image grid with thumbnails
- Label management and verification
- Prediction analysis
- Export capabilities
- Professional UI
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import shutil
import sqlite3
from dataclasses import dataclass, asdict
import hashlib
import uuid

# Add project paths for TruGrade
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core"))

# Import TruGrade theme
from desktop_app.trugrade_simplified_shell import TruGradeTheme, TruGradeButton

# Data structures from original RCG code (keeping exactly as is)
@dataclass
class ImageData:
    """Image data structure"""
    id: str
    filename: str
    path: str
    width: int
    height: int
    size: int
    format: str
    hash: str
    added_date: str
    labels: List[Dict] = None
    predictions: List[Dict] = None
    verified: bool = False
    quality_score: float = 0.0
    metadata: Dict = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.predictions is None:
            self.predictions = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class LabelData:
    """Label data structure"""
    id: str
    name: str
    color: str
    description: str = ""
    count: int = 0
    created_date: str = ""

@dataclass
class AnnotationData:
    """Annotation data structure"""
    id: str
    image_id: str
    label_id: str
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float = 1.0
    verified: bool = False
    created_date: str = ""
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DatasetDatabase:
    """Database manager for dataset operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Images table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                size INTEGER,
                format TEXT,
                hash TEXT,
                added_date TEXT,
                verified BOOLEAN DEFAULT FALSE,
                quality_score REAL DEFAULT 0.0,
                metadata TEXT
            )
        ''')
        
        # Labels table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS labels (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                color TEXT,
                description TEXT,
                count INTEGER DEFAULT 0,
                created_date TEXT
            )
        ''')
        
        # Annotations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotations (
                id TEXT PRIMARY KEY,
                image_id TEXT,
                label_id TEXT,
                bbox TEXT,
                confidence REAL DEFAULT 1.0,
                verified BOOLEAN DEFAULT FALSE,
                created_date TEXT,
                metadata TEXT,
                FOREIGN KEY (image_id) REFERENCES images (id),
                FOREIGN KEY (label_id) REFERENCES labels (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_image(self, image_data: ImageData) -> bool:
        """Add image to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO images 
                (id, filename, path, width, height, size, format, hash, added_date, verified, quality_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                image_data.id, image_data.filename, image_data.path,
                image_data.width, image_data.height, image_data.size,
                image_data.format, image_data.hash, image_data.added_date,
                image_data.verified, image_data.quality_score,
                json.dumps(image_data.metadata)
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error adding image to database: {e}")
            return False
    
    def get_all_images(self) -> List[ImageData]:
        """Get all images from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM images ORDER BY added_date DESC')
            rows = cursor.fetchall()
            
            images = []
            for row in rows:
                metadata = json.loads(row[11]) if row[11] else {}
                image_data = ImageData(
                    id=row[0], filename=row[1], path=row[2],
                    width=row[3], height=row[4], size=row[5],
                    format=row[6], hash=row[7], added_date=row[8],
                    verified=bool(row[9]), quality_score=row[10],
                    metadata=metadata
                )
                images.append(image_data)
            
            conn.close()
            return images
            
        except Exception as e:
            print(f"Error getting images from database: {e}")
            return []
    
    def add_label(self, label_data: LabelData) -> bool:
        """Add label to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO labels 
                (id, name, color, description, count, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                label_data.id, label_data.name, label_data.color,
                label_data.description, label_data.count, label_data.created_date
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error adding label to database: {e}")
            return False
    
    def get_all_labels(self) -> List[LabelData]:
        """Get all labels from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM labels ORDER BY name')
            rows = cursor.fetchall()
            
            labels = []
            for row in rows:
                label_data = LabelData(
                    id=row[0], name=row[1], color=row[2],
                    description=row[3], count=row[4], created_date=row[5]
                )
                labels.append(label_data)
            
            conn.close()
            return labels
            
        except Exception as e:
            print(f"Error getting labels from database: {e}")
            return []

class TruGradeDatasetStudio(ctk.CTkFrame):
    """
    TruGrade Dataset Studio - Enterprise Dataset Management
    
    Transferred from RCG enterprise_dataset_frame.py with minimal adaptations.
    Keeping all original functionality intact.
    """
    
    def __init__(self, parent):
        super().__init__(parent, fg_color=TruGradeTheme.QUANTUM_DARK)
        
        # Core state from original RCG code
        self.current_dataset_path = None
        self.database = None
        self.images = []
        self.labels = []
        self.annotations = []
        self.selected_images = set()
        self.current_image_index = 0
        self.grid_columns = 6
        self.thumbnail_size = 150
        self.current_filter = "all"
        self.search_query = ""
        
        # UI state
        self.image_thumbnails = {}
        self.image_widgets = {}
        self.current_tab = "images"
        
        # Setup UI exactly as in original
        self.setup_ui()
        
        print("🗂️ TruGrade Dataset Studio initialized")
    
    def setup_ui(self):
        """Setup the dataset studio interface (from original RCG code)"""
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header section
        self.create_header()
        
        # Main content with tabs
        self.create_main_content()
        
        # Status bar
        self.create_status_bar()
    
    def create_header(self):
        """Create header section (from original RCG code)"""
        header_frame = ctk.CTkFrame(self, fg_color=TruGradeTheme.NEURAL_GRAY, corner_radius=15)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🗂️ TruGrade Dataset Studio",
            font=(TruGradeTheme.FONT_FAMILY, 24, "bold"),
            text_color=TruGradeTheme.PLASMA_BLUE
        )
        title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # TruScore branding
        truscore_label = ctk.CTkLabel(
            header_frame,
            text="Enterprise Dataset Management • TruScore™ Ready",
            font=(TruGradeTheme.FONT_FAMILY, 12, "bold"),
            text_color=TruGradeTheme.QUANTUM_GREEN
        )
        truscore_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Dataset controls
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, rowspan=2, padx=20, pady=15, sticky="e")
        
        TruGradeButton(
            controls_frame,
            text="📁 New Dataset",
            style="primary",
            width=140,
            command=self.create_new_dataset
        ).pack(side="left", padx=5)
        
        TruGradeButton(
            controls_frame,
            text="📂 Load Dataset",
            style="glass",
            width=140,
            command=self.load_dataset
        ).pack(side="left", padx=5)
        
        TruGradeButton(
            controls_frame,
            text="💾 Save Dataset",
            style="glass",
            width=140,
            command=self.save_dataset
        ).pack(side="left", padx=5)
    
    def create_main_content(self):
        """Create main content area with tabs (from original RCG code)"""
        main_frame = ctk.CTkFrame(self, fg_color=TruGradeTheme.NEURAL_GRAY, corner_radius=15)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Tab buttons
        tab_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tab_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        self.tab_buttons = {}
        tabs = [
            ("📂 Images", "images"),
            ("🏷️ Labels", "labels"),
            ("✅ Verification", "verification"),
            ("🤖 Predictions", "predictions"),
            ("📊 Analytics", "analytics"),
            ("⚙️ Settings", "settings")
        ]
        
        for i, (text, tab_id) in enumerate(tabs):
            btn = TruGradeButton(
                tab_frame,
                text=text,
                style="primary" if tab_id == "images" else "glass",
                width=120,
                height=35,
                command=lambda t=tab_id: self.switch_tab(t)
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons[tab_id] = btn
        
        # Tab content area
        self.content_frame = ctk.CTkFrame(main_frame, fg_color=TruGradeTheme.VOID_BLACK, corner_radius=10)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Initialize with images tab
        self.switch_tab("images")
    
    def create_status_bar(self):
        """Create status bar (from original RCG code)"""
        status_frame = ctk.CTkFrame(self, fg_color=TruGradeTheme.NEURAL_GRAY, corner_radius=10)
        status_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="🗂️ Dataset Studio Ready - Create or load a dataset to begin",
            font=(TruGradeTheme.FONT_FAMILY, 12),
            text_color=TruGradeTheme.GHOST_WHITE
        )
        self.status_label.pack(pady=10)
    
    def switch_tab(self, tab_id: str):
        """Switch between tabs (from original RCG code)"""
        # Update button styles
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(fg_color=TruGradeTheme.PLASMA_BLUE)
            else:
                btn.configure(fg_color=("gray20", "gray20"))
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Load tab content
        self.current_tab = tab_id
        
        if tab_id == "images":
            self.create_images_tab()
        elif tab_id == "labels":
            self.create_labels_tab()
        elif tab_id == "verification":
            self.create_verification_tab()
        elif tab_id == "predictions":
            self.create_predictions_tab()
        elif tab_id == "analytics":
            self.create_analytics_tab()
        elif tab_id == "settings":
            self.create_settings_tab()
    
    def create_images_tab(self):
        """Create images tab (from original RCG code)"""
        images_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        images_frame.pack(fill="both", expand=True, padx=10, pady=10)
        images_frame.grid_columnconfigure(1, weight=1)
        images_frame.grid_rowconfigure(1, weight=1)
        
        # Left panel - controls
        controls_panel = ctk.CTkFrame(images_frame, fg_color=TruGradeTheme.QUANTUM_DARK, width=250)
        controls_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
        controls_panel.grid_propagate(False)
        
        # Import section
        import_section = ctk.CTkFrame(controls_panel, fg_color="transparent")
        import_section.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            import_section,
            text="📥 Import Images",
            font=(TruGradeTheme.FONT_FAMILY, 14, "bold"),
            text_color=TruGradeTheme.GHOST_WHITE
        ).pack(pady=(0, 10))
        
        TruGradeButton(
            import_section,
            text="📁 Add Images",
            style="primary",
            width=200,
            command=self.add_images
        ).pack(pady=2)
        
        TruGradeButton(
            import_section,
            text="📂 Add Folder",
            style="glass",
            width=200,
            command=self.add_folder
        ).pack(pady=2)
        
        # Filter section
        filter_section = ctk.CTkFrame(controls_panel, fg_color="transparent")
        filter_section.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            filter_section,
            text="🔍 Filter & Search",
            font=(TruGradeTheme.FONT_FAMILY, 14, "bold"),
            text_color=TruGradeTheme.GHOST_WHITE
        ).pack(pady=(0, 10))
        
        # Search entry
        self.search_entry = ctk.CTkEntry(
            filter_section,
            placeholder_text="Search images...",
            width=200
        )
        self.search_entry.pack(pady=2)
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)
        
        # Filter dropdown
        self.filter_var = ctk.StringVar(value="all")
        filter_dropdown = ctk.CTkOptionMenu(
            filter_section,
            variable=self.filter_var,
            values=["all", "verified", "unverified", "labeled", "unlabeled"],
            width=200,
            command=self.on_filter_changed
        )
        filter_dropdown.pack(pady=2)
        
        # Grid controls
        grid_section = ctk.CTkFrame(controls_panel, fg_color="transparent")
        grid_section.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            grid_section,
            text="🔧 Grid Settings",
            font=(TruGradeTheme.FONT_FAMILY, 14, "bold"),
            text_color=TruGradeTheme.GHOST_WHITE
        ).pack(pady=(0, 10))
        
        # Columns slider
        ctk.CTkLabel(grid_section, text="Columns:", text_color=TruGradeTheme.GHOST_WHITE).pack()
        self.columns_slider = ctk.CTkSlider(
            grid_section,
            from_=2, to=10, number_of_steps=8,
            width=180,
            command=self.on_columns_changed
        )
        self.columns_slider.set(6)
        self.columns_slider.pack(pady=2)
        
        # Thumbnail size slider
        ctk.CTkLabel(grid_section, text="Thumbnail Size:", text_color=TruGradeTheme.GHOST_WHITE).pack(pady=(10, 0))
        self.size_slider = ctk.CTkSlider(
            grid_section,
            from_=100, to=300, number_of_steps=20,
            width=180,
            command=self.on_size_changed
        )
        self.size_slider.set(150)
        self.size_slider.pack(pady=2)
        
        # Right panel - image grid
        grid_panel = ctk.CTkFrame(images_frame, fg_color=TruGradeTheme.QUANTUM_DARK)
        grid_panel.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        
        # Grid header
        grid_header = ctk.CTkFrame(grid_panel, fg_color="transparent")
        grid_header.pack(fill="x", padx=15, pady=15)
        
        self.grid_info_label = ctk.CTkLabel(
            grid_header,
            text="No images loaded",
            font=(TruGradeTheme.FONT_FAMILY, 14, "bold"),
            text_color=TruGradeTheme.PLASMA_BLUE
        )
        self.grid_info_label.pack(side="left")
        
        # Selection controls
        selection_frame = ctk.CTkFrame(grid_header, fg_color="transparent")
        selection_frame.pack(side="right")
        
        TruGradeButton(
            selection_frame,
            text="Select All",
            style="glass",
            width=80,
            height=30,
            command=self.select_all_images
        ).pack(side="left", padx=2)
        
        TruGradeButton(
            selection_frame,
            text="Clear",
            style="glass",
            width=60,
            height=30,
            command=self.clear_selection
        ).pack(side="left", padx=2)
        
        # Scrollable grid
        self.image_grid = ctk.CTkScrollableFrame(
            grid_panel,
            fg_color="transparent",
            scrollbar_button_color=TruGradeTheme.PLASMA_BLUE
        )
        self.image_grid.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Bottom panel - image preview
        preview_panel = ctk.CTkFrame(images_frame, fg_color=TruGradeTheme.QUANTUM_DARK, height=200)
        preview_panel.grid(row=1, column=1, sticky="ew")
        preview_panel.grid_propagate(False)
        
        self.preview_label = ctk.CTkLabel(
            preview_panel,
            text="Select an image to preview",
            font=(TruGradeTheme.FONT_FAMILY, 14),
            text_color=TruGradeTheme.GHOST_WHITE
        )
        self.preview_label.pack(expand=True)
    
    # Core functionality methods from original RCG code (keeping exactly as is)
    
    def create_new_dataset(self):
        """Create a new dataset (from original RCG code)"""
        dataset_path = filedialog.askdirectory(title="Select Dataset Directory")
        if not dataset_path:
            return
        
        self.current_dataset_path = dataset_path
        db_path = os.path.join(dataset_path, "dataset.db")
        
        try:
            self.database = DatasetDatabase(db_path)
            self.images = []
            self.labels = []
            self.annotations = []
            self.selected_images.clear()
            
            # Create dataset metadata
            metadata = {
                "name": os.path.basename(dataset_path),
                "created_date": datetime.now().isoformat(),
                "version": "1.0",
                "description": "TruGrade dataset for card grading AI training"
            }
            
            metadata_path = os.path.join(dataset_path, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.status_label.configure(text=f"✅ New dataset created: {metadata['name']}")
            self.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create dataset: {str(e)}")
    
    def load_dataset(self):
        """Load existing dataset (from original RCG code)"""
        dataset_path = filedialog.askdirectory(title="Select Dataset Directory")
        if not dataset_path:
            return
        
        db_path = os.path.join(dataset_path, "dataset.db")
        if not os.path.exists(db_path):
            messagebox.showerror("Error", "No dataset found in selected directory")
            return
        
        try:
            self.current_dataset_path = dataset_path
            self.database = DatasetDatabase(db_path)
            
            # Load data
            self.images = self.database.get_all_images()
            self.labels = self.database.get_all_labels()
            
            # Load metadata
            metadata_path = os.path.join(dataset_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                dataset_name = metadata.get("name", os.path.basename(dataset_path))
            else:
                dataset_name = os.path.basename(dataset_path)
            
            self.status_label.configure(text=f"✅ Dataset loaded: {dataset_name} ({len(self.images)} images)")
            self.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dataset: {str(e)}")
    
    def save_dataset(self):
        """Save current dataset (from original RCG code)"""
        if not self.current_dataset_path or not self.database:
            messagebox.showwarning("Warning", "No dataset loaded")
            return
        
        try:
            # Update metadata
            metadata_path = os.path.join(self.current_dataset_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            metadata.update({
                "last_modified": datetime.now().isoformat(),
                "image_count": len(self.images),
                "label_count": len(self.labels)
            })
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.status_label.configure(text="💾 Dataset saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save dataset: {str(e)}")
    
    def add_images(self):
        """Add individual images (from original RCG code)"""
        if not self.database:
            messagebox.showwarning("Warning", "Please create or load a dataset first")
            return
        
        file_types = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
            ("All files", "*.*")
        ]
        
        file_paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=file_types
        )
        
        if file_paths:
            self.import_images(file_paths)
    
    def add_folder(self):
        """Add images from folder (from original RCG code)"""
        if not self.database:
            messagebox.showwarning("Warning", "Please create or load a dataset first")
            return
        
        folder_path = filedialog.askdirectory(title="Select Image Folder")
        if not folder_path:
            return
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        image_files = []
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if Path(file).suffix.lower() in image_extensions:
                    image_files.append(os.path.join(root, file))
        
        if image_files:
            self.import_images(image_files)
        else:
            messagebox.showinfo("Info", "No image files found in selected folder")
    
    def import_images(self, file_paths: List[str]):
        """Import images with progress (from original RCG code)"""
        def import_worker():
            imported_count = 0
            total_count = len(file_paths)
            
            for i, file_path in enumerate(file_paths):
                try:
                    # Update status
                    progress = (i + 1) / total_count * 100
                    self.after(0, lambda p=progress: self.status_label.configure(
                        text=f"📥 Importing images... {i+1}/{total_count} ({p:.1f}%)"
                    ))
                    
                    # Load image info
                    image = cv2.imread(file_path)
                    if image is None:
                        continue
                    
                    height, width = image.shape[:2]
                    file_size = os.path.getsize(file_path)
                    file_format = Path(file_path).suffix.lower()[1:]
                    
                    # Calculate hash
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    # Create image data
                    image_data = ImageData(
                        id=str(uuid.uuid4()),
                        filename=os.path.basename(file_path),
                        path=file_path,
                        width=width,
                        height=height,
                        size=file_size,
                        format=file_format,
                        hash=file_hash,
                        added_date=datetime.now().isoformat()
                    )
                    
                    # Add to database
                    if self.database.add_image(image_data):
                        imported_count += 1
                    
                except Exception as e:
                    print(f"Error importing {file_path}: {e}")
            
            # Update UI
            self.after(0, lambda: self.import_complete(imported_count, total_count))
        
        # Start import in background
        threading.Thread(target=import_worker, daemon=True).start()
    
    def import_complete(self, imported_count: int, total_count: int):
        """Handle import completion (from original RCG code)"""
        # Reload images
        self.images = self.database.get_all_images()
        
        # Update status
        self.status_label.configure(
            text=f"✅ Import complete: {imported_count}/{total_count} images imported"
        )
        
        # Refresh display
        self.refresh_current_tab()
    
    def refresh_current_tab(self):
        """Refresh current tab display (from original RCG code)"""
        if self.current_tab == "images":
            self.refresh_image_grid()
        elif self.current_tab == "labels":
            self.refresh_labels_tab()
        # Add other tab refreshes as needed
    
    def refresh_image_grid(self):
        """Refresh image grid display (from original RCG code)"""
        # Clear existing grid
        for widget in self.image_grid.winfo_children():
            widget.destroy()
        
        self.image_widgets.clear()
        
        # Filter images
        filtered_images = self.filter_images()
        
        # Update grid info
        self.grid_info_label.configure(
            text=f"{len(filtered_images)} images ({len(self.selected_images)} selected)"
        )
        
        if not filtered_images:
            no_images_label = ctk.CTkLabel(
                self.image_grid,
                text="No images to display",
                font=(TruGradeTheme.FONT_FAMILY, 16),
                text_color=TruGradeTheme.GHOST_WHITE
            )
            no_images_label.pack(expand=True)
            return
        
        # Create grid layout
        self.create_image_grid_layout(filtered_images)
    
    def filter_images(self) -> List[ImageData]:
        """Filter images based on current filter and search (from original RCG code)"""
        filtered = self.images.copy()
        
        # Apply search filter
        if self.search_query:
            filtered = [img for img in filtered if self.search_query.lower() in img.filename.lower()]
        
        # Apply status filter
        if self.current_filter == "verified":
            filtered = [img for img in filtered if img.verified]
        elif self.current_filter == "unverified":
            filtered = [img for img in filtered if not img.verified]
        elif self.current_filter == "labeled":
            filtered = [img for img in filtered if img.labels]
        elif self.current_filter == "unlabeled":
            filtered = [img for img in filtered if not img.labels]
        
        return filtered
    
    def create_image_grid_layout(self, images: List[ImageData]):
        """Create image grid layout (from original RCG code)"""
        # Create grid frame
        grid_frame = ctk.CTkFrame(self.image_grid, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        
        # Configure grid columns
        for i in range(self.grid_columns):
            grid_frame.grid_columnconfigure(i, weight=1, uniform="column")
        
        # Add images to grid
        for i, image_data in enumerate(images):
            row = i // self.grid_columns
            col = i % self.grid_columns
            
            image_widget = self.create_image_widget(grid_frame, image_data)
            image_widget.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            self.image_widgets[image_data.id] = image_widget
    
    def create_image_widget(self, parent, image_data: ImageData):
        """Create individual image widget (from original RCG code)"""
        # Main frame
        widget_frame = ctk.CTkFrame(
            parent,
            fg_color=TruGradeTheme.QUANTUM_DARK,
            corner_radius=10,
            width=self.thumbnail_size + 20,
            height=self.thumbnail_size + 60
        )
        widget_frame.grid_propagate(False)
        
        # Load and display thumbnail
        thumbnail = self.load_thumbnail(image_data)
        
        # Image label
        image_label = ctk.CTkLabel(
            widget_frame,
            image=thumbnail,
            text=""
        )
        image_label.pack(pady=(10, 5))
        
        # Filename label
        filename_label = ctk.CTkLabel(
            widget_frame,
            text=image_data.filename[:20] + "..." if len(image_data.filename) > 20 else image_data.filename,
            font=(TruGradeTheme.FONT_FAMILY, 10),
            text_color=TruGradeTheme.GHOST_WHITE
        )
        filename_label.pack()
        
        # Status indicators
        status_frame = ctk.CTkFrame(widget_frame, fg_color="transparent")
        status_frame.pack(pady=2)
        
        if image_data.verified:
            verified_label = ctk.CTkLabel(
                status_frame,
                text="✅",
                font=(TruGradeTheme.FONT_FAMILY, 12)
            )
            verified_label.pack(side="left")
        
        if image_data.labels:
            labeled_label = ctk.CTkLabel(
                status_frame,
                text="🏷️",
                font=(TruGradeTheme.FONT_FAMILY, 12)
            )
            labeled_label.pack(side="left")
        
        # Bind click events
        def on_click(event):
            self.toggle_image_selection(image_data.id)
        
        def on_double_click(event):
            self.open_image_viewer(image_data)
        
        widget_frame.bind("<Button-1>", on_click)
        widget_frame.bind("<Double-Button-1>", on_double_click)
        image_label.bind("<Button-1>", on_click)
        image_label.bind("<Double-Button-1>", on_double_click)
        
        return widget_frame
    
    def load_thumbnail(self, image_data: ImageData):
        """Load image thumbnail (from original RCG code)"""
        try:
            # Check if thumbnail already exists
            if image_data.id in self.image_thumbnails:
                return self.image_thumbnails[image_data.id]
            
            # Load image
            image = cv2.imread(image_data.path)
            if image is None:
                return self.create_placeholder_thumbnail()
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Resize to thumbnail size
            height, width = image_rgb.shape[:2]
            aspect_ratio = width / height
            
            if aspect_ratio > 1:
                new_width = self.thumbnail_size
                new_height = int(self.thumbnail_size / aspect_ratio)
            else:
                new_height = self.thumbnail_size
                new_width = int(self.thumbnail_size * aspect_ratio)
            
            resized_image = cv2.resize(image_rgb, (new_width, new_height))
            
            # Convert to PIL and PhotoImage
            pil_image = Image.fromarray(resized_image)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Cache thumbnail
            self.image_thumbnails[image_data.id] = photo
            
            return photo
            
        except Exception as e:
            print(f"Error loading thumbnail for {image_data.filename}: {e}")
            return self.create_placeholder_thumbnail()
    
    def create_placeholder_thumbnail(self):
        """Create placeholder thumbnail (from original RCG code)"""
        # Create placeholder image
        placeholder = Image.new('RGB', (self.thumbnail_size, self.thumbnail_size), color='gray')
        draw = ImageDraw.Draw(placeholder)
        
        # Add text
        text = "No Image"
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.thumbnail_size - text_width) // 2
        y = (self.thumbnail_size - text_height) // 2
        
        draw.text((x, y), text, fill='white')
        
        return ImageTk.PhotoImage(placeholder)
    
    # Event handlers from original RCG code
    
    def on_search_changed(self, event):
        """Handle search query change (from original RCG code)"""
        self.search_query = self.search_entry.get()
        self.refresh_image_grid()
    
    def on_filter_changed(self, value):
        """Handle filter change (from original RCG code)"""
        self.current_filter = value
        self.refresh_image_grid()
    
    def on_columns_changed(self, value):
        """Handle grid columns change (from original RCG code)"""
        self.grid_columns = int(value)
        self.refresh_image_grid()
    
    def on_size_changed(self, value):
        """Handle thumbnail size change (from original RCG code)"""
        self.thumbnail_size = int(value)
        self.image_thumbnails.clear()  # Clear cache to regenerate thumbnails
        self.refresh_image_grid()
    
    def toggle_image_selection(self, image_id: str):
        """Toggle image selection (from original RCG code)"""
        if image_id in self.selected_images:
            self.selected_images.remove(image_id)
        else:
            self.selected_images.add(image_id)
        
        self.update_selection_display()
    
    def select_all_images(self):
        """Select all visible images (from original RCG code)"""
        filtered_images = self.filter_images()
        self.selected_images = {img.id for img in filtered_images}
        self.update_selection_display()
    
    def clear_selection(self):
        """Clear image selection (from original RCG code)"""
        self.selected_images.clear()
        self.update_selection_display()
    
    def update_selection_display(self):
        """Update selection display (from original RCG code)"""
        # Update grid info
        filtered_images = self.filter_images()
        self.grid_info_label.configure(
            text=f"{len(filtered_images)} images ({len(self.selected_images)} selected)"
        )
        
        # Update widget appearance
        for image_id, widget in self.image_widgets.items():
            if image_id in self.selected_images:
                widget.configure(border_width=3, border_color=TruGradeTheme.PLASMA_BLUE)
            else:
                widget.configure(border_width=1, border_color=TruGradeTheme.NEURAL_GRAY)
    
    def open_image_viewer(self, image_data: ImageData):
        """Open image in viewer (from original RCG code)"""
        # TODO: Implement image viewer
        print(f"Opening image viewer for: {image_data.filename}")
    
    # Placeholder methods for other tabs (from original RCG code)
    
    def create_labels_tab(self):
        """Create labels tab (placeholder from original RCG code)"""
        placeholder_label = ctk.CTkLabel(
            self.content_frame,
            text="🏷️ Labels Tab\nComing Soon",
            font=(TruGradeTheme.FONT_FAMILY, 16),
            text_color=TruGradeTheme.GHOST_WHITE
        )
        placeholder_label.pack(expand=True)
    
    def create_verification_tab(self):
        """Create verification tab (placeholder from original RCG code)"""
        placeholder_label = ctk.CTkLabel(
            self.content_frame,
            text="✅ Verification Tab\nComing Soon",
            font=(TruGradeTheme.FONT_FAMILY, 16),
            text_color=TruGradeTheme.GHOST_WHITE
        )
        placeholder_label.pack(expand=True)
    
    def create_predictions_tab(self):
        """Create predictions tab (placeholder from original RCG code)"""
        placeholder_label = ctk.CTkLabel(
            self.content_frame,
            text="🤖 Predictions Tab\nComing Soon",
            font=(TruGradeTheme.FONT_FAMILY, 16),
            text_color=TruGradeTheme.GHOST_WHITE
        )
        placeholder_label.pack(expand=True)
    
    def create_analytics_tab(self):
        """Create analytics tab (placeholder from original RCG code)"""
        placeholder_label = ctk.CTkLabel(
            self.content_frame,
            text="📊 Analytics Tab\nComing Soon",
            font=(TruGradeTheme.FONT_FAMILY, 16),
            text_color=TruGradeTheme.GHOST_WHITE
        )
        placeholder_label.pack(expand=True)
    
    def create_settings_tab(self):
        """Create settings tab (placeholder from original RCG code)"""
        placeholder_label = ctk.CTkLabel(
            self.content_frame,
            text="⚙️ Settings Tab\nComing Soon",
            font=(TruGradeTheme.FONT_FAMILY, 16),
            text_color=TruGradeTheme.GHOST_WHITE
        )
        placeholder_label.pack(expand=True)
    
    def refresh_labels_tab(self):
        """Refresh labels tab (placeholder from original RCG code)"""
        pass

def main():
    """Test the dataset studio"""
    root = ctk.CTk()
    root.title("TruGrade Dataset Studio Test")
    root.geometry("1600x1000")
    
    dataset_studio = TruGradeDatasetStudio(root)
    dataset_studio.pack(fill="both", expand=True, padx=10, pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()