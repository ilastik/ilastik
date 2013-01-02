import os
import urllib2
import numpy

from lazyflow.pathHelpers import PathComponents
from lazyflow.jsonConfig import JsonConfigSchema, AutoEval, FormattedField

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
        "shape" : list,
        "dtype" : AutoEval(),
        "origin_offset" : list,
        "url_format" : FormattedField( requiredFields=["x_start", "x_stop", "y_start", "y_stop", "z_start", "z_stop"], 
                                       optionalFields=["t_start", "t_stop", "c_start", "c_stop"] ),
        "hdf5_dataset" : str
    }
    DescriptionSchema = JsonConfigSchema( DescriptionFields )

    @classmethod
    def readDescription(cls, descriptionFilePath):
        return RESTfulVolume.DescriptionSchema.parseConfigFile( descriptionFilePath )

    @classmethod
    def writeDescription(cls, descriptionFilePath, descriptionFields):
        RESTfulVolume.DescriptionSchema.writeConfigFile( descriptionFilePath, descriptionFields )

    def __init__( self, descriptionFilePath ):
        self.descriptionFilePath = descriptionFilePath
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
        logger.debug( "Downloading region {}..{}: {}".format(roi[0], roi[1], url) )
        hdf5RawFileObject = urllib2.urlopen( url, timeout=10 )

        pathComponents = PathComponents(outputDatasetPath)

        if pathComponents.internalPath != self.description.hdf5_dataset:
            # We could just open the file and rename the dataset to match what the user asked for, but that would probably be slow.
            # It's better just to force him to use the correct dataset name to begin with.
            raise RuntimeError("The RESTful volume format uses internal dataset name '{}', but you seem to be expecting '{}'.".format( self.description.hdf5_dataset, pathComponents.internalPath ) )

        # Write the data from the url out to disk
        logger.debug( "Saving RESTful subvolume to file: {}".format( pathComponents.externalPath ) )
        with open(pathComponents.externalPath, 'w') as rawFileToWrite:
            rawFileToWrite.write( hdf5RawFileObject.read() )
    
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
