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
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.gp import gp_Dir, gp_Pnt, gp_Vec
import math

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
                normal = surf.Plane().Axis().Direction()
                
                planar_faces.append({
                    "face": face,
                    "area": area,
                    "normal": [normal.X(), normal.Y(), normal.Z()]
                })
            explorer.Next()
        
        # Sort by area descending
        planar_faces.sort(key=lambda x: x["area"], reverse=True)
        return planar_faces

    def calculate_min_wall_thickness(self) -> float:
        """Estimates minimum wall thickness using distance between opposing planar faces."""
        planar_faces = self.extract_planar_faces()
        min_thickness = float('inf')
        
        for i in range(len(planar_faces)):
            for j in range(i + 1, len(planar_faces)):
                f1 = planar_faces[i]
                f2 = planar_faces[j]
                
                n1 = gp_Dir(f1["normal"][0], f1["normal"][1], f1["normal"][2])
                n2 = gp_Dir(f2["normal"][0], f2["normal"][1], f2["normal"][2])
                
                # Check if they are nearly parallel and opposing
                dot = n1.Dot(n2)
                if dot < -0.99: # Almost opposite
                    # Calculate distance
                    dist_engine = BRepExtrema_DistShapeShape(f1["face"], f2["face"])
                    if dist_engine.IsDone():
                        dist = dist_engine.Value()
                        if dist > 1e-6 and dist < min_thickness:
                            min_thickness = dist
                            
        return min_thickness if min_thickness != float('inf') else 0.0

    def extract_panel_angles(self) -> List[float]:
        """Calculates angles between adjacent planar faces."""
        planar_faces = self.extract_planar_faces()
        angles = []
        
        # This is a simplified approach. Ideally we'd check for shared edges.
        # For v1, we'll just check all pairs of non-parallel planar faces.
        for i in range(len(planar_faces)):
            for j in range(i + 1, len(planar_faces)):
                n1 = gp_Dir(planar_faces[i]["normal"][0], planar_faces[i]["normal"][1], planar_faces[i]["normal"][2])
                n2 = gp_Dir(planar_faces[j]["normal"][0], planar_faces[j]["normal"][1], planar_faces[j]["normal"][2])
                
                dot = abs(n1.Dot(n2))
                if dot < 0.99: # Not parallel
                    angle_rad = n1.Angle(n2)
                    angle_deg = math.degrees(angle_rad)
                    # We usually want the angle between the panels themselves (internal or external)
                    # For milling, we care about the angle of the meat/void.
                    # Here we just report the angle between normals.
                    angles.append(angle_deg)
        return angles
