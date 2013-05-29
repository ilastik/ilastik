import os
import sys
import argparse

import numpy
import h5py
import vigra

def gen_rand_npy(shape, dtype, drange, output_dir, filename):
    a = numpy.random.random(shape)
    a *= (drange[1] - drange[0])
    a += drange[0]
    numpy.save(os.path.join(output_dir, filename), a.astype(dtype))

def gen_cubes_npy(intensity_weights, cube_parameters, dtype, output_dir, filename):
    """
    intensity_weights: a volume.  Specifies the total volume shape, and the intensities of all non-zero pixels in the final volume.
    cube_parameters: a list of tuples: (width, distance, offset)
    """
    fileshape = intensity_weights.shape
    data = numpy.zeros(fileshape, dtype=dtype)
    for cube_width, cube_distance, cube_offset in cube_parameters:
        data |= cubes(fileshape, cube_width, cube_distance, cube_offset)
    
    data *= intensity_weights
    numpy.save( os.path.join(output_dir, filename), data.astype(dtype) )

def cubes(dimblock, dimcube, cubedist, cubeoffset):
    n = len(dimblock)
    dimcube = getlist(dimcube, n=n)
    cubedist = getlist(cubedist, n=n)
    cubeoffset = getlist(cubeoffset, n=n)
    
    indices = numpy.indices(dimblock)
    indices = numpy.rollaxis( indices, 0, len(dimblock)+1 )
    
    out = numpy.ones(dimblock, dtype=numpy.bool)
    
    for i in range(len(dimblock)):
        out = numpy.bitwise_and(out,(indices[...,i] + cubeoffset[i]) % cubedist[i] < dimcube[i])
    out = out.astype(numpy.uint8)
    return out

def getlist(a, n=3):
    try:
        len(a)
    except TypeError:
        a = [a]*n
    
    assert len(a)==n
    return a

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a set of images in various formats for testing.")
    parser.add_argument('output_dir', help='Directory to write the test images to.  Will be created if necessary')
    parsed_args = parser.parse_args()
    
    output_dir = parsed_args.output_dir
    
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except:
            sys.stderr("Wasn't able to create output directory: {}".format( output_dir ))
            sys.exit(1)

    if not os.path.isdir(output_dir):
        sys.stderr("Output location is not a directory! Giving up.")
        sys.exit(2)

    # Random data of various dimensionalities
    gen_rand_npy(shape=(1,100,100,20,1), dtype=numpy.uint8, drange=(0,255), output_dir=output_dir, filename='rand_uint8_5d.npy' )
    gen_rand_npy(shape=(100,100,20,1), dtype=numpy.uint8, drange=(0,255), output_dir=output_dir, filename='rand_uint8_4d.npy' )
    gen_rand_npy(shape=(100,100,20), dtype=numpy.uint8, drange=(0,255), output_dir=output_dir, filename='rand_uint8_3d.npy' )
    gen_rand_npy(shape=(100,100,20), dtype=numpy.uint8, drange=(0,255), output_dir=output_dir, filename='rand_uint8_3d.npy' )
    gen_rand_npy(shape=(100,100), dtype=numpy.uint8, drange=(0,255), output_dir=output_dir, filename='rand_uint8_2d.npy' )

    ## Volumes suitable for object classification
    
    # Two sizes of cube, offset from eachother
    cube_params = [ (5, 20, 0), (2, 20, 10) ]
    
    volume_shape = (100,100,100)
    
    # Binary segmentation
    binary_intensities = 255*numpy.ones(volume_shape, dtype=numpy.uint8)
    gen_cubes_npy( binary_intensities, cube_params, numpy.uint8, output_dir, 'cube_objects_binary.npy' )

    # Raw cubes (intensity image)    
    intensities = binary_intensities
    intensities[0:50] /= 2 # Left half is not as bright
    gen_cubes_npy( intensities, cube_params, numpy.uint8, output_dir, 'cube_objects_raw.npy' )














