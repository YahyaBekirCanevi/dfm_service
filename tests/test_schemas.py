import pytest
from app.models.schemas import (
    GeometricReference, FaceData, EdgeData, VertexData, 
    GeometryIndex, DFMFeedback, AnalysisResponse, BoundingBox, Features
)

def test_geometric_reference():
    ref = GeometricReference(type="face", id="f1")
    assert ref.type == "face"
    assert ref.id == "f1"

def test_face_data():
    face = FaceData(area=100.0, normal=[0, 0, 1], vertices=["v1", "v2"])
    assert face.area == 100.0
    assert face.normal == [0, 0, 1]

def test_dfm_feedback():
    feedback = DFMFeedback(
        rule_id="RULE_01",
        severity="high",
        message="Test error",
        geometric_references=[GeometricReference(type="face", id="f1")],
        metadata={"val": 10.5}
    )
    assert feedback.rule_id == "RULE_01"
    assert len(feedback.geometric_references) == 1
    assert feedback.metadata["val"] == 10.5

def test_geometry_index():
    index = GeometryIndex(
        faces={"f1": FaceData(area=50.0, normal=[1, 0, 0], vertices=[])}
    )
    assert "f1" in index.faces
    assert index.faces["f1"].area == 50.0

def test_analysis_response():
    # Minimal valid object check
    bbox = BoundingBox(min=[0,0,0], max=[10,10,10], center=[5,5,5], dimensions=[10,10,10])
    features = Features(holes=[], panel_angles=[], min_wall_thickness={"thickness": 0, "faces": []}, internal_corners=[])
    geo_index = GeometryIndex()
    
    response = AnalysisResponse(
        status="success",
        units="mm",
        bounding_box=bbox,
        geometry_index=geo_index,
        features=features,
        dfm_feedback=[]
    )
    assert response.status == "success"
    assert response.units == "mm"
