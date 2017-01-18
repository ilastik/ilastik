from builtins import zip
from builtins import range
from builtins import object
class TransposedView( object ):
    """
    A read-only transposed view of an array-like object.
    """
    def __init__(self, base, permutation):
        """
        Parameters
        ----------
        base
            The original array-like object. Must have the following members:
            - shape
            - dtype
            - ndim
            - transpose()
            - __getitem__()
        
        permutation
            A tuple of index orders, as you would pass to ndarray.transpose(), with one extra feature:
            You may insert None into the permutation, which inserts a singleton dimension into view.
        """
        self.base = base
        self.dtype = base.dtype
        self.ndim = base.ndim + len([p for p in permutation if p is None])
        self._permutation = permutation or tuple(range(self.base.ndim))
        
        if set([p for p in self._permutation if p is not None]) != set(range(self.base.ndim)):
            raise ValueError("axes don't match array")

        shape = ()
        for p in self._permutation:
            if p is not None:
                shape += (base.shape[p],)
            else:
                shape += (1,)
        self.shape = shape
        self.ndim = len(shape)
    
    def __getitem__(self, args):
        if not isinstance(args, tuple):
            args = (args,)
        # Reorder the args in the same order as the base
        baseargs = [slice(None)]*self.base.ndim
        for (p, arg) in zip(self._permutation, args):
            if p is not None:
                baseargs[p] = arg
        baseargs = tuple(baseargs)
        base_permutation = [p for p in self._permutation if p is not None]

        # Extract from base
        data_from_base = self.base[baseargs]
        
        # Transpose to our viewed order
        transposed = data_from_base.transpose(*base_permutation)
        
        # Insert singleton dimensions for each 'None' in our view permuation ('unsqueeze' the base data)
        unsqueeze_slicing = [ slice(None) if p is not None else None for p in self._permutation ]
        unsqueezed = transposed[unsqueeze_slicing]
        return unsqueezed

    def transpose(self, *permutation):
        """
        Return a transposed view of self
        """
        if not permutation:
            permutation = tuple(range(self.ndim)[::-1])
        return _TransposedView( self, permutation )

if __name__ == "__main__":
    import numpy as np
    a = np.random.random( (34, 12, 23) )
    t = TransposedView(a, (2,0,1,None))
    assert t.shape == a.transpose(2,0,1)[...,None].shape
    assert (t[:] == a.transpose(2,0,1)[...,None]).all()
