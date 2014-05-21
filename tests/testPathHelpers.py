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
from lazyflow.utility.pathHelpers import compressPathForDisplay, getPathVariants

class TestPathHelpers(object):
    
    def testCompressPathForDisplay(self):
        assert compressPathForDisplay("/a/b.txt", 30) == "/a/b.txt"
        path = "/test/bla/bla/this_is_a_very_long_filename_bla_bla.txt"
        for l in [5,10,15,20,30]:
            assert len(compressPathForDisplay(path, l)) == l

    def test_getPathVariants(self):
        abs, rel = getPathVariants('/aaa/bbb/ccc/ddd.txt', '/aaa/bbb/ccc/eee')
        assert abs == '/aaa/bbb/ccc/ddd.txt'
        assert rel == '../ddd.txt'
    
        abs, rel = getPathVariants('../ddd.txt', '/aaa/bbb/ccc/eee')
        assert abs == '/aaa/bbb/ccc/ddd.txt'
        assert rel == '../ddd.txt'
    
        abs, rel = getPathVariants('ddd.txt', '/aaa/bbb/ccc')
        assert abs == '/aaa/bbb/ccc/ddd.txt'
        assert rel == 'ddd.txt'

        assert getPathVariants('', '/abc') == ('/abc', '')
        
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
