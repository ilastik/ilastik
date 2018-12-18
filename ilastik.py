#!/usr/bin/env python

###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################

import sys
import os

def _clean_paths( ilastik_dir ):
    # remove undesired paths from PYTHONPATH and add ilastik's submodules
    pythonpath = [k for k in sys.path if k.startswith(ilastik_dir)]
    for k in ['/ilastik/lazyflow', '/ilastik/volumina', '/ilastik/ilastik']:
        new_path = ilastik_dir + k.replace('/', os.path.sep)
        if os.path.isdir(new_path):
            pythonpath.append(new_path)
    sys.path = pythonpath

    if sys.platform.startswith('win'):
        # empty PATH except for gurobi and CPLEX and add ilastik's installation paths
        path_var = os.environ.get('PATH')
        if path_var is None:
            path_array = []
        else:
            path_array = path_var.split(os.pathsep)
        path = [k for k in path_array \
                   if k.count('CPLEX') > 0 or k.count('gurobi') > 0 or \
                      k.count('windows\\system32') > 0]
        for k in ['/Qt4/bin', '/Library/bin', '/python', '/bin']:
            new_path = ilastik_dir + k.replace('/', os.path.sep)
            if os.path.isdir(new_path):
                path.append(new_path)
        os.environ['PATH'] = os.pathsep.join(reversed(path))
    else:
        # clean LD_LIBRARY_PATH and add ilastik's installation paths
        # (gurobi and CPLEX are supposed to be located there as well)
        path = [k for k in os.environ['LD_LIBRARY_PATH'] if k.startswith(ilastik_dir)]
        
        for k in ['/lib']:
            path.append(ilastik_dir + k.replace('/', os.path.sep))
        os.environ['LD_LIBRARY_PATH'] = os.pathsep.join(reversed(path))

def main():
    if "--clean_paths" in sys.argv:
        this_path = os.path.dirname(__file__)
        ilastik_dir = os.path.abspath(os.path.join(this_path, "..%s.." % os.path.sep))
        _clean_paths( ilastik_dir )

    import ilastik_main
    parsed_args, workflow_cmdline_args = ilastik_main.parse_known_args()
    
    # allow to start-up by double-clicking an '.ilp' file
    if len(workflow_cmdline_args) == 1 and \
       workflow_cmdline_args[0].endswith('.ilp') and \
       parsed_args.project is None:
            parsed_args.project = workflow_cmdline_args[0]
            workflow_cmdline_args = []

    hShell = ilastik_main.main(parsed_args, workflow_cmdline_args)
    # in headless mode the headless shell is returned and its project manager still has an open project file
    hShell.closeCurrentProject()

if __name__ == "__main__":
    main()
