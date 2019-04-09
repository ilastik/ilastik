from __future__ import print_function
import sys
import logging
import argparse

import h5py
import numpy as np

logger = logging.getLogger(__name__)


def subsample_h5(input_filepath, dset_name, output_filepath, sample_stride):
    """
    Sub-sample an HDF5 volume.
    Merely picks existing pixel values -- does not do any averaging.
    """
    logger.info("Opening files...")
    with h5py.File(input_filepath, "r") as input_file, h5py.File(output_filepath) as output_file:

        input_dset = input_file[dset_name]

        if dset_name in output_file:
            del output_file[dset_name]

        # This will use a lot of RAM if the volume is big...
        # TODO: Process in blocks
        logger.info("Extracting subsampled volume (shape={})...".format(input_dset.shape))
        subsample_slicing = input_dset.ndim * (slice(None, None, sample_stride),)

        # Note: The extra [:] here is because h5py is really slow at slicing.
        #       It's better to just read the whole volume and then let numpy do the slicing in RAM.
        subsampled_volume = input_file[dset_name][:][subsample_slicing]

        logger.info("Writing subsampled volume (shape={})...".format(subsampled_volume.shape))
        output_dset = output_file.create_dataset(
            dset_name,
            data=subsampled_volume,
            chunks=input_dset.chunks,
            compression=input_dset.compression,
            compression_opts=input_dset.compression_opts,
        )

    logger.info("Wrote volume to {}/{}".format(output_filepath, dset_name))


def main():
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sample-stride", help="Subsample stride", type=int, default=2)
    parser.add_argument("input_filepath_and_dset", help="example: myfile.h5/myvolume")
    parser.add_argument("output_filepath", help="example: my_subsampled.h5")
    args = parser.parse_args()

    input_filepath, dset_name = args.input_filepath_and_dset.split(".h5")
    input_filepath += ".h5"
    dset_name = dset_name[1:]  # drop leading '/'
    if not dset_name:
        sys.stderr.write("You must provide a dataset name, e.g. myfile.h5/mydataset\n")
        sys.exit(1)

    subsample_h5(input_filepath, dset_name, args.output_filepath, args.sample_stride)


if __name__ == "__main__":
    main()
