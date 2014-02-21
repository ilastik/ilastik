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

import lazyflow.graph
import copy
from lazyflow.operators import OpAttributeSelector

class SomeClass(object):
    def __init__(self):
        self.x = 0
        self.name = "Hello"
        self.whatever = None

class TestOpAttributeSelector(object):

    @classmethod
    def setupClass(cls):
        pass

    @classmethod
    def teardownClass(cls):
        pass

    def test_selection(self):
        c = SomeClass()

        opSelector = OpAttributeSelector( graph=lazyflow.graph.Graph() )
        opSelector.InputObject.setValue( c )
        opSelector.AttributeName.setValue( 'x' )

        selectedField = opSelector.Result.value

        assert selectedField == c.x

    def test_dirtyPropagation(self):

        c = SomeClass()

        opSelector = OpAttributeSelector( graph=lazyflow.graph.Graph() )
        opSelector.InputObject.setValue( c )
        opSelector.AttributeName.setValue( 'x' )

        # Create a list to track the number of times the output is marked dirty
        l = []
        def handleDirty(slot, roi):
            l.append(True)

        opSelector.Result.notifyDirty(handleDirty)

        c = copy.copy(c)
        c.x = 1
        opSelector.InputObject.setValue(c)
        assert len(l) == 1

        d = copy.copy(c)
        # Didn't actually change any fields, so this shouldn't cause dirtyness to propagate
        opSelector.InputObject.setValue(d)
        assert len(l) == 1

        # Must be dirty if we start listening to a different attribute
        opSelector.AttributeName.setValue('name')
        assert len(l) == 2

if __name__ == "__main__":
    import nose
    ret = nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
    if not ret: sys.exit(1)
