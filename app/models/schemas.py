from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class BoundingBox(BaseModel):
    x: float
    y: float
    z: float

class GeometricReference(BaseModel):
    type: str  # "face", "edge", "vertex", "solid"
    id: str

class FaceData(BaseModel):
    surface_type: str
    area: float
    centroid: List[float]
    normal: Optional[List[float]] = None

class EdgeData(BaseModel):
    curve_type: str
    length: float
    faces: List[str]
    vertices: List[str]
    radius: Optional[float] = None

class VertexData(BaseModel):
    point: List[float]

class GeometryIndex(BaseModel):
    solids: Dict[str, Dict[str, Any]] = {}
    faces: Dict[str, FaceData] = {}
    edges: Dict[str, EdgeData] = {}
    vertices: Dict[str, VertexData] = {}

class HoleFeature(BaseModel):
    id: str
    diameter: float
    depth: float
    type: str  # "blind", "through", "counterbore", "countersink"
    axis: List[float]
    faces: List[str] = []
    sub_features: Optional[List[Dict[str, Any]]] = None

class Features(BaseModel):
    holes: List[HoleFeature] = []
    min_wall_thickness: Optional[float] = None
    internal_corners: List[Dict[str, Any]] = []

class DFMFeedback(BaseModel):
    rule_id: str
    severity: str  # "low", "medium", "high"
    message: str
    feature_id: Optional[str] = None
    geometric_references: List[GeometricReference] = []
    metadata: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    status: str
    units: str
    bounding_box: BoundingBox
    geometry_index: GeometryIndex
    features: Features
    dfm_feedback: List[DFMFeedback]
