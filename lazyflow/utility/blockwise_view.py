import numpy

def blockwise_view( a, blockshape, require_aligned_blocks=True ):
    """
    Return a 2N-D view of the given N-D array, rearranged so each ND block (tile) 
    of the original array is indexed by its block address using the first N 
    indexes of the output array.
    
    Args:
        a: The ND array
        blockshape: The tile shape
        require_aligned_blocks: If True, check to make sure no data is "left over" 
                                in each row/column/etc. of the output view.
                                That is, the blockshape must divide evenly into the full array shape.
                                If False, "leftover" items that cannot be made into complete blocks 
                                will be discarded from the output view.
 
    Here's a 2D example (this function also works for ND):
    
    >>> a = numpy.arange(1,21).reshape(4,5)
    >>> print a
    [[ 1  2  3  4  5]
     [ 6  7  8  9 10]
     [11 12 13 14 15]
     [16 17 18 19 20]]

    >>> view = blockwise_view(a, (2,2), False)
    >>> print view
    [[[[ 1  2]
       [ 6  7]]
    <BLANKLINE>
      [[ 3  4]
       [ 8  9]]]
    <BLANKLINE>
    <BLANKLINE>
     [[[11 12]
       [16 17]]
    <BLANKLINE>
      [[13 14]
       [18 19]]]]

    Inspired by the 2D example shown here: http://stackoverflow.com/a/8070716/162094
    """
    assert a.flags['C_CONTIGUOUS'], "This function relies on the memory layout of the array."
    blockshape = tuple(blockshape)
    view_shape = tuple(numpy.array(a.shape) / blockshape) + blockshape

    if require_aligned_blocks:
        assert (numpy.mod(a.shape, blockshape) == 0).all(), \
            "blockshape {} must divide evenly into array shape {}"\
            .format( blockshape, a.shape )

    # The code below is for the ND case.
    # For example, in 4D, given shape=(t,z,y,x) and blockshape=(bt,bz,by,bx),
    # we could have written this:
    #
    # intra_block_strides = a.itemsize * numpy.array([z*y*x,    y*x,    x,     1])
    # inter_block_strides = a.itemsize * numpy.array([z*y*x*bt, y*x*bz, x*by, bx])

    # strides within each block
    intra_block_strides = [1]
    for s in a.shape[-1:0:-1]:
        intra_block_strides.append( s*intra_block_strides[-1] )
    intra_block_strides = numpy.array(intra_block_strides[::-1])
    
    # strides from one block to another
    inter_block_strides = numpy.array(intra_block_strides) * blockshape
    
    intra_block_strides *= a.itemsize
    inter_block_strides *= a.itemsize

    strides = tuple(inter_block_strides) + tuple(intra_block_strides)

    # This is where the magic happens.
    # Generate a view with our new strides.
    return numpy.lib.stride_tricks.as_strided(a, shape=view_shape, strides=strides)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
