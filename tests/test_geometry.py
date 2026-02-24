import pytest
import os
from app.core.geometry_utils import TopologyIndexer
# Note: OCC might not be available in all test environments, so we might need to skip if import fails
try:
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
    OCC_AVAILABLE = True
except ImportError:
    OCC_AVAILABLE = False

@pytest.mark.skipif(not OCC_AVAILABLE, reason="pythonocc-core not installed")
def test_topology_indexer_stable_ids():
    # Create two identical boxes
    box1 = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()
    box2 = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()
    
    indexer1 = TopologyIndexer(box1)
    indexer2 = TopologyIndexer(box2)
    
    # Check if they have the same number of faces
    assert len(indexer1.faces) == 6
    assert len(indexer2.faces) == 6
    
    # Check if IDs are consistent across two different instances of same geometry
    # (Since it's deterministic based on topology/geometry hashes)
    ids1 = sorted(indexer1.faces.keys())
    ids2 = sorted(indexer2.faces.keys())
    
    assert ids1 == ids2
    
    # Verify properties
    face_id = ids1[0]
    face_data = indexer1.get_face_data(indexer1.faces[face_id])
    assert "area" in face_data
    assert face_data["area"] == pytest.approx(100.0)

@pytest.mark.skipif(not OCC_AVAILABLE, reason="pythonocc-core not installed")
def test_topology_indexer_hierarchy():
    box = BRepPrimAPI_MakeBox(10.0, 20.0, 30.0).Shape()
    indexer = TopologyIndexer(box)
    
    # Test face to edge mapping
    face_id = list(indexer.faces.keys())[0]
    edge_ids = indexer.get_face_edges(face_id)
    assert len(edge_ids) > 0
    for eid in edge_ids:
        assert eid in indexer.edges
