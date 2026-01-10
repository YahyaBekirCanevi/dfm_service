from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax1
from OCC.Core.Interface import Interface_Static
from OCC.Core.IFSelect import IFSelect_RetDone
import os

def create_v2_test_part(filename: str):
    # 1. Base Box (100x100x40)
    box = BRepPrimAPI_MakeBox(100.0, 100.0, 40.0).Shape()
    
    # 2. Counterbore Hole at (50, 50)
    # Larger hole (diameter 20, depth 10)
    c1 = BRepPrimAPI_MakeCylinder(gp_Ax1(gp_Pnt(50, 50, 40), gp_Dir(0, 0, -1)), 10.0, 10.0).Shape()
    # Smaller hole (diameter 10, depth 40 - through)
    c2 = BRepPrimAPI_MakeCylinder(gp_Ax1(gp_Pnt(50, 50, 40), gp_Dir(0, 0, -1)), 5.0, 40.0).Shape()
    
    # Combined cut
    cut1 = BRepAlgoAPI_Cut(box, c1).Shape()
    final_shape = BRepAlgoAPI_Cut(cut1, c2).Shape()
    
    # 3. Write to STEP
    writer = STEPControl_Writer()
    Interface_Static.SetCVal("write.step.schema", "AP203")
    writer.Transfer(final_shape, STEPControl_AsIs)
    writer.Write(filename)
    print(f"V2 Test Part created: {filename}")

if __name__ == "__main__":
    test_dir = "test_data_v2"
    os.makedirs(test_dir, exist_ok=True)
    create_v2_test_part(os.path.join(test_dir, "complex_part.step"))
