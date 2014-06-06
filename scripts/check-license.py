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
#!/usr/bin/env/python

import os
import glob

gplv2orlater = """###############################################################################
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
"""

def check_file(fname):
    if fname in ["../docs/conf.py"]:
        return
    
    #print "checking %s" % fname
    assert os.path.exists(fname)
    f = open(fname, 'r')
    lines = f.readlines()
    f.close()
    
    firstline = None
    
    if len(lines) and lines[0].startswith("#!"):
        print "shebang in %s" % fname 
        firstline = lines[0]
        c = "".join(lines[1:]) 
    elif len(lines) and "coding" in lines[0]:
        print "coding in %s" % fname
        firstline = lines[0]
        c = "".join(lines[1:]) 
    else:
        c = "".join(lines)

    if not c.startswith(gplv2orlater):
        f = open(fname, 'w')
        if firstline is not None:
            f.write(firstline)
            f.write("\n")
        f.write(gplv2orlater)
        f.write(c)
        f.close()

def check_directory(arg, dirname, name):
    for fname in sorted(glob.glob("%s/*.py" % dirname)):
        check_file(fname)

if __name__ == "__main__":
    os.path.walk("../", check_directory, "") 
