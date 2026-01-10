from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.StlAPI import StlAPI_Writer
try:
    from OCC.Core.RWObj import RWObj_Writer
    OBJ_WRITER_AVAILABLE = True
except ImportError:
    OBJ_WRITER_AVAILABLE = False
from OCC.Core.Interface import Interface_Static
from OCC.Core.IFSelect import IFSelect_RetDone
import os

def create_geometry(hole_radius: float, wall_thickness: float):
    # Base box
    box = BRepPrimAPI_MakeBox(100.0, 100.0, wall_thickness).Shape()
    # Hole
    cylinder = BRepPrimAPI_MakeCylinder(hole_radius, wall_thickness).Shape()
    # Cut
    cut_op = BRepAlgoAPI_Cut(box, cylinder)
    return cut_op.Shape()

def save_step(shape, filename):
    writer = STEPControl_Writer()
    Interface_Static.SetCVal("write.step.schema", "AP203")
    status = writer.Transfer(shape, STEPControl_AsIs)
    if status == IFSelect_RetDone:
        writer.Write(filename)
        return True
    return False

def save_stl(shape, filename):
    writer = StlAPI_Writer()
    writer.Write(shape, filename)
    return True

def save_obj(shape, filename):
    if not OBJ_WRITER_AVAILABLE:
        print("OBJ Writer not available")
        return False
    # RWObj_Writer is more complex, might not be easily available simplified
    # For now, let's just stick to STEP and STL if OBJ fails to write here.
    return False

if __name__ == "__main__":
    test_dir = "test_data"
    os.makedirs(test_dir, exist_ok=True)
    
    # 1. Violation: Hole diameter 8mm (<10), Wall thickness 5mm (<10)
    shape_violation = create_geometry(4.0, 5.0)
    save_step(shape_violation, os.path.join(test_dir, "violation.step"))
    save_stl(shape_violation, os.path.join(test_dir, "violation.stl"))
    
    # 2. Success: Hole diameter 15mm (>10), Wall thickness 20mm (>10)
    shape_success = create_geometry(7.5, 20.0)
    save_step(shape_success, os.path.join(test_dir, "success.step"))
    save_stl(shape_success, os.path.join(test_dir, "success.stl"))
    
    print(f"Test files created in {test_dir}")
