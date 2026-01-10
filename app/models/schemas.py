from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class BoundingBox(BaseModel):
    x: float
    y: float
    z: float

class HoleFeature(BaseModel):
    id: str
    diameter: float
    depth: float
    type: str  # "blind", "through", "counterbore", "countersink"
    axis: List[float]
    sub_features: Optional[List[Dict[str, Any]]] = None

class Features(BaseModel):
    holes: List[HoleFeature] = []
    panel_angles: List[float] = []
    min_wall_thickness: Optional[float] = None
    internal_corners: List[Dict[str, Any]] = []

class DFMFeedback(BaseModel):
    rule_id: str
    severity: str  # "low", "medium", "high"
    message: str
    feature_id: Optional[str] = None

class AnalysisResponse(BaseModel):
    status: str
    units: str
    bounding_box: BoundingBox
    features: Features
    dfm_feedback: List[DFMFeedback]
