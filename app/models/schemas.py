from pydantic import BaseModel, Field
from typing import List, Optional

class BoundingBox(BaseModel):
    x: float
    y: float
    z: float

class HoleFeature(BaseModel):
    id: str
    diameter: float
    depth: float
    type: str  # "blind" or "through"
    axis: List[float]

class Features(BaseModel):
    holes: List[HoleFeature] = []
    panel_angles: List[float] = []
    min_wall_thickness: Optional[float] = None

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
