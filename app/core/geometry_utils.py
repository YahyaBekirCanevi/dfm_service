import os
from typing import Tuple, Optional
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.StlAPI import StlAPI_Reader
try:
    from OCC.Core.RWObj import RWObj_Reader
    OBJ_SUPPORTED = True
except ImportError:
    OBJ_SUPPORTED = False

class GeometryEngine:
    def __init__(self):
        self.shape: Optional[TopoDS_Shape] = None
        self.units: str = "mm"

    def load_step(self, file_path: str) -> bool:
        """Loads a STEP file and returns success status."""
        if not os.path.exists(file_path):
            return False

        reader = STEPControl_Reader()
        status = reader.ReadFile(file_path)

        if status == IFSelect_RetDone:
            reader.TransferRoots()
            self.shape = reader.OneShape()
            return True
        return False

    def load_stl(self, file_path: str) -> bool:
        """Loads an STL file and returns success status."""
        if not os.path.exists(file_path):
            return False

        reader = StlAPI_Reader()
        self.shape = TopoDS_Shape()
        status = reader.Read(self.shape, file_path)
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
        # Defaulting to mm for v1 as per PRD normalization requirement
        return "mm"
