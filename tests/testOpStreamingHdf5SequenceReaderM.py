import unittest
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStreamingHdf5SequenceReaderM


class TestOpStreamingHdf5SequenceReader(unittest.TestCase):

    def setUp(self):
        self.graph = Graph()

    def test_globStringValidity(self):
        """Check whether globStrings are correctly verified"""
        testGlobString = '/tmp/test.h5/somedata'
        with self.assertRaises(OpStreamingHdf5SequenceReaderM.NoExternalPlaceholderError):
            OpStreamingHdf5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = '/tmp/test.jpg/*'
        with self.assertRaises(OpStreamingHdf5SequenceReaderM.WrongFileTypeError):
            OpStreamingHdf5SequenceReaderM.checkGlobString(testGlobString)

        testGlobString = '/tmp/test.h5/data:/tmp/test.h5/data2'
        with self.assertRaises(OpStreamingHdf5SequenceReaderM.SameFileError):
            OpStreamingHdf5SequenceReaderM.checkGlobString(testGlobString)

        validGlobStrings = [
            '/tmp/test-*.h5/data',
            '/tmp/test-1.h5/data1:/tmp/test-2.h5/data1',
        ]

        for testGlobString in validGlobStrings:
            self.assertTrue(
                OpStreamingHdf5SequenceReaderM.checkGlobString(testGlobString))


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
