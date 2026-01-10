import os
from typing import Tuple, Optional
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.Interface import Interface_Static

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
            # Check for units
            # In pythonocc, units are usually mm by default or handled by the kernel.
            # We can force mm if needed or detect.
            # For simplicity in v1, we assume the reader handles the conversion or we report what's there.
            reader.TransferRoots()
            self.shape = reader.OneShape()
            return True
        return False

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
