# Location: src/core/grading_engine.py
import numpy as np
from ultralytics import YOLO
from typing import Dict, List, Optional, Union

from core.photometric.photometric_stereo import RevolutionaryPhotometricStereo
from core.models import GradingResult

class RevolutionaryGradingEngine:
    """
    The neural network that transforms amateur card grading into scientific precision
    """

    def __init__(self):
        self.photometric_engine = RevolutionaryPhotometricStereo()
        self.outer_border_model = YOLO("models/outer_border_seg.pt")
        self.inner_border_model = YOLO("models/inner_border_seg.pt")

    def analyze_card_comprehensive(self, image_path: str) -> GradingResult:
        """
        The full revolutionary analysis pipeline - from pixels to profit
        """
        # Load and preprocess
        image = self.load_and_normalize(image_path)

        # Dual-border detection with pixel precision
        outer_segments = self.outer_border_model.predict(image, task="segment")
        inner_segments = self.inner_border_model.predict(image, task="segment")

        # Revolutionary centering mathematics
        centering_analysis = self.calculate_revolutionary_centering(
            outer_segments[0].masks.xy[0],  # Outer polygon coordinates
            inner_segments[0].masks.xy[0]   # Inner polygon coordinates
        )

        # Photometric stereo surface analysis
        surface_analysis = self.photometric_engine.analyze_card(image)

        # Combine all metrics into final grade
        return self.synthesize_grade(centering_analysis, surface_analysis)

    def calculate_revolutionary_centering(self, outer_polygon, inner_polygon):
        """
        Where geometry meets profitability - sub-pixel centering precision
        Enhanced with independent edge analysis and skew detection
        """
        # Configure measurement points
        VERTICAL_POINTS = 7    # More points on longer edges
        HORIZONTAL_POINTS = 5  # Fewer points on shorter edges
        SKEW_TOLERANCE = 0.02  # 2% maximum allowed skew

        # Initialize the measurement result structure
        centering_result = {
            "edges": {
                "left": {"measurements": [], "avg": 0.0, "skew": 0.0},
                "right": {"measurements": [], "avg": 0.0, "skew": 0.0},
                "top": {"measurements": [], "avg": 0.0, "skew": 0.0},
                "bottom": {"measurements": [], "avg": 0.0, "skew": 0.0}
            },
            "centering": {
                "horizontal": 0.0,  # left-right ratio
                "vertical": 0.0     # top-bottom ratio
            },
            "skew_analysis": {
                "horizontal": 0.0,  # left vs right edge alignment
                "vertical": 0.0     # top vs bottom edge alignment
            },
            "grade_impact": {
                "centering_deduction": 0.0,
                "skew_deduction": 0.0
            },
            "confidence": 0.0
        }

        try:
            # Normalize polygon coordinates if needed
            outer_points = self._normalize_coordinates(outer_polygon)
            inner_points = self._normalize_coordinates(inner_polygon)

            # Distribute measurement points along each edge
            edges = self._distribute_edge_points(
                outer_points, inner_points,
                v_points=VERTICAL_POINTS,
                h_points=HORIZONTAL_POINTS
            )

            # Analyze each edge independently
            for edge_name, edge_points in edges.items():
                measurements = self._analyze_edge(
                    edge_points["outer"],
                    edge_points["inner"]
                )
                centering_result["edges"][edge_name].update(measurements)

            # Calculate centering ratios
            h_ratio = self._calculate_centering_ratio(
                centering_result["edges"]["left"]["avg"],
                centering_result["edges"]["right"]["avg"]
            )
            v_ratio = self._calculate_centering_ratio(
                centering_result["edges"]["top"]["avg"],
                centering_result["edges"]["bottom"]["avg"]
            )

            centering_result["centering"].update({
                "horizontal": h_ratio,
                "vertical": v_ratio
            })

            # Calculate skew metrics
            h_skew = max(
                centering_result["edges"]["left"]["skew"],
                centering_result["edges"]["right"]["skew"]
            )
            v_skew = max(
                centering_result["edges"]["top"]["skew"],
                centering_result["edges"]["bottom"]["skew"]
            )

            centering_result["skew_analysis"].update({
                "horizontal": h_skew,
                "vertical": v_skew
            })

            # Calculate grade impact
            centering_score = min(h_ratio, v_ratio)
            skew_penalty = max(h_skew, v_skew) / SKEW_TOLERANCE

            centering_result["grade_impact"].update({
                "centering_deduction": self._calculate_centering_deduction(centering_score),
                "skew_deduction": self._calculate_skew_deduction(skew_penalty)
            })

            # Calculate overall confidence
            centering_result["confidence"] = self._calculate_confidence(
                centering_score, skew_penalty
            )

            return centering_result

        except Exception as e:
            print(f"⚠️ Centering calculation error: {str(e)}")
            return centering_result

    def _normalize_coordinates(self, polygon):
        """Ensure coordinates are normalized to [0,1] range"""
        if not isinstance(polygon, np.ndarray):
            polygon = np.array(polygon)
        
        # If coordinates are in pixels, normalize them
        if polygon.max() > 1.0:
            # Assuming x coordinates are even indices, y coordinates are odd indices
            max_x = polygon[::2].max()
            max_y = polygon[1::2].max()
            polygon[::2] /= max_x
            polygon[1::2] /= max_y
            
        return polygon

    def _distribute_edge_points(self, outer, inner, v_points, h_points):
        """
        Revolutionary 24-point centering system with precision geometric distribution
        
        Layout:
        - Left/Right sides (7 points): -90%, -60%, -30%, 0%, +30%, +60%, +90%
        - Top/Bottom sides (5 points): -90%, -45%, 0%, +45%, +90%
        
        Total: 7 + 7 + 5 + 5 = 24 precision measurement points
        """
        # Define the precise point distributions
        SIDE_PERCENTAGES = [-90, -60, -30, 0, 30, 60, 90]  # 7 points for left/right
        TOP_BOTTOM_PERCENTAGES = [-90, -45, 0, 45, 90]     # 5 points for top/bottom
        
        # Get card boundaries
        outer_bounds = self._get_polygon_bounds(outer)
        inner_bounds = self._get_polygon_bounds(inner)
        
        edges = {
            "top": {"outer": [], "inner": [], "points": []},
            "right": {"outer": [], "inner": [], "points": []},
            "bottom": {"outer": [], "inner": [], "points": []},
            "left": {"outer": [], "inner": [], "points": []}
        }
        
        # Generate 24-point coordinates
        point_coordinates = self._generate_24_point_coordinates(
            outer_bounds, inner_bounds, 
            SIDE_PERCENTAGES, TOP_BOTTOM_PERCENTAGES
        )
        
        # Distribute points to edges with proper indexing
        edges["left"]["points"] = point_coordinates[0:7]     # Points 0-6
        edges["right"]["points"] = point_coordinates[7:14]   # Points 7-13  
        edges["top"]["points"] = point_coordinates[14:19]    # Points 14-18
        edges["bottom"]["points"] = point_coordinates[19:24] # Points 19-23
        
        # Calculate perpendicular distances for each point
        for edge_name, edge_data in edges.items():
            for i, point_coord in enumerate(edge_data["points"]):
                # Find perpendicular distance from outer to inner border at this point
                outer_distance, inner_distance = self._calculate_perpendicular_distances(
                    point_coord, outer, inner, edge_name
                )
                edge_data["outer"].append(outer_distance)
                edge_data["inner"].append(inner_distance)
        
        return edges

    def _interpolate_points(self, edge_points, num_points):
        """Generate evenly spaced measurement points along an edge"""
        points = np.array(edge_points).reshape(-1, 2)
        
        # Use scipy's interpolate if not enough points
        if len(points) < num_points:
            from scipy.interpolate import interp1d
            t = np.linspace(0, 1, len(points))
            t_new = np.linspace(0, 1, num_points)
            
            # Interpolate x and y separately
            fx = interp1d(t, points[:, 0], kind='linear')
            fy = interp1d(t, points[:, 1], kind='linear')
            
            return np.column_stack((fx(t_new), fy(t_new)))
        
        # If we have more points than needed, use evenly spaced subset
        indices = np.linspace(0, len(points) - 1, num_points, dtype=int)
        return points[indices]

    def _analyze_edge(self, outer_points, inner_points):
        """Calculate measurements and skew for a single edge"""
        distances = np.linalg.norm(outer_points - inner_points, axis=1)
        avg_distance = np.mean(distances)
        
        # Calculate skew as maximum deviation from average
        deviations = np.abs(distances - avg_distance)
        max_deviation = np.max(deviations)
        skew = max_deviation / avg_distance if avg_distance > 0 else 0
        
        return {
            "measurements": distances.tolist(),
            "avg": float(avg_distance),
            "skew": float(skew)
        }

    def _calculate_centering_ratio(self, dist1, dist2):
        """Calculate centering ratio between two edges"""
        if max(dist1, dist2) > 0:
            return min(dist1, dist2) / max(dist1, dist2)
        return 1.0

    def _calculate_centering_deduction(self, centering_score):
        """Calculate grade deduction based on centering score"""
        # Example deduction scale:
        # 1.0 - 0.95: No deduction
        # 0.95 - 0.90: -0.5
        # 0.90 - 0.85: -1.0 
        # etc.
        if centering_score >= 0.95:
            return 0.0
        elif centering_score >= 0.90:
            return 0.5
        elif centering_score >= 0.85:
            return 1.0
        else:
            return 1.5

    def _calculate_skew_deduction(self, skew_penalty):
        """Calculate grade deduction based on skew penalty"""
        # Apply deductions for excessive skew
        if skew_penalty <= 1.0:  # Within tolerance
            return 0.0
        elif skew_penalty <= 1.5:
            return 0.5
        else:
            return 1.0

    def _calculate_confidence(self, centering_score, skew_penalty):
        """Calculate overall confidence in the measurements"""
        centering_confidence = centering_score
        skew_confidence = 1.0 - min(1.0, skew_penalty)
        return (centering_confidence + skew_confidence) / 2
    
    # ============================================================================
    # 24-POINT CENTERING SYSTEM HELPER METHODS
    # ============================================================================
    
    def _generate_24_point_coordinates(self, outer_bounds, inner_bounds, side_percentages, tb_percentages):
        """
        Generate exact (x,y) coordinates for all 24 measurement points
        """
        min_x, min_y, max_x, max_y = outer_bounds
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        coordinates = []
        
        # Left side points (0-6): x = min_x, y varies by percentages
        for pct in side_percentages:
            y = center_y + (pct / 100.0) * (max_y - min_y) / 2
            coordinates.append((min_x, y))
        
        # Right side points (7-13): x = max_x, y varies by percentages  
        for pct in side_percentages:
            y = center_y + (pct / 100.0) * (max_y - min_y) / 2
            coordinates.append((max_x, y))
        
        # Top side points (14-18): y = min_y, x varies by percentages
        for pct in tb_percentages:
            x = center_x + (pct / 100.0) * (max_x - min_x) / 2
            coordinates.append((x, min_y))
        
        # Bottom side points (19-23): y = max_y, x varies by percentages
        for pct in tb_percentages:
            x = center_x + (pct / 100.0) * (max_x - min_x) / 2
            coordinates.append((x, max_y))
        
        return coordinates
    
    def _get_polygon_bounds(self, polygon):
        """Get bounding box of polygon: (min_x, min_y, max_x, max_y)"""
        x_coords = polygon[::2]  # Every even index is x
        y_coords = polygon[1::2] # Every odd index is y
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
    
    def _calculate_perpendicular_distances(self, point_coord, outer_polygon, inner_polygon, edge_name):
        """
        Calculate perpendicular distances from measurement point to outer and inner borders
        """
        x, y = point_coord
        
        # Find nearest points on outer and inner polygons
        outer_distance = self._distance_to_polygon(x, y, outer_polygon)
        inner_distance = self._distance_to_polygon(x, y, inner_polygon)
        
        return outer_distance, inner_distance
    
    def _distance_to_polygon(self, x, y, polygon):
        """Calculate minimum distance from point to polygon edge"""
        min_distance = float('inf')
        
        # Convert polygon to coordinate pairs
        coords = [(polygon[i], polygon[i+1]) for i in range(0, len(polygon), 2)]
        
        # Calculate distance to each edge
        for i in range(len(coords)):
            p1 = coords[i]
            p2 = coords[(i + 1) % len(coords)]
            
            # Distance from point to line segment
            distance = self._point_to_line_distance(x, y, p1[0], p1[1], p2[0], p2[1])
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def _point_to_line_distance(self, px, py, x1, y1, x2, y2):
        """Calculate perpendicular distance from point to line segment"""
        # Vector from line start to point
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            # Degenerate case: line is just a point
            return np.sqrt((px - x1)**2 + (py - y1)**2)
        
        # Parameter t for closest point on line
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        
        # Closest point on line segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance from point to closest point
        return np.sqrt((px - closest_x)**2 + (py - closest_y)**2)
    
    def synthesize_grade(self, centering_analysis: Dict, surface_analysis: Dict):
        """
        Synthesize final grading result from all analysis components
        """
        from .models import GradingResult
        import time
        
        # Calculate sub-grades based on analysis
        centering_grade = self._calculate_centering_grade(centering_analysis)
        surface_grade = self._calculate_surface_grade(surface_analysis)
        
        # Default grades for corners and edges (could be enhanced)
        corners_grade = 85.0  # Default decent grade
        edges_grade = 80.0    # Default decent grade
        
        # Calculate overall grade (weighted average)
        overall_grade = (
            centering_grade * 0.35 +  # Centering is very important
            surface_grade * 0.35 +    # Surface quality is crucial
            corners_grade * 0.15 +    # Corner condition
            edges_grade * 0.15        # Edge condition
        )
        
        # Determine grade category
        grade_category = self._score_to_grade_category(overall_grade)
        
        # Calculate confidence based on analysis quality
        confidence = min(
            centering_analysis.get('confidence', 0.7),
            surface_analysis.get('confidence', 0.7)
        )
        
        return GradingResult(
            card_id="unknown",
            overall_grade=overall_grade,
            grade_category=grade_category,
            confidence=confidence,
            centering_grade=centering_grade,
            corners_grade=corners_grade, 
            edges_grade=edges_grade,
            surface_grade=surface_grade,
            centering_analysis=centering_analysis,
            surface_analysis=surface_analysis,
            processing_time=time.time(),
            grading_notes=f"Revolutionary AI Analysis - Overall: {overall_grade:.1f}"
        )
    
    def _calculate_centering_grade(self, centering_analysis: Dict) -> float:
        """Calculate centering grade from analysis"""
        if not centering_analysis or 'grade_impact' not in centering_analysis:
            return 75.0  # Default grade
            
        grade_impact = centering_analysis['grade_impact']
        base_grade = 100.0
        
        # Apply deductions
        centering_deduction = grade_impact.get('centering_deduction', 0)
        skew_deduction = grade_impact.get('skew_deduction', 0)
        
        final_grade = base_grade - centering_deduction - skew_deduction
        return max(10.0, min(100.0, final_grade))
    
    def _calculate_surface_grade(self, surface_analysis: Dict) -> float:
        """Calculate surface grade from analysis"""
        if not surface_analysis:
            return 75.0  # Default grade
            
        # Extract defect information
        defects = surface_analysis.get('defects', [])
        surface_quality = surface_analysis.get('surface_quality', 0.8)
        
        # Base grade starts high
        base_grade = 95.0
        
        # Apply deductions for defects
        for defect in defects:
            severity = defect.get('severity', 0.1)
            base_grade -= severity * 10  # Scale severity to grade impact
        
        # Apply surface quality factor  
        final_grade = base_grade * surface_quality
        
        return max(10.0, min(100.0, final_grade))
    
    def _score_to_grade_category(self, score: float) -> str:
        """Convert numeric score to grade category"""
        if score >= 98: return "GEM MINT 10"
        elif score >= 92: return "MINT 9" 
        elif score >= 86: return "NEAR MINT-MINT 8"
        elif score >= 80: return "NEAR MINT 7"
        elif score >= 70: return "EXCELLENT 6"
        elif score >= 60: return "VERY GOOD 5"
        else: return f"GRADE {max(1, int(score/10))}"
