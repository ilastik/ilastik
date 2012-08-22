import os
import uuid
import tempfile

def mktempdir(prefix=None):
    if prefix is None:
        prefix = '/tmp'
    else:
        prefix = tempfile.gettempdir()
    
    d = os.path.join( prefix, str(uuid.uuid1()) )
    d = os.path.abspath(d)
    os.mkdir(d)
    return d