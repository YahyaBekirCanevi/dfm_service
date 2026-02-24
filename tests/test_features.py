import pytest
from app.core.feature_extraction import FeatureExtractor
from app.core.geometry_utils import TopologyIndexer

try:
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax1
    OCC_AVAILABLE = True
except ImportError:
    OCC_AVAILABLE = False

@pytest.mark.skipif(not OCC_AVAILABLE, reason="pythonocc-core not installed")
def test_extract_holes():
    # Box with a through hole
    box = BRepPrimAPI_MakeBox(50.0, 50.0, 50.0).Shape()
    # Hole radius 5, depth 50
    cylinder = BRepPrimAPI_MakeCylinder(gp_Ax1(gp_Pnt(25, 25, 50), gp_Dir(0, 0, -1)), 5.0, 50.0).Shape()
    shape = BRepAlgoAPI_Cut(box, cylinder).Shape()
    
    indexer = TopologyIndexer(shape)
    extractor = FeatureExtractor(shape, indexer)
    features = extractor.extract_features()
    
    assert len(features["holes"]) == 1
    hole = features["holes"][0]
    assert hole["diameter"] == pytest.approx(10.0)
    assert hole["depth"] == pytest.approx(50.0)
    assert len(hole["faces"]) > 0

@pytest.mark.skipif(not OCC_AVAILABLE, reason="pythonocc-core not installed")
def test_calculate_min_wall_thickness():
    # Two pockets separated by 1mm
    box = BRepPrimAPI_MakeBox(50.0, 50.0, 20.0).Shape()
    p1 = BRepPrimAPI_MakeBox(gp_Pnt(5, 5, 5), gp_Pnt(24.5, 45, 21)).Shape()
    p2 = BRepPrimAPI_MakeBox(gp_Pnt(25.5, 5, 5), gp_Pnt(45, 45, 21)).Shape()
    
    s1 = BRepAlgoAPI_Cut(box, p1).Shape()
    shape = BRepAlgoAPI_Cut(s1, p2).Shape()
    
    indexer = TopologyIndexer(shape)
    extractor = FeatureExtractor(shape, indexer)
    thickness = extractor.calculate_min_wall_thickness()
    
    assert thickness["thickness"] == pytest.approx(1.0)
    assert len(thickness["faces"]) == 2
