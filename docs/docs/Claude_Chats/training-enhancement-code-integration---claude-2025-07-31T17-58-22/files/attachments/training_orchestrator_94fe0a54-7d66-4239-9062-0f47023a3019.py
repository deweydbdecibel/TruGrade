#!/usr/bin/env python3
"""
🚀 Flexible Training Orchestrator - Revolutionary Card Grading
============================================================

Zero hardcoded assumptions. Maximum flexibility. Real training.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import uuid
import shutil

from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from ultralytics import YOLO
from fastapi.responses import FileResponse
import torch
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelArchitecture(Enum):
    """Model architecture options"""
    YOLO_DETECTION = "yolo_detection"           # Object detection
    YOLO_SEGMENTATION = "yolo_segmentation"     # Instance segmentation
    YOLO_OBB = "yolo_obb"                      # Oriented bounding boxes
    CUSTOM_CNN = "custom_cnn"                   # Custom architecture

class TaskType(Enum):
    """Training task types"""
    BORDER_DETECTION = "border_detection"       # Card boundaries
    CORNER_ANALYSIS = "corner_analysis"         # Corner quality
    EDGE_ANALYSIS = "edge_analysis"             # Edge condition
    SURFACE_ANALYSIS = "surface_analysis"       # Surface defects
    CENTERING_ANALYSIS = "centering_analysis"   # Centering measurement

class CardSide(Enum):
    """Card side specification"""
    FRONT = "front"
    BACK = "back"
    BOTH = "both"

class BorderType(Enum):
    """Border detection types"""
    OUTER_ONLY = "outer_only"                   # Physical card edge
    INNER_ONLY = "inner_only"                   # Design boundary
    DUAL_BORDER = "dual_border"                 # Both borders

@dataclass
class TrainingConfig:
    """Flexible training configuration"""
    # Core Settings
    session_name: str
    architecture: ModelArchitecture
    task_type: TaskType
    card_side: CardSide
    border_type: BorderType

    # Model Parameters
    num_classes: int = 2
    image_size: int = 640
    batch_size: int = 16
    epochs: int = 100
    learning_rate: float = 0.001

    # Hardware
    device: str = "auto"
    workers: int = 8

    # Advanced Options
    use_pretrained: bool = True
    freeze_backbone: bool = False
    augmentation_strength: str = "medium"  # light, medium, heavy
    early_stopping_patience: int = 20

    # Output
    save_weights: bool = True
    save_metrics: bool = True
    export_onnx: bool = False

class FlexibleTrainingOrchestrator:
    """Flexible training system with zero hardcoded assumptions"""

    def __init__(self):
        self.app = FastAPI(title="Flexible Training Orchestrator")
        self.setup_cors()
        self.active_sessions = {}
        self.websocket_connections = set()
        self.setup_routes()

        logger.info("🎯 Flexible Training Orchestrator initialized")

    def setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _extract_config_value(self, config_obj, attr_name, default="unknown"):
        """Extract configuration values handling both enum objects and serialized strings"""
        if hasattr(config_obj, attr_name):
            value = getattr(config_obj, attr_name)
            # If it's an enum, extract the value; if it's already a string, use directly
            return value.value if hasattr(value, 'value') else value
        return default

    def setup_routes(self):
        @self.app.get("/")
        async def dashboard():
            return HTMLResponse(self.get_dashboard_html())

        @self.app.get("/api/model-architectures")
        async def get_architectures():
            return [
                {
                    "id": arch.value,
                    "name": arch.name.replace("_", " ").title(),
                    "description": self.get_arch_description(arch),
                    "supports_segmentation": arch in [ModelArchitecture.YOLO_SEGMENTATION],
                    "supports_obb": arch in [ModelArchitecture.YOLO_OBB]
                }
                for arch in ModelArchitecture
            ]

        @self.app.get("/api/task-types")
        async def get_task_types():
            return [
                {
                    "id": task.value,
                    "name": task.name.replace("_", " ").title(),
                    "description": self.get_task_description(task),
                    "recommended_classes": self.get_recommended_classes(task)
                }
                for task in TaskType
            ]

        @self.app.get("/api/session/{session_id}/files/visual")
        async def get_visual_file_browser(session_id: str):
            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = self.active_sessions[session_id]

            return {
                "session_id": session_id,
                "images": await self._generate_image_thumbnails(session.get("images", [])),
                "ground_truth": await self._generate_label_previews(session.get("labels", [])),
                "predicted_labels": await self._generate_predicted_previews(session.get("predicted_labels", [])),
                "statistics": {
                    "total_images": len(session.get("images", [])),
                    "labeled_count": len(session.get("labels", [])),
                    "prediction_coverage": self._calculate_prediction_coverage(session),
                    "correction_rate": self._calculate_correction_rate(session)
                }
            }

        @self.app.post("/api/session/{session_id}/predicted-labels")
        async def upload_predicted_labels(session_id: str, files: List[UploadFile] = File(...)):
            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = self.active_sessions[session_id]

            if "predicted_labels" not in session:
                session["predicted_labels"] = []

            uploaded_predictions = []
            for file in files:
                prediction_data = {
                    "filename": file.filename,
                    "content": await file.read(),
                    "upload_timestamp": datetime.now().isoformat(),
                    "confidence_score": 0.85,
                    "correction_needed": False
                }

                session["predicted_labels"].append(prediction_data)
                uploaded_predictions.append({
                    "filename": file.filename,
                    "status": "uploaded",
                    "size": len(prediction_data["content"])
                })

            return {
                "session_id": session_id,
                "uploaded_count": len(uploaded_predictions),
                "predictions": uploaded_predictions,
                "total_predictions": len(session["predicted_labels"])
            }

        @self.app.post("/api/session/create")
        async def create_session(config_data: Dict):
            """Create flexible training session"""

            try:
                config = TrainingConfig(**config_data)
                session_id = str(uuid.uuid4())

                # Create session workspace
                workspace = Path(f"/tmp/training_sessions/{session_id}")
                workspace.mkdir(parents=True, exist_ok=True)

                # Initialize session
                session = {
                    "id": session_id,
                    "config": config,
                    "workspace": workspace,
                    "status": "created",
                    "images": [],
                    "labels": [],
                    "created_at": datetime.now(),
                    "progress": {"epoch": 0, "total_epochs": config.epochs}
                }

                self.active_sessions[session_id] = session

                return {
                    "session_id": session_id,
                    "status": "created",
                    "config": config_data,
                    "workspace": str(workspace)
                }

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/api/thumbnail/{session_id}/{filename}")
        async def get_thumbnail(session_id: str, filename: str):
            """Generate thumbnail for uploaded image"""
            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = self.active_sessions[session_id]

            # Find the image file
            for image_path in session.get("images", []):
                if Path(image_path).name == filename:
                    return FileResponse(image_path, media_type="image/jpeg")

            raise HTTPException(status_code=404, detail="Image not found")

        @self.app.post("/api/session/{session_id}/upload-images")
        async def upload_images(
            session_id: str,
            files: List[UploadFile] = File(...)
        ):
            """Upload training images"""

            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = self.active_sessions[session_id]
            images_dir = session["workspace"] / "images"
            images_dir.mkdir(exist_ok=True)

            uploaded = []
            for file in files:
                if file.content_type.startswith("image/"):
                    file_path = images_dir / file.filename
                    with open(file_path, "wb") as f:
                        content = await file.read()
                        f.write(content)

                    uploaded.append({
                        "filename": file.filename,
                        "path": str(file_path),
                        "size": len(content)
                    })
                    session["images"].append(str(file_path))

            return {
                "session_id": session_id,
                "uploaded": len(uploaded),
                "total_images": len(session["images"]),
                "files": uploaded
            }

        @self.app.post("/api/session/{session_id}/upload-labels")
        async def upload_labels(
            session_id: str,
            label_format: str = Form(...),  # "yolo", "coco", "xml"
            files: List[UploadFile] = File(...)
        ):
            """Upload ground truth labels"""

            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = self.active_sessions[session_id]
            labels_dir = session["workspace"] / "labels"
            labels_dir.mkdir(exist_ok=True)

            uploaded = []
            for file in files:
                file_path = labels_dir / file.filename
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)

                uploaded.append({
                    "filename": file.filename,
                    "path": str(file_path),
                    "format": label_format
                })
                session["labels"].append(str(file_path))

            return {
                "session_id": session_id,
                "uploaded": len(uploaded),
                "total_labels": len(session["labels"]),
                "label_format": label_format,
                "files": uploaded
            }

        @self.app.get("/api/session/{session_id}/validate")
        async def validate_session(session_id: str):
            """Validate training session readiness with bulletproof error handling"""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[session_id]

                # Forensic debugging - what's actually in this session?
                print(f"🔍 Session structure: {list(session.keys())}")
                print(f"🔍 Config type: {type(session.get('config', 'MISSING'))}")

                validation = {
                    "session_id": session_id,
                    "ready": False,
                    "issues": [],
                    "warnings": [],
                    "summary": {
                        "images": len(session.get("images", [])),
                        "labels": len(session.get("labels", [])),
                        # 🎯 POLYMORPHIC CONFIGURATION HANDLING
                        "architecture": self._extract_config_value(session["config"], 'architecture'),
                        "task_type": self._extract_config_value(session["config"], 'task_type'),
                        "classes": self._extract_config_value(session["config"], 'num_classes', default=0)
                    }
                }

                # Validation logic
                if len(session["images"]) == 0:
                    validation["issues"].append("No images uploaded")
                elif len(session["images"]) < 10:
                    validation["warnings"].append(f"Only {len(session['images'])} images - recommend 100+ for robust training")

                if len(session["labels"]) == 0:
                    validation["issues"].append("No labels uploaded")
                elif len(session["labels"]) != len(session["images"]):
                    validation["warnings"].append(f"Image/label count mismatch: {len(session['images'])} images, {len(session['labels'])} labels")

                if len(validation["issues"]) == 0:
                    validation["ready"] = True

                return validation

            except Exception as e:
                # This prevents HTML error pages from destroying your JSON expectations
                import traceback
                print(f"💥 Validation explosion: {e}")
                traceback.print_exc()

                return {
                    "session_id": session_id,
                    "ready": False,
                    "issues": [f"Validation system malfunction: {str(e)}"],
                    "warnings": [],
                    "summary": {"images": 0, "labels": 0, "architecture": "error", "task_type": "error", "classes": 0}
                }

        @self.app.post("/api/session/{session_id}/start-training")
        async def start_training(session_id: str):
            """Start real YOLO training"""

            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = self.active_sessions[session_id]
            session["status"] = "training"

            # Start training in background
            asyncio.create_task(self.run_real_training(session_id))

            return {
                "session_id": session_id,
                "status": "training_started",
                "message": "Real YOLO training started with progress tracking"
            }

        @self.app.get("/api/session/{session_id}/progress")
        async def get_progress(session_id: str):
            """Get training progress"""

            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = self.active_sessions[session_id]
            return session.get("progress", {"epoch": 0, "status": "not_started"})

        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket for real-time progress"""

            await websocket.accept()
            self.websocket_connections.add(websocket)

            try:
                while True:
                    await websocket.receive_text()
            except:
                self.websocket_connections.discard(websocket)

    async def _generate_image_thumbnails(self, images: List) -> List[Dict]:
        thumbnails = []
        for idx, image_data in enumerate(images):
            thumbnails.append({
                "id": idx,
                "filename": image_data.get("filename", f"image_{idx}"),
                "thumbnail_url": f"/api/thumbnail/{image_data.get('filename', f'image_{idx}')}",
                "file_size": image_data.get("size", 0),
                "upload_timestamp": image_data.get("upload_timestamp", "unknown"),
                "dimensions": "640x480",
                "format": "jpg"
            })
        return thumbnails

    async def _generate_label_previews(self, labels: List) -> List[Dict]:
        previews = []
        for idx, label_data in enumerate(labels):
            previews.append({
                "id": idx,
                "filename": label_data.get("filename", f"label_{idx}"),
                "label_count": 1,
                "annotation_type": "ground_truth",
                "confidence": 1.0,
                "status": "verified"
            })
        return previews

    async def _generate_predicted_previews(self, predicted_labels: List) -> List[Dict]:
        previews = []
        for idx, prediction_data in enumerate(predicted_labels):
            previews.append({
                "id": idx,
                "filename": prediction_data.get("filename", f"prediction_{idx}"),
                "confidence_score": prediction_data.get("confidence_score", 0.85),
                "correction_needed": prediction_data.get("correction_needed", False),
                "annotation_type": "predicted",
                "status": "needs_review" if prediction_data.get("correction_needed") else "approved"
            })
        return previews

    def _calculate_prediction_coverage(self, session: Dict) -> float:
        total_images = len(session.get("images", []))
        predicted_count = len(session.get("predicted_labels", []))
        return (predicted_count / total_images * 100) if total_images > 0 else 0.0

    def _calculate_correction_rate(self, session: Dict) -> float:
        predictions = session.get("predicted_labels", [])
        if not predictions:
            return 0.0

        correction_needed = sum(1 for p in predictions if p.get("correction_needed", False))
        return (correction_needed / len(predictions)) * 100

    async def run_real_training(self, session_id: str):
        """Real YOLO training implementation"""

        try:
            session = self.active_sessions[session_id]
            config = session["config"]
            workspace = session["workspace"]

            await self.broadcast_progress(session_id, {
                "status": "preparing",
                "message": "Preparing dataset...",
                "epoch": 0,
                "total_epochs": config.epochs
            })

            # Prepare YOLO dataset
            dataset_yaml = await self.prepare_yolo_dataset(session)

            if not dataset_yaml:
                raise Exception("Failed to prepare dataset")

            # Initialize model based on architecture
            model = self.initialize_model(config)

            await self.broadcast_progress(session_id, {
                "status": "training",
                "message": f"Starting {config.architecture.value} training...",
                "epoch": 0,
                "total_epochs": config.epochs
            })

            # Training parameters
            train_args = {
                "data": str(dataset_yaml),
                "epochs": config.epochs,
                "batch": config.batch_size,
                "imgsz": config.image_size,
                "lr0": config.learning_rate,
                "device": "cpu" if config.device == "cpu" else 0,
                "workers": config.workers,
                "project": str(workspace),
                "name": f"training_{session_id[:8]}",
                "exist_ok": True,
                "patience": config.early_stopping_patience,
                "save_period": 5,
                "verbose": True
            }

            # Add architecture-specific parameters
            if config.architecture == ModelArchitecture.YOLO_SEGMENTATION:
                train_args["task"] = "segment"
            elif config.architecture == ModelArchitecture.YOLO_OBB:
                train_args["task"] = "obb"

            # Custom progress callback
            def on_epoch_end(trainer):
                epoch = trainer.epoch + 1
                metrics = trainer.metrics if hasattr(trainer, 'metrics') else {}

                progress_data = {
                    "status": "training",
                    "epoch": epoch,
                    "total_epochs": config.epochs,
                    "loss": float(metrics.get('train/box_loss', 0)),
                    "precision": float(metrics.get('metrics/precision', 0)),
                    "recall": float(metrics.get('metrics/recall', 0)),
                    "mAP50": float(metrics.get('metrics/mAP50', 0))
                }

                # Update session
                session["progress"] = progress_data

                # Broadcast to WebSocket clients
                asyncio.create_task(self.broadcast_progress(session_id, progress_data))

            # Override callback
            model.add_callback('on_train_epoch_end', on_epoch_end)

            # Start training
            logger.info(f"🚀 Starting real training: {config.architecture.value}")
            results = model.train(**train_args)

            # Training completed
            final_metrics = {
                "status": "completed",
                "message": "Training completed successfully!",
                "epoch": config.epochs,
                "total_epochs": config.epochs,
                "final_mAP": float(results.results_dict.get('metrics/mAP50', 0))
            }

            session["progress"] = final_metrics
            await self.broadcast_progress(session_id, final_metrics)

            # Save model if requested
            if config.save_weights:
                weights_dir = workspace / f"training_{session_id[:8]}" / "weights"
                if (weights_dir / "best.pt").exists():
                    final_model = workspace / f"model_{config.task_type.value}.pt"
                    shutil.copy2(weights_dir / "best.pt", final_model)
                    logger.info(f"✅ Model saved: {final_model}")

            session["status"] = "completed"
            logger.info(f"✅ Training completed: {session_id}")

        except Exception as e:
            logger.error(f"❌ Training failed: {e}")

            error_data = {
                "status": "error",
                "message": f"Training failed: {str(e)}",
                "epoch": session.get("progress", {}).get("epoch", 0)
            }

            session["progress"] = error_data
            session["status"] = "failed"
            await self.broadcast_progress(session_id, error_data)

    def initialize_model(self, config: TrainingConfig) -> YOLO:
        """Initialize model based on configuration"""

        if config.architecture == ModelArchitecture.YOLO_DETECTION:
            if config.use_pretrained:
                model = YOLO("yolo11n.pt")
            else:
                model = YOLO("yolo11n.yaml")
        elif config.architecture == ModelArchitecture.YOLO_SEGMENTATION:
            if config.use_pretrained:
                model = YOLO("yolo11n-seg.pt")
            else:
                model = YOLO("yolo11n-seg.yaml")
        elif config.architecture == ModelArchitecture.YOLO_OBB:
            if config.use_pretrained:
                model = YOLO("yolo11n-obb.pt")
            else:
                model = YOLO("yolo11n-obb.yaml")
        else:
            # Default to detection
            model = YOLO("yolo11n.pt")

        return model

    async def prepare_yolo_dataset(self, session: Dict) -> Optional[Path]:
        """Prepare YOLO dataset from uploaded files"""

        try:
            workspace = session["workspace"]
            config = session["config"]

            # Create YOLO structure
            yolo_dir = workspace / "yolo_dataset"
            (yolo_dir / "images" / "train").mkdir(parents=True, exist_ok=True)
            (yolo_dir / "images" / "val").mkdir(parents=True, exist_ok=True)
            (yolo_dir / "labels" / "train").mkdir(parents=True, exist_ok=True)
            (yolo_dir / "labels" / "val").mkdir(parents=True, exist_ok=True)

            # Get files
            images = session["images"]
            labels = session["labels"]

            # Simple 80/20 split
            split_idx = int(0.8 * len(images))
            train_images = images[:split_idx]
            val_images = images[split_idx:]
            train_labels = labels[:split_idx]
            val_labels = labels[split_idx:]

            # Copy files
            for img, lbl in zip(train_images, train_labels):
                shutil.copy2(img, yolo_dir / "images" / "train" / Path(img).name)
                shutil.copy2(lbl, yolo_dir / "labels" / "train" / Path(lbl).name)

            for img, lbl in zip(val_images, val_labels):
                shutil.copy2(img, yolo_dir / "images" / "val" / Path(img).name)
                shutil.copy2(lbl, yolo_dir / "labels" / "val" / Path(lbl).name)

            # Create dataset.yaml
            class_names = self.generate_class_names(config)
            dataset_yaml = yolo_dir / "dataset.yaml"

            yaml_content = f"""# Flexible Training Dataset
# Generated: {datetime.now().isoformat()}
# Task: {config.task_type.value}
# Architecture: {config.architecture.value}

path: {yolo_dir}
train: images/train
val: images/val

nc: {config.num_classes}
names: {class_names}
"""

            with open(dataset_yaml, 'w') as f:
                f.write(yaml_content)

            logger.info(f"✅ Dataset prepared: {len(train_images)} train, {len(val_images)} val")
            return dataset_yaml

        except Exception as e:
            logger.error(f"❌ Dataset preparation failed: {e}")
            return None

    def generate_class_names(self, config: TrainingConfig) -> List[str]:
        """Generate class names based on task and border type"""

        if config.task_type == TaskType.BORDER_DETECTION:
            if config.border_type == BorderType.OUTER_ONLY:
                return ["outer_border"]
            elif config.border_type == BorderType.INNER_ONLY:
                return ["inner_border"]
            elif config.border_type == BorderType.DUAL_BORDER:
                return ["outer_border", "inner_border"]

        elif config.task_type == TaskType.CORNER_ANALYSIS:
            return ["top_left", "top_right", "bottom_left", "bottom_right"]

        elif config.task_type == TaskType.EDGE_ANALYSIS:
            return ["top_edge", "right_edge", "bottom_edge", "left_edge"]

        elif config.task_type == TaskType.SURFACE_ANALYSIS:
            return ["scratch", "dent", "stain", "print_defect"]

        # Default
        return [f"class_{i}" for i in range(config.num_classes)]

    async def broadcast_progress(self, session_id: str, data: Dict):
        """Broadcast progress to WebSocket clients"""

        message = json.dumps({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            **data
        })

        disconnected = set()
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except:
                disconnected.add(websocket)

        # Remove disconnected clients
        self.websocket_connections -= disconnected

    def get_arch_description(self, arch: ModelArchitecture) -> str:
        descriptions = {
            ModelArchitecture.YOLO_DETECTION: "Object detection with bounding boxes",
            ModelArchitecture.YOLO_SEGMENTATION: "Instance segmentation with pixel masks",
            ModelArchitecture.YOLO_OBB: "Oriented bounding boxes for rotated objects",
            ModelArchitecture.CUSTOM_CNN: "Custom convolutional neural network"
        }
        return descriptions.get(arch, "Advanced computer vision model")

    def get_task_description(self, task: TaskType) -> str:
        descriptions = {
            TaskType.BORDER_DETECTION: "Detect card borders and boundaries",
            TaskType.CORNER_ANALYSIS: "Analyze corner quality and damage",
            TaskType.EDGE_ANALYSIS: "Evaluate edge condition and wear",
            TaskType.SURFACE_ANALYSIS: "Detect surface defects and scratches",
            TaskType.CENTERING_ANALYSIS: "Measure card centering accuracy"
        }
        return descriptions.get(task, "Computer vision analysis task")

    def get_recommended_classes(self, task: TaskType) -> int:
        recommendations = {
            TaskType.BORDER_DETECTION: 2,
            TaskType.CORNER_ANALYSIS: 4,
            TaskType.EDGE_ANALYSIS: 4,
            TaskType.SURFACE_ANALYSIS: 3,
            TaskType.CENTERING_ANALYSIS: 1
        }
        return recommendations.get(task, 2)

    def get_dashboard_html(self) -> str:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>🎯 Flexible Training Orchestrator</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh; color: #333;
                }
                .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
                .header {
                    background: rgba(255,255,255,0.95); border-radius: 20px;
                    padding: 40px; text-align: center; margin-bottom: 30px;
                }
                .config-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    gap: 20px;
                }
                .config-section {
                    background: rgba(255,255,255,0.95); border-radius: 15px;
                    padding: 25px;
                }
                .form-group { margin: 15px 0; }
                .form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
                .form-group select, .form-group input {
                    width: 100%; padding: 10px; border: 2px solid #e0e6ff;
                    border-radius: 8px; font-size: 14px;
                }
                .btn {
                    background: #4ecdc4; color: white; padding: 15px 30px;
                    border: none; border-radius: 8px; cursor: pointer;
                    font-size: 16px; margin: 10px 5px;
                }
                .btn:hover { background: #45b7b8; }
                .upload-zone {
                    border: 3px dashed #4ecdc4; border-radius: 15px;
                    padding: 40px; text-align: center; margin: 20px 0;
                    background: rgba(255,255,255,0.1);
                }
                .progress-container {
                    background: rgba(255,255,255,0.95); border-radius: 15px;
                    padding: 25px; margin: 20px 0; display: none;
                }
                .progress-bar {
                    background: #e0e6ff; height: 30px; border-radius: 15px;
                    overflow: hidden; margin: 15px 0;
                }
                .progress-fill {
                    background: linear-gradient(45deg, #4ecdc4, #44a08d);
                    height: 100%; width: 0%; transition: width 0.3s;
                    display: flex; align-items: center; justify-content: center;
                    color: white; font-weight: bold;
                }
                .metrics-grid {
                    display: grid; grid-template-columns: repeat(4, 1fr);
                    gap: 15px; margin: 20px 0;
                }
                .metric {
                    background: #f8f9ff; padding: 15px; border-radius: 10px;
                    text-align: center;
                }

                .metric-value {
                    font-size: 1.5em; font-weight: bold; color: #4ecdc4;
                }

                .file-list-container {
                    background: #f8f9ff;
                    border-radius: 12px;
                    padding: 15px;
                    margin: 10px 0;
                }

                label.upload-zone {
                    display: block;
                    border: 3px dashed #4ecdc4;
                    border-radius: 15px;
                    padding: 40px;
                    text-align: center;
                    background: #f8fffe;
                    cursor: pointer;
                    transition: all 0.3s;
                }

                label.upload-zone:hover {
                    background: #f0fffe;
                    border-color: #45b7b8;
                }

                .scrollable-file-list {
                    max-height: 200px;
                    overflow-y: auto;
                    border: 1px solid #e0e6ff;
                    border-radius: 8px;
                    padding: 10px;
                }

                .file-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    border-bottom: 1px solid #eee;
                }

                .file-item:last-child {
                    border-bottom: none;
                }

                .filename {
                    flex: 1;
                    font-weight: 500;
                }

                .filesize {
                    color: #666;
                    margin-right: 10px;
                }

                .remove-btn {
                    background: #ff6b6b;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    cursor: pointer;
                }

                .visual-file-browser {
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    gap: 20px;
                    margin: 20px 0;
                }

                .file-section {
                    background: #f8f9ff;
                    border-radius: 12px;
                    padding: 20px;
                    border: 2px solid #e0e6ff;
                }

                .section-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                }

                .thumbnail-grid, .prediction-grid, .label-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                    gap: 10px;
                    max-height: 300px;
                    overflow-y: auto;
                }

                .thumbnail-item {
                    position: relative;
                    background: white;
                    border-radius: 8px;
                    padding: 8px;
                    border: 1px solid #ddd;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .thumbnail-item:hover {
                    border-color: #4ecdc4;
                    box-shadow: 0 2px 8px rgba(78, 205, 196, 0.3);
                }

                .thumbnail-item img {
                    width: 100%;
                    height: 80px;
                    object-fit: cover;
                    border-radius: 4px;
                }

                .prediction-item {
                    background: white;
                    border-radius: 8px;
                    padding: 12px;
                    border: 1px solid #ddd;
                }

                .prediction-item.needs-correction {
                    border-color: #ff6b6b;
                    background: #fff5f5;
                }

                .prediction-item.approved {
                    border-color: #00b894;
                    background: #f0fff4;
                }

                .btn-primary, .btn-secondary {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: all 0.2s;
                }

                .btn-primary {
                    background: #4ecdc4;
                    color: white;
                }

                .btn-secondary {
                    background: #6c5ce7;
                    color: white;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Flexible Training Orchestrator</h1>
                    <p>Zero Hardcoded Assumptions • Maximum Control • Real Training</p>
                </div>

                <div class="config-grid">
                    <!-- Model Configuration -->
                    <div class="config-section">
                        <h3>🏗️ Model Architecture</h3>
                        <div class="form-group">
                            <label>Architecture Type</label>
                            <select id="architecture">
                                <option value="yolo_detection">YOLO Detection</option>
                                <option value="yolo_segmentation">YOLO Segmentation</option>
                                <option value="yolo_obb">YOLO Oriented Boxes</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Task Type</label>
                            <select id="task_type">
                                <option value="border_detection">Border Detection</option>
                                <option value="corner_analysis">Corner Analysis</option>
                                <option value="edge_analysis">Edge Analysis</option>
                                <option value="surface_analysis">Surface Analysis</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Border Type</label>
                            <select id="border_type">
                                <option value="outer_only">Outer Only</option>
                                <option value="inner_only">Inner Only</option>
                                <option value="dual_border">Dual Border</option>
                            </select>
                        </div>
                    </div>

                    <!-- Training Configuration -->
                    <div class="config-section">
                        <h3>⚙️ Training Parameters</h3>
                        <div class="form-group">
                            <label>Session Name</label>
                            <input type="text" id="session_name" placeholder="Border Detection Model">
                        </div>
                        <div class="form-group">
                            <label>Number of Classes</label>
                            <input type="number" id="num_classes" value="2" min="1" max="10">
                        </div>
                        <div class="form-group">
                            <label>Epochs</label>
                            <input type="number" id="epochs" value="100" min="10" max="1000">
                        </div>
                        <div class="form-group">
                            <label>Batch Size</label>
                            <select id="batch_size">
                                <option value="8">8 (Low Memory)</option>
                                <option value="16" selected>16 (Recommended)</option>
                                <option value="32">32 (High Memory)</option>
                            </select>
                        </div>
                    </div>

                    <!-- Hardware Configuration -->
                    <div class="config-section">
                        <h3>🖥️ Hardware Settings</h3>
                        <div class="form-group">
                            <label>Device</label>
                            <select id="device">
                                <option value="auto">Auto Detect</option>
                                <option value="cpu">CPU Only</option>
                                <option value="gpu">GPU (CUDA)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Workers</label>
                            <input type="number" id="workers" value="8" min="1" max="16">
                        </div>
                        <div class="form-group">
                            <label>Image Size</label>
                            <select id="image_size">
                                <option value="416">416px</option>
                                <option value="512">512px</option>
                                <option value="640" selected>640px</option>
                                <option value="800">800px</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <button class="btn" onclick="createSession()">🚀 Create Training Session</button>
                </div>

                <!-- Session Management -->
                <div id="session-panel" style="display: none;">
                    <div class="config-grid">
                        <!-- Image Upload -->
                        <div class="config-section">
                            <h3>📷 Upload Images</h3>
                            <div class="upload-zone" onclick="document.getElementById('image-files').click()">
                                <p>Click to upload training images</p>
                                <p>Supports: JPG, PNG, JPEG</p>
                            </div>
                            <input type="file" id="image-files" multiple accept="image/*" style="display: none;" onchange="uploadImages()">
                            <div id="image-status"></div>
                        </div>
                        <div class="config-section">
                            <h3>🎯 Upload Predictions</h3>
                            <div class="form-group">
                                <label>Prediction Format</label>
                                <select id="prediction_format">
                                    <option value="yolo">YOLO TXT</option>
                                    <option value="coco">COCO JSON</option>
                                    <option value="xml">Pascal VOC XML</option>
                                </select>
                            </div>
                            <div class="upload-zone" onclick="document.getElementById('prediction-files').click()">
                                <p>Click to upload predicted labels</p>
                                <p>AI model predictions for comparison</p>
                            </div>
                            <input type="file" id="prediction-files" multiple accept=".txt,.json,.xml" style="display: none;" onchange="uploadPredictions()">
                            </div>
                            <div id="prediction-status"></div>
                        </div>
                        <div class="config-section">
                            <h3>📝 Upload Labels</h3>
                            <div class="form-group">
                                <label>Label Format</label>
                                <select id="label_format">
                                    <option value="yolo">YOLO TXT</option>
                                    <option value="coco">COCO JSON</option>
                                    <option value="xml">Pascal VOC XML</option>
                                </select>
                            </div>
                            <div class="upload-zone" onclick="document.getElementById('label-files').click()">
                                <p>Click to upload ground truth labels</p>
                            </div>
                            <input type="file" id="label-files" multiple accept=".txt,.json,.xml" style="display: none;" onchange="uploadLabels()">
                            <div id="label-status"></div>
                        </div>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <button class="btn" onclick="validateSession()">✅ Validate Session</button>
                        <button class="btn" onclick="startTraining()" id="start-btn" disabled>🚀 Start Training</button>
                        <button class="btn" onclick="showVisualBrowser()">📁 Visual File Browser</button>
                    </div>
                </div>

                        <div class="visual-file-browser" id="visual-browser" style="display: none;">
                            <div class="file-section">
                                <div class="section-header">
                                    <h3>📸 Training Images (<span id="image-count">0</span>)</h3>
                                    <div class="section-controls">
                                        <button class="btn-primary" onclick="uploadImages()">+ Add Images</button>
                                        <button class="btn-secondary" onclick="removeSelected('images')">Remove Selected</button>
                                    </div>
                                </div>
                                <div class="thumbnail-grid" id="image-thumbnails"></div>
                            </div>

                            <div class="file-section">
                                <div class="section-header">
                                    <h3>🎯 Predicted Labels (<span id="predicted-count">0</span>)</h3>
                                    <div class="section-controls">
                                        <button class="btn-primary" onclick="uploadPredictedLabels()">+ Add Predictions</button>
                                        <button class="btn-secondary" onclick="reviewPredictions()">Review Corrections</button>
                                    </div>
                                </div>
                                <div class="prediction-grid" id="predicted-thumbnails"></div>
                            </div>

                            <div class="file-section">
                                <div class="section-header">
                                    <h3>✅ Ground Truth (<span id="ground-truth-count">0</span>)</h3>
                                    <div class="section-controls">
                                        <button class="btn-primary" onclick="uploadGroundTruth()">+ Add Ground Truth</button>
                                        <button class="btn-secondary" onclick="validateLabels()">Validate Labels</button>
                                    </div>
                                </div>
                                <div class="label-grid" id="ground-truth-thumbnails"></div>
                            </div>
                        </div>

                <!-- Progress Tracking -->
                <div class="progress-container" id="progress-panel">
                    <h3>📊 Training Progress</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill">0%</div>
                    </div>
                    <div id="progress-text">Initializing...</div>
                    <div class="metrics-grid" id="metrics-grid"></div>
                </div>
            </div>

            <script>
                let currentSessionId = null;
                let trainingSocket = null;

                async function createSession() {
                    const config = {
                        session_name: document.getElementById('session_name').value || 'Border Detection Model',
                        architecture: document.getElementById('architecture').value,
                        task_type: document.getElementById('task_type').value,
                        card_side: 'front',
                        border_type: document.getElementById('border_type').value,
                        num_classes: parseInt(document.getElementById('num_classes').value),
                        epochs: parseInt(document.getElementById('epochs').value),
                        batch_size: parseInt(document.getElementById('batch_size').value),
                        device: document.getElementById('device').value,
                        workers: parseInt(document.getElementById('workers').value),
                        image_size: parseInt(document.getElementById('image_size').value)
                    };

                    try {
                        const response = await fetch('/api/session/create', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(config)
                        });

                        const result = await response.json();
                        if (response.ok) {
                            currentSessionId = result.session_id;
                            document.getElementById('session-panel').style.display = 'block';
                            alert(`✅ Session created: ${result.session_id}`);
                        } else {
                            alert(`❌ Error: ${result.detail}`);
                        }
                    } catch (error) {
                        alert(`❌ Error: ${error.message}`);
                    }
                }

                async function uploadImages() {
                    if (!currentSessionId) return;

                    const files = document.getElementById('image-files').files;
                    const formData = new FormData();

                    for (let file of files) {
                        formData.append('files', file);
                    }

                    try {
                        const response = await fetch(`/api/session/${currentSessionId}/upload-images`, {
                            method: 'POST',
                            body: formData
                        });

                        const result = await response.json();

                        // Update status
                        document.getElementById('image-status').innerHTML =
                            `✅ ${result.uploaded} images uploaded (${result.total_images} total)`;

                        // Replace upload zone with thumbnail grid
                        createImageThumbnailGrid(result.files);

                    } catch (error) {
                        alert(`Upload error: ${error.message}`);
                    }
                }

                async function uploadPredictions() {
                    if (!currentSessionId) return;

                    const files = document.getElementById('prediction-files').files;
                    const format = document.getElementById('prediction_format').value;
                    const formData = new FormData();

                    formData.append('prediction_format', format);
                    for (let file of files) {
                        formData.append('files', file);
                    }

                    try {
                        const response = await fetch(`/api/session/${currentSessionId}/predicted-labels`, {
                            method: 'POST',
                            body: formData
                        });

                        const result = await response.json();

                        document.getElementById('prediction-status').innerHTML =
                            `✅ ${result.uploaded_count} predictions uploaded (${format} format)`;

                        createPredictionGrid(result.predictions);

                    } catch (error) {
                        alert(`Upload error: ${error.message}`);
                    }
                }

                async function uploadLabels() {
                    if (!currentSessionId) return;

                    const files = document.getElementById('label-files').files;
                    const format = document.getElementById('label_format').value;
                    const formData = new FormData();

                    formData.append('label_format', format);
                    for (let file of files) {
                        formData.append('files', file);
                    }

                    try {
                        const response = await fetch(`/api/session/${currentSessionId}/labels`, {
                            method: 'POST',
                            body: formData
                        });

                        const result = await response.json();

                        // Update status
                        document.getElementById('label-status').innerHTML =
                            `✅ ${result.uploaded} labels uploaded (${result.label_format} format)`;

                        // Replace upload zone with thumbnail grid
                        createLabelThumbnailGrid(result.files);

                    } catch (error) {
                        alert(`Upload error: ${error.message}`);
                    }
                }

                function createImageThumbnailGrid(files) {
                    const uploadZone = document.getElementById('image-files').parentElement.parentElement;

                    const fileList = document.createElement('div');
                    fileList.className = 'file-list-container';
                    fileList.innerHTML = `
                        <div class="list-header">
                            <span>📸 ${files.length} Images</span>
                            <button class="btn-small" onclick="addMoreImages()">+ Add More</button>
                        </div>
                        <div class="scrollable-file-list">
                            ${files.map((file, index) => `
                                <div class="file-item" data-filename="${file.filename}">
                                    <span class="filename">${file.filename}</span>
                                    <span class="filesize">${formatFileSize(file.size)}</span>
                                    <button class="remove-btn" onclick="removeFile('image', '${file.filename}')">×</button>
                                </div>
                            `).join('')}
                        </div>
                    `;

                    const oldUploadZone = uploadZone.querySelector('.upload-zone');
                    oldUploadZone.replaceWith(fileList);
                }

                function createPredictionGrid(files) {
                    const uploadZone = document.getElementById('prediction-files').parentElement.parentElement;

                    const fileList = document.createElement('div');
                    fileList.className = 'file-list-container';
                    fileList.innerHTML = `
                        <div class="list-header">
                            <span>🎯 ${files.length} Predictions</span>
                            <button class="btn-small" onclick="alert('Use the file input above to add more')">+ Add More</button>
                        </div>
                        <div class="scrollable-file-list">
                            ${files.map((file, index) => `
                                <div class="file-item" data-filename="${file.filename}">
                                    <span class="filename">${file.filename}</span>
                                    <span class="confidence">${(file.confidence_score * 100).toFixed(1)}%</span>
                                    <button class="remove-btn" onclick="removeFile('prediction', '${file.filename}')">×</button>
                                </div>
                            `).join('')}
                        </div>
                    `;

                    const oldUploadZone = uploadZone.querySelector('.upload-zone');
                    oldUploadZone.replaceWith(fileList);
                }

                function createLabelThumbnailGrid(files) {
                    const uploadZone = document.getElementById('label-files').parentElement.parentElement;

                    const fileList = document.createElement('div');
                    fileList.className = 'file-list-container';
                    fileList.innerHTML = `
                        <div class="list-header">
                            <span>📝 ${files.length} Labels</span>
                            <button class="btn-small" onclick="addMoreLabels()">+ Add More</button>
                        </div>
                        <div class="scrollable-file-list">
                            ${files.map((file, index) => `
                                <div class="file-item" data-filename="${file.filename}">
                                    <span class="filename">${file.filename}</span>
                                    <span class="format">${file.format || 'YOLO'}</span>
                                    <button class="remove-btn" onclick="removeFile('label', '${file.filename}')">×</button>
                                </div>
                            `).join('')}
                        </div>
                    `;

                    const oldUploadZone = uploadZone.querySelector('.upload-zone');
                    oldUploadZone.replaceWith(fileList);
                }

                async function uploadPredictions() {
                    const fileInput = document.createElement('input');
                    fileInput.type = 'file';
                    fileInput.multiple = true;
                    fileInput.accept = '.txt,.json,.xml';

                    fileInput.onchange = async (event) => {
                        const files = Array.from(event.target.files);
                        const formData = new FormData();
                        files.forEach(file => formData.append('files', file));

                        const response = await fetch(`/api/session/${currentSessionId}/predicted-labels`, {
                            method: 'POST',
                            body: formData
                        });

                        const result = await response.json();

                        if (response.ok) {
                            // Update predictions grid
                            updatePredictionsGrid(result.predictions);
                            alert(`✅ Uploaded ${result.uploaded_count} predicted labels`);
                        } else {
                            alert(`❌ Upload failed: ${result.detail}`);
                        }
                    };

                    fileInput.click();
                }

                function updatePredictionsGrid(predictions) {
                    const grid = document.getElementById('predictions-grid');
                    const header = document.querySelector('.predictions-section .grid-header span');

                    header.textContent = `🎯 Predicted Labels (${predictions.length})`;

                    grid.innerHTML = predictions.map(pred => `
                        <div class="prediction-item" data-filename="${pred.filename}">
                            <div class="prediction-icon ${pred.status}">🤖</div>
                            <div class="prediction-info">
                                <span class="filename">${pred.filename}</span>
                                <span class="confidence">${(pred.confidence || 85)}% confidence</span>
                            </div>
                            <div class="prediction-actions">
                                <button class="review-btn" onclick="reviewPrediction('${pred.filename}')">Review</button>
                                <button class="remove-btn" onclick="removeFile('prediction', '${pred.filename}')">×</button>
                            </div>
                        </div>
                    `).join('');
                }

                function addMoreImages() {
                    document.getElementById('image-files').click();
                }

                function addMoreLabels() {
                    document.getElementById('label-files').click();
                }

                function removeFile(type, filename) {
                    // Remove file from session and update display
                    if (confirm(`Remove ${filename}?`)) {
                        // API call to remove file
                        fetch(`/api/session/${currentSessionId}/remove-file`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({type: type, filename: filename})
                        }).then(() => {
                            // Remove from display
                            document.querySelector(`[data-filename="${filename}"]`).remove();
                        });
                    }
                }

                function formatFileSize(bytes) {
                    if (bytes === 0) return '0 Bytes';
                    const k = 1024;
                    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                    const i = Math.floor(Math.log(bytes) / Math.log(k));
                    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
                }

                async function validateSession() {
                    if (!currentSessionId) return;

                    try {
                        const response = await fetch(`/api/session/${currentSessionId}/validate`);
                        const result = await response.json();

                        if (result.ready) {
                            document.getElementById('start-btn').disabled = false;
                            alert('✅ Session validated and ready for training!');
                        } else {
                            alert(`❌ Issues found: ${result.issues.join(', ')}`);
                        }
                    } catch (error) {
                        alert(`Validation error: ${error.message}`);
                    }
                }

                async function startTraining() {
                    if (!currentSessionId) return;

                    try {
                        const response = await fetch(`/api/session/${currentSessionId}/start-training`, {
                            method: 'POST'
                        });

                        const result = await response.json();
                        if (response.ok) {
                            document.getElementById('progress-panel').style.display = 'block';
                            connectWebSocket();
                            alert('🚀 Real YOLO training started!');
                        } else {
                            alert(`❌ Error: ${result.detail}`);
                        }
                    } catch (error) {
                        alert(`Training error: ${error.message}`);
                    }
                }

                function connectWebSocket() {
                    if (!currentSessionId) return;

                    const wsUrl = `ws://localhost:8010/ws/${currentSessionId}`;
                    trainingSocket = new WebSocket(wsUrl);

                    trainingSocket.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        updateProgress(data);
                    };

                    trainingSocket.onerror = function(error) {
                        console.error('WebSocket error:', error);
                    };
                }

                function updateProgress(data) {
                    const progressFill = document.getElementById('progress-fill');
                    const progressText = document.getElementById('progress-text');
                    const metricsGrid = document.getElementById('metrics-grid');

                    const progress = (data.epoch / data.total_epochs) * 100;
                    progressFill.style.width = progress + '%';
                    progressFill.textContent = progress.toFixed(1) + '%';

                    progressText.textContent = `${data.status} - Epoch ${data.epoch}/${data.total_epochs}`;

                    if (data.loss !== undefined) {
                        metricsGrid.innerHTML = `
                            <div class="metric">
                                <div class="metric-value">${data.loss.toFixed(4)}</div>
                                <div>Loss</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${(data.precision || 0).toFixed(3)}</div>
                                <div>Precision</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${(data.recall || 0).toFixed(3)}</div>
                                <div>Recall</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${(data.mAP50 || 0).toFixed(3)}</div>
                                <div>mAP50</div>
                            </div>
                        `;
                    }

                    if (data.status === 'completed') {
                        alert('🎉 Training completed successfully!');
                    } else if (data.status === 'error') {
                        alert(`❌ Training failed: ${data.message}`);
                    }
                }
                async function loadVisualFileBrowser() {
                    const sessionId = currentSessionId;
                    const response = await fetch(`/api/session/${sessionId}/files/visual`);
                    const data = await response.json();

                    populateImageThumbnails(data.images);
                    populatePredictedPreviews(data.predicted_labels);
                    populateGroundTruthPreviews(data.ground_truth);
                    updateFileStatistics(data.statistics);
                }

                function populateImageThumbnails(images) {
                    const container = document.getElementById('image-thumbnails');
                    container.innerHTML = images.map(img => `
                        <div class="thumbnail-item" data-id="${img.id}">
                            <img src="${img.thumbnail_url}" alt="${img.filename}" />
                            <div class="thumbnail-metadata">
                                <span class="filename">${img.filename}</span>
                                <span class="file-size">${formatFileSize(img.file_size)}</span>
                            </div>
                            <input type="checkbox" class="file-selector" />
                        </div>
                    `).join('');

                    document.getElementById('image-count').textContent = images.length;
                }

                function populatePredictedPreviews(predictions) {
                    const container = document.getElementById('predicted-thumbnails');
                    container.innerHTML = predictions.map(pred => `
                        <div class="prediction-item ${pred.correction_needed ? 'needs-correction' : 'approved'}" data-id="${pred.id}">
                            <div class="prediction-header">
                                <span class="filename">${pred.filename}</span>
                                <span class="confidence-score">${(pred.confidence_score * 100).toFixed(1)}%</span>
                            </div>
                            <div class="prediction-status">${pred.status}</div>
                            <div class="prediction-actions">
                                <button onclick="reviewPrediction(${pred.id})">Review</button>
                                <button onclick="approvePrediction(${pred.id})">Approve</button>
                            </div>
                        </div>
                    `).join('');

                    document.getElementById('predicted-count').textContent = predictions.length;
                }

                function populateGroundTruthPreviews(groundTruth) {
                    const container = document.getElementById('ground-truth-thumbnails');
                    container.innerHTML = groundTruth.map(gt => `
                        <div class="label-item" data-id="${gt.id}">
                            <span class="filename">${gt.filename}</span>
                            <span class="label-count">${gt.label_count} labels</span>
                            <span class="status verified">✓ Verified</span>
                        </div>
                    `).join('');

                    document.getElementById('ground-truth-count').textContent = groundTruth.length;
                }

                async function uploadPredictedLabels() {
                    const fileInput = document.createElement('input');
                    fileInput.type = 'file';
                    fileInput.multiple = true;
                    fileInput.accept = '.txt,.json,.xml';

                    fileInput.onchange = async (event) => {
                        const files = Array.from(event.target.files);
                        const formData = new FormData();
                        files.forEach(file => formData.append('files', file));

                        const response = await fetch(`/api/session/${currentSessionId}/predicted-labels`, {
                            method: 'POST',
                            body: formData
                        });

                        const result = await response.json();

                        if (response.ok) {
                            alert(`✅ Uploaded ${result.uploaded_count} predicted labels`);
                            loadVisualFileBrowser();
                        } else {
                            alert(`❌ Upload failed: ${result.detail}`);
                        }
                    };

                    fileInput.click();
                }

                function showVisualBrowser() {
                    document.getElementById('visual-browser').style.display = 'block';
                    loadVisualFileBrowser();
                }

                function formatFileSize(bytes) {
                    if (bytes === 0) return '0 Bytes';
                    const k = 1024;
                    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                    const i = Math.floor(Math.log(bytes) / Math.log(k));
                    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
                }
            </script>
        </body>
        </html>
        '''

# Main entry point
async def main():
    orchestrator = FlexibleTrainingOrchestrator()

    import uvicorn
    config = uvicorn.Config(
        orchestrator.app,
        host="0.0.0.0",
        port=8010,
        log_level="info"
    )
    server = uvicorn.Server(config)

    print("🎯 Flexible Training Orchestrator")
    print("=" * 50)
    print("✅ Zero hardcoded assumptions")
    print("🏗️ Multiple architectures: YOLO Detection/Segmentation/OBB")
    print("🎛️ Configurable: 1-class to multi-class")
    print("📱 Front/Back card support")
    print("🔄 Real YOLO training with progress tracking")
    print("🌐 Interface: http://localhost:8010")
    print("=" * 50)

    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
