import sys
import os
import glob

import h5py
import vigra

if len(sys.argv) < 3:
    sys.stderr.write('Example usage: {} output_file.h5 "my_stack_channel_one_*.png" "my_stack_channel_two_*.png" ...\n'.format( sys.argv[0] ))
    sys.exit(1)

h5_path = sys.argv[1]
stack_globs = sys.argv[2:]

stack_lists = []
for globstr in stack_globs:
    files = sorted( glob.glob(globstr) )

    if len(files) == 0:
        sys.stderr.write("Couldn't find any input files matching pattern: {}".format( globstr ))
        sys.exit(2)
    if stack_lists and len(files) != len(stack_lists[-1]):
        sys.stderr.write("Wrong number of files detected with pattern: {}".format( globstr ))
        sys.exit(2)

    stack_lists.append(files)

C = len(stack_lists)
Z = len(stack_lists[0])
info = vigra.impex.ImageInfo(stack_lists[0][0])
X, Y, _chan = info.getShape()
assert _chan == 1, "This code assumes each input stack contains exactly 1 channel."

dtype = info.getDtype()

volume_shape = (Z, Y, X, C)
axistags = vigra.defaultAxistags('zyxc')

with h5py.File(h5_path, 'w') as f:
    dset = f.create_dataset('stacked_channels', shape=volume_shape, dtype=dtype, chunks=True)
    dset.attrs['axistags'] = axistags.toJSON()

    for c, files in enumerate(stack_lists):
        print "Copying channel {}...".format( c )
        for z, filename in enumerate(files):
            sys.stdout.write("{} ".format( z ))
            sys.stdout.flush()
            img = vigra.impex.readImage(filename, dtype='NATIVE')
            dset[z,:,:,c] = img.transpose()
        sys.stdout.write('\n')

print "FINISHED"

