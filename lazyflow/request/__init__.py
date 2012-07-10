backend = 'new'

if backend == 'old':
    from request import *
elif backend == 'new':
    from request_rewrite import *
else:
    assert False
