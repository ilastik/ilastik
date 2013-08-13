import os
currentdir = os.path.dirname(__file__) 
import ctypes
libraryname = "libcplexwrapper.so"
dllname = "cplexwrapper.dll"
HAS_CPLEX = False
paths = [os.path.dirname(os.path.abspath(__file__)) + os.path.sep, ""]
for path in paths:
    try:
        sofile = path + libraryname
        extlib = ctypes.cdll.LoadLibrary(sofile)
        HAS_CPLEX = True
    except Exception as err:
        raise err

    try:
        dllfile = path + dllname
        extlib = ctypes.cdll.LoadLibrary(dllfile)
        HAS_CPLEX = True
    except:
        pass



if not HAS_CPLEX:
    raise RuntimeError("No cplex wrapper found")
