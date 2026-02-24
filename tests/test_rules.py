import pytest
from app.core.dfm_rules import DFMRulesEngine

def test_rules_engine_logic():
    engine = DFMRulesEngine()
    
    # Mock features data
    mock_features = {
        "holes": [
            {"id": "h1", "diameter": 1.0, "depth": 5.0, "faces": ["f1"]}, # Min diameter violation
            {"id": "h2", "diameter": 5.0, "depth": 60.0, "faces": ["f2"]} # Depth ratio violation
        ],
        "panel_angles": [
            {"faces": ["f3", "f4"], "angle": 45.0} # Panel angle violation
        ],
        "min_wall_thickness": {
            "thickness": 0.5, # Min wall violation
            "faces": ["f5", "f6"]
        }
    }
    
    feedback = engine.evaluate_all(mock_features)
    
    # Map feedback by rule_id for easier checking
    results = {f.rule_id: f for f in feedback}
    
    assert "CNC_MIN_HOLE_DIAMETER" in results
    assert "CNC_HOLE_DEPTH_RATIO" in results
    assert "CNC_PANEL_ANGLE" in results
    assert "CNC_MIN_WALL_THICKNESS" in results
    
    # Check severity and localization
    assert results["CNC_MIN_WALL_THICKNESS"].severity == "high"
    assert "f5" in [ref.id for ref in results["CNC_MIN_WALL_THICKNESS"].geometric_references]
    assert results["CNC_HOLE_DEPTH_RATIO"].metadata["ratio"] == 12.0

def test_no_violations():
    engine = DFMRulesEngine()
    mock_features = {
        "holes": [{"id": "h1", "diameter": 10.0, "depth": 20.0, "faces": ["f1"]}],
        "panel_angles": [{"faces": ["f2", "f3"], "angle": 120.0}],
        "min_wall_thickness": {"thickness": 5.0, "faces": ["f4", "f5"]}
    }
    feedback = engine.evaluate_all(mock_features)
    assert len(feedback) == 0
