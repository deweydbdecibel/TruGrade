#!/usr/bin/env python3
"""
🚀 Advanced Training Platform - Revolutionary Card Grader
========================================================

FLEXIBLE TRAINING: Complete control over any model type, any dataset, any technique
- Choose model type: Border/Corner/Edge/Surface/Photometric
- Add images from any era/source
- Retrain existing models or create new ones
- Advanced techniques: 2-class borders, multi-modal fusion
- Prediction + Correction learning workflow
- Validation for any model configuration
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid
import shutil

from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, Integer, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

# Database setup
DATABASE_URL = "postgresql://revolutionary_user:revolutionary_pass@localhost/card_grading"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType:
    BORDER_DETECTION = "border_detection"
    CORNER_ANALYSIS = "corner_analysis" 
    EDGE_ANALYSIS = "edge_analysis"
    SURFACE_DEFECTS = "surface_defects"
    PHOTOMETRIC_INTEGRATION = "photometric_integration"

class TrainingTechnique:
    SINGLE_CLASS = "single_class"
    DUAL_CLASS = "dual_class"  # For borders: physical + graphic
    MULTI_MODAL = "multi_modal"
    PREDICTION_CORRECTION = "prediction_correction"
    TRANSFER_LEARNING = "transfer_learning"

class AdvancedTrainingPlatform:
    """Advanced, flexible training platform for any model type"""

    def __init__(self):
        self.app = FastAPI(title="Advanced Training Platform")
        self.setup_cors()
        
        # Dynamic dataset discovery
        self.dataset_scan_paths = [
            "/home/dewster/RCG/data/datasets",
            "/home/dewster/RCG/data/training",
            "/home/dewster/RCG/models"
        ]
        
        self.setup_routes()
        logger.info("🚀 Advanced Training Platform initialized")

    def setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):

        @self.app.get("/")
        async def advanced_training_dashboard():
            """Advanced training platform dashboard"""
            return HTMLResponse(self.get_dashboard_html())

        @self.app.get("/api/model-types")
        async def get_model_types():
            """Get available model types with descriptions"""
            return [
                {
                    "id": ModelType.BORDER_DETECTION,
                    "name": "Border Detection",
                    "description": "Detect card borders (physical edges, graphic boundaries)",
                    "techniques": ["single_class", "dual_class"],
                    "formats": ["YOLO", "Segmentation"],
                    "icon": "🎯"
                },
                {
                    "id": ModelType.CORNER_ANALYSIS,
                    "name": "Corner Analysis", 
                    "description": "Analyze corner quality and damage",
                    "techniques": ["classification", "regression"],
                    "formats": ["Vision Transformer", "CNN"],
                    "icon": "📐"
                },
                {
                    "id": ModelType.EDGE_ANALYSIS,
                    "name": "Edge Analysis",
                    "description": "Edge quality, straightness, damage detection",
                    "techniques": ["edge_detection", "quality_scoring"],
                    "formats": ["CNN", "Classical CV"],
                    "icon": "📏"
                },
                {
                    "id": ModelType.SURFACE_DEFECTS,
                    "name": "Surface Defect Detection",
                    "description": "Scratches, stains, print defects, surface quality",
                    "techniques": ["defect_detection", "quality_regression"],
                    "formats": ["ViT", "U-Net", "YOLO"],
                    "icon": "🔍"
                },
                {
                    "id": ModelType.PHOTOMETRIC_INTEGRATION,
                    "name": "Photometric Integration",
                    "description": "Integrate all models with photometric stereo",
                    "techniques": ["multi_modal", "fusion"],
                    "formats": ["Custom Architecture"],
                    "icon": "🌟"
                }
            ]

        @self.app.get("/api/existing-models/{model_type}")
        async def get_existing_models(model_type: str):
            """Get existing trained models for retraining"""
            models = []
            
            # Scan for existing models
            for scan_path in self.dataset_scan_paths:
                model_path = Path(scan_path)
                if model_path.exists():
                    # Look for model files
                    for model_file in model_path.rglob("*.pt"):
                        if model_type in str(model_file):
                            models.append({
                                "name": model_file.stem,
                                "path": str(model_file),
                                "size": model_file.stat().st_size,
                                "modified": model_file.stat().st_mtime,
                                "type": "PyTorch"
                            })
            
            return models

        @self.app.get("/api/datasets/scan-all")
        async def scan_all_datasets():
            """Dynamically scan for any available datasets"""
            datasets = []
            
            for scan_path in self.dataset_scan_paths:
                base_path = Path(scan_path)
                if not base_path.exists():
                    continue
                    
                # Find directories with images
                for dataset_dir in base_path.rglob("*"):
                    if not dataset_dir.is_dir():
                        continue
                        
                    # Check for image files
                    image_files = list(dataset_dir.glob("*.jpg")) + list(dataset_dir.glob("*.png"))
                    if len(image_files) < 5:  # Skip if too few images
                        continue
                    
                    # Check for label files
                    txt_files = list(dataset_dir.glob("*.txt"))
                    json_files = list(dataset_dir.glob("*.json"))
                    
                    datasets.append({
                        "id": str(dataset_dir).replace("/", "_"),
                        "name": dataset_dir.name,
                        "path": str(dataset_dir),
                        "images": len(image_files),
                        "txt_labels": len(txt_files),
                        "json_labels": len(json_files),
                        "type": "auto_discovered"
                    })
            
            return sorted(datasets, key=lambda x: x["images"], reverse=True)

        @self.app.post("/api/training-session/create")
        async def create_training_session(session_config: Dict):
            """Create new training session with full configuration"""
            
            session_id = str(uuid.uuid4())
            
            # Validate configuration
            required_fields = ["model_type", "session_name"]
            for field in required_fields:
                if field not in session_config:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
            
            # Create session directory
            session_dir = Path(f"/home/dewster/RCG/data/training_sessions/{session_id}")
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            config_file = session_dir / "config.json"
            with open(config_file, 'w') as f:
                json.dump(session_config, f, indent=2)
            
            return {
                "session_id": session_id,
                "session_dir": str(session_dir),
                "config": session_config,
                "status": "created"
            }

        @self.app.post("/api/training-session/{session_id}/add-images")
        async def add_images_to_session(
            session_id: str,
            source_type: str = Form(...),  # "upload", "existing_dataset", "copy_from"
            files: List[UploadFile] = File(default=[]),
            source_path: str = Form(default="")
        ):
            """Add images to training session from various sources"""
            
            session_dir = Path(f"/home/dewster/RCG/data/training_sessions/{session_id}")
            if not session_dir.exists():
                raise HTTPException(status_code=404, detail="Session not found")
            
            images_dir = session_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            added_files = []
            
            if source_type == "upload" and files:
                # Handle uploaded files
                for file in files:
                    file_path = images_dir / file.filename
                    with open(file_path, "wb") as f:
                        content = await file.read()
                        f.write(content)
                    added_files.append({
                        "name": file.filename,
                        "path": str(file_path),
                        "size": file_path.stat().st_size
                    })
            
            elif source_type == "existing_dataset" and source_path:
                # Copy from existing dataset
                source = Path(source_path)
                if source.exists():
                    for img_file in source.glob("*.jpg"):
                        target = images_dir / img_file.name
                        shutil.copy2(img_file, target)
                        added_files.append({
                            "name": img_file.name,
                            "path": str(target),
                            "size": target.stat().st_size
                        })
            
            return {
                "session_id": session_id,
                "added_files": len(added_files),
                "source_type": source_type,
                "files": added_files
            }

        @self.app.get("/api/training-session/{session_id}/files")
        async def get_session_files(session_id: str, file_type: str = "images"):
            """Get all files in training session"""
            
            session_dir = Path(f"/home/dewster/RCG/data/training_sessions/{session_id}")
            if not session_dir.exists():
                raise HTTPException(status_code=404, detail="Session not found")
            
            files = []
            
            if file_type == "images":
                images_dir = session_dir / "images"
                if images_dir.exists():
                    for img_file in images_dir.glob("*"):
                        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                            files.append({
                                "name": img_file.name,
                                "path": str(img_file),
                                "size": img_file.stat().st_size,
                                "type": "image"
                            })
            
            elif file_type.startswith("labels_"):
                label_type = file_type.replace("labels_", "")
                labels_dir = session_dir / "labels" / label_type
                if labels_dir.exists():
                    for label_file in labels_dir.glob("*"):
                        files.append({
                            "name": label_file.name,
                            "path": str(label_file),
                            "size": label_file.stat().st_size,
                            "type": "label"
                        })
            
            return {"files": files, "count": len(files)}

        @self.app.delete("/api/training-session/{session_id}/file")
        async def delete_session_file(session_id: str, file_path: str):
            """Delete specific file from session"""
            
            session_dir = Path(f"/home/dewster/RCG/data/training_sessions/{session_id}")
            if not session_dir.exists():
                raise HTTPException(status_code=404, detail="Session not found")
            
            file_to_delete = Path(file_path)
            if file_to_delete.exists() and str(file_to_delete).startswith(str(session_dir)):
                file_to_delete.unlink()
                return {"status": "deleted", "file": file_path}
            else:
                raise HTTPException(status_code=404, detail="File not found")

        @self.app.post("/api/training-session/{session_id}/add-labels")
        async def add_labels_to_session(
            session_id: str,
            label_type: str = Form(...),  # "predictions", "corrections", "ground_truth"
            label_format: str = Form(...),  # "yolo_txt", "json", "coco"
            files: List[UploadFile] = File(...)
        ):
            """Add label files (predictions, corrections, ground truth)"""
            
            session_dir = Path(f"/home/dewster/RCG/data/training_sessions/{session_id}")
            if not session_dir.exists():
                raise HTTPException(status_code=404, detail="Session not found")
            
            labels_dir = session_dir / "labels" / label_type
            labels_dir.mkdir(parents=True, exist_ok=True)
            
            added_labels = []
            for file in files:
                file_path = labels_dir / file.filename
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                added_labels.append({
                    "name": file.filename,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "type": label_type
                })
            
            return {
                "session_id": session_id,
                "label_type": label_type,
                "label_format": label_format,
                "added_labels": len(added_labels),
                "files": added_labels
            }

        @self.app.post("/api/training-session/{session_id}/validate")
        async def validate_training_session(session_id: str):
            """Validate training session before starting"""
            
            session_dir = Path(f"/home/dewster/RCG/data/training_sessions/{session_id}")
            if not session_dir.exists():
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Load config
            config_file = session_dir / "config.json"
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            validation = {
                "session_id": session_id,
                "status": "validating",
                "issues": [],
                "warnings": [],
                "ready": False,
                "summary": {}
            }
            
            # Check images
            images_dir = session_dir / "images"
            image_files = list(images_dir.glob("*.jpg")) if images_dir.exists() else []
            
            # Check labels
            labels_dir = session_dir / "labels"
            predictions = list((labels_dir / "predictions").glob("*")) if (labels_dir / "predictions").exists() else []
            corrections = list((labels_dir / "corrections").glob("*")) if (labels_dir / "corrections").exists() else []
            
            validation["summary"] = {
                "model_type": config.get("model_type"),
                "technique": config.get("technique", "standard"),
                "images": len(image_files),
                "predictions": len(predictions),
                "corrections": len(corrections),
                "training_ready": False
            }
            
            # Validation logic
            if len(image_files) == 0:
                validation["issues"].append("No images found")
            elif len(image_files) < 10:
                validation["warnings"].append(f"Only {len(image_files)} images - recommend 50+ for good training")
            
            if config.get("technique") == "prediction_ground_truth":
                if len(predictions) == 0:
                    validation["issues"].append("Prediction vs Ground Truth technique requires prediction files")
                if len(ground_truth) == 0:
                    validation["issues"].append("Prediction vs Ground Truth technique requires ground truth files")
            
            if len(validation["issues"]) == 0:
                validation["ready"] = True
                validation["status"] = "ready"
                validation["summary"]["training_ready"] = True
            
            return validation

        @self.app.post("/api/training-session/{session_id}/start")
        async def start_training_session(session_id: str):
            """Start training with validated session"""
            
            # This would integrate with actual training code
            # For now, return training started confirmation
            
            return {
                "session_id": session_id,
                "status": "training_started",
                "message": "Advanced training started with full configuration",
                "training_id": str(uuid.uuid4())
            }

    def get_dashboard_html(self) -> str:
        """Advanced training platform dashboard"""
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🚀 Advanced Training Platform</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh; color: #333;
                }
                .container { max-width: 1800px; margin: 0 auto; padding: 20px; }
                .header {
                    background: rgba(255,255,255,0.95); border-radius: 20px;
                    padding: 40px; text-align: center; margin-bottom: 30px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }
                .header h1 {
                    font-size: 3em; font-weight: 300; margin-bottom: 10px;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                }
                .workflow-nav {
                    display: flex; justify-content: center; gap: 10px;
                    margin: 20px 0; flex-wrap: wrap;
                }
                .nav-step {
                    background: rgba(255,255,255,0.2); padding: 10px 20px;
                    border-radius: 25px; cursor: pointer; transition: all 0.3s;
                    border: 2px solid transparent;
                }
                .nav-step.active {
                    background: #4ecdc4; color: white;
                    border-color: #44a08d;
                }
                .content-panel {
                    background: rgba(255,255,255,0.95); border-radius: 20px;
                    padding: 40px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    min-height: 600px;
                }
                .model-grid {
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                    gap: 25px; margin: 30px 0;
                }
                .model-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 30px; border-radius: 15px;
                    cursor: pointer; transition: all 0.3s; position: relative;
                }
                .model-card:hover { transform: translateY(-5px) scale(1.02); }
                .model-card.selected {
                    border: 3px solid #4ecdc4;
                    box-shadow: 0 0 20px rgba(78, 205, 196, 0.5);
                }
                .technique-grid {
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 20px; margin: 20px 0;
                }
                .technique-card {
                    background: #f8f9ff; border: 2px solid #e0e6ff;
                    border-radius: 12px; padding: 25px; cursor: pointer;
                    transition: all 0.3s;
                }
                .technique-card:hover, .technique-card.selected {
                    border-color: #4ecdc4; background: #f0fffe;
                    transform: translateY(-2px);
                }
                .upload-zone {
                    border: 3px dashed #4ecdc4; border-radius: 15px;
                    padding: 40px; text-align: center; margin: 20px 0;
                    background: #f0fffe; transition: all 0.3s;
                }
                .upload-zone:hover { background: #e0fffe; }
                .upload-zone.dragover {
                    border-color: #44a08d; background: #d0fffc;
                }
                .btn {
                    background: #4ecdc4; color: white; padding: 15px 30px;
                    border: none; border-radius: 8px; cursor: pointer;
                    font-size: 16px; font-weight: 500; transition: all 0.3s;
                    margin: 10px 5px; display: inline-block;
                }
                .btn:hover { background: #45b7b8; transform: translateY(-2px); }
                .btn-secondary { background: #6c5ce7; }
                .btn-success { background: #00b894; }
                .validation-panel {
                    background: linear-gradient(45deg, #4ecdc4, #44a08d);
                    color: white; padding: 30px; border-radius: 15px;
                    margin: 20px 0;
                }
                .session-info {
                    position: fixed; top: 20px; right: 20px;
                    background: rgba(255,255,255,0.95); padding: 20px;
                    border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    min-width: 250px;
                }
                .hidden { display: none; }
                .form-grid {
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px; margin: 20px 0;
                }
                .form-group {
                    margin: 15px 0;
                }
                .form-group label {
                    display: block; margin-bottom: 8px; font-weight: 500;
                }
                .form-group input, .form-group select, .form-group textarea {
                    width: 100%; padding: 12px; border: 2px solid #e0e6ff;
                    border-radius: 8px; font-size: 14px;
                }
                .form-group input:focus, .form-group select:focus {
                    outline: none; border-color: #4ecdc4;
                }
                .file-item {
                    display: flex; justify-content: space-between; align-items: center;
                    padding: 8px 12px; margin: 5px 0; background: #f8f9ff;
                    border-radius: 6px; border: 1px solid #e0e6ff;
                    cursor: pointer; transition: all 0.2s;
                }
                .file-item:hover {
                    background: #f0f9ff; border-color: #4ecdc4;
                }
                .file-item.selected {
                    background: #e6f7ff; border-color: #4ecdc4;
                    box-shadow: 0 2px 4px rgba(78, 205, 196, 0.2);
                }
                .file-item-info {
                    flex: 1; display: flex; align-items: center;
                }
                .file-item-name {
                    font-weight: 500; margin-right: 10px;
                }
                .file-item-size {
                    font-size: 0.8em; color: #666;
                }
                .file-item-actions {
                    display: flex; gap: 5px;
                }
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Advanced Training Platform</h1>
                    <p>Complete Control • Any Model Type • Any Technique • Any Dataset</p>
                    
                    <div class="workflow-nav">
                        <div class="nav-step active" onclick="showStep('model-selection')">
                            🎯 Select Model
                        </div>
                        <div class="nav-step" onclick="showStep('technique-config')">
                            ⚙️ Configure Technique
                        </div>
                        <div class="nav-step" onclick="showStep('data-management')">
                            📁 Manage Data
                        </div>
                        <div class="nav-step" onclick="showStep('validation')">
                            ✅ Validate
                        </div>
                        <div class="nav-step" onclick="showStep('training')">
                            🚀 Train
                        </div>
                    </div>
                </div>

                <div class="content-panel">
                    
                    <!-- Step 1: Model Selection -->
                    <div id="model-selection">
                        <h2>🎯 Choose Model Type</h2>
                        <p>Select the type of model you want to train or retrain:</p>
                        
                        <div class="model-grid" id="model-types-container">
                            <!-- Model types loaded here -->
                        </div>

                        <div style="margin-top: 30px;">
                            <h3>🔄 Or Retrain Existing Model</h3>
                            <div class="form-group">
                                <select id="existing-models" style="width: 100%;">
                                    <option value="">Select existing model to retrain...</option>
                                </select>
                            </div>
                        </div>

                        <div style="text-align: center; margin-top: 30px;">
                            <button class="btn" onclick="showStep('technique-config')" id="next-to-technique" disabled>
                                Configure Technique →
                            </button>
                        </div>
                    </div>

                    <!-- Step 2: Technique Configuration -->
                    <div id="technique-config" class="hidden">
                        <h2>⚙️ Configure Training Technique</h2>
                        <p>Choose training approach and advanced options:</p>

                        <div class="form-grid">
                            <div class="form-group">
                                <label>Session Name</label>
                                <input type="text" id="session-name" placeholder="My Advanced Model Training">
                            </div>
                            <div class="form-group">
                                <label>Training Technique</label>
                                <select id="training-technique">
                                <option value="standard">Standard Training</option>
                                <option value="dual_class">Dual-Class (2 border types)</option>
                                <option value="prediction_ground_truth">Prediction vs Ground Truth Learning</option>
                                <option value="transfer_learning">Transfer Learning</option>
                                <option value="multi_modal">Multi-Modal Fusion</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Architecture</label>
                                <select id="architecture">
                                    <option value="yolo11">YOLO11 (Detection)</option>
                                    <option value="vit">Vision Transformer</option>
                                    <option value="cnn">Custom CNN</option>
                                    <option value="unet">U-Net (Segmentation)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Training Epochs</label>
                                <input type="number" id="epochs" value="100" min="1" max="1000">
                            </div>
                        </div>

                        <div id="technique-options">
                            <!-- Dynamic options based on selected technique -->
                        </div>

                        <div style="text-align: center; margin-top: 30px;">
                            <button class="btn btn-secondary" onclick="showStep('model-selection')">← Back</button>
                            <button class="btn" onclick="createTrainingSession()">Create Session →</button>
                        </div>
                    </div>

                    <!-- Step 3: Data Management -->
                    <div id="data-management" class="hidden">
                        <h2>📁 Manage Training Data</h2>
                        <p>Add and manage your training files with full visual control:</p>

                        <!-- Images Section -->
                        <div style="background: #f8f9ff; border-radius: 15px; padding: 25px; margin: 20px 0;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                <h3>📷 Training Images (<span id="image-count">0</span>)</h3>
                                <div>
                                    <button class="btn" onclick="document.getElementById('image-files').click()">+ Add Images</button>
                                    <button class="btn btn-secondary" onclick="removeSelectedImages()">Remove Selected</button>
                                    <button class="btn" onclick="refreshImageBrowser()">🔄 Refresh</button>
                                </div>
                            </div>
                            <input type="file" id="image-files" multiple accept="image/*" style="display: none;" onchange="handleImageUpload()">
                            
                            <div class="file-browser" id="image-browser" style="max-height: 300px; overflow-y: auto; border: 2px solid #e0e6ff; border-radius: 10px; padding: 15px;">
                                <p style="text-align: center; color: #666;">No images loaded yet - click "+ Add Images" to get started</p>
                            </div>
                        </div>

                        <!-- Labels Section -->
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 25px; margin: 20px 0;">
                            
                            <!-- Predictions -->
                            <div style="background: #f0f9ff; border-radius: 12px; padding: 25px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                    <h4>🤖 Model Predictions (<span id="predictions-count">0</span>)</h4>
                                    <div>
                                        <button class="btn" onclick="document.getElementById('predictions-files').click()">+ Add Predictions</button>
                                        <button class="btn btn-secondary" onclick="removeSelectedLabels('predictions')">Remove Selected</button>
                                    </div>
                                </div>
                                <p style="color: #666; margin-bottom: 15px;">What your model originally predicted (before corrections)</p>
                                <input type="file" id="predictions-files" multiple accept=".txt,.json" style="display: none;" onchange="handleLabelUpload('predictions')">
                                <div class="file-browser" id="predictions-browser" style="max-height: 250px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: white;">
                                    <p style="text-align: center; color: #666; font-size: 0.9em;">Upload predicted labels</p>
                                </div>
                            </div>

                            <!-- Ground Truth -->
                            <div style="background: #f0fff0; border-radius: 12px; padding: 25px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                    <h4>✅ Ground Truth (<span id="ground-truth-count">0</span>)</h4>
                                    <div>
                                        <button class="btn" onclick="document.getElementById('ground-truth-files').click()">+ Add Ground Truth</button>
                                        <button class="btn btn-secondary" onclick="removeSelectedLabels('ground_truth')">Remove Selected</button>
                                    </div>
                                </div>
                                <p style="color: #666; margin-bottom: 15px;">Your manually calibrated labels (the actual truth)</p>
                                <input type="file" id="ground-truth-files" multiple accept=".txt,.json" style="display: none;" onchange="handleLabelUpload('ground_truth')">
                                <div class="file-browser" id="ground-truth-browser" style="max-height: 250px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: white;">
                                    <p style="text-align: center; color: #666; font-size: 0.9em;">Upload ground truth labels</p>
                                </div>
                            </div>
                        </div>

                        <div style="text-align: center; margin-top: 30px;">
                            <button class="btn btn-secondary" onclick="showStep('technique-config')">← Back</button>
                            <button class="btn" onclick="showStep('validation')">Validate Data →</button>
                        </div>
                    </div>

                    <!-- Step 4: Validation -->
                    <div id="validation" class="hidden">
                        <h2>✅ Validate Training Configuration</h2>
                        <p>Review and validate your training setup:</p>

                        <div id="validation-results" class="validation-panel">
                            <h3>🔍 Configuration Validation</h3>
                            <div id="validation-content">
                                Click "Validate Session" to check your configuration
                            </div>
                        </div>

                        <div style="text-align: center; margin-top: 30px;">
                            <button class="btn btn-secondary" onclick="showStep('data-management')">← Back</button>
                            <button class="btn" onclick="validateSession()">Validate Session</button>
                            <button class="btn btn-success" onclick="showStep('training')" id="start-training-btn" disabled>
                                Start Training →
                            </button>
                        </div>
                    </div>

                    <!-- Step 5: Training -->
                    <div id="training" class="hidden">
                        <h2>🚀 Start Advanced Training</h2>
                        <div id="training-summary">
                            <!-- Training summary will be shown here -->
                        </div>

                        <div style="text-align: center; margin-top: 30px;">
                            <button class="btn btn-secondary" onclick="showStep('validation')">← Back</button>
                            <button class="btn btn-success" onclick="startTraining()" id="final-start-btn">
                                🚀 Start Advanced Training
                            </button>
                        </div>

                        <div id="training-progress" class="hidden">
                            <h3>Training in Progress...</h3>
                            <div id="progress-info"></div>
                        </div>
                    </div>

                </div>

                <!-- Session Info Panel -->
                <div class="session-info" id="session-info">
                    <h4>📋 Current Session</h4>
                    <p><strong>Model:</strong> <span id="current-model">None</span></p>
                    <p><strong>Technique:</strong> <span id="current-technique">None</span></p>
                    <p><strong>Images:</strong> <span id="current-images">0</span></p>
                    <p><strong>Labels:</strong> <span id="current-labels">0</span></p>
                    <p><strong>Status:</strong> <span id="current-status">Setup</span></p>
                </div>
            </div>

            <script>
                let selectedModelType = null;
                let currentSessionId = null;
                let sessionData = {
                    images: 0,
                    predictions: 0,
                    ground_truth: 0
                };

                async function loadModelTypes() {
                    try {
                        const response = await fetch('/api/model-types');
                        const models = await response.json();
                        
                        const container = document.getElementById('model-types-container');
                        container.innerHTML = models.map(model => `
                            <div class="model-card" onclick="selectModelType('${model.id}', '${model.name}')">
                                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                                    <div style="font-size: 2.5em; margin-right: 20px;">${model.icon}</div>
                                    <div>
                                        <h3>${model.name}</h3>
                                        <p style="opacity: 0.9; margin-top: 5px;">${model.description}</p>
                                    </div>
                                </div>
                                <div style="margin-top: 15px;">
                                    <p><strong>Techniques:</strong> ${model.techniques.join(', ')}</p>
                                    <p><strong>Formats:</strong> ${model.formats.join(', ')}</p>
                                </div>
                            </div>
                        `).join('');
                    } catch (error) {
                        console.error('Error loading model types:', error);
                    }
                }

                function selectModelType(modelId, modelName) {
                    selectedModelType = modelId;
                    
                    // Visual feedback
                    document.querySelectorAll('.model-card').forEach(card => {
                        card.classList.remove('selected');
                    });
                    event.target.closest('.model-card').classList.add('selected');
                    
                    // Update session info
                    document.getElementById('current-model').textContent = modelName;
                    document.getElementById('next-to-technique').disabled = false;
                    
                    // Load existing models for this type
                    loadExistingModels(modelId);
                }

                async function loadExistingModels(modelType) {
                    try {
                        const response = await fetch(`/api/existing-models/${modelType}`);
                        const models = await response.json();
                        
                        const select = document.getElementById('existing-models');
                        select.innerHTML = '<option value="">Select existing model to retrain...</option>';
                        
                        models.forEach(model => {
                            const option = document.createElement('option');
                            option.value = model.path;
                            option.textContent = `${model.name} (${(model.size / 1024 / 1024).toFixed(1)} MB)`;
                            select.appendChild(option);
                        });
                    } catch (error) {
                        console.error('Error loading existing models:', error);
                    }
                }

                async function createTrainingSession() {
                    const config = {
                        model_type: selectedModelType,
                        session_name: document.getElementById('session-name').value,
                        technique: document.getElementById('training-technique').value,
                        architecture: document.getElementById('architecture').value,
                        epochs: parseInt(document.getElementById('epochs').value),
                        existing_model: document.getElementById('existing-models').value
                    };

                    try {
                        const response = await fetch('/api/training-session/create', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(config)
                        });

                        const result = await response.json();
                        currentSessionId = result.session_id;
                        
                        document.getElementById('current-technique').textContent = config.technique;
                        document.getElementById('current-status').textContent = 'Session Created';
                        
                        showStep('data-management');
                        
                        // Initialize file browsers
                        setTimeout(() => {
                            refreshImageBrowser();
                            refreshLabelBrowser('predictions');
                            refreshLabelBrowser('ground_truth');
                        }, 100);

                    } catch (error) {
                        alert(`Error creating session: ${error.message}`);
                    }
                }

                async function handleImageUpload() {
                    const files = document.getElementById('image-files').files;
                    if (!files.length || !currentSessionId) return;

                    const formData = new FormData();
                    formData.append('source_type', 'upload');
                    
                    for (let file of files) {
                        formData.append('files', file);
                    }

                    try {
                        const response = await fetch(`/api/training-session/${currentSessionId}/add-images`, {
                            method: 'POST',
                            body: formData
                        });

                        const result = await response.json();
                        
                        // Refresh image browser
                        await refreshImageBrowser();
                        
                        // Visual feedback
                        document.getElementById('current-status').textContent = 'Files Added';
                        
                        // Show success message
                        showUploadSuccess(`✅ Added ${result.added_files} images`);

                    } catch (error) {
                        showUploadError(`Error uploading images: ${error.message}`);
                    }
                }

                async function refreshImageBrowser() {
                    if (!currentSessionId) return;

                    try {
                        const response = await fetch(`/api/training-session/${currentSessionId}/files?file_type=images`);
                        const result = await response.json();
                        
                        const browser = document.getElementById('image-browser');
                        const countElement = document.getElementById('image-count');
                        
                        countElement.textContent = result.count;
                        document.getElementById('current-images').textContent = result.count;
                        sessionData.images = result.count;
                        
                        if (result.files.length === 0) {
                            browser.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">No images uploaded yet - click "+ Add Images" to get started</p>';
                        } else {
                            browser.innerHTML = `
                                <div style="background: #e6f7ff; border: 1px solid #4ecdc4; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                                    <strong>✅ ${result.files.length} images loaded and ready for training!</strong>
                                </div>
                                ${result.files.map((file, index) => `
                                    <div class="file-item" onclick="toggleFileSelection(this, '${file.path}')" style="border-left: 4px solid #4ecdc4;">
                                        <div class="file-item-info">
                                            <div class="file-item-name">📷 ${index + 1}. ${file.name}</div>
                                            <div class="file-item-size">${(file.size / 1024).toFixed(1)} KB • Ready</div>
                                        </div>
                                        <div class="file-item-actions">
                                            <button onclick="deleteFile(event, '${file.path}')" style="background: #ff6b6b; color: white; border: none; padding: 6px 10px; border-radius: 4px; font-size: 0.8em; font-weight: bold;">×</button>
                                        </div>
                                    </div>
                                `).join('')}
                            `;
                        }
                    } catch (error) {
                        console.error('Error refreshing image browser:', error);
                    }
                }

                async function refreshLabelBrowser(labelType) {
                    if (!currentSessionId) return;

                    console.log(`Refreshing ${labelType} browser...`);

                    try {
                        const response = await fetch(`/api/training-session/${currentSessionId}/files?file_type=labels_${labelType}`);
                        const result = await response.json();
                        
                        console.log(`${labelType} refresh result:`, result);
                        
                        const browser = document.getElementById(`${labelType}-browser`);
                        const countElement = document.getElementById(`${labelType}-count`);
                        
                        countElement.textContent = result.count;
                        sessionData[labelType] = result.count;
                        updateLabelsCount();
                        
                        if (result.files.length === 0) {
                            browser.innerHTML = `<p style="text-align: center; color: #666; font-size: 0.9em; padding: 15px;">No ${labelType} uploaded yet</p>`;
                        } else {
                            const labelIcon = labelType === 'predictions' ? '🤖' : '✅';
                            const labelColor = labelType === 'predictions' ? '#3498db' : '#00b894';
                            browser.innerHTML = `
                                <div style="background: ${labelType === 'predictions' ? '#e3f2fd' : '#e8f5e8'}; border: 1px solid ${labelColor}; border-radius: 6px; padding: 10px; margin-bottom: 10px; font-size: 0.9em;">
                                    <strong>${labelIcon} ${result.files.length} ${labelType} files ready</strong>
                                </div>
                                ${result.files.map((file, index) => `
                                    <div class="file-item" onclick="toggleFileSelection(this, '${file.path}')" style="border-left: 3px solid ${labelColor};">
                                        <div class="file-item-info">
                                            <div class="file-item-name">${labelIcon} ${index + 1}. ${file.name}</div>
                                            <div class="file-item-size">${(file.size / 1024).toFixed(1)} KB • ${labelType}</div>
                                        </div>
                                        <div class="file-item-actions">
                                            <button onclick="deleteFile(event, '${file.path}')" style="background: #ff6b6b; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">×</button>
                                        </div>
                                    </div>
                                `).join('')}
                            `;
                        }
                    } catch (error) {
                        console.error(`Error refreshing ${labelType} browser:`, error);
                    }
                }

                function toggleFileSelection(element, filePath) {
                    element.classList.toggle('selected');
                }

                async function deleteFile(event, filePath) {
                    event.stopPropagation();
                    
                    if (!confirm('Delete this file?')) return;

                    try {
                        const response = await fetch(`/api/training-session/${currentSessionId}/file?file_path=${encodeURIComponent(filePath)}`, {
                            method: 'DELETE'
                        });

                        if (response.ok) {
                            // Refresh appropriate browser
                            if (filePath.includes('/images/')) {
                                await refreshImageBrowser();
                            } else {
                                const labelType = filePath.includes('/predictions/') ? 'predictions' : 
                                                 filePath.includes('/corrections/') ? 'corrections' : 'ground_truth';
                                await refreshLabelBrowser(labelType);
                            }
                        }
                    } catch (error) {
                        alert(`Error deleting file: ${error.message}`);
                    }
                }

                function removeSelectedImages() {
                    const selected = document.querySelectorAll('#image-browser .file-item.selected');
                    if (selected.length === 0) {
                        alert('Please select images to remove');
                        return;
                    }
                    
                    if (confirm(`Remove ${selected.length} selected images?`)) {
                        selected.forEach(item => {
                            const filePath = item.getAttribute('onclick').match(/'([^']+)'/)[1];
                            deleteFile({stopPropagation: () => {}}, filePath);
                        });
                    }
                }

                function removeSelectedLabels(labelType) {
                    const selected = document.querySelectorAll(`#${labelType}-browser .file-item.selected`);
                    if (selected.length === 0) {
                        alert(`Please select ${labelType} to remove`);
                        return;
                    }
                    
                    if (confirm(`Remove ${selected.length} selected ${labelType}?`)) {
                        selected.forEach(item => {
                            const filePath = item.getAttribute('onclick').match(/'([^']+)'/)[1];
                            deleteFile({stopPropagation: () => {}}, filePath);
                        });
                    }
                }

                async function handleLabelUpload(labelType) {
                    const fileId = labelType + '-files';
                    const files = document.getElementById(fileId).files;
                    if (!files.length || !currentSessionId) return;

                    console.log(`Uploading ${files.length} files for ${labelType}`);

                    const formData = new FormData();
                    formData.append('label_type', labelType);
                    formData.append('label_format', 'auto_detect');
                    
                    for (let file of files) {
                        formData.append('files', file);
                    }

                    try {
                        const response = await fetch(`/api/training-session/${currentSessionId}/add-labels`, {
                            method: 'POST',
                            body: formData
                        });

                        const result = await response.json();
                        console.log('Upload result:', result);
                        
                        // Refresh label browser
                        await refreshLabelBrowser(labelType);
                        
                        alert(`✅ Added ${result.added_labels} ${labelType} labels`);

                    } catch (error) {
                        console.error('Upload error:', error);
                        alert(`Error uploading labels: ${error.message}`);
                    }
                }

                function updateLabelsCount() {
                    const total = sessionData.predictions + sessionData.ground_truth;
                    document.getElementById('current-labels').textContent = total;
                }

                async function validateSession() {
                    if (!currentSessionId) {
                        alert('No active session');
                        return;
                    }

                    try {
                        const response = await fetch(`/api/training-session/${currentSessionId}/validate`, {
                            method: 'POST'
                        });

                        const validation = await response.json();
                        
                        const content = document.getElementById('validation-content');
                        content.innerHTML = `
                            <div style="margin-bottom: 20px;">
                                <h4>📊 Session Summary</h4>
                                <p><strong>Model Type:</strong> ${validation.summary.model_type}</p>
                                <p><strong>Technique:</strong> ${validation.summary.technique}</p>
                                <p><strong>Images:</strong> ${validation.summary.images}</p>
                                <p><strong>Predictions:</strong> ${validation.summary.predictions}</p>
                                <p><strong>Corrections:</strong> ${validation.summary.corrections}</p>
                            </div>

                            ${validation.issues.length > 0 ? `
                                <div style="background: rgba(255,107,107,0.2); padding: 15px; border-radius: 8px; margin: 10px 0;">
                                    <strong>❌ Issues:</strong><br>
                                    ${validation.issues.map(issue => `• ${issue}`).join('<br>')}
                                </div>
                            ` : ''}

                            ${validation.warnings.length > 0 ? `
                                <div style="background: rgba(255,193,7,0.2); padding: 15px; border-radius: 8px; margin: 10px 0;">
                                    <strong>⚠️ Warnings:</strong><br>
                                    ${validation.warnings.map(warning => `• ${warning}`).join('<br>')}
                                </div>
                            ` : ''}

                            <div style="margin-top: 20px; font-size: 1.2em;">
                                <strong>Status: ${validation.ready ? '✅ Ready for Training' : '❌ Not Ready'}</strong>
                            </div>
                        `;

                        document.getElementById('start-training-btn').disabled = !validation.ready;
                        document.getElementById('current-status').textContent = validation.ready ? 'Validated' : 'Issues Found';

                    } catch (error) {
                        alert(`Validation error: ${error.message}`);
                    }
                }

                async function startTraining() {
                    if (!currentSessionId) {
                        alert('No active session');
                        return;
                    }

                    if (!confirm('🚀 Start Advanced Training?\\n\\nThis will begin training with your configuration.')) {
                        return;
                    }

                    try {
                        const response = await fetch(`/api/training-session/${currentSessionId}/start`, {
                            method: 'POST'
                        });

                        const result = await response.json();
                        
                        document.getElementById('final-start-btn').style.display = 'none';
                        document.getElementById('training-progress').classList.remove('hidden');
                        document.getElementById('progress-info').innerHTML = `
                            <p>🚀 Training started: ${result.training_id}</p>
                            <p>Session: ${result.session_id}</p>
                            <p>${result.message}</p>
                        `;
                        
                        document.getElementById('current-status').textContent = 'Training';

                    } catch (error) {
                        alert(`Training error: ${error.message}`);
                    }
                }

                function showStep(stepId) {
                    // Hide all steps
                    ['model-selection', 'technique-config', 'data-management', 'validation', 'training'].forEach(id => {
                        document.getElementById(id).classList.add('hidden');
                    });
                    
                    // Remove active class from nav
                    document.querySelectorAll('.nav-step').forEach(step => {
                        step.classList.remove('active');
                    });
                    
                    // Show current step
                    document.getElementById(stepId).classList.remove('hidden');
                    
                    // Find and activate the correct nav step
                    const navSteps = document.querySelectorAll('.nav-step');
                    const stepIndex = ['model-selection', 'technique-config', 'data-management', 'validation', 'training'].indexOf(stepId);
                    if (stepIndex >= 0 && navSteps[stepIndex]) {
                        navSteps[stepIndex].classList.add('active');
                    }
                }

                function showUploadSuccess(message) {
                    const toast = document.createElement('div');
                    toast.style.cssText = `
                        position: fixed; top: 20px; right: 20px; z-index: 9999;
                        background: linear-gradient(45deg, #00b894, #00cec9);
                        color: white; padding: 15px 25px; border-radius: 12px;
                        box-shadow: 0 10px 30px rgba(0,184,148,0.3);
                        font-weight: 500; animation: slideIn 0.3s ease;
                    `;
                    toast.innerHTML = `<div style="display: flex; align-items: center;"><span style="margin-right: 10px;">✅</span>${message}</div>`;
                    document.body.appendChild(toast);
                    setTimeout(() => {
                        toast.style.animation = 'slideOut 0.3s ease forwards';
                        setTimeout(() => document.body.removeChild(toast), 300);
                    }, 3000);
                }

                function showUploadError(message) {
                    const toast = document.createElement('div');
                    toast.style.cssText = `
                        position: fixed; top: 20px; right: 20px; z-index: 9999;
                        background: linear-gradient(45deg, #e74c3c, #c0392b);
                        color: white; padding: 15px 25px; border-radius: 12px;
                        box-shadow: 0 10px 30px rgba(231,76,60,0.3);
                        font-weight: 500; animation: slideIn 0.3s ease;
                    `;
                    toast.innerHTML = `<div style="display: flex; align-items: center;"><span style="margin-right: 10px;">❌</span>${message}</div>`;
                    document.body.appendChild(toast);
                    setTimeout(() => {
                        toast.style.animation = 'slideOut 0.3s ease forwards';
                        setTimeout(() => document.body.removeChild(toast), 300);
                    }, 4000);
                }

                // Initialize
                loadModelTypes();
            </script>
        </body>
        </html>
        '''

# Main entry point
async def main():
    """Start the advanced training platform"""

    platform = AdvancedTrainingPlatform()

    import uvicorn
    config = uvicorn.Config(
        platform.app,
        host="0.0.0.0",
        port=8006,
        log_level="info"
    )
    server = uvicorn.Server(config)

    print("🚀 Advanced Training Platform")
    print("=" * 50)
    print("🎯 Any Model Type: Border/Corner/Edge/Surface/Photometric")
    print("⚙️ Any Technique: Standard/Dual-Class/Prediction-Correction/Multi-Modal")
    print("📁 Any Data Source: Upload/Existing/Copy/Era-Agnostic")
    print("🔄 Retrain Existing Models")
    print("✅ Complete Validation")
    print("🔗 Interface: http://localhost:8006")
    print("=" * 50)

    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
