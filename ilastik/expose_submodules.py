import os
import sys

def expose_submodules( submodule_dir ):
    walker = os.walk(submodule_dir, followlinks=True)
    try:
        path, dirnames, filenames = walker.next()
    except StopIteration:
        pass
    else:
        for dirname in dirnames:
            if dirname[0] != '.':
                sys.path.append( os.path.abspath( os.path.join(path, dirname) ) )
            
