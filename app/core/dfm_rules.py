from typing import List, Dict, Any
from abc import ABC, abstractmethod
from ..models.schemas import DFMFeedback, GeometricReference

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
                ratio = depth / diameter
                feedback.append(DFMFeedback(
                    rule_id="CNC_HOLE_DEPTH_RATIO",
                    severity="high",
                    message=f"Hole {hole['id']} depth-to-diameter ratio ({ratio:.1f}) exceeds recommended limit (10).",
                    feature_id=hole["id"],
                    geometric_references=[
                        GeometricReference(type="face", id=fid) for fid in hole.get("faces", [])
                    ],
                    metadata={
                        "ratio": ratio,
                        "max_allowed": 10.0
                    }
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
                    feature_id=hole["id"],
                    geometric_references=[
                        GeometricReference(type="face", id=fid) for fid in hole.get("faces", [])
                    ],
                    metadata={
                        "diameter": diameter,
                        "min_allowed": 2.0
                    }
                ))
        return feedback

class PanelAngleRule(DFMRule):
    def evaluate(self, features: Dict[str, Any]) -> List[DFMFeedback]:
        feedback = []
        for i, entry in enumerate(features.get("panel_angles", [])):
            angle = entry.get("angle", 0)
            if angle < 90.5: # 90 degrees plus slight tolerance
                feedback.append(DFMFeedback(
                    rule_id="CNC_PANEL_ANGLE",
                    severity="medium",
                    message=f"Panel junction {i+1} has an angle of {angle:.1f} degrees, which exceeds the 90-degree limit for standard setups.",
                    geometric_references=[
                        GeometricReference(type="edge", id=entry.get("edge_id", "unknown")),
                        *[GeometricReference(type="face", id=fid) for fid in entry.get("faces", [])]
                    ],
                    metadata={
                        "angle": angle,
                        "limit": 90.0
                    }
                ))
        return feedback

class MinWallThicknessRule(DFMRule):
    def evaluate(self, features: Dict[str, Any]) -> List[DFMFeedback]:
        feedback = []
        thickness_data = features.get("min_wall_thickness", {"thickness": 0.0, "faces": []})
        thickness = thickness_data.get("thickness", 0.0)
        if 0 < thickness < 2.0:
            feedback.append(DFMFeedback(
                rule_id="CNC_MIN_WALL_THICKNESS",
                severity="high",
                message=f"Minimum wall thickness detected ({thickness:.2f}mm) is below the recommended 2mm for structural integrity.",
                geometric_references=[
                    GeometricReference(type="face", id=fid) for fid in thickness_data.get("faces", [])
                ],
                metadata={
                    "thickness": thickness,
                    "min_allowed": 2.0
                }
            ))
        return feedback

class SharpInternalCornerRule(DFMRule):
    def evaluate(self, features: Dict[str, Any]) -> List[DFMFeedback]:
        # Placeholder for complex logic (as per PRD, this is a target but v1/v2 initial set is limited)
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
