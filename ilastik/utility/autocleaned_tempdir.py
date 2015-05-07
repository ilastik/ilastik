import contextlib    
import tempfile
import shutil

@contextlib.contextmanager
def autocleaned_tempdir(autoclean=True):
    """
    Context manager.
    Creates a temporary directory upon entry, and removes it upon exit.
    
    Args:
        autoclean: For debugging purposes, it may sometimes be convenient 
                    to inspect the temporary files after a test.
    
    Example:    
        with autocleaned_tempdir() as tmpdir_path:
            with open(tmpdir_path, 'w') as f:
                f.write('Just testing here...')    
    """
    tmpdir = tempfile.mkdtemp()
    try:
        yield tmpdir
    finally:
        if autoclean:
            shutil.rmtree(tmpdir)
