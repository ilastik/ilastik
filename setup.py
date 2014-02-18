# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

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
