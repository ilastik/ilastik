import sys
import urllib2
import numpy
import shutil

from lazyflow.utility import PathComponents
from lazyflow.utility.jsonConfig import JsonConfigSchema, AutoEval, FormattedField

import logging
logger = logging.getLogger(__name__)

class RESTfulVolume(object):
    """
    This class provides access to data obtained via a RESTful API (e.g. from http://openconnecto.me).
    A description of the remote volume must be provided via a JSON file, 
    whose schema is specified by :py:data:`RESTfulVolume.DescriptionFields`.
    
    See the unit tests in ``tests/testRESTfulVolume.py`` for example usage.
    
    .. note:: This class does not keep track of the data you've already downloaded.  
              Every call to :py:func:`downloadSubVolume()` results in a new download.
              For automatic blockwise local caching of remote datasets, see :py:class:`RESTfulBlockwiseFileset`.

    .. note:: See the unit tests in ``tests/testRESTfulVolume.py`` for example usage.              
    """
    
    #: These fields describe the schema of the description file.
    #: See the source code comments for a description of each field.    
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
        """
        Parse the description file at the given path and return a 
        :py:class:`jsonConfig.Namespace` object with the description parameters.
        The file will be parsed according to the schema given by :py:data:`RESTfulVolume.DescriptionFields`.
        Any optional parameters not provided by the user are filled in automatically.
        
        :param descriptionFilePath: The path to the description file to parse.
        """
        # Read file
        description = RESTfulVolume.DescriptionSchema.parseConfigFile( descriptionFilePath )
        cls.updateDescription(description)
        return description

    @classmethod
    def updateDescription(cls, description):
        """
        Some description fields are optional.
        If they aren't provided in the description JSON file, then this function provides 
        them with default values, based on the other description fields.
        """
        # Augment with default parameters.
        if description.origin_offset is None:
            description.origin_offset = numpy.array( [0]*len(description.bounds) )
        description.shape = description.bounds - description.origin_offset

    @classmethod
    def writeDescription(cls, descriptionFilePath, descriptionFields):
        """
        Write a :py:class:`jsonConfig.Namespace` object to the given path.
        
        :param descriptionFilePath: The path to overwrite with the description fields.
        :param descriptionFields: The fields to write.
        """
        RESTfulVolume.DescriptionSchema.writeConfigFile( descriptionFilePath, descriptionFields )

    def __init__( self, descriptionFilePath=None, preparsedDescription=None ):
        """
        Constructor.  Uses `readDescription` interally.
        
        :param descriptionFilePath: The path to the .json file that describes the remote volume.
        :param preparsedDescription: (Optional) Provide pre-parsed description fields, in which 
                                     case the provided description file will not be parsed.
        """
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
        """
        Download a cutout volume from the remote dataset.
        
        :param roi: The subset of the volume to download, specified as a tuple of coordinates: ``(start, stop)``
        :param outputDatasetPath: The path to overwrite with the downloaded hdf5 file.
        """
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
        logger.info( "Opening url for region {}..{}: {}".format(roi[0], roi[1], url) )

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
        logger.info( "Downloading RESTful subvolume to file: {}".format( pathComponents.externalPath ) )
        with open(pathComponents.externalPath, 'w') as rawFileToWrite:
            # This is where the data is actually downloaded.
            # Limit memory usage here: Use shutil instead of the write/read combo commented out below.
            # Download in 20MB bursts
            shutil.copyfileobj( hdf5RawFileObject, rawFileToWrite, length=20*1024*1024 )
            # rawFileToWrite.write( hdf5RawFileObject.read() ) # <--Memory-hog
        logger.info( "Finished downloading file: {}".format( pathComponents.externalPath ) )

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
