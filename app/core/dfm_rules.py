from typing import List, Dict, Any
from ..models.schemas import DFMFeedback

class DFMRulesEngine:
    @staticmethod
    def check_hole_depth_ratio(holes: List[Dict[str, Any]]) -> List[DFMFeedback]:
        feedback = []
        for hole in holes:
            diameter = hole.get("diameter", 0)
            depth = hole.get("depth", 0)
            if diameter > 0 and (depth / diameter) > 10:
                feedback.append(DFMFeedback(
                    rule_id="CNC_HOLE_DEPTH_RATIO",
                    severity="high",
                    message=f"Hole {hole['id']} depth-to-diameter ratio ({depth/diameter:.1f}) exceeds recommended limit (10).",
                    feature_id=hole["id"]
                ))
        return feedback

    @staticmethod
    def check_min_hole_diameter(holes: List[Dict[str, Any]]) -> List[DFMFeedback]:
        feedback = []
        for hole in holes:
            diameter = hole.get("diameter", 0)
            if diameter < 2.0:
                feedback.append(DFMFeedback(
                    rule_id="CNC_MIN_HOLE_DIAMETER",
                    severity="medium",
                    message=f"Hole {hole['id']} diameter ({diameter:.2f}mm) is below recommended minimum (2mm).",
                    feature_id=hole["id"]
                ))
        return feedback

    @staticmethod
    def check_panel_angles(angles: List[float]) -> List[DFMFeedback]:
        feedback = []
        for i, angle in enumerate(angles):
            if angle <= 90.0:
                feedback.append(DFMFeedback(
                    rule_id="CNC_PANEL_ANGLE",
                    severity="medium",
                    message=f"Panel junction {i+1} has an angle of {angle:.1f} degrees, which exceeds the 90-degree limit.",
                ))
        return feedback

    @staticmethod
    def check_min_wall_thickness(thickness: float) -> List[DFMFeedback]:
        feedback = []
        if thickness > 0 and thickness < 2.0:
            feedback.append(DFMFeedback(
                rule_id="CNC_MIN_WALL_THICKNESS",
                severity="high",
                message=f"Minimum wall thickness detected ({thickness:.2f}mm) is below the required 2mm.",
            ))
        return feedback

    @staticmethod
    def check_sharp_corners(shape_data: Any) -> List[DFMFeedback]:
        # Placeholder for v1: check internal radii
        return []

    def evaluate_all(self, features: Dict[str, Any]) -> List[DFMFeedback]:
        feedback = []
        holes = features.get("holes", [])
        angles = features.get("panel_angles", [])
        wall_thickness = features.get("min_wall_thickness", 0.0)
        
        feedback.extend(self.check_hole_depth_ratio(holes))
        feedback.extend(self.check_min_hole_diameter(holes))
        feedback.extend(self.check_panel_angles(angles))
        feedback.extend(self.check_min_wall_thickness(wall_thickness))
        
        return feedback
