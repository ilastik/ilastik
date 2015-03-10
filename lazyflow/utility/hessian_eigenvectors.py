import numpy
import vigra

def hessian_eigenvectors( a, sigma, sort=True ):
    """
    For the given grayscale image, return the eigenvalues and eigenvectors 
    of its scaled hessian matrix image.
    
    The input image must not have a channel dimension.  That is, it must 
    only contain spatial dimensions, no singleton channel dimension.

    NOTE: This function relies on the broadcasting behavior in the numpy.linalg module.
          Older versions of numpy do not provide that behavior.
    
    Args:
        a: The image to process.  Must not have a channel dimension.
        sigma: The scale of the hessian computation
        sort: If True, sort the results in descending order by eigenvalue 
              (i.e. from largest to smallest eigenvalue)     
    """
    assert numpy.__version__ >= '1.8.0', \
        "This function requires broadcasting support in `numpy.linalg.eigh()`, so you need at least numpy v1.8.0"
    assert a.shape[-1] != 1, \
        "This function is designed to work on single-channel images without a channel dimension.  "\
        "Drop any singleton dimensions before calling this function."
    
    if hasattr(sigma, '__len__'):
        assert len(sigma) == a.ndim, \
            "sigma {} doesn't match the dimensionality of the input image, which has shape {}"\
            .format( sigma, a.shape )
    
    # Note: vigra returns only the upper-triangle of the hessian (to save memory)
    hessian_upper = vigra.filters.hessianOfGaussian(a, sigma)
    
    # Convert it to a full tensor (upper half only)
    hessian_full = convert_symmetric_tensor_vector_to_full_tensor_matrix(hessian_upper, a.ndim, upper_only=True)

    # Solve eigensystem at each pixel (where each pixel is an NxN matrix)
    eig_vals, eig_vects = numpy.linalg.eigh(hessian_full, UPLO='U')
    
    # eig_vects contains COLUMN vectors, but we want ROW vectors
    eig_vects = eig_vects.transpose( tuple(range(len(eig_vects.shape)))[:-2] + (-1,-2)  )
    
    if sort:
        # We need to sort the eigenvalues and then re-order the eigen vectors in the same way.
        # You would think the following code would do the trick, but this is horribly slow for some reason.
        # sort_order = numpy.argsort( eig_vals, axis=-1 )
        # eig_vals = eig_vals[sort_order[...,::-1]]
        # eig_vects = eig_vects[sort_order[...,::-1]]

        # Instead, we concatenate the values + vectors into one array,
        # and then "view" each concatenated pixel as a single combined value,
        # sort the combined values, and then split the results back into the value/vector images.
        # Believe it or not, this is WAY faster than using numpy.argsort() + fancy indexing.
        assert eig_vals.dtype == eig_vects.dtype
        
        combined = numpy.concatenate((eig_vals[...,None], eig_vects), axis=-1)
        combined = numpy.ascontiguousarray(combined)
        combined_dtypes = [eig_vals.dtype.str]*(1+eig_vects.shape[-1])
        combined_names = map(str, range(1+eig_vects.shape[-1]))
        
        combined_view = combined.view( dtype={'names':combined_names, 'formats':combined_dtypes } )
        combined_view.sort(axis=-1)

        # We sorted the VIEW, so the original combined array is now sorted.
        # (Use ::-1 to obtain DESCENDING order.)
        eig_vals = combined[...,::-1,0]
        eig_vects = combined[...,::-1,1:]

    return eig_vals, eig_vects

def convert_symmetric_tensor_vector_to_full_tensor_matrix(tensor_vector_image, tensor_ndim, upper_only=False):
    """
    The Vigra API often uses vectors for tensor images (such as a Hessian image)
    instead of the full tensor matrix image.  See vigra docs for details.
    
    For example, a symmetric 2x2 tensor [[t00, t01], [t10, t11] in vigra is stored as a 3-element vector:
    [t00, t01, t11] (since t01 == t10 due to symmetry)
    
    This function converts such a vector image into a full tensor image.
    For example, an image with shape (100,100,3) would be converted to a new image (100,100,2,2).
    
    If upper_only is True, then the lower triangular elements will be left UNINITIALIZED.
    """
    image_shape = tensor_vector_image.shape[:-1] # Shape WITHOUT tensor dimensions
    assert tensor_vector_image.shape[-1] == tensor_ndim*(tensor_ndim+1)/2

    # 2D: Use a stride trick to return a view
    if tensor_ndim == 2:
        img = numpy.ascontiguousarray(tensor_vector_image)    
        new_shape = img.shape[:-1] + (2,2)
        new_strides = img.strides[:-1] + 2*(img.strides[-1],)
        img_view = numpy.lib.stride_tricks.as_strided(img, new_shape, new_strides)
        return img_view    
    
    # Convert the vigra form into the full tensor form
    # Create a the full tensor array and copy the vigra data into each half
    full_tensor = numpy.ndarray( image_shape + (tensor_ndim,tensor_ndim),
                                 dtype=tensor_vector_image.dtype )

    upper_indices = (slice(None),)*len(image_shape) + numpy.triu_indices(tensor_ndim)
    assert len(upper_indices[-1]) == tensor_vector_image.shape[-1]

    # Copy into upper triangle 
    full_tensor[upper_indices] = tensor_vector_image
    
    # Now copy lower triangle (via a transpose)   
    # For optimization, this can be skipped if the user doesn't need it.
    if not upper_only:
        full_tensor.transpose( tuple(range(len(image_shape))) + (-1,-2)  )[upper_indices] = tensor_vector_image
    return full_tensor

if __name__ == "__main__":
    #
    # FIXME: This quick little test only verifies the eigenVALUES, not eigenVECTORS.
    #
    import time
    from sklearn.externals import joblib
    #img = joblib.load("testData/img.jlb").astype(numpy.float32)
    img = numpy.random.random((50,100,110)).astype(numpy.float32)
    assert img.ndim == 3
    print "img.shape:", img.shape

    print "Computing eigenvalues with vigra"
    t1 = time.time()
    vigra_eig_vals = vigra.filters.hessianOfGaussianEigenvalues( img, 1.0 )
    print "...", time.time() - t1, "seconds"

    print "Computing eigenvalues with vigra+numpy.linalg"
    t1 = time.time()
    hessian_upper = vigra.filters.hessianOfGaussian(img, 1.0)
    hessian_full = convert_symmetric_tensor_vector_to_full_tensor_matrix(hessian_upper, img.ndim, upper_only=True)
    numpy_eig_vals = numpy.linalg.eigvalsh(hessian_full, 'U')[...,::-1]
    print "...", time.time() - t1, "seconds"

    print "Computing eigenvalues and eigenvectors"    
    t1 = time.time()
    sorted_eig_vals, sorted_eig_vects = hessian_eigenvectors(img, 1.0)
    print "...", time.time() - t1, "seconds"

    #numpy.save('/tmp/sorted_eig_vals.npy', sorted_eig_vals)
    #numpy.save('/tmp/vigra_eig_vals.npy', vigra_eig_vals)

    print "comparing eigenVALUE results..."
    assert numpy.allclose(sorted_eig_vals, vigra_eig_vals, rtol=0.001, atol=0.1)
    assert numpy.allclose(sorted_eig_vals, numpy_eig_vals, rtol=0.001, atol=0.1)
    print "DONE. TEST PASSED."
