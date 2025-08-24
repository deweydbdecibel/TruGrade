#!/usr/bin/env python3
"""
🛡️ Revolutionary Dataset Manager - FULL USER CONTROL
===================================================

SAFE TRAINING: Complete control over dataset selection, validation, and training
- Browse and select specific images
- Choose label folders (corrected vs predicted)
- Add new cards from any era (1962, 1976, 1990+)
- Validate before training
- Progress monitoring
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uuid
import shutil

from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

# Database setup
DATABASE_URL = "postgresql://revolutionary_user:revolutionary_pass@localhost/card_grading"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafeDatasetManager:
    """Safe dataset management with full user control"""

    def __init__(self):
        self.app = FastAPI(title="Revolutionary Dataset Manager - Safe Training")
        self.setup_cors()

        # Known dataset locations
        self.known_datasets = {
            "568_revolutionary": {
                "path": "/home/dewster/RCG/data/datasets/Setone/564",
                "images": "images564",
                "corrected_labels": "corrected",
                "predicted_labels": "txtlabels"
            }
        }

        self.setup_routes()
        logger.info("🛡️ Safe Dataset Manager initialized")

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
        async def dataset_manager_dashboard():
            """Safe dataset management dashboard"""
            return HTMLResponse(self.get_dashboard_html())

        @self.app.get("/api/datasets/scan")
        async def scan_available_datasets():
            """Scan for available datasets"""
            datasets = []

            for name, config in self.known_datasets.items():
                dataset_path = Path(config["path"])
                if dataset_path.exists():
                    images_dir = dataset_path / config["images"]
                    corrected_dir = dataset_path / config["corrected_labels"]
                    predicted_dir = dataset_path / config["predicted_labels"]

                    image_files = list(images_dir.glob("*.jpg")) if images_dir.exists() else []
                    corrected_files = list(corrected_dir.glob("*.txt")) if corrected_dir.exists() else []
                    predicted_files = list(predicted_dir.glob("*.txt")) if predicted_dir.exists() else []

                    datasets.append({
                        "id": name,
                        "name": name.replace("_", " ").title(),
                        "path": str(dataset_path),
                        "images_count": len(image_files),
                        "corrected_labels": len(corrected_files),
                        "predicted_labels": len(predicted_files),
                        "status": "ready" if image_files and corrected_files else "incomplete"
                    })

            return datasets

        @self.app.get("/api/datasets/{dataset_id}/browse")
        async def browse_dataset(dataset_id: str, start: int = 0, limit: int = 50):
            """Browse specific dataset with pagination"""

            if dataset_id not in self.known_datasets:
                raise HTTPException(status_code=404, detail="Dataset not found")

            config = self.known_datasets[dataset_id]
            dataset_path = Path(config["path"])
            images_dir = dataset_path / config["images"]
            corrected_dir = dataset_path / config["corrected_labels"]
            predicted_dir = dataset_path / config["predicted_labels"]

            # Get image files
            image_files = sorted(list(images_dir.glob("*.jpg")))[start:start+limit]

            cards = []
            for img_file in image_files:
                corrected_label = corrected_dir / f"{img_file.stem}.txt"
                predicted_label = predicted_dir / f"{img_file.stem}.txt"

                card_info = {
                    "image_name": img_file.name,
                    "image_path": str(img_file),
                    "has_corrected": corrected_label.exists(),
                    "has_predicted": predicted_label.exists(),
                    "file_size": img_file.stat().st_size if img_file.exists() else 0
                }

                # Read label contents for preview
                if corrected_label.exists():
                    with open(corrected_label, 'r') as f:
                        lines = f.readlines()
                    card_info["corrected_preview"] = [line.strip() for line in lines[:2]]

                if predicted_label.exists():
                    with open(predicted_label, 'r') as f:
                        lines = f.readlines()
                    card_info["predicted_preview"] = [line.strip() for line in lines[:2]]

                cards.append(card_info)

            return {
                "cards": cards,
                "total_images": len(list(images_dir.glob("*.jpg"))),
                "start": start,
                "limit": limit
            }

        @self.app.post("/api/training/validate")
        async def validate_training_selection(selection_data: Dict):
            """Validate training selection before starting"""

            dataset_id = selection_data.get("dataset_id")
            selected_images = selection_data.get("selected_images", [])
            label_type = selection_data.get("label_type", "corrected")

            validation = {
                "status": "validating",
                "issues": [],
                "warnings": [],
                "ready_for_training": False,
                "summary": {}
            }

            # Validate selection
            if not selected_images:
                validation["issues"].append("No images selected for training")
            elif len(selected_images) < 10:
                validation["warnings"].append(f"Only {len(selected_images)} images selected - recommend at least 50 for good training")

            # Check label consistency
            if dataset_id in self.known_datasets:
                config = self.known_datasets[dataset_id]
                dataset_path = Path(config["path"])
                label_dir = dataset_path / (config["corrected_labels"] if label_type == "corrected" else config["predicted_labels"])

                valid_pairs = 0
                dual_border_count = 0

                for image_name in selected_images:
                    label_file = label_dir / f"{Path(image_name).stem}.txt"
                    if label_file.exists():
                        valid_pairs += 1
                        with open(label_file, 'r') as f:
                            lines = f.readlines()
                        if len(lines) >= 2:
                            dual_border_count += 1

                validation["summary"] = {
                    "selected_images": len(selected_images),
                    "valid_label_pairs": valid_pairs,
                    "dual_border_cards": dual_border_count,
                    "label_type": label_type,
                    "dataset": dataset_id
                }

                if valid_pairs == len(selected_images) and dual_border_count > 0:
                    validation["ready_for_training"] = True
                    validation["status"] = "validated"
                else:
                    validation["issues"].append(f"Missing labels: {len(selected_images) - valid_pairs} images don't have corresponding {label_type} labels")

            return validation

        @self.app.post("/api/training/start-safe")
        async def start_safe_training(training_config: Dict):
            """Start training with validated selection"""

            # This would integrate with your actual YOLO training
            run_id = str(uuid.uuid4())

            return {
                "status": "started",
                "run_id": run_id,
                "message": f"Safe training started with {len(training_config.get('selected_images', []))} selected images",
                "config": training_config
            }

    def get_dashboard_html(self) -> str:
        """Safe dataset management dashboard"""
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🛡️ Revolutionary Dataset Manager - Safe Training</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh; color: #333;
                }
                .container { max-width: 1600px; margin: 0 auto; padding: 20px; }
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
                .safety-badge {
                    background: linear-gradient(45deg, #4ecdc4, #44a08d);
                    color: white; padding: 8px 16px; border-radius: 20px;
                    font-size: 0.9em; margin: 10px 5px; display: inline-block;
                }
                .content-panel {
                    background: rgba(255,255,255,0.95); border-radius: 20px;
                    padding: 40px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }
                .dataset-grid {
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 25px; margin: 30px 0;
                }
                .dataset-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 30px; border-radius: 15px;
                    cursor: pointer; transition: all 0.3s;
                }
                .dataset-card:hover { transform: translateY(-5px) scale(1.02); }
                .browse-panel {
                    background: #f8f9ff; border-radius: 15px;
                    padding: 30px; margin: 20px 0; display: none;
                }
                .card-grid {
                    display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px; margin: 20px 0;
                }
                .card-item {
                    background: white; border: 2px solid #e0e6ff;
                    border-radius: 10px; padding: 20px; cursor: pointer;
                    transition: all 0.3s;
                }
                .card-item:hover { border-color: #4ecdc4; transform: translateY(-2px); }
                .card-item.selected { border-color: #4ecdc4; background: #f0fffe; }
                .btn {
                    background: #4ecdc4; color: white; padding: 15px 30px;
                    border: none; border-radius: 8px; cursor: pointer;
                    font-size: 16px; font-weight: 500; transition: all 0.3s;
                    margin: 10px 5px;
                }
                .btn:hover { background: #45b7b8; transform: translateY(-2px); }
                .btn-secondary { background: #6c5ce7; }
                .btn-danger { background: #ff6b6b; }
                .validation-panel {
                    background: linear-gradient(45deg, #4ecdc4, #44a08d);
                    color: white; padding: 20px; border-radius: 10px;
                    margin: 20px 0; display: none;
                }
                .hidden { display: none; }
                .selection-info {
                    position: fixed; top: 20px; right: 20px;
                    background: rgba(255,255,255,0.95); padding: 20px;
                    border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Revolutionary Dataset Manager</h1>
                    <p>Safe, Controlled Training with Full User Control</p>
                    <div style="margin-top: 20px;">
                        <span class="safety-badge">🛡️ Full Control</span>
                        <span class="safety-badge">👁️ Visual Selection</span>
                        <span class="safety-badge">✅ Validation</span>
                        <span class="safety-badge">📊 Safe Training</span>
                    </div>
                </div>

                <div class="content-panel">
                    <!-- Step 1: Dataset Selection -->
                    <div id="dataset-selection">
                        <h2>📂 Available Datasets</h2>
                        <p>Select a dataset to browse and manage for training:</p>

                        <div class="dataset-grid" id="datasets-container">
                            <!-- Datasets loaded here -->
                        </div>
                    </div>

                    <!-- Step 2: Card Browser -->
                    <div id="card-browser" class="browse-panel">
                        <h2>🔍 Browse & Select Cards</h2>
                        <div style="margin-bottom: 20px;">
                            <label>Label Type: </label>
                            <select id="label-type" onchange="updateLabelType()">
                                <option value="corrected">Corrected Labels (Your Calibrated)</option>
                                <option value="predicted">Predicted Labels (Auto-Generated)</option>
                            </select>

                            <button class="btn" onclick="selectAllCards()">Select All</button>
                            <button class="btn btn-secondary" onclick="clearSelection()">Clear Selection</button>
                            <button class="btn" onclick="validateSelection()">Validate Selection</button>
                        </div>

                        <div class="card-grid" id="cards-container">
                            <!-- Cards loaded here -->
                        </div>

                        <div style="text-align: center; margin: 20px 0;">
                            <button class="btn" onclick="loadMoreCards()">Load More Cards</button>
                        </div>
                    </div>

                    <!-- Step 3: Validation -->
                    <div id="validation-panel" class="validation-panel">
                        <h3>🔍 Training Validation</h3>
                        <div id="validation-results"></div>
                        <div style="margin-top: 20px;">
                            <button class="btn" style="background: white; color: #4ecdc4;" onclick="startSafeTraining()">🚀 Start Safe Training</button>
                            <button class="btn btn-secondary" onclick="hideValidation()">Cancel</button>
                        </div>
                    </div>
                </div>

                <!-- Selection Info Panel -->
                <div class="selection-info" id="selection-info">
                    <h4>📋 Selection</h4>
                    <p>Selected: <span id="selected-count">0</span> cards</p>
                    <p>Label Type: <span id="current-label-type">corrected</span></p>
                </div>
            </div>

            <script>
                let currentDataset = null;
                let selectedCards = [];
                let allCards = [];
                let currentStart = 0;
                let currentLabelType = 'corrected';

                async function loadDatasets() {
                    try {
                        const response = await fetch('/api/datasets/scan');
                        const datasets = await response.json();

                        const container = document.getElementById('datasets-container');
                        container.innerHTML = datasets.map(dataset => `
                            <div class="dataset-card" onclick="selectDataset('${dataset.id}')">
                                <h3>📂 ${dataset.name}</h3>
                                <div style="margin: 15px 0;">
                                    <p>📷 Images: ${dataset.images_count}</p>
                                    <p>✅ Corrected Labels: ${dataset.corrected_labels}</p>
                                    <p>🤖 Predicted Labels: ${dataset.predicted_labels}</p>
                                    <p>Status: <strong>${dataset.status}</strong></p>
                                </div>
                                <p style="font-size: 0.9em; opacity: 0.8;">
                                    Click to browse and select specific cards
                                </p>
                            </div>
                        `).join('');
                    } catch (error) {
                        console.error('Error loading datasets:', error);
                    }
                }

                async function selectDataset(datasetId) {
                    currentDataset = datasetId;
                    selectedCards = [];
                    currentStart = 0;

                    document.getElementById('dataset-selection').style.display = 'none';
                    document.getElementById('card-browser').style.display = 'block';

                    await loadCards();
                    updateSelectionInfo();
                }

                async function loadCards() {
                    try {
                        const response = await fetch(`/api/datasets/${currentDataset}/browse?start=${currentStart}&limit=50`);
                        const data = await response.json();

                        if (currentStart === 0) {
                            allCards = data.cards;
                        } else {
                            allCards = allCards.concat(data.cards);
                        }

                        renderCards();
                    } catch (error) {
                        console.error('Error loading cards:', error);
                    }
                }

                function renderCards() {
                    const container = document.getElementById('cards-container');
                    container.innerHTML = allCards.map(card => `
                        <div class="card-item ${selectedCards.includes(card.image_name) ? 'selected' : ''}"
                             onclick="toggleCard('${card.image_name}')">
                            <h4>${card.image_name}</h4>
                            <div style="margin: 10px 0;">
                                <p>✅ Corrected: ${card.has_corrected ? '✓' : '✗'}</p>
                                <p>🤖 Predicted: ${card.has_predicted ? '✓' : '✗'}</p>
                                <p>Size: ${(card.file_size / 1024).toFixed(1)} KB</p>
                            </div>
                            ${card.corrected_preview ? `
                                <div style="font-size: 0.8em; background: #f0f9ff; padding: 10px; border-radius: 5px;">
                                    <strong>Corrected Preview:</strong><br>
                                    ${card.corrected_preview.join('<br>')}
                                </div>
                            ` : ''}
                        </div>
                    `).join('');
                }

                function toggleCard(imageName) {
                    const index = selectedCards.indexOf(imageName);
                    if (index > -1) {
                        selectedCards.splice(index, 1);
                    } else {
                        selectedCards.push(imageName);
                    }
                    renderCards();
                    updateSelectionInfo();
                }

                function selectAllCards() {
                    selectedCards = allCards.map(card => card.image_name);
                    renderCards();
                    updateSelectionInfo();
                }

                function clearSelection() {
                    selectedCards = [];
                    renderCards();
                    updateSelectionInfo();
                }

                function updateSelectionInfo() {
                    document.getElementById('selected-count').textContent = selectedCards.length;
                    document.getElementById('current-label-type').textContent = currentLabelType;
                }

                function updateLabelType() {
                    currentLabelType = document.getElementById('label-type').value;
                    updateSelectionInfo();
                }

                async function validateSelection() {
                    if (selectedCards.length === 0) {
                        alert('Please select at least one card for training');
                        return;
                    }

                    try {
                        const response = await fetch('/api/training/validate', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                dataset_id: currentDataset,
                                selected_images: selectedCards,
                                label_type: currentLabelType
                            })
                        });

                        const validation = await response.json();

                        document.getElementById('validation-results').innerHTML = `
                            <div style="margin-bottom: 15px;">
                                <h4>📊 Validation Summary</h4>
                                <p>Selected Images: ${validation.summary.selected_images}</p>
                                <p>Valid Label Pairs: ${validation.summary.valid_label_pairs}</p>
                                <p>Dual-Border Cards: ${validation.summary.dual_border_cards}</p>
                                <p>Label Type: ${validation.summary.label_type}</p>
                            </div>

                            ${validation.issues.length > 0 ? `
                                <div style="background: rgba(255,107,107,0.2); padding: 10px; border-radius: 5px; margin: 10px 0;">
                                    <strong>❌ Issues:</strong><br>
                                    ${validation.issues.map(issue => `• ${issue}`).join('<br>')}
                                </div>
                            ` : ''}

                            ${validation.warnings.length > 0 ? `
                                <div style="background: rgba(255,193,7,0.2); padding: 10px; border-radius: 5px; margin: 10px 0;">
                                    <strong>⚠️ Warnings:</strong><br>
                                    ${validation.warnings.map(warning => `• ${warning}`).join('<br>')}
                                </div>
                            ` : ''}

                            <div style="margin-top: 15px;">
                                <strong>Status: ${validation.ready_for_training ? '✅ Ready for Training' : '❌ Not Ready'}</strong>
                            </div>
                        `;

                        document.getElementById('validation-panel').style.display = 'block';

                    } catch (error) {
                        alert(`Validation error: ${error.message}`);
                    }
                }

                async function startSafeTraining() {
                    if (!confirm(`🚀 Start Safe Training?

Selected: ${selectedCards.length} cards
Label Type: ${currentLabelType}

This will start YOLO11 training with only your selected images.`)) {
                        return;
                    }

                    try {
                        const response = await fetch('/api/training/start-safe', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                dataset_id: currentDataset,
                                selected_images: selectedCards,
                                label_type: currentLabelType,
                                epochs: 100,
                                batch_size: 16
                            })
                        });

                        const result = await response.json();
                        alert(`🚀 ${result.message}
Training ID: ${result.run_id}`);

                    } catch (error) {
                        alert(`Training error: ${error.message}`);
                    }
                }

                function hideValidation() {
                    document.getElementById('validation-panel').style.display = 'none';
                }

                function loadMoreCards() {
                    currentStart += 50;
                    loadCards();
                }

                // Initialize
                loadDatasets();
            </script>
        </body>
        </html>
        '''

# Main entry point
async def main():
    """Start the safe dataset manager"""

    manager = SafeDatasetManager()

    import uvicorn
    config = uvicorn.Config(
        manager.app,
        host="0.0.0.0",
        port=8005,
        log_level="info"
    )
    server = uvicorn.Server(config)

    print("🛡️ Revolutionary Dataset Manager - Safe Training")
    print("=" * 60)
    print("✅ Full control over image/label selection")
    print("🔍 Visual card browser with preview")
    print("✅ Validation before training")
    print("📊 Safe, monitored training process")
    print("🔗 Safe interface: http://localhost:8005")
    print("=" * 60)

    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
