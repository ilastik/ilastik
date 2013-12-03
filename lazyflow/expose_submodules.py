import os
import sys

def expose_submodules( submodule_dir ):
    walker = os.walk(submodule_dir, followlinks=True)
    path, dirnames, filenames = walker.next()
    for dirname in dirnames:
        if dirname[0] != '.':
            sys.path.append( os.path.abspath( os.path.join(path, dirname) ) )
            
