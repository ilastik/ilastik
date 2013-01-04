import numpy

import vigra
from numpy.testing import assert_equal, assert_almost_equal, assert_array_equal, assert_array_almost_equal
import lazyflow
from context.applets.pixelClassification.opBatchIoSelective import OpBatchIoSelective
import h5py
from lazyflow.operators.ioOperators import OpInputDataReader
from ilastik.applets.batchIo.opBatchIo import ExportFormat

testfile="/home/akreshuk/data/dummytestdata.h5"

def createDataset():
    aaa = numpy.zeros((5, 5, 5, 1))
    for i in range(aaa.shape[2]):
        aaa[:, :, i, 0]=i
    f = h5py.File(testfile, 'w')
    f.create_dataset("/volume/data", data=aaa)
    f.close()
    
def test():
    graph = lazyflow.graph.Graph()
    
    opReaderRaw = OpInputDataReader(graph=graph)
    opReaderRaw.FilePath.setValue(testfile+"/volume/data")
    #opReaderRaw.WorkingDirectory.setValue("")
    for input in opReaderRaw.inputs:
        print input, opReaderRaw.inputs[input].ready()

    opBatchResults = OpBatchIoSelective(graph=graph)
    opBatchResults.ExportDirectory.setValue("/home/akreshuk/data")
    opBatchResults.Format.setValue(ExportFormat.H5)
    opBatchResults.Suffix.setValue("_out")
    opBatchResults.InternalPath.setValue("/volume/data")
    opBatchResults.DatasetPath.setValue(testfile)
    
    opBatchResults.SelectedSlices.setValue([1, 3])
    opBatchResults.ImageToExport.connect(opReaderRaw.Output)
    print
    #for input in opBatchResults.inputs:
    #    print input, opBatchResults.inputs[input].value
    
    result = opBatchResults.ExportResult[0].wait()
    return

if __name__=="__main__":
    #createDataset()
    test()
        