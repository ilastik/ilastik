import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

from ilastik.applets.objectClassification.opObjectClassification import OpObjectClassification
import numpy

class TestTransferLabelsFunction(object):
    coords_old = dict()
    coords_old["Coord<Minimum>"]=numpy.array([[0, 0, 0], [0, 0, 0], [0, 0, 0], [15, 15, 15], [22, 22, 22], [31, 31, 31]])
    coords_old["Coord<Maximum>"]=numpy.array([[50, 50, 50], [10, 10, 10], [3, 3, 3], [20, 20, 20], [30, 30, 30], [35, 35, 35]])
    
    coords_new = dict()
    coords_new["Coord<Minimum>"]=numpy.array([[0, 0, 0], [2, 2, 2], [17, 17, 17], [22, 22, 22], [26, 26, 26]])
    coords_new["Coord<Maximum>"]=numpy.array([[50, 50, 50], [5, 5, 5], [20, 20, 20], [25, 25, 25], [33, 33, 33]])
    
    labels = numpy.zeros((6,))
    labels[0]=0
    labels[1]=1
    labels[2]=0
    labels[3]=2
    labels[4]=3
    labels[5]=4
   
    newlabels, oldlost, newlost = OpObjectClassification.transferLabels(labels, coords_old, coords_new, None)
    assert numpy.all(newlabels == [0, 1, 2, 0, 0])
    print newlabels
    print "not present anymore:", oldlost["full"]
    print "partially gone:", oldlost["partial"]
    print "in conflict in the new labels:", newlost["conflict"]
    
    
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)