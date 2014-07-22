"""
(This script is not generally useful for most ilastik users or developers.)

Input: hdf5 volume
Output: directory of .png tiles representing the volume.  
"""
import sys
import os

import argparse

import h5py
import vigra

from lazyflow.utility import PathComponents
from lazyflow.roi import getIntersectingBlocks, roiFromShape, getBlockBounds, roiToSlice

def main():
    # Usage: python make_tiles.py --tile_size=250 /path/to/my_vol.h5/some/dataset /path/to/output_dir
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--tile_size', type=int)
    parser.add_argument('hdf5_datset_path')
    parser.add_argument('output_dir')
    
    parsed_args = parser.parse_args( sys.argv[1:] )
    path_comp = PathComponents( parsed_args.hdf5_datset_path )
    
    with h5py.File(path_comp.externalPath) as input_file:
        vol_dset = input_file[path_comp.internalPath]
        assert len(vol_dset.shape) == 3
        
        tile_blockshape = (1, parsed_args.tile_size, parsed_args.tile_size)
        tile_starts = getIntersectingBlocks( tile_blockshape, roiFromShape( vol_dset.shape ) )

        if not os.path.exists(parsed_args.output_dir):
            os.makedirs(parsed_args.output_dir)

        print "Writing {} tiles ...".format( len(tile_starts) )
        for tile_start in tile_starts:
            tile_roi = getBlockBounds( vol_dset.shape, tile_blockshape, tile_start )
            sys.stdout.write("Tile: {} ".format( tile_roi ))
            sys.stdout.flush()

            tile_data = vol_dset[ roiToSlice(*tile_roi) ]
            tile_data = vigra.taggedView(tile_data, 'zyx')
            sys.stdout.write('reading... ')
            sys.stdout.flush()

            tile_name = 'tile_z{:05}_y{:05}_x{:05}.png'.format( *tile_start )
            output_path = os.path.join( parsed_args.output_dir, tile_name )

            sys.stdout.write('writing... ')
            sys.stdout.flush()
            vigra.impex.writeImage( tile_data[0], output_path, dtype='NATIVE' )
            sys.stdout.write('done.\n')
            sys.stdout.flush()
        print "DONE."
    
if __name__ == "__main__":
    sys.exit( main() )
