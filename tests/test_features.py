import pytest
from app.core.feature_extraction import FeatureExtractor
from app.core.geometry_utils import TopologyIndexer

try:
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax1, gp_Ax2
    OCC_AVAILABLE = True
except ImportError:
    OCC_AVAILABLE = False

@pytest.mark.skipif(not OCC_AVAILABLE, reason="pythonocc-core not installed")
def test_extract_holes():
    # Box with a through hole
    box = BRepPrimAPI_MakeBox(50.0, 50.0, 50.0).Shape()
    # Hole radius 5, depth 50
    cylinder = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(25, 25, 50), gp_Dir(0, 0, -1)), 5.0, 50.0).Shape()
    shape = BRepAlgoAPI_Cut(box, cylinder).Shape()
    
    indexer = TopologyIndexer(shape)
    extractor = FeatureExtractor(shape, indexer)
    holes = extractor.extract_holes()
    
    assert len(holes) == 1
    hole = holes[0]
    assert hole["diameter"] == pytest.approx(10.0)
    # Through hole depth should be approximately box height
    assert hole["depth"] >= 50.0 
    assert len(hole["faces"]) > 0

@pytest.mark.skipif(not OCC_AVAILABLE, reason="pythonocc-core not installed")
def test_calculate_min_wall_thickness():
    # Two pockets separated by 1mm
    box = BRepPrimAPI_MakeBox(50.0, 50.0, 20.0).Shape()
    # Pockets at x=5 to 24.5 and x=25.5 to 45
    p1 = BRepPrimAPI_MakeBox(gp_Pnt(5, 5, 5), gp_Pnt(24.5, 45, 21)).Shape()
    p2 = BRepPrimAPI_MakeBox(gp_Pnt(25.5, 5, 5), gp_Pnt(45, 45, 21)).Shape()
    
    s1 = BRepAlgoAPI_Cut(box, p1).Shape()
    shape = BRepAlgoAPI_Cut(s1, p2).Shape()
    
    indexer = TopologyIndexer(shape)
    extractor = FeatureExtractor(shape, indexer)
    # Use exact features method
    all_f = extractor.extract_all_features()
    thickness = all_f["min_wall_thickness"]
    
    assert thickness["thickness"] > 0
    assert thickness["thickness"] == pytest.approx(1.0, abs=1e-2)
    assert len(thickness["faces"]) == 2
