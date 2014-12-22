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
# Setup script that uses py2app to generate a redistributable binary from an existing ilastik build.
# To run: python setup_mac.py py2app [--include-meta-repo]
import sys
from setuptools import setup, find_packages
from ilastik import __version__


# Running into recursion limit too quickly, which stops build.
sys.setrecursionlimit(1500)

APP = ['ilastik.py']
DATA_FILES = []

includes = [\
                'h5py', 'h5py.defs', 'h5py.utils', 'h5py._proxy', 'h5py._errors',
                'PyQt4.pyqtconfig', 'PyQt4.uic','PyQt4.QtCore','PyQt4.QtGui',
                'site', 'os',
                'vtk',
                'vtk.vtkCommonPythonSIP',
                'sklearn', 'sklearn.utils',
             ]

# The py2app dependency walker finds this code, which is intended only for Python3.
# Exclude it!
excludes= ['PyQt4.uic.port_v3']

# By default, cplex is excluded from the bundle.
if '--include-cplex' in sys.argv:
    sys.argv.remove('--include-cplex')
    dylib_forced_removal = []
else:
    # Since the cplex libs can't be found with macholib, the py2app dylib_excludes option doesn't work here.
    # We'll handle this manually in the custom run() function, below.
    dylib_forced_removal = ['libcplex.dylib', 'libconcert.dylib', 'libilocplex.dylib']

OPTIONS = {'argv_emulation': False, 'includes':includes, 'excludes':excludes, 'iconfile' : 'appIcon.icns', 'extra_scripts':['bin/mac_execfile.py']}

packages=find_packages(exclude=["tests", "tests.*"])
package_data={'ilastik': ['ilastik-splash.png',
                          'ilastik-splash.xcf'],
              'ilastik.applets.dataSelection': ['*.ui'],
              'ilastik.applets.labeling': ['*.ui', 'icons/*.png', 'icons/*.jpg'],
              'ilastik.shell.gui': ['ui/*.ui', '*.qss'],
              'ilastik.ilastik_logging': ['logging_config.json'],
              'ilastik.plugins': ['*.yapsy-plugin'],
              '': ['*.ui']
              }

class ilastik_recipe(object):
    def check(self, dist, mf):
        m = mf.findNode('ilastik')
        if m is None:
            return None
        
        # Don't put ilastik in the site-packages.zip file
        return dict(
            packages=['ilastik']
        )

class volumina_recipe(object):
    def check(self, dist, mf):
        m = mf.findNode('volumina')
        if m is None:
            return None

        # Don't put volumina in the site-packages.zip file
        return dict(
            packages=['volumina']
        )

class lazyflow_recipe(object):
    def check(self, dist, mf):
        m = mf.findNode('lazyflow')
        if m is None:
            return None

        # Don't put lazyflow in the site-packages.zip file
        return dict(
            packages=['lazyflow']
        )

class vtk_recipe(object):
    def check(self, dist, mf):
        m = mf.findNode('vtk')
        if m is None:
            return None

        # Don't put vtk in the site-packages.zip file
        return dict(
            packages=['vtk']
        )

class sklearn_recipe(object):
    def check(self, dist, mf):
        m = mf.findNode('sklearn')
        if m is None:
            return None

        # Don't put sklearn in the site-packages.zip file
        return dict(
            packages=['sklearn']
        )

class jsonschema_recipe(object):
    def check(self, dist, mf):
        m = mf.findNode('jsonschema')
        if m is None:
            return None

        # Don't put jsonschema in the site-packages.zip file
        return dict(
            packages=['jsonschema']
        )

import py2app.recipes
py2app.recipes.ilastik = ilastik_recipe()
py2app.recipes.volumina = volumina_recipe()
py2app.recipes.lazyflow = lazyflow_recipe()
py2app.recipes.vtk = vtk_recipe()
py2app.recipes.sklearn = sklearn_recipe()
py2app.recipes.jsonschema = jsonschema_recipe()


##
## The --include-meta-repo option is a special option added by this script.
## If given, we will include the entire ilastik-meta git repo directory (which includes ilastik, lazyflow, and volumina).
## (Otherwise, py2app just includes the individual python module directories, without the supporting files.)
##

include_meta_repo = False
if '--include-meta-repo' in sys.argv:
    include_meta_repo = True
    sys.argv.remove('--include-meta-repo')

# This hack allows us to run custom code before/after the py2app command executes.
# http://www.niteoweb.com/blog/setuptools-run-custom-code-during-install
import os
import shutil

import ilastik
ilastik_meta_repo = os.path.abspath( os.path.split(ilastik.__file__)[0] + '/../..')
assert os.path.exists(ilastik_meta_repo + '/ilastik')
assert os.path.exists(ilastik_meta_repo + '/lazyflow')
assert os.path.exists(ilastik_meta_repo + '/volumina')

import py2app.build_app
class custom_py2app(py2app.build_app.py2app):
    __dist_dir = os.path.split( os.path.abspath(__file__) )[0] + '/dist'
    __destination_libpython_dir = __dist_dir + '/ilastik.app/Contents/Resources/lib/python2.7'
    __replace_modules = ['ilastik', 'volumina', 'lazyflow']

    def run(self):
        """
        The normal py2app run() function copies the ilastik, volumina, and 
        lazyflow modules in the .app without the enclosing repo directory.
        
        This function deletes those modules from the app (after saving the drtile.so binary), 
        copies the ENTIRE repo directory for each module, and then creates a symlink to the 
        inner module directory so that the final .app doesn't know the difference.
        
        Just to be clear, our usual py2app command (including our recipes) 
        produces a lib/python2.7 directory that looks like this:
        
        $ ls -l dist/ilastik.app/Contents/Resources/lib/python2.7/
        ilastik/
        lazyflow/
        volumina/
        site-packages.zip
        ...etc...
        
        But with the --include-meta-repo option, we post-process the package so it looks like this:
        $ ls -l dist/ilastik.app/Contents/Resources/lib/python2.7/
        ilastik-meta
        ilastik@ -> ilastik-meta/ilastik/ilastik
        lazyflow@ -> ilastik-meta/lazyflow/lazyflow
        volumina@ -> ilastik-meta/volumina/volumina
        site-packages.zip
        ...etc...            

        Hence, the ilastik, lazyflow, and volumina modules are present via symlinks,
        so the .app doesn't know the difference.
        
        Also, this function removes any dylibs in the dylib_forced_removal list from the final distribution.
        """
        # Remove modules/repos from an earlier build (if any)
        self.remove_repos()
        
        # Run the normal py2app command
        py2app.build_app.py2app.run(self)

        if include_meta_repo:
            # Save drtile.so first!
            shutil.move( self.__destination_libpython_dir + '/lazyflow/drtile/drtile.so', self.__dist_dir )
            
            # Copy repos and create symlinks to modules
            self.install_repos()
            
            # Replace drtile.so
            shutil.move( self.__dist_dir + '/drtile.so', self.__destination_libpython_dir + '/ilastik-meta/lazyflow/lazyflow/drtile/drtile.so' )

        # Remove excluded dylibs.
        # (The py2app exclude_dylib feature doesn't work if macholib can't find the dylib.)
        for dylib in dylib_forced_removal:
            dylib_path = self.__dist_dir + '/ilastik.app/Contents/Frameworks/' + dylib
            try:
                os.remove(dylib_path)
                print "Excluded {} from distribution.".format( dylib )
            except OSError as ex:
                if ex.errno != 2:
                    raise


    def install_repos(self):
        self.remove_repos()
        src = ilastik_meta_repo
        dst = self.__destination_libpython_dir + '/ilastik-meta'
        print "Copying {} to {}".format(src, dst )

        # Don't copy copy the .app itself!
        # (which would lead to infinite recursion)
        def ignore(d, contents):
            return ['dist', 'build']

        # Copy the whole repo
        shutil.copytree(src, dst, symlinks=True, ignore=ignore)
            
        # symlink to the actual module within the meta-repo
        for module in self.__replace_modules:
            relative_link = os.path.relpath( dst + '/' + module + '/' + module, self.__destination_libpython_dir )
            os.symlink( relative_link, self.__destination_libpython_dir + '/' + module )

    def remove_repos(self):
        """
        Remove the existing modules/repos left in the .app tree.
        """
        try:
            # repo dir created by this custom post-processing step (if present from an earlier build)
            p = self.__destination_libpython_dir + '/' + ilastik_meta_repo
            shutil.rmtree(p)
        except Exception as ex:
            pass

        for module in self.__replace_modules:
            # Remove symlink (if present from a previous build)
            try:
                p = self.__destination_libpython_dir + '/' + module
                os.remove( p )
            except Exception as ex:
                pass

            # Module created by py2app
            try:
                p = self.__destination_libpython_dir + '/' + module
                shutil.rmtree(p)
            except Exception as ex:
                pass
                
setup(
    cmdclass={ 'py2app' : custom_py2app }, # See hack above.
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    version=__version__,
    description='Interactive Image Analysis',
    url='http://github.com/ilastik',
    packages=packages,
    package_data=package_data
)

    
