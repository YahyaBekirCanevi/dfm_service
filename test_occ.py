try:
    from OCC.Core.StlAPI import StlAPI_Reader
    print("StlAPI_Reader available")
except ImportError:
    print("StlAPI_Reader NOT available")

try:
    from OCC.Core.RWObj import RWObj_Reader
    print("RWObj_Reader available")
except ImportError:
    print("RWObj_Reader NOT available")
