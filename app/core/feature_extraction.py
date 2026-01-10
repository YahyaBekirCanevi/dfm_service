from typing import List, Dict, Any
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Face
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.BRep import BRep_Tool
from OCC.Core.gp import gp_Dir, gp_Pnt
from OCC.Core.BRepGProp import brepgprop_SurfaceProperties
from OCC.Core.GProp import GProp_GProps

class FeatureExtractor:
    def __init__(self, shape: TopoDS_Shape):
        self.shape = shape

    def extract_holes(self) -> List[Dict[str, Any]]:
        """Identifies cylindrical faces and extracts hole data."""
        holes = []
        explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
        idx = 1
        
        processed_faces = set() # To avoid duplicate counting if needed

        while explorer.More():
            face = explorer.Current()
            surf = BRepAdaptor_Surface(face)
            
            if surf.GetType() == GeomAbs_Cylinder:
                cylinder = surf.Cylinder()
                radius = cylinder.Radius()
                axis = cylinder.Axis().Direction()
                location = cylinder.Location()
                
                # Simple depth calculation: for v1, we can use the face bounds
                # or project the face vertices onto the axis.
                # A more robust way is to find the bounds of the face in the U/V space
                # but for v1 we'll use a simplified approach.
                # Here we just get the 'height' of the cylindrical face if it's trimmed.
                u_min, u_max, v_min, v_max = surf.FirstUParameter(), surf.LastUParameter(), surf.FirstVParameter(), surf.LastVParameter()
                depth = abs(v_max - v_min) # In OpenCascade cylindrical surfaces, V usually represents the axis height
                
                holes.append({
                    "id": f"hole_{idx}",
                    "diameter": radius * 2,
                    "depth": depth,
                    "axis": [axis.X(), axis.Y(), axis.Z()],
                    "type": "blind" # Simplified for v1, through-hole check would need intersection
                })
                idx += 1
            
            explorer.Next()
        return holes

    def extract_planar_faces(self) -> List[Dict[str, Any]]:
        """Identifies planar faces and calculates their surface area."""
        planar_faces = []
        explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
        
        while explorer.More():
            face = explorer.Current()
            surf = BRepAdaptor_Surface(face)
            
            if surf.GetType() == GeomAbs_Plane:
                props = GProp_GProps()
                brepgprop_SurfaceProperties(face, props)
                area = props.Mass()
                
                planar_faces.append({
                    "area": area,
                    "normal": [surf.Plane().Axis().Direction().X(), 
                               surf.Plane().Axis().Direction().Y(), 
                               surf.Plane().Axis().Direction().Z()]
                })
            explorer.Next()
        
        # Sort by area descending to find setup candidates
        planar_faces.sort(key=lambda x: x["area"], reverse=True)
        return planar_faces
