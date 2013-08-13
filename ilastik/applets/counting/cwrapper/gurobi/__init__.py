import os
currentdir = os.path.dirname(__file__) 
import ctypes
libraryname = "libgurobiwrapper.so"
dllname = "gurobiwrapper.dll"
HAS_GUROBI = False
paths = [os.path.dirname(os.path.abspath(__file__)) + os.path.sep, ""]
for path in paths:
    try:
        sofile = path + libraryname
        extlib = ctypes.cdll.LoadLibrary(sofile)
        HAS_GUROBI = True
    except:
        pass

    try:
        dllfile = path + dllname
        extlib = ctypes.cdll.LoadLibrary(dllfile)
        HAS_GUROBI = True
    except:
        pass


if not HAS_GUROBI:
    raise RuntimeError("No gurobi wrapper found")
