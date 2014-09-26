import numpy
import vigra

# Here are two possible ways of measuring the size of the contact area between two objects in a label volume.

def measure_surface_contact_A( label_volume, object_label_1, object_label_2, contact_distance=1 ):
    """
    Measure the area of contact between two objects by counting the number of 
    pixels within object 2 that lie exactly N distant from object 1.
    """
    # Reduce to 3D if necessary: remove singleton axes.
    label_volume = label_volume.squeeze()
    assert label_volume.ndim == 3
    
    # Remove everything but object 1
    vol_1 = numpy.where( label_volume == object_label_1, object_label_1, 0 )

    # Compute distance to object 1 for all pixels in the volume. 
    distances = vigra.filters.distanceTransform3D( vol_1.astype(numpy.float32) )
    distances_int = numpy.round_(distances).astype(int)
    #distances_int = distances.astype(int)

    # Consider only the pixels within object 2
    distances_to_object_2 = numpy.where( label_volume == object_label_2, distances_int, 9999 )
    
    # Measure contact surface area
    contact_area = (distances_to_object_2 == contact_distance).astype(int).sum()
    return contact_area

def measure_surface_contact_B( label_volume, object_label_1, object_label_2, contact_distance=1 ):
    """
    Measure the area of contact between two objects by generating a shell around object 1 via 
    dilation and then counting the number of pixels in the shell that fall within object 2.
    
    Does not yield the same results as method 1, above.
    """
    assert object_label_1 <= 255
    assert object_label_2 <= 255
    object_label_1 = numpy.uint8(object_label_1)
    object_label_2 = numpy.uint8(object_label_2)
    
    # Reduce to 3D if necessary: remove singleton axes.
    label_volume = label_volume.squeeze()
    assert label_volume.ndim == 3
    
    label_volume = numpy.asarray(label_volume, numpy.uint8)
    
    # Remove everything but object 1
    vol_1 = numpy.where( label_volume == object_label_1, numpy.uint8(object_label_1), numpy.uint8(0) )

    # Generate a "shell" of pixels around object 1 via a dilation
    dilated = vigra.filters.multiBinaryDilation(vol_1, contact_distance)
    if contact_distance > 1:
        # Generate: shell: Subtract everything but the outermost pixels of the dilation.
        dilated -= vigra.filters.multiBinaryDilation(vol_1, contact_distance-1)

    # Consider only the pixels within object 2
    contact_volume = numpy.where( label_volume == object_label_2, dilated, 0 )
    
    # Measure contact surface area
    contact_area = contact_volume.sum()
    return contact_area

if __name__ == "__main__":
    import h5py
    import argparse
    from lazyflow.utility import PathComponents

    parser = argparse.ArgumentParser()
    parser.add_argument('h5_volume_path', help='A path to the hdf5 volume, with internal dataset name, e.g. /tmp/myfile.h5/myvolume')
    parser.add_argument('object_label_1', help='The label value of the first object for comparison')
    parser.add_argument('object_label_2', help='The label value of the second object for comparison')
    
    parsed_args = parser.parse_args()
    h5_path_comp = PathComponents(parsed_args.h5_volume_path)
    object_label_1 = int(parsed_args.object_label_1)
    object_label_2 = int(parsed_args.object_label_2)
    
    with h5py.File(h5_path_comp.externalPath, 'r') as f:
        volume = f[h5_path_comp.internalPath][:]

    contact_area = measure_surface_contact_A(volume, object_label_1, object_label_2, contact_distance=1)

    # Alternative implementation:
    #contact_area = measure_surface_contact_B(volume, object_label_1, object_label_2, contact_distance=1)

    print contact_area
