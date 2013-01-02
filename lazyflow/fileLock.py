"""
Implementation of a simple cross-platform file locking mechanism.
Modified from code retrieved on 2013-01-01 from http://www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python
Original code was released under the BSD License, as is this modified version.

Modifications in this version:
 - Accept an absolute path for the protected file (instead of a file name relative to cwd).
 - Allow timeout to be None.
 - Fixed a bug that caused the original code to be NON-threadsafe when the same FileLock instance was shared by multiple threads in one process.
   (The original was safe for multiple processes, but not multiple threads in a single process.  This version is safe for both cases.)
 - Mimic threading.Lock interface:
   - Added blocking parameter to ``acquire()`` method
   - ``__enter__`` always calls ``acquire()``, and therefore blocks if ``acquire()`` was called previously.
   - ``__exit__`` always calls ``release()``.  It is therefore a bug to call ``release()`` from within a context manager.
   - Added ``locked()`` function. 
"""

import os
import time
import errno
 
class FileLockException(Exception):
    pass
 
class FileLock(object):
    """ A file locking mechanism that has context-manager support so 
        you can use it in a with statement. This should be relatively cross
        compatible as it doesn't rely on msvcrt or fcntl for the locking.
    """
 
    def __init__(self, protected_file_path, timeout=None, delay=1):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the delay between each attempt to lock.
        """
        self.is_locked = False
        self.lockfile = protected_file_path + ".lock"
        self.timeout = timeout
        self.delay = delay
 
    def locked(self):
        return self.is_locked
 
    def acquire(self, blocking=True):
        """ Acquire the lock, if possible. If the lock is in use, and `blocking` is False, return False.
            Otherwise, check again every `self.delay` seconds until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it raises an exception.
        """
        start_time = time.time()
        while True:
            try:
                # Attempt to create the lockfile.
                # These flags cause os.open to raise an OSError if the file already exists.
                self.fd = os.open( self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR )
                os.close(self.fd)
                break;
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise 
                if self.timeout is not None and (time.time() - start_time) >= self.timeout:
                    raise FileLockException("Timeout occurred.")
                if not blocking:
                    return False
                time.sleep(self.delay)
        self.is_locked = True
        return True
 
    def release(self):
        """ Get rid of the lock by deleting the lockfile. 
            When working in a `with` statement, this gets automatically 
            called at the end.
        """
        self.is_locked = False
        os.unlink(self.lockfile)

 
    def __enter__(self):
        """ Activated when used in the with statement. 
            Should automatically acquire a lock to be used in the with block.
        """
        self.acquire()
        return self
 
 
    def __exit__(self, type, value, traceback):
        """ Activated at the end of the with statement.
            It automatically releases the lock if it isn't locked.
        """
        self.release()
 
 
    def __del__(self):
        """ Make sure that the FileLock instance doesn't leave a lockfile
            lying around.
        """
        if self.is_locked:
            self.release()

if __name__ == "__main__":
    import sys
    import functools
    import threading
    import tempfile
    temp_dir = tempfile.mkdtemp()
    protected_filepath = os.path.join( temp_dir, "somefile.txt" )
    fl = FileLock( protected_filepath )

    def writeLines(line, repeat=10):
        with fl:
            for _ in range(repeat):
                with open( protected_filepath, 'a' ) as f:
                    f.write( line + "\n" )
                    f.flush()
    
    th1 = threading.Thread(target=functools.partial( writeLines, "1111111111111111111111111111111" ) )
    th2 = threading.Thread(target=functools.partial( writeLines, "2222222222222222222222222222222" ) )
    th3 = threading.Thread(target=functools.partial( writeLines, "3333333333333333333333333333333" ) )
    th4 = threading.Thread(target=functools.partial( writeLines, "4444444444444444444444444444444" ) )
    
    th1.start()
    th2.start()
    th3.start()
    th4.start()
    
    th1.join()
    th2.join()
    th3.join()
    th4.join()
    
    assert not os.path.exists( fl.lockfile ), "The lock file wasn't cleaned up!"
    
    # Print the contents of the file.
    # Please manually inspect the output.  Does it look like the operations were atomic?
    with open( protected_filepath, 'r' ) as f:
        sys.stdout.write( f.read() )
    
    