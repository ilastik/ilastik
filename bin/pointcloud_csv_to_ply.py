import sys
import csv
import textwrap
import collections

import numpy

from ilastik.utility.commandLineProcessing import ParseListFromString

import logging
logger = logging.getLogger(__name__)

CSV_FORMAT = { 'delimiter' : '\t', 'lineterminator' : '\n' }
Point3D = collections.namedtuple("Point3D", "x_px y_px z_px")

def pointcloud_csv_to_ply( csv_filepath, ply_filepath, offset=None, scale=None ):
    """
    Convert the given ilastik csv pointcloud file to Stanford PLY format.
    
    csv_filepath: input path
    ply_filepath: output path to overwrite
    offset: If provided, will be subtracted from all points before export. (Can be either scalar or XYZ vector.)
    scale: If provided, will be divided from all points before export. (Can be either scalar or XYZ vector.)    
    """
    logger.debug( "Reading input: {}".format( csv_filepath ) )
    points = []
    with open(csv_filepath, 'r') as f_in:
        csv_reader = csv.DictReader(f_in, **CSV_FORMAT)
        for row in csv_reader:
            x_px, y_px, z_px = list(map(int, (row["x_px"], row["y_px"], row["z_px"])))
            point = Point3D(x_px, y_px, z_px)
            points.append(point)

    if offset or scale:
        logger.debug( "Copying to array" )
        point_array = numpy.asarray( points, dtype=numpy.float32 )

        if offset:
            logger.debug( "Removing offset: {}".format( offset ) )
            point_array -= offset

        if scale:
            logger.debug( "Removing scale: {}".format( scale ) )
            point_array /= scale
        
        points = point_array

    logger.debug( "Writing to output: {}".format( ply_filepath ) )
    with open(ply_filepath, 'w') as f_out:
        header = textwrap.dedent( """\
            ply
            format ascii 1.0
            element vertex {num_points}
            property float x
            property float y
            property float z
            end_header
            """)
        header = header.format( num_points=len(points) )
        f_out.write( header )

        for point in points:
            f_out.write("{:.5f} {:.5f} {:.5f}\n".format( *point ))

    logger.debug("POINTCLOUD EXPORT COMPLETE")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_filepath")
    parser.add_argument("ply_filepath")
    parser.add_argument("offset", required=False,
                        help="Offset to remove from all point coordinates during export, e.g. [7.1, 8, 0]",
                        action=ParseListFromString)
    parser.add_argument("scale", required=False,
                        help="Scale to divide from all point coordinates during export, e.g. [100, 100, 1.1]",
                        action=ParseListFromString)

    parsed_args = parser.parse_args()

    logger.addHandler( logging.StreamHandler(sys.stdout) )
    logger.setLevel(logging.DEBUG)    

    # Evaluate offset/scale strings if provided
    offset = parsed_args.offset
    scale = parsed_args.scale

    sys.exit( pointcloud_csv_to_ply( parsed_args.csv_filepath, 
                                     parsed_args.ply_filepath,
                                     offset,
                                     scale ) )
