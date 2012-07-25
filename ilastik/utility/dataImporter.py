from lazyflow.operators import OpArrayPiper, OpH5ReaderBigDataset, OpSlicedBlockedArrayCache
import numpy
import vigra
import os

class DataImporter(object):
    def __init__(self, graph):
        self.graph = graph

    def openFile(self, fileNames):
        """
        Create an ArrayPiper operator with the data from the given file(s).
        """
        inputProvider = None
        fName, fExt = os.path.splitext(str(fileNames[0]))
        print "Opening Files %r" % fileNames
        if fExt=='.npy':
            inputProvider = self.createArrayPiperFromNpyFile(fileNames)
        elif fExt=='.h5':
            inputProvider = self.createArrayPiperFromHdf5File(fileNames)
        else:
            raise RuntimeError("Opening filenames=%r not supported yet" % fileNames)

        return inputProvider
    
    def createArrayPiperFromNpyFile(self, fileNames):
        """
        Open given .npy file(s) and produce an array piper operator with the data.
        """
        fileName = fileNames[0]
        if len(fileNames)>1:
            print "WARNING: only the first file will be read, multiple file prediction not supported yet"
        fName, fExt = os.path.splitext(str(fileName))
        raw = numpy.load(str(fileName))
        min, max = numpy.min(raw), numpy.max(raw)
        inputProvider = OpArrayPiper(self.graph)
        raw = raw.view(vigra.VigraArray)
        raw.axistags =  vigra.AxisTags(
            vigra.AxisInfo('t',vigra.AxisType.Time),
            vigra.AxisInfo('x',vigra.AxisType.Space),
            vigra.AxisInfo('y',vigra.AxisType.Space),
            vigra.AxisInfo('z',vigra.AxisType.Space),
            vigra.AxisInfo('c',vigra.AxisType.Channels))

        inputProvider.inputs["Input"].setValue(raw)
        return inputProvider

    def createArrayPiperFromHdf5File(self, fileNames):
        """
        Open given .h5 file(s) and produce an array piper operator with the data.
        """
        readerNew=OpH5ReaderBigDataset(self.graph)
        
        readerNew.inputs["Filenames"].setValue(fileNames)
        readerNew.inputs["hdf5Path"].setValue("volume/data")

        readerCache =  OpSlicedBlockedArrayCache(self.graph)
        readerCache.inputs["fixAtCurrent"].setValue(False)
        readerCache.inputs["innerBlockShape"].setValue(((1,256,256,1,2),(1,256,1,256,2),(1,1,256,256,2)))
        readerCache.inputs["outerBlockShape"].setValue(((1,256,256,4,2),(1,256,4,256,2),(1,4,256,256,2)))
        readerCache.inputs["Input"].connect(readerNew.outputs["Output"])

        inputProvider = OpArrayPiper(self.graph)
        inputProvider.inputs["Input"].connect(readerCache.outputs["Output"])
        return inputProvider
    
    def createArrayPiperFromHdf5Dataset(self, hdf5Dataset):
        """
        Given an HDF5 group, extract the data as a vigra numpy array and return an OpArrayPiper.
        """
        # Extract the numpy data from the hdf5 dataset
        rawNumpyData = hdf5Dataset.value
        
        # View the data as a vigra array
        rawVigraData = rawNumpyData.view(vigra.VigraArray)
        rawVigraData.axistags = vigra.AxisTags(
            vigra.AxisInfo('t',vigra.AxisType.Time),
            vigra.AxisInfo('x',vigra.AxisType.Space),
            vigra.AxisInfo('y',vigra.AxisType.Space),
            vigra.AxisInfo('z',vigra.AxisType.Space),
            vigra.AxisInfo('c',vigra.AxisType.Channels))
                
        # Create the array piper operator
        inputProvider = OpArrayPiper(self.graph)
        inputProvider.inputs["Input"].setValue(rawVigraData)        
        return inputProvider

if __name__ == "__main__":
    from lazyflow.graph import Graph
    graph = Graph()
#    di = DataImporter(graph)
#    piper = di.createArrayPiperFromHdf5File(['test.h5'])
#    print piper.Output[:].wait().shape

#    from lazyflow.operators import OpH5Reader
#    h5Reader = OpH5Reader(graph)
#    h5Reader.Filename.setValue('test.h5')
#    h5Reader.hdf5Path.setValue('volume/data')
#    h5Reader.Image[:].wait().shape
    
    
    
    
    