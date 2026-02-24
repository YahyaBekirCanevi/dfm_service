from app.main import app
from app.models.schemas import AnalysisResponse
from app.core.geometry_utils import GeometryEngine
from app.core.feature_extraction import FeatureExtractor
from app.core.dfm_rules import DFMRulesEngine

print("All imports successful.")

# Basic schema validation check
try:
    dummy_response = {
        "status": "success",
        "units": "mm",
        "bounding_box": {"x": 10, "y": 10, "z": 10},
        "geometry_index": {"solids": {}, "faces": {}, "edges": {}, "vertices": {}},
        "features": {"holes": [], "min_wall_thickness": 0.0, "internal_corners": []},
        "dfm_feedback": []
    }
    AnalysisResponse(**dummy_response)
    print("Schema validation successful.")
except Exception as e:
    print(f"Schema validation failed: {e}")
