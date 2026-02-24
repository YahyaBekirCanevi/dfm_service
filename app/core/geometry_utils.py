import os
from typing import Tuple, Optional, Dict, List, Any
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add
from OCC.Core.TopoDS import TopoDS_Shape, topods
from OCC.Core.StlAPI import StlAPI_Reader
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_SOLID
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCC.Core.GeomAbs import GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Circle
from OCC.Core.BRepGProp import brepgprop_SurfaceProperties, brepgprop_LinearProperties
from OCC.Core.GProp import GProp_GProps
from OCC.Core.gp import gp_Pnt, gp_Dir

try:
    from OCC.Core.RWObj import RWObj_Reader
    OBJ_SUPPORTED = True
except ImportError:
    OBJ_SUPPORTED = False

class TopologyIndexer:
    """Helper class to assign deterministic IDs to topological entities."""
    def __init__(self, shape: TopoDS_Shape):
        self.shape = shape
        self.face_map: Dict[TopoDS_Shape, str] = {}
        self.edge_map: Dict[TopoDS_Shape, str] = {}
        self.vertex_map: Dict[TopoDS_Shape, str] = {}
        self.solid_map: Dict[TopoDS_Shape, str] = {}
        self._index_all()

    @property
    def faces(self): return self.face_map
    @property
    def edges(self): return self.edge_map
    @property
    def vertices(self): return self.vertex_map

    def _index_all(self):
        # Index Solids
        explorer = TopExp_Explorer(self.shape, TopAbs_SOLID)
        i = 1
        while explorer.More():
            self.solid_map[explorer.Current()] = f"solid_{i}"
            i += 1
            explorer.Next()

        # Index Faces
        explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
        i = 1
        while explorer.More():
            self.face_map[explorer.Current()] = f"face_{i}"
            i += 1
            explorer.Next()

        # Index Edges
        explorer = TopExp_Explorer(self.shape, TopAbs_EDGE)
        i = 1
        while explorer.More():
            self.edge_map[explorer.Current()] = f"edge_{i}"
            i += 1
            explorer.Next()

        # Index Vertices
        explorer = TopExp_Explorer(self.shape, TopAbs_VERTEX)
        i = 1
        while explorer.More():
            self.vertex_map[explorer.Current()] = f"vertex_{i}"
            i += 1
            explorer.Next()

    def get_id(self, shape: TopoDS_Shape) -> str:
        if shape in self.face_map: return self.face_map[shape]
        if shape in self.edge_map: return self.edge_map[shape]
        if shape in self.vertex_map: return self.vertex_map[shape]
        if shape in self.solid_map: return self.solid_map[shape]
        return "unknown"

    def get_face_edges(self, face_id: str) -> List[str]:
        """Returns a list of edge IDs belonging to the given face ID."""
        # Find the face shape by ID
        face_shape = None
        for shape, fid in self.face_map.items():
            if fid == face_id:
                face_shape = shape
                break
        
        if not face_shape:
            return []
            
        edge_ids = []
        explorer = TopExp_Explorer(face_shape, TopAbs_EDGE)
        while explorer.More():
            edge_ids.append(self.get_id(explorer.Current()))
            explorer.Next()
        return edge_ids

class GeometryEngine:
    def __init__(self):
        self.shape: Optional[TopoDS_Shape] = None
        self.units: str = "mm"
        self.indexer: Optional[TopologyIndexer] = None

    def load_step(self, file_path: str) -> bool:
        """Loads a STEP file and returns success status."""
        if not os.path.exists(file_path):
            return False

        reader = STEPControl_Reader()
        status = reader.ReadFile(file_path)

        if status == IFSelect_RetDone:
            reader.TransferRoots()
            self.shape = reader.OneShape()
            self.indexer = TopologyIndexer(self.shape)
            return True
        return False

    def load_stl(self, file_path: str) -> bool:
        """Loads an STL file and returns success status."""
        if not os.path.exists(file_path):
            return False

        reader = StlAPI_Reader()
        self.shape = TopoDS_Shape()
        status = reader.Read(self.shape, file_path)
        if status:
            self.indexer = TopologyIndexer(self.shape)
        return status

    def load_obj(self, file_path: str) -> bool:
        """Loads an OBJ file and returns success status."""
        if not OBJ_SUPPORTED:
            return False
        if not os.path.exists(file_path):
            return False

        reader = RWObj_Reader()
        if not reader.ReadFile(file_path):
            return False
        
        reader.TransferRoots()
        self.shape = reader.OneShape()
        self.indexer = TopologyIndexer(self.shape)
        return True

    def get_bounding_box(self) -> Tuple[float, float, float]:
        """Calculates the bounding box dimensions (X, Y, Z)."""
        if self.shape is None:
            return 0.0, 0.0, 0.0

        bbox = Bnd_Box()
        brepbndlib_Add(self.shape, bbox)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
        
        return abs(xmax - xmin), abs(ymax - ymin), abs(zmax - zmin)

    def get_units(self) -> str:
        return self.units

    def get_geometry_index(self) -> Dict[str, Any]:
        """Generates the geometry index as required by PRD v2."""
        if not self.indexer:
            return {"solids": {}, "faces": {}, "edges": {}, "vertices": {}}

        index = {
            "solids": {v: {} for v in self.indexer.solid_map.values()},
            "faces": {},
            "edges": {},
            "vertices": {}
        }

        # Faces
        for face, fid in self.indexer.face_map.items():
            surf = BRepAdaptor_Surface(topods.Face(face))
            stype = self._get_surface_type_name(surf.GetType())
            
            props = GProp_GProps()
            brepgprop_SurfaceProperties(face, props)
            
            centroid = props.CentreOfMass()
            
            face_data = {
                "surface_type": stype,
                "area": props.Mass(),
                "centroid": [centroid.X(), centroid.Y(), centroid.Z()]
            }
            
            if surf.GetType() == GeomAbs_Plane:
                norm = surf.Plane().Axis().Direction()
                face_data["normal"] = [norm.X(), norm.Y(), norm.Z()]
                
            index["faces"][fid] = face_data

        # Edges
        for edge_shape, eid in self.indexer.edge_map.items():
            edge = topods.Edge(edge_shape)
            curve = BRepAdaptor_Curve(edge)
            
            props = GProp_GProps()
            brepgprop_LinearProperties(edge, props)
            
            # Find adjacent faces
            adj_faces = []
            explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
            while explorer.More():
                f = explorer.Current()
                sub_exp = TopExp_Explorer(f, TopAbs_EDGE)
                while sub_exp.More():
                    if sub_exp.Current().IsSame(edge):
                        adj_faces.append(self.indexer.get_id(f))
                        break
                    sub_exp.Next()
                explorer.Next()
                
            # Find vertices
            verts = []
            sub_exp = TopExp_Explorer(edge, TopAbs_VERTEX)
            while sub_exp.More():
                verts.append(self.indexer.get_id(sub_exp.Current()))
                sub_exp.Next()

            edge_data = {
                "curve_type": self._get_curve_type_name(curve.GetType()),
                "length": props.Mass(),
                "faces": list(set(adj_faces)),
                "vertices": verts
            }
            
            if curve.GetType() == GeomAbs_Circle:
                edge_data["radius"] = curve.Circle().Radius()
                
            index["edges"][eid] = edge_data

        # Vertices
        for vert_shape, vid in self.indexer.vertex_map.items():
            pnt = topods.Vertex(vert_shape)
            gp_pnt = BRepAdaptor_Curve.Point(pnt) if False else gp_Pnt() # Placeholder logic
            # Correct vertex extraction
            from OCC.Core.BRep import BRep_Tool
            p = BRep_Tool.Pnt(topods.Vertex(vert_shape))
            index["vertices"][vid] = {"point": [p.X(), p.Y(), p.Z()]}

        return index

    def _get_surface_type_name(self, stype: int) -> str:
        mapping = {
            0: "plane", 1: "cylinder", 2: "cone", 3: "sphere", 4: "torus",
            5: "bezier", 6: "bspline", 7: "surface_of_revolution",
            8: "surface_of_extrusion", 9: "offset_surface", 10: "other"
        }
        return mapping.get(stype, "unknown")

    def _get_curve_type_name(self, ctype: int) -> str:
        mapping = {
            0: "line", 1: "circle", 2: "ellipse", 3: "hyperbola", 4: "parabola",
            5: "bezier", 6: "bspline", 7: "offset", 8: "other"
        }
        return mapping.get(ctype, "unknown")
