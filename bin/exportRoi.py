#!python
"""
Executable script for obtaining cutout volumes from a blockwise fileset.
Two export formats are supported:
- 'single-hdf5' exports an arbitrary roi to a single hdf5 output file
- 'blockwise-subset' creates a new blockwise fileset directory tree, simply 
    by copying the necessary files from the original fileset. This is much 
    faster than 'single-hdf5' for large cutout volumes.
"""

import os
import sys
import logging
import argparse

from lazyflow.utility.io import BlockwiseFileset, BlockwiseFilesetFactory

# DEBUG:
#sys.argv.append( "--format=blockwise-subset" )
#sys.argv.append( "/nobackup/bock/bock11/description-256.json" )
#sys.argv.append( "[(0,1024*20,1024*20),(1233, 1024*20+256*2, 1024*20+256*2)]" )
#sys.argv.append( "/tmp/test_export" )

logger = logging.getLogger("lazyflow.utility.io.blockwiseFileset")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

argparser = argparse.ArgumentParser( description="Blockwise Fileset Cutout Export Utility")
argparser.add_argument('--format', default="blockwise-subset", help='The format to export to.', choices=['single-hdf5', 'blockwise-subset'], required=False)
argparser.add_argument('--coordinates', default="absolute", help='How to interpret the roi arg.', choices=['absolute', 'view'], required=False)
argparser.add_argument('description_path', help='Path to source dataset description JSON file.')
argparser.add_argument('roi', help='The roi you want to export, in ABSOLUTE coordinates (i.e. the coords on the filesystem, not the current view)')
argparser.add_argument('export_dir', help='The directory to write the cutout data to.')

example_usage = 'Example: %(prog)s --format=blockwise-subset data_description.json "[(0,10,20), (10,20,30)]" /tmp/exported_data\n'
argparser.usage = argparser.format_usage() + example_usage

parsed_args = argparser.parse_args(sys.argv[1:])


def showUsage():
    argparser.print_help(sys.stderr)
    exit(1)

description_path = parsed_args.description_path
export_dir = parsed_args.export_dir

if not os.path.exists(description_path):
    sys.stderr.write( "Couldn't find description file: {}.\n".format( description_path ) )
    showUsage()

try:
    roi = eval( parsed_args.roi )
except:
    sys.stderr.write( "Didn't understand roi: {}\n".format(parsed_args.roi) )
    showUsage()

try:
    if not os.path.exists(export_dir):
        os.makedirs(parsed_args.export_dir)
except:
    sys.stderr.write( "Couldn't find/create export directory: {}\n".format( parsed_args.export_dir ) )
    raise # Re-raise so the user sees what went wrong

if not isinstance( roi, (list,tuple) ) \
or not isinstance( roi[0], (list, tuple) ) \
or not isinstance( roi[1], (list, tuple) ):
    sys.stderr.write( "Roi: {} is not valid type.\n".format( roi ) )
    showUsage()

with BlockwiseFilesetFactory.create(description_path, 'r') as bfs:
    if not ( len(roi[0]) == len(roi[1]) == len(bfs.description.view_shape) ):
            sys.stderr.write( "Roi dimensionality doesn't match dataset dimensionality.\n" )
            sys.exit(1)

    use_view_coordinates = (parsed_args.coordinates == 'view')

    if parsed_args.format == 'single-hdf5':
        exportedPath = bfs.exportRoiToHdf5( roi, export_dir, use_view_coordinates )
        print "Exported data to file: {}".format( exportedPath )
    elif parsed_args.format == 'blockwise-subset':
        exported_description_path = bfs.exportSubset( roi, export_dir, use_view_coordinates )
        print "Exported data to blockwise subset: {}".format( exported_description_path )
    


