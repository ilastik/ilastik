import numpy

def blockwise_view( a, blockshape, require_aligned_blocks=True ):
    """
    For a given N-D array, return a 2N-D array, rearranged so each ND block (tile) 
    of the original array is indexed by its block address using the first N 
    indexes of the output array.
    
    Args:
        a: The ND array (5D or less)
        blockshape: The tile shape
        require_aligned_blocks: If True, check to make sure no data is "left over" 
                                in each row/column/etc. of the output view.
                                That is, the blockshape must divide evenly into the full array shape.
                                If False, "leftover" items that cannot be made into complete blocks 
                                will be discarded from the output view.
    
    Note: This implementation simply calls blockwise_view_5d() below, 
          and drops the extra axes before returning the result.  
          Therefore, this function doesn't support arrays with more than 5 dimensions.
    """
    assert a.ndim <= 5, "This function supports only up to 5 dimensions."
    assert len(a.shape) == len(blockshape)
    assert a.flags['C_CONTIGUOUS'], "This function relies on the memory layout of the array."

    if require_aligned_blocks:
        assert (numpy.mod(a.shape, blockshape) == 0).all(), \
            "blockshape {} must divide evenly into array shape {}"\
            .format( blockshape, a.shape )

    blockshape = tuple(blockshape)

    # Pad leading dims with 1
    padded_dims = 5-a.ndim
    blockshape_5d = (1,) * padded_dims + blockshape
    a_5d = a[(None,)*padded_dims]

    view_10d = blockwise_view_5d( a_5d, blockshape_5d )
    
    # Drop the extra dimensions
    slicing_5d = (0,)*padded_dims + (slice(None),)*a.ndim
    slicing_10d = slicing_5d + slicing_5d
    
    view = view_10d[slicing_10d]
    assert view.shape == tuple(numpy.array(a.shape) / blockshape) + blockshape
    if require_aligned_blocks:
        assert view.size == a.size
    return view
    
def blockwise_view_5d( a, blockshape ):
    """
    Return a 10-D view of a 5-D array, rearranged so each 5D block (tile) of the 
    original array is indexed by its block address using the first 5 indexes 
    of the output array.
    
    This technique could be generalized to truly ND arrays, but that would be 
    harder to read and 5 is enough for our purposes.
    
    Inspired by the 2D example shown here:
    http://stackoverflow.com/a/8070716/162094
    """
    assert len(blockshape) == len(a.shape) == 5
    assert a.flags['C_CONTIGUOUS'], "This function relies on the memory layout of the array."
    blockshape = tuple(blockshape)

    # Give each axis a name: 
    # For readability, we use the typical names (tzyxc), 
    #  but the true order of your input array is irrelevant.
    t,z,y,x,c = a.shape
    bt, bz, by, bx, bc = blockshape
    view_shape = tuple(numpy.array(a.shape) / blockshape) + blockshape

    # Strides from one block to another
    inter_block_strides = a.itemsize * numpy.array( [ z*y*x*c*bt,
                                                        y*x*c*bz,
                                                          x*c*by,
                                                            c*bx,
                                                              bc ] )

    # Strides within each block
    intra_block_strides = a.itemsize * numpy.array( [ z*y*x*c,
                                                        y*x*c,
                                                          x*c,
                                                            c,
                                                            1 ] )
    
    strides = tuple(inter_block_strides) + tuple(intra_block_strides)

    # This is where the magic happens.
    # Generate a view with our new strides.
    return numpy.lib.stride_tricks.as_strided(a, shape=view_shape, strides=strides)
