from ilastik.applets.objectClassification.opObjectClassification import OpObjectClassification
import numpy

class TestTransferLabelsFunction(object):
    coords_old = dict()
    coords_old["Coord<Minimum>"]=numpy.array([[0, 0, 0], [15, 15, 15], [22, 22, 22], [31, 31, 31], [0, 0, 0]])
    coords_old["Coord<Maximum>"]=numpy.array([[10, 10, 10], [20, 20, 20], [30, 30, 30], [35, 35, 35], [3, 3, 3]])
    
    coords_new = dict()
    coords_new["Coord<Minimum>"]=numpy.array([[2, 2, 2], [17, 17, 17], [22, 22, 22], [26, 26, 26]])
    coords_new["Coord<Maximum>"]=numpy.array([[5, 5, 5], [20, 20, 20], [25, 25, 25], [33, 33, 33]])
    
    labels = numpy.zeros((4,))
    labels[0]=1
    labels[1]=2
    labels[2]=3
    labels[3]=4
    
    newlabels = OpObjectClassification.transferLabels(labels, coords_old, coords_new, None)
    assert numpy.all(newlabels == [1, 2, 0, 0])
    
    
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)