from setuptools import setup, find_packages
from ilastik import __version__

APP = ['ilastik.py']
DATA_FILES = []

includes = [\
                'distutils', 'sip', 'ctypes','ctypes.util','h5py', 'h5py.defs', 'h5py.utils', 'h5py._proxy', 'h5py._errors',
                'PyQt4.pyqtconfig', 'PyQt4.uic','PyQt4.QtCore','PyQt4.QtGui',
                'site', 'os',
                'vtk',
                'vtk.vtkCommonPythonSIP',
#                #'vtk.vtkFilteringPythonSIP',
#                'vtk.vtkRenderingPythonSIP',
#                'vtk.vtkFilteringPythonSIP',
                'numpy.core.multiarray',
                'vigra', #'h5py._proxy', 'csv', #'vigra.svs',
                'qimage2ndarray',
                'greenlet',
                'psutil',
             ]

OPTIONS = {'argv_emulation': True, 'includes':includes }

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

class vtk_recipe(object):
    def check(self, dist, mf):
        m = mf.findNode('vtk')
        if m is None:
            return None

        # Don't put vtk in the site-packages.zip file
        return dict(
            packages=['vtk']
        )

import py2app.recipes
py2app.recipes.ilastik = ilastik_recipe()
py2app.recipes.volumina = volumina_recipe()
py2app.recipes.vtk = vtk_recipe()

setup(
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
