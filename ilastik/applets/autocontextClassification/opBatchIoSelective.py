import os
import h5py
import traceback
import threading
import logging

from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal
from lazyflow.operators import OpBlockedArrayCache
from lazyflow.operators.ioOperators import OpH5WriterBigDataset
from ilastik.utility.pathHelpers import PathComponents
from lazyflow.rtype import SubRegion
logger = logging.getLogger(__name__)

class ExportFormat():
    H5 = 0
    Npy = 1
    Tiff = 2 # 3d only, up to 3 channels

    def __init__(self, name, extension):
        self.name = name
        self.extension = extension    

SupportedFormats = { ExportFormat.H5   : ExportFormat("Hdf5", '.h5') }

#SupportedFormats = { ExportFormat.H5   : ExportFormat("Hdf5", '.h5'),
#                     ExportFormat.Npy  : ExportFormat("Numpy", '.npy'),
#                     ExportFormat.Tiff : ExportFormat("Tiff", '.tiff') }

class OpBatchIoSelective(Operator):
    """
    The top-level operator for the Batch IO applet.
    """
    name = "OpBatchIo"
    category = "Top-level"

    ExportDirectory = InputSlot(stype='filestring') # A separate directory to export to.  If '', then exports to the input data's directory
    Format = InputSlot(stype='int')                 # The export format
    Suffix = InputSlot(stype='string')              # Appended to the file name (before the extension)
    
    InternalPath = InputSlot(stype='string', optional=True) # Hdf5 internal path

    DatasetPath = InputSlot(stype='string') # The path to the original the dataset we're saving
    ImageToExport = InputSlot()             # The image that needs to be saved
    
    SelectedSlices = InputSlot(stype='list')

    OutputFileNameBase = InputSlot(stype='string', optional=True) # Override for the file name base. (Input filename is used by default.)

    Dirty = OutputSlot(stype='bool')            # Whether or not the result currently matches what's on disk
    OutputDataPath = OutputSlot(stype='string')
    ExportResult = OutputSlot(stype='string')   # When requested, attempts to store the data to disk.  Returns the path that the data was saved to.
    
    ProgressSignal = OutputSlot(stype='object')

    def __init__(self, *args, **kwargs):
        super(OpBatchIoSelective, self).__init__(*args, **kwargs)
        
        self.Dirty.meta.shape = (1,)
        self.Dirty.meta.dtype = bool
        self.OutputDataPath.meta.shape = (1,)
        self.OutputDataPath.meta.dtype = object
        self.ExportResult.meta.shape = (1,)
        self.ExportResult.meta.dtype = object
        
        # Provide default values
        self.ExportDirectory.setValue( '' )
        self.Format.setValue( ExportFormat.H5 )
        self.Suffix.setValue( '_results' )
        self.Dirty.setValue(True)
        
        self.progressSignal = OrderedSignal()
        self.ProgressSignal.setValue( self.progressSignal )
        
        self._createDirLock = threading.Lock()
        
        #make a cache of the input image not to request too much
        self.ImageCache = OpBlockedArrayCache(parent=self, graph=self.graph)
        self.ImageCache.fixAtCurrent.setValue(False)
        self.ImageCache.Input.connect(self.ImageToExport)

    def setupOutputs(self):        
        # Create the output data path
        formatId = self.Format.value
        ext = SupportedFormats[formatId].extension
        inputPathComponents = PathComponents(self.DatasetPath.value)
        
        # If no export directory was given, use the original input data's directory
        if self.ExportDirectory.value == '':
            outputPath = inputPathComponents.externalDirectory
        else:
            outputPath = self.ExportDirectory.value
            
        if self.OutputFileNameBase.ready():
            filenameBase = PathComponents(self.OutputFileNameBase.value).filenameBase
        else:
            filenameBase = inputPathComponents.filenameBase
        outputPath = os.path.join(outputPath, filenameBase + self.Suffix.value + ext).replace('\\', '/')
        
        # Set up the path for H5 export
        if formatId == ExportFormat.H5:
            if self.InternalPath.ready() and self.InternalPath.value != '':
                # User-specified internal path
                self._internalPath = self.InternalPath.value
                if self._internalPath[0] != '/':
                    self._internalPath = "/" + self._internalPath
            elif inputPathComponents.internalPath is not None:
                # Mirror the input data internal path
                self._internalPath = inputPathComponents.internalPath
            else:
                self._internalPath = '/volume/data'

            self.OutputDataPath.setValue( outputPath + self._internalPath )
        elif formatId == ExportFormat.Npy:
            self.OutputDataPath.setValue( outputPath )
        elif formatId == ExportFormat.Tiff:
            self.OutputDataPath.setValue( outputPath )
            
        self.setupCaches()
    
    def setupCaches(self):
        # Set the blockshapes for each input image separately, depending on which axistags it has.
        axisOrder = [ tag.key for tag in self.ImageToExport.meta.axistags ]

        ## Pixel Cache blocks
        blockDimsX = { 't' : (1,1),
                       'z' : (128,256),
                       'y' : (128,256),
                       'x' : (1,1),
                       'c' : (100, 100) }

        blockDimsY = { 't' : (1,1),
                       'z' : (128,256),
                       'y' : (1,1),
                       'x' : (128,256),
                       'c' : (100,100) }

        blockDimsZ = { 't' : (1,1),
                       'z' : (1,1),
                       'y' : (128,256),
                       'x' : (128,256),
                       'c' : (100,100) }

        innerBlockShapeX = tuple( blockDimsX[k][0] for k in axisOrder )
        outerBlockShapeX = tuple( blockDimsX[k][1] for k in axisOrder )

        innerBlockShapeY = tuple( blockDimsY[k][0] for k in axisOrder )
        outerBlockShapeY = tuple( blockDimsY[k][1] for k in axisOrder )

        innerBlockShapeZ = tuple( blockDimsZ[k][0] for k in axisOrder )
        outerBlockShapeZ = tuple( blockDimsZ[k][1] for k in axisOrder )

        self.ImageCache.inputs["innerBlockShape"].setValue( innerBlockShapeZ )
        self.ImageCache.inputs["outerBlockShape"].setValue(  outerBlockShapeZ )

    def propagateDirty(self, slot, subindex, roi):
        # Out input data changed, so we have work to do when we get executed.
        self.Dirty.setValue(True)

    def execute(self, slot, subindex, roi, result):
        if slot == self.Dirty:
            assert False # Shouldn't get to this line because the dirty output is given a value directly
        
        if slot == self.OutputDataPath:
            assert False # This slot is already set via setupOutputs

        if slot == self.ExportResult:
            # We can stop now if the output isn't dirty
            if not self.Dirty.value:
                result[0] = True
                return
            
            exportFormat = self.Format.value
            
            # Export H5
            if exportFormat == ExportFormat.H5:
                pathComp = PathComponents(self.OutputDataPath.value)

                # Ensure the directory exists
                if not os.path.exists(pathComp.externalDirectory):
                    with self._createDirLock:
                        # Check again now that we have the lock.
                        if not os.path.exists(pathComp.externalDirectory):
                            os.makedirs(pathComp.externalDirectory)

                # Open the file
                try:
                    hdf5File = h5py.File(pathComp.externalPath)
                except:
                    logger.error("Unable to open hdf5File: " + pathComp.externalPath)
                    logger.error( traceback.format_exc() )
                    result[0] = False
                    return
                
                # Set up the write operator
                opH5Writer = OpH5WriterBigDataset(parent=self, graph=self.graph)
                opH5Writer.hdf5File.setValue( hdf5File )
                opH5Writer.hdf5Path.setValue( pathComp.internalPath )
                #opH5Writer.Image.connect( self.ImageToExport )
                opH5Writer.Image.connect(self.ImageCache.Output)

                print "computing predictions for the selected slices:"
                self.ImageCache.fixAtCurrent.setValue(False)
                #check readiness
                for inp in self.ImageCache.inputs:
                    print inp, self.ImageCache.inputs[inp].ready()
                
                print "input shape:", self.ImageCache.Input.meta.shape
                print "output shape:", self.ImageCache.Output.meta.shape
                
                selectedSlices = self.SelectedSlices.value
                zaxis = self.ImageToExport.meta.axistags.index('z')
                for isl, sl in enumerate(selectedSlices):
                    print "computing for slice ...", isl
                    start = [0]*len(self.ImageToExport.meta.shape)
                    start[zaxis]=sl
                    stop = list(self.ImageToExport.meta.shape)
                    stop[zaxis]=sl+1
                    roi = SubRegion(self.ImageCache, start=start, stop=stop)
                    print roi
                    temp = self.ImageCache.Output[roi.toSlice()].wait()
                    #print temp
                    
                self.ImageCache.fixAtCurrent.setValue(True)
                #tstart = [0]*len(self.ImageToExport.meta.shape)
                #tstop = list(self.ImageToExport.meta.shape)
                #troi = SubRegion(self.ImageCache, start=tstart, stop=tstop)
                #tttemp = self.ImageCache.Output[troi.toSlice()].wait()
                #print tttemp
                
                # The H5 Writer provides it's own progress signal, so just connect ours to it.
                opH5Writer.progressSignal.subscribe( self.progressSignal )

                # Trigger the write
                self.Dirty.setValue( not opH5Writer.WriteImage.value )
                
                hdf5File.close()

                opH5Writer.cleanUp()

#            elif exportFormat == ExportFormat.Npy:
#                assert False # TODO
#            elif exportFormat == ExportFormat.Npy:
#                assert False # TODO
            else:
                assert False, "Unknown export format"

            result[0] = not self.Dirty.value

            





