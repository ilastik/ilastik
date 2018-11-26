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
