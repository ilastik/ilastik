from __future__ import print_function
###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
#!/usr/bin/env/python

import os
import glob

gplv2orlater = """###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
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
        print("shebang in %s" % fname) 
        firstline = lines[0]
        c = "".join(lines[1:]) 
    elif len(lines) and "coding" in lines[0]:
        print("coding in %s" % fname)
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
