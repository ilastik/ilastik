from setuptools import setup, find_packages
from ilastik import __version__

packages=find_packages(exclude=["tests", "tests.*"])
package_data={'ilastik': ['ilastik-splash.png',
                          'ilastik-splash.xcf'],
              'ilastik.applets.labeling': ['*.ui', 'icons/*.png', 'icons/*.jpg'],
              'ilastik.shell.gui': ['ui/*.ui', '*.qss', '*.png'],
              'ilastik.ilastik_logging': ['logging_config.json'],
              'ilastik.plugins': ['*.yapsy-plugin'],
              '': ['*.ui']
              }

setup(name='ilastik',
      version=__version__,
      description='Interactive Image Analysis',
      url='https://github.com/Ilastik',
      packages=packages,
      package_data=package_data
     )
