import os
import sys
import vigra
import logging

logger = logging.getLogger(__name__)

from lazyflow.roi import getIntersectingBlocks, roiFromShape, getBlockBounds, roiToSlice


def export_to_tiles(volume, tile_size, output_dir, print_progress=True):
    """
    volume: The volume to export (either hdf5 dataset or numpy array).  Must be 3D.
    tile_size: The width of the tiles to generate
    output_dir: The directory to dump the tiles to.
    """
    assert len(volume.shape) == 3

    tile_blockshape = (1, tile_size, tile_size)
    tile_starts = getIntersectingBlocks(tile_blockshape, roiFromShape(volume.shape))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logger.info("Writing {} tiles ...".format(len(tile_starts)))
    for tile_start in tile_starts:
        tile_roi = getBlockBounds(volume.shape, tile_blockshape, tile_start)

        if print_progress:
            sys.stdout.write("Tile: {} ".format(tile_roi))
            sys.stdout.flush()

        tile_data = volume[roiToSlice(*tile_roi)]
        tile_data = vigra.taggedView(tile_data, "zyx")

        if print_progress:
            sys.stdout.write("reading... ")
            sys.stdout.flush()

        tile_name = "tile_z{:05}_y{:05}_x{:05}.png".format(*tile_start)
        output_path = os.path.join(output_dir, tile_name)

        if print_progress:
            sys.stdout.write("writing... ")
            sys.stdout.flush()

        vigra.impex.writeImage(tile_data[0], output_path, dtype="NATIVE")

        if print_progress:
            sys.stdout.write("done.\n")
            sys.stdout.flush()

    logger.info("TILES COMPLETE.")
