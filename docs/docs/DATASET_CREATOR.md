# Dataset Creator Requirements

## Core Functionality
- Add images with quality analysis ✅
- Import/use border calibrator annotations
- Add prediction labels for model retraining
- Support multiple dataset types for various models
- Auto-convert between label formats (YOLO, COCO, etc.)

## Dataset Types & Models

### Border Analysis
- Outer border detection model
- Graphical border detection model
- 24-point centering model

### Damage Assessment
- Corner damage/sharpness models
- Surface damage detection
- Edge damage detection

### Advanced Analysis
- Photometric stereo datasets
- Future experimental dataset types

## Technical Requirements

### Label Management
1. **Import Annotations**
   - Import from border calibrator
   - Store precise calibration data
   - Maintain adjustment parameters

2. **Prediction Integration**
   - Import model predictions
   - Allow correction/refinement
   - Support retraining workflows

3. **Format Conversion**
   - YOLO → Custom format converter
   - COCO → Custom format converter
   - Maintain metadata during conversion

### Dataset Organization
1. **Model-Specific Datasets**
   - Separate organization per model type
   - Clear versioning system
   - Training/validation/test splits

2. **Multi-Modal Support**
   - Photometric stereo data
   - Combined damage assessments
   - Extensible for future types

### Training Integration
1. **Model Retraining**
   - Use corrected predictions
   - Mix ground truth & predictions
   - Track accuracy improvements

2. **Experimental Features**
   - Support for new analysis types
   - Flexible data organization
   - Custom label formats

## Implementation Notes

- Keep UI minimal - focus on data management
- Reuse border calibrator for annotations
- Support batch operations for efficiency
- Maintain data quality metrics
- Enable easy dataset export/import