from typing import List, Dict, Any, Tuple
from enum import Enum
from OCC.Core.TopoDS import TopoDS_Shape, topods
from OCC.Core.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCC.Core.TopExp import topexp_MapShapesAndAncestors, TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCC.Core.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.gp import gp_Dir, gp_Ax1
from OCC.Core.BRepGProp import brepgprop_SurfaceProperties
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
import math

class FeatureType(str, Enum):
    HOLE = "hole"
    PLANAR_FACE = "planar_face"
    INTERNAL_CORNER = "internal_corner"

class GeometryFeature:
    def __init__(self, feature_id: str, feature_type: FeatureType):
        self.id = feature_id
        self.type = feature_type

class HoleFeature(GeometryFeature):
    def __init__(self, feature_id: str, diameter: float, depth: float, axis: gp_Ax1, hole_type: str = "blind"):
        super().__init__(feature_id, FeatureType.HOLE)
        self.diameter = diameter
        self.depth = depth
        self.axis = axis
        self.hole_type = hole_type # "blind", "through", "countersink", "counterbore"
        self.faces: List[str] = []
        self.sub_features: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.hole_type,
            "diameter": self.diameter,
            "depth": self.depth,
            "axis": [self.axis.Direction().X(), self.axis.Direction().Y(), self.axis.Direction().Z()],
            "faces": self.faces,
            "sub_features": self.sub_features
        }

class FeatureExtractor:
    def __init__(self, shape: TopoDS_Shape, indexer: Any = None):
        self.shape = shape
        self.indexer = indexer

    def extract_holes(self) -> List[Dict[str, Any]]:
        """Identifies coaxial cylindrical faces and classifies complex holes."""
        cylindrical_features = []
        explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
        
        while explorer.More():
            face = explorer.Current()
            surf = BRepAdaptor_Surface(face)
            
            if surf.GetType() == GeomAbs_Cylinder:
                cylinder = surf.Cylinder()
                cylindrical_features.append({
                    "face": face,
                    "face_id": self.indexer.get_id(face) if self.indexer else "unknown",
                    "radius": cylinder.Radius(),
                    "axis": cylinder.Axis(),
                    "location": cylinder.Location(),
                    "u_bounds": (surf.FirstUParameter(), surf.LastUParameter()),
                    "v_bounds": (surf.FirstVParameter(), surf.LastVParameter())
                })
            explorer.Next()

        # Group by axis
        grouped_holes: List[HoleFeature] = []
        for feat in cylindrical_features:
            found_group = False
            feat_axis = feat["axis"]
            
            for group in grouped_holes:
                # Check if axes are collinear
                if group.axis.IsCoaxial(feat_axis, 1e-4, 1e-4):
                    # Add as sub-feature
                    group.sub_features.append({
                        "diameter": feat["radius"] * 2,
                        "depth": abs(feat["v_bounds"][1] - feat["v_bounds"][0]),
                        "radius": feat["radius"],
                        "face_id": feat["face_id"]
                    })
                    if feat["face_id"] not in group.faces:
                        group.faces.append(feat["face_id"])
                        
                    # Update main diameter to the smallest one (likely the drill diameter)
                    if feat["radius"] * 2 < group.diameter:
                        group.diameter = feat["radius"] * 2
                    group.depth += abs(feat["v_bounds"][1] - feat["v_bounds"][0])
                    found_group = True
                    break
            
            if not found_group:
                new_hole = HoleFeature(
                    feature_id=f"hole_{len(grouped_holes)+1}",
                    diameter=feat["radius"] * 2,
                    depth=abs(feat["v_bounds"][1] - feat["v_bounds"][0]),
                    axis=feat_axis
                )
                new_hole.faces.append(feat["face_id"])
                new_hole.sub_features.append({
                    "diameter": feat["radius"] * 2,
                    "depth": abs(feat["v_bounds"][1] - feat["v_bounds"][0]),
                    "radius": feat["radius"],
                    "face_id": feat["face_id"]
                })
                grouped_holes.append(new_hole)

        # Refine hole types
        for hole in grouped_holes:
            if len(hole.sub_features) > 1:
                radii = sorted([s["radius"] for s in hole.sub_features])
                if radii[0] < radii[-1]:
                    hole.hole_type = "counterbore" if len(hole.sub_features) == 2 else "complex"
            
            if self._is_through_hole(hole):
                hole.hole_type = "through"

        return [h.to_dict() for h in grouped_holes]

    def _is_through_hole(self, hole: HoleFeature) -> bool:
        dx, dy, dz = self._get_bbox_dims()
        axis_dir = hole.axis.Direction()
        dim_along_axis = abs(axis_dir.X() * dx) + abs(axis_dir.Y() * dy) + abs(axis_dir.Z() * dz)
        if hole.depth > 0.9 * dim_along_axis:
            return True
        return False

    def _get_bbox_dims(self) -> Tuple[float, float, float]:
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib_Add
        bbox = Bnd_Box()
        brepbndlib_Add(self.shape, bbox)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
        return abs(xmax - xmin), abs(ymax - ymin), abs(zmax - zmin)

    def extract_internal_corners(self) -> List[Dict[str, Any]]:
        """Identifies sharp internal corners that are hard to machine."""
        internal_corners = []
        # In PRD v2, we should at least returned localized edges if possible.
        # Placeholder implementation for now as per v1, but returning empty list for safety.
        return internal_corners

    def extract_all_features(self) -> Dict[str, Any]:
        """Orchestrates all extraction logic."""
        return {
            "holes": self.extract_holes(),
            "panel_angles": self.extract_panel_angles(),
            "min_wall_thickness": self.calculate_min_wall_thickness(),
            "internal_corners": self.extract_internal_corners()
        }

    def extract_planar_faces(self) -> List[Dict[str, Any]]:
        """Identifies planar faces and calculates their surface area."""
        planar_faces = []
        explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
        
        while explorer.More():
            face = explorer.Current()
            surf = BRepAdaptor_Surface(face)
            
            if surf.GetType() == GeomAbs_Plane:
                from OCC.Core.TopAbs import TopAbs_REVERSED
                props = GProp_GProps()
                brepgprop_SurfaceProperties(face, props)
                area = props.Mass()
                
                # Get geometric normal
                gp_norm = surf.Plane().Axis().Direction()
                # Adjust for face orientation
                if face.Orientation() == TopAbs_REVERSED:
                    gp_norm.Reverse()
                
                planar_faces.append({
                    "face": face,
                    "face_id": self.indexer.get_id(face) if self.indexer else "unknown",
                    "area": area,
                    "normal": [gp_norm.X(), gp_norm.Y(), gp_norm.Z()]
                })
            explorer.Next()
        
        planar_faces.sort(key=lambda x: x["area"], reverse=True)
        return planar_faces

    def calculate_min_wall_thickness(self) -> Dict[str, Any]:
        """Estimates minimum wall thickness and returns localized faces."""
        planar_faces = self.extract_planar_faces()
        min_thickness = float('inf')
        affected_faces = []
        
        for i in range(len(planar_faces)):
            for j in range(i + 1, len(planar_faces)):
                f1 = planar_faces[i]
                f2 = planar_faces[j]
                
                n1 = gp_Dir(f1["normal"][0], f1["normal"][1], f1["normal"][2])
                n2 = gp_Dir(f2["normal"][0], f2["normal"][1], f2["normal"][2])
                
                dot = n1.Dot(n2)
                if dot < -0.99:
                    dist_engine = BRepExtrema_DistShapeShape(f1["face"], f2["face"])
                    if dist_engine.IsDone():
                        dist = dist_engine.Value()
                        if dist > 1e-6 and dist < min_thickness:
                            min_thickness = dist
                            affected_faces = [f1["face_id"], f2["face_id"]]
                            
        return {
            "thickness": min_thickness if min_thickness != float('inf') else 0.0,
            "faces": affected_faces
        }

    def extract_panel_angles(self) -> List[Dict[str, Any]]:
        """Calculates angles between adjacent planar faces."""
        angles = []
        edge_face_map = TopTools_IndexedDataMapOfShapeListOfShape()
        topexp_MapShapesAndAncestors(self.shape, TopAbs_EDGE, TopAbs_FACE, edge_face_map)
        
        processed_pairs = set()
        num_items = 0
        try: num_items = edge_face_map.Extent()
        except: pass
        
        for i in range(1, num_items + 1):
            faces_list = edge_face_map.FindFromIndex(i)
            num_faces = 0
            try: num_faces = faces_list.Extent()
            except: pass
            
            if num_faces == 2:
                f1 = topods.Face(faces_list.First())
                f2 = topods.Face(faces_list.Last())
                
                def get_shape_hash(shape):
                    try: return shape.HashCode(10000000)
                    except: return hash(shape)
                
                pair = tuple(sorted((get_shape_hash(f1), get_shape_hash(f2))))
                if pair not in processed_pairs:
                    processed_pairs.add(pair)
                    s1 = BRepAdaptor_Surface(f1)
                    s2 = BRepAdaptor_Surface(f2)
                    
                    if s1.GetType() == GeomAbs_Plane and s2.GetType() == GeomAbs_Plane:
                        n1 = s1.Plane().Axis().Direction()
                        n2 = s2.Plane().Axis().Direction()
                        dot = abs(n1.Dot(n2))
                        if dot < 0.999:
                            angle_rad = n1.Angle(n2)
                            angle_deg = math.degrees(angle_rad)
                            angles.append({
                                "angle": angle_deg,
                                "faces": [
                                    self.indexer.get_id(f1) if self.indexer else "unknown",
                                    self.indexer.get_id(f2) if self.indexer else "unknown"
                                ]
                            })
        return angles
