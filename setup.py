#!/usr/bin/env python
import os

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

#if os.path.exists(os.path.join(build,context)):os.rmdir(os.path.join(build,context))

do('cp -rf ../src/context .')
do('mv *.so context/ ')


