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
      package_data=package_data, requires=['PyQt4', 'numpy', 'h5py']
     )
