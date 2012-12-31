from lazyflow.jsonConfig import JsonConfigSchema, AutoEval, FormattedField

RESTfulVolumeDescriptionFields = \
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

def parseRESTfulVolumeDescriptionFile( descriptionFilePath ):
    """
    Convenience function for parsing RESTful volume description files.
    Returns a Namespace object.
    (Similar to the behavior of argparse.ArgumentParser.parse_args() )
    """
    schema = JsonConfigSchema( RESTfulVolumeDescriptionFields )
    return schema.parseConfigFile( descriptionFilePath )

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
    "hdf5_dataset" : "cube"
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
    
    description = parseRESTfulVolumeDescriptionFile( descriptionFilePath )

    assert description.name == "Bock11-level0"
    assert description.axes == "zyx"
    assert description.dtype == numpy.uint8
