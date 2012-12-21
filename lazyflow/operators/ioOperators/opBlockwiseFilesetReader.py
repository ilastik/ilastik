import os
import tempfile
import urllib2
import numpy
import h5py
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.jsonConfig import JsonConfigSchema, AutoEval, FormattedField

import logging
logger = logging.getLogger(__name__)

OpBlockwiseFilesetDescriptionFields = \
{
    "name" : str,
    "format" : str,
    "axes" : str,
    "shape" : list,
    "dtype" : AutoEval(),
    "block_side" : { 't' : 1, 'x' : 500, 'y' : 500, 'z' : 500, 'c' : 100 },
    "block_file_name_format" : "cube{roi}.h5/volume/data",
    "hdf5_dataset" : str
}

class OpBlockwiseFilesetReader(Operator):
    """
    """
    name = "OpBlockwiseFilesetReader"

    DescriptionFilePath = InputSlot(stype='filestring')
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpBlockwiseFilesetReader, self).__init__(*args, **kwargs)
        self._configSchema = JsonConfigSchema( OpBlockwiseFilesetReader )
        self._axes = None

    def setupOutputs(self):
        # Read the dataset description file
        descriptionFields = self._configSchema.parseConfigFile( self.DescriptionFilePath.value )

        # Check for errors in the description file
        axes = descriptionFields.axes 
        assert False not in map(lambda a: a in 'txyzc', axes), "Unknown axis type.  Known axes: txyzc  Your axes:".format(axes)
        assert descriptionFields.format == "hdf5", "Only hdf5 blockwise filesets are supported so far."

        # Save description file members
        self._axes = descriptionFields.axes
        self._urlFormat = descriptionFields.url_format
        self._origin_offset = numpy.array(descriptionFields.origin_offset)
        self._block_file_name_format = descriptionFields.block_file_name_format

        outputShape = tuple( descriptionFields.shape )

        # If the dataset has no channel axis, add one.
        if 'c' not in axes:
            outputShape += (1,)
            self._axes += 'c'
            self._origin_offset = numpy.array( list(self._origin_offset) + [0] )

        self.Output.meta.shape = outputShape
        self.Output.meta.dtype = descriptionFields.dtype
        self.Output.meta.axistags = vigra.defaultAxistags(self._axes)

    def execute(self, slot, subindex, roi, result):
        accessStart = numpy.array(roi.start)
        accessStart += self._origin_offset
        accessStop = numpy.array(roi.stop)
        accessStop += self._origin_offset

        axistags = self.Output.meta.axistags
        RESTArgs = {}
        for axisindex, tag in enumerate(axistags):
            startKey = '{}_start'.format(tag.key)
            stopKey = '{}_stop'.format(tag.key)
            RESTArgs[startKey] = accessStart[ axisindex ]
            RESTArgs[stopKey] = accessStop[ axisindex ]

        # Open the url
        url = self._urlFormat.format( **RESTArgs )
        logger.debug( "Downloading region {}..{}: {}".format(roi.start, roi.stop, url) )
        hdf5RawFileObject = urllib2.urlopen( url, timeout=10 )

        # Write the data from the url out to disk (in a temporary file)
        hdf5FilePath = os.path.join(tempfile.mkdtemp(), 'cube.h5')
        with open(hdf5FilePath, 'w') as rawFileToWrite:
            rawFileToWrite.write( hdf5RawFileObject.read() )

        # Open the file we just created using h5py
        with h5py.File( hdf5FilePath, 'r' ) as hdf5File:
            dataset = hdf5File[self._hdf5_dataset]
            if len(result.shape) > len(dataset.shape):
                result[...,0] = dataset[...]
            else:
                result[...] = dataset[...]
        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.DescriptionFilePath, "Unknown input slot."
        self.Output.setDirty( slice(None) )




















