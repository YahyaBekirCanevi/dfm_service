from typing import List, Dict, Any
from abc import ABC, abstractmethod
from ..models.schemas import DFMFeedback

class DFMRule(ABC):
    @abstractmethod
    def evaluate(self, features: Dict[str, Any]) -> List[DFMFeedback]:
        pass

class HoleDepthRatioRule(DFMRule):
    def evaluate(self, features: Dict[str, Any]) -> List[DFMFeedback]:
        feedback = []
        for hole in features.get("holes", []):
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

class MinHoleDiameterRule(DFMRule):
    def evaluate(self, features: Dict[str, Any]) -> List[DFMFeedback]:
        feedback = []
        for hole in features.get("holes", []):
            diameter = hole.get("diameter", 0)
            if diameter < 2.0:
                feedback.append(DFMFeedback(
                    rule_id="CNC_MIN_HOLE_DIAMETER",
                    severity="medium",
                    message=f"Hole {hole['id']} diameter ({diameter:.2f}mm) is below recommended minimum (2mm).",
                    feature_id=hole["id"]
                ))
        return feedback

class PanelAngleRule(DFMRule):
    def evaluate(self, features: Dict[str, Any]) -> List[DFMFeedback]:
        feedback = []
        for i, angle in enumerate(features.get("panel_angles", [])):
            if angle > 90.5: # 90 degrees plus slight tolerance
                feedback.append(DFMFeedback(
                    rule_id="CNC_PANEL_ANGLE",
                    severity="medium",
                    message=f"Panel junction {i+1} has an angle of {angle:.1f} degrees, which exceeds the 90-degree limit for standard setups.",
                ))
        return feedback

class MinWallThicknessRule(DFMRule):
    def evaluate(self, features: Dict[str, Any]) -> List[DFMFeedback]:
        feedback = []
        thickness = features.get("min_wall_thickness", 0.0)
        if 0 < thickness < 2.0:
            feedback.append(DFMFeedback(
                rule_id="CNC_MIN_WALL_THICKNESS",
                severity="high",
                message=f"Minimum wall thickness detected ({thickness:.2f}mm) is below the recommended 2mm for structural integrity.",
            ))
        return feedback

class SharpInternalCornerRule(DFMRule):
    def evaluate(self, features: Dict[str, Any]) -> List[DFMFeedback]:
        # Placeholder for complex logic
        return []

class DFMRulesEngine:
    def __init__(self):
        self.rules: List[DFMRule] = [
            HoleDepthRatioRule(),
            MinHoleDiameterRule(),
            PanelAngleRule(),
            MinWallThicknessRule(),
            SharpInternalCornerRule()
        ]

    def evaluate_all(self, features: Dict[str, Any]) -> List[DFMFeedback]:
        all_feedback = []
        for rule in self.rules:
            all_feedback.extend(rule.evaluate(features))
        return all_feedback
