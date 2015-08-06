import numpy
import h5py
import vigra

def concatenate_hdf5_volumes(input_filepaths, output_filepath, axis=0):
    input_volumes = []
    for input_filepath in input_filepaths:
        print "Loading " + input_filepath + " ..."
        with h5py.File(input_filepath, 'r') as f_in:
            vol = get_dataset(f_in)[:]
            input_volumes.append( vol )

    print "Concatenating..."
    output_volume = numpy.concatenate( input_volumes, axis=axis )

    print "Output has shape: {}".format( output_volume.shape )
    print "Writing to: " + output_filepath + '/volume'
    with h5py.File(output_filepath, 'w') as f_out:
        f_out.create_dataset( 'volume', 
                              data=output_volume, 
                              chunks=True, 
                              compression='gzip', 
                              compression_opts=1 )
    print "DONE."

def get_dataset(f):
    """
    Return the only dataset in the hdf5 file.
    If there's more than one, it's an error.
    """
    dataset_names = []
    f.visit(dataset_names.append)
    if len(dataset_names) != 1:
        sys.stderr.write("Input HDF5 file should have exactly 1 dataset, but {} has {} datasets\n"
                         .format(f.filename, len(dataset_names)))
        sys.exit(1)
    return f[dataset_names[0]]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--axis", default=0, type=int)
    parser.add_argument("input_filepaths", nargs='+')
    parsed_args = parser.parse_args()
    
    concatenate_hdf5_volumes(parsed_args.input_filepaths, parsed_args.output, parsed_args.axis)
