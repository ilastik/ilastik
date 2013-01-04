#!/usr/bin/env python
import os
import vigra

# FIXME: If using a special python prefix, CMake will probably find the 
#        WRONG boost_python/vigra/python libs and headers.
#        You may have to launch cmake-gui to select the correct paths by hand.

# FIXME: On Mac, the build process produces a file called cppcontext.dylib.
#        Python apparently expects it to be named cppcontext.so.
#        Simply renaming the file seems to fix the problem.

build='build'
context='context'

def do(cmd):
    cmd= 'cd ' + build +"/ && " + cmd
    print cmd
    os.system(cmd)



if os.path.exists(build): os.system('rm -rf '+ build)
os.mkdir(build)

do('cmake ..')
do(' make ')
do ('touch __init__.py')

#if os.path.exists(os.path.join(build,context)):os.rmdir(os.path.join(build,context))
#do('mkdir context')
#do('cp -rf ../src/contextmodule/* context/.')
#do('mv *.so context/ ')


