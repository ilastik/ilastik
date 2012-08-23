backend = 'new'

if backend == 'old':
    import warnings
    warnings.warn("Using OLD request implementation.")
    from request import *
elif backend == 'new':
    from request_rewrite import *
else:
    assert False
