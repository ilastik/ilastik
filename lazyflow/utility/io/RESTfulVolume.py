import sys
import urllib2
import numpy
import shutil

from lazyflow.utility import PathComponents
from lazyflow.utility.jsonConfig import JsonConfigSchema, AutoEval, FormattedField

import logging
logger = logging.getLogger(__name__)

class RESTfulVolume(object):
    
    DescriptionFields = \
    {
        "_schema_name" : "RESTful-volume-description",
        "_schema_version" : 1.0,

        "name" : str,
        "format" : str,
        "axes" : str,
        "dtype" : AutoEval(),
        "bounds" : AutoEval(numpy.array),
        "shape" : AutoEval(numpy.array), # Provided for you. Computed as bounds - origin_offset
        "origin_offset" : AutoEval(numpy.array),
        "url_format" : FormattedField( requiredFields=["x_start", "x_stop", "y_start", "y_stop", "z_start", "z_stop"], 
                                       optionalFields=["t_start", "t_stop", "c_start", "c_stop"] ),
        "hdf5_dataset" : str
    }
    DescriptionSchema = JsonConfigSchema( DescriptionFields )

    @classmethod
    def readDescription(cls, descriptionFilePath):
        # Read file
        description = RESTfulVolume.DescriptionSchema.parseConfigFile( descriptionFilePath )
        cls.updateDescription(description)
        return description

    @classmethod
    def updateDescription(cls, description):        
        # Augment with default parameters.
        if description.origin_offset is None:
            description.origin_offset = numpy.array( [0]*len(description.bounds) )
        description.shape = description.bounds - description.origin_offset

    @classmethod
    def writeDescription(cls, descriptionFilePath, descriptionFields):
        RESTfulVolume.DescriptionSchema.writeConfigFile( descriptionFilePath, descriptionFields )

    def __init__( self, descriptionFilePath=None, preparsedDescription=None ):
        if preparsedDescription is not None:
            assert descriptionFilePath is None, "Can't provide BOTH description file and pre-parsed description fields."
            self.description = preparsedDescription
        else:
            assert descriptionFilePath is not None, "Must provide either a description file or pre-parsed description fields"
            self.description = RESTfulVolume.readDescription( descriptionFilePath )

        # Check for errors        
        assert False not in map(lambda a: a in 'txyzc', self.description.axes), "Unknown axis type.  Known axes: txyzc  Your axes:".format(self.description.axes)
        assert self.description.format == "hdf5", "Only hdf5 RESTful volumes are supported so far."
        assert self.description.hdf5_dataset is not None, "RESTful volume description file must specify the hdf5_dataset name"

        if self.description.hdf5_dataset[0] != '/':
            self.description.hdf5_dataset = '/' + self.description.hdf5_dataset
    
    def downloadSubVolume(self, roi, outputDatasetPath):
        origin_offset = numpy.array(self.description.origin_offset)
        accessStart = numpy.array(roi[0])
        accessStart += origin_offset
        accessStop = numpy.array(roi[1])
        accessStop += origin_offset

        RESTArgs = {}
        for axisindex, axiskey in enumerate(self.description.axes):
            startKey = '{}_start'.format(axiskey)
            stopKey = '{}_stop'.format(axiskey)
            RESTArgs[startKey] = accessStart[ axisindex ]
            RESTArgs[stopKey] = accessStop[ axisindex ]

        # Open the url
        url = self.description.url_format.format( **RESTArgs )
        logger.info( "Downloading region {}..{}: {}".format(roi[0], roi[1], url) )

        try:
            # This merely opens the url (but does not download it).
            # Still, we need a long timeout because this seems to take a long time for big files.
            hdf5RawFileObject = urllib2.urlopen( url, timeout=300 )
        except:
            logger.error( "Failed to open url: {}\n".format(url) )
            raise

        pathComponents = PathComponents(outputDatasetPath)

        if pathComponents.internalPath != self.description.hdf5_dataset:
            # We could just open the file and rename the dataset to match what the user asked for, but that would probably be slow.
            # It's better just to force him to use the correct dataset name to begin with.
            raise RuntimeError("The RESTful volume format uses internal dataset name '{}', but you seem to be expecting '{}'.".format( self.description.hdf5_dataset, pathComponents.internalPath ) )

        # Write the data from the url out to disk
        logger.info( "Saving RESTful subvolume to file: {}".format( pathComponents.externalPath ) )
        with open(pathComponents.externalPath, 'w') as rawFileToWrite:
            # This is where the data is actually downloaded.
            # Limit memory usage here: Use shutil instead of the write/read combo commented out below.
            # Download in 20MB bursts
            shutil.copyfileobj( hdf5RawFileObject, rawFileToWrite, length=20*1024*1024 )
            # rawFileToWrite.write( hdf5RawFileObject.read() ) # <--Memory-hog
        logger.info( "Finished saving file: {}".format( pathComponents.externalPath ) )

if __name__ == "__main__":
    testParameters0 = """
{
    "_schema_name" : "RESTful-volume-description",
    "_schema_version" : 1.0,

    "name" : "Bock11-level0",
    "format" : "hdf5",
    "axes" : "zyx",

    "##NOTE":"The first z-slice of the bock dataset is 2917, so the origin_offset must be at least 2917",
    "origin_offset" : [2917, 50000, 50000],

    "###shape" : [1239, 135424, 119808],
    "shape" : [1239, 10000, 10000],
    "dtype" : "numpy.uint8",
    "url_format" : "http://openconnecto.me/emca/bock11/hdf5/0/{x_start},{x_stop}/{y_start},{y_stop}/{z_start},{z_stop}/",
    "hdf5_dataset" : "/cube"
}
"""
    import os
    import tempfile
    import numpy

    # Write test to a temp file
    d = tempfile.mkdtemp()
    descriptionFilePath = os.path.join(d, 'remote_volume_parameters.json')
    with file( descriptionFilePath, 'w' ) as f:
        f.write(testParameters0)
    
    description = RESTfulVolume.readDescription( descriptionFilePath )

    assert description.name == "Bock11-level0"
    assert description.axes == "zyx"
    assert description.dtype == numpy.uint8
