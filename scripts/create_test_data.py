from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.Interface import Interface_Static
from OCC.Core.IFSelect import IFSelect_RetDone

def create_test_step(filename: str):
    # Create a box (100x100x40)
    box = BRepPrimAPI_MakeBox(100.0, 100.0, 40.0).Shape()
    
    # Create a cylinder for a hole (radius 3, height 40)
    # This will be a through hole
    cylinder = BRepPrimAPI_MakeCylinder(3.0, 40.0).Shape()
    
    # Cut the hole out of the box
    cut_op = BRepAlgoAPI_Cut(box, cylinder)
    shape = cut_op.Shape()
    
    # Write to STEP
    writer = STEPControl_Writer()
    Interface_Static.SetCVal("write.step.schema", "AP203")
    status = writer.Transfer(shape, STEPControl_AsIs)
    
    if status == IFSelect_RetDone:
        writer.Write(filename)
        print(f"Test STEP file created: {filename}")
    else:
        print("Failed to create test STEP file.")

if __name__ == "__main__":
    create_test_step("test_part.step")
