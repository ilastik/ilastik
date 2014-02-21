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
setup(
    name = "lazyflow",
#    version = "0.1",
    packages = find_packages(),
    scripts = [],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['greenlet', 'psutil', 'blist', 'h5py'],

    package_data = {
        'lazyflow': ['*.txt', '*.py'],
        'lazyflow.drtile': ['drtile.so']
    },

    include_package_data = True,    # include everything in source control


    # metadata for upload to PyPI
    author = "Christoph Straehle",
    author_email = "christoph.straehle@iwr.uni-heidelberg.de",
    description = "Lazyflow - graph based lazy numpy data flows",
    license = "BSD",
    keywords = "graph numpy dataflow",
    url = "http://ilastik.org/lazyflow",
)
