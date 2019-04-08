"""
(This script is not generally useful for most ilastik users or developers.)

Input: hdf5 volume
Output: directory of .png tiles representing the volume.
"""
if __name__ == "__main__":
    import sys
    import h5py

    import logging
    import argparse
    from lazyflow.utility import PathComponents, export_to_tiles

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.INFO)

    # Usage: python make_tiles.py --tile_size=250 /path/to/my_vol.h5/some/dataset /path/to/output_dir
    parser = argparse.ArgumentParser()
    parser.add_argument("--tile_size", type=int)
    parser.add_argument("hdf5_dataset_path")
    parser.add_argument("output_dir")

    parsed_args = parser.parse_args(sys.argv[1:])

    path_comp = PathComponents(parsed_args.hdf5_dataset_path)
    with h5py.File(path_comp.externalPath) as input_file:
        vol_dset = input_file[path_comp.internalPath]
        export_to_tiles(vol_dset, parsed_args.tile_size, parsed_args.output_dir)
