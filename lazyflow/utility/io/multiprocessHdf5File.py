import os
import copy
import h5py
import threading
import warnings
import multiprocessing
import numpy

# This code uses multiprocessing to read hdf5 datasets faster
# NOTES:
# - So far, this code is:
#  -- *much slower* for unchunked datasets,
#  -- somewhat slower for chunked uncompressed datasets,
#  -- faster for compressed datasets
#
# THINGS TO TRY:
#  -- Right now we launch the process only once, which means it must serve requests of varying sizes
#     Instead, we might try launching a new throwaway process for every request.  
#     Overhead would be increased, but it would allow us to pass a shared-memory Array to the process, 
#         since we know the request size in advance.
#  -- Could memory-sharing be achieved instead via memory-mapped files and/or mem-mapped arrays?
#  -- Create a pool of requests instead of creating a request for every thread and volume combo.

class ReaderProcess(multiprocessing.Process):
    
    def __init__(self, filepath):
        name = 'ilastik_helper-' + os.path.split(filepath)[1]
        super( ReaderProcess, self ).__init__(name=name)
        self._filepath = filepath
        self._request_queue_recv, self._request_queue_send = multiprocessing.Pipe(duplex=False)
        self._result_queue_recv, self._result_queue_send = multiprocessing.Pipe(duplex=False)
        self.daemon = True

    def run(self):
        with h5py.File(self._filepath, 'r') as h5_file:
            (internal_path, slicing) = self._request_queue_recv.recv()
            # 'None' means stop the process.
            while internal_path is not None:
                try:
                    data = h5_file[internal_path][slicing]
                except Exception as ex:
                    self._result_queue_send.send( ex )
                else:
                    self._result_queue_send.send( (data.shape, data.dtype) )
                    #self._result_queue_send.send( data )
                    self._result_queue_send.send_bytes( numpy.getbuffer(data) )
                
                # Wait for the next request
                (internal_path, slicing) = self._request_queue_recv.recv()

    def read_subvolume(self, internal_path, slicing):
        # The reader process is not supposed to be shared by multiple threads.
        # Each thread should create its own reader process.
        self._request_queue_send.send( (internal_path, slicing) )
        response_info = self._result_queue_recv.recv()
        if isinstance(response_info, Exception):
            raise response_info
        shape, dtype = response_info
        #result = self._result_queue_recv.recv()
        raw_buffer = self._result_queue_recv.recv_bytes()
        result = numpy.frombuffer(raw_buffer, dtype=dtype).reshape(shape)
        result.setflags(write=True)
        return result

    def join(self):
        self._request_queue_send.send( (None, None) )
        super( ReaderProcess, self ).join()

class _Dataset(object):
    def __init__(self, mp_file, reader_process, internal_path):
        self._internal_path = internal_path
        self._reader_process = reader_process
        self.mp_file = mp_file
        
        if self.compression is None:
            warnings.warn( "MultiProcessHdf5File does not improve performance for non-compressed datasets! "
                           "Your dataset '{}' is not compressed.".format( self.mp_file._filepath + internal_path ) )
    
    def __getitem__(self, slicing):
        return self._reader_process.read_subvolume(self._internal_path, slicing)

    def __getattribute__(self, name):
        try:
            # If we have this attr, use it. 
            # (e.g. self.mp_file, self._internal_path, etc.)
            return object.__getattribute__(self, name)
        except:
            # Briefly open the file and read the attribute directly from h5py
            with h5py.File(self.mp_file._filepath) as f:
                val = getattr(f[self._internal_path], name)
                assert not callable(val), "MultiprocessingHdf5File Datasets cannot provide access to callable items."
                
                # Special case: copy hdf5 dataset attrs into a dict
                if name == 'attrs':
                    val = dict(val.items())
                return val

    def read_direct(self, out_array, slicing):
        out_array[:] = self[slicing]

class _Group(object):
    def __init__(self, mp_file, internal_path):
        self.mp_file = mp_file
        if internal_path == '':
            internal_path = '/'
        if internal_path[0] != '/':
            internal_path = '/' + internal_path
        if internal_path != '/' and internal_path[-1] == '/':
            internal_path = internal_path[:-1]
        self._internal_path = internal_path
    
    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def __iter__(self):
        return self.iterkeys()
    
    def keys(self):
        return list(self.iterkeys())
    
    def iterkeys(self):
        internal_path = self._internal_path
        if internal_path == '/':
            internal_path = ''
        for p in self.mp_file._all_paths:
            if p != internal_path and p.startswith(internal_path) and p[len(internal_path)] == '/':
                sub_path = p[len(internal_path):]
                splits = sub_path.split('/')
                if len(splits) == 2:
                    yield splits[1]

    def __getitem__(self, sub_path):
        if sub_path[0] != '/':
            sub_path = '/' + sub_path

        if self._internal_path != '/': 
            full_internal_path = self._internal_path + sub_path
        else:
            full_internal_path = sub_path

        try:        
            object_type = self.mp_file._all_paths[full_internal_path]
        except KeyError:
            raise
        
        if object_type is h5py.Dataset:
            return self.mp_file._get_dataset(full_internal_path)
        elif object_type is h5py.Group:
            return _Group( self.mp_file, full_internal_path )
        else:
            assert False, "Don't know how to access object: {}".format( object_type )

    def __getattribute__(self, name):
        try:
            # If we have this attr, use it. 
            # (e.g. self.mp_file, self._internal_path, etc.)
            return object.__getattribute__(self, name)
        except:
            # Briefly open the file and read the attribute directly from h5py
            with h5py.File(self.mp_file._filepath) as f:
                val = getattr(f[self._internal_path], name)
                assert not callable(val), "MultiprocessingHdf5File Groups cannot provide access to callable items."
                return copy.copy(val)

class MultiProcessHdf5File(_Group):
    
    def __init__(self, filepath, mode='r'):
        super( MultiProcessHdf5File, self ).__init__( self, '' )
        assert mode == 'r', "Only read-only access is permitted when using MultiProcessHdf5File objects."
        self._filepath = filepath
        self._reader_processes = {}
        self._lock = threading.Lock()
        
        self._all_paths = {}
        def add_path(key, val):
            # Store just the type for now.
            # All attributes will be read with high overhead (i.e. temporarily opening the file...)
            if key[0] != '/':
                key = '/' + key
            self._all_paths[key] = type(val)
        with h5py.File(filepath, 'r') as f:
            f.visititems(add_path)

    def _get_dataset(self, internal_path):
        thread_id = threading.current_thread().ident
        if thread_id not in self._reader_processes:
            with self._lock:
                if thread_id not in self._reader_processes:
                    self._reader_processes[thread_id] = ReaderProcess(self._filepath)
                    self._reader_processes[thread_id].start()
        return _Dataset( self, self._reader_processes[thread_id], internal_path )
    
    def __setitem__(self, *args):
        raise NotImplementedError("Not permitted to write to a file via MultiProcessHdf5File")
            
    def close(self):
        with self._lock:
            readers = self._reader_processes.values()
            self._reader_processes.clear()
            for reader in readers:
                reader.join()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()

if __name__ == "__main__":
    import numpy
    from functools import partial
    
    filepath = '/tmp/testfile.h5'
    datapath = 'mygroup/bigdata'
    
    testvol = numpy.indices((100,100,100)).astype(numpy.uint32).sum(0)
    with h5py.File(filepath, 'w') as f:
        f.create_dataset( datapath, data=testvol, chunks=True )
        f.create_dataset('mygroup/mybla/bla/somedata', data=1)
        f.create_dataset('othergroup/otherbla/bla/somedata', data=1)
        f.create_dataset('othergroup/otherbla2/bla/somedata', data=1)
    
    with MultiProcessHdf5File(filepath) as mphf:
        whole_vol = mphf[datapath][:]
        assert (whole_vol == testvol).all()

        print mphf[u'mygroup'].name
        print mphf[datapath].attrs.keys()
        print mphf[datapath].shape
        print mphf[datapath].dtype
        print 'mygroup' in mphf
        print '/mygroup/bigdata' in mphf
        print 'bigdata' in mphf['mygroup']

        print 'root keys are: ', list(mphf.iterkeys())
        print 'mygroup keys are: ', list(mphf['mygroup'].iterkeys())
        print 'othergroup keys are: ', list(mphf['othergroup'].iterkeys())
        
        mphf[datapath].read_direct(whole_vol[0], numpy.s_[0])

        def test_subvol( slicing ):
            expected_vol = testvol[slicing]
            read_vol = mphf[datapath][slicing]
            assert (read_vol == expected_vol).all()
        
        threads = []
        for i in range( 40 ):
            threads.append( threading.Thread( target=partial(test_subvol, (numpy.s_[i:i+1],))) )
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()

    bigfile_path = '/tmp/big_testfile7.h5'
    if not os.path.exists(bigfile_path):
        print "generating test file:", bigfile_path
        with h5py.File(bigfile_path, 'w') as f:
            f.create_dataset( 'data', 
                              data=numpy.random.randint(0,255, (100,10000,1000)).astype(numpy.uint8), 
                              chunks=True,
                              compression='gzip', 
                              compression_opts=4 )
    
    
    with h5py.File(bigfile_path, 'r') as f:
        bigvol = f['data'][:]
    
    from lazyflow.utility import Timer
    
    # Switch File type
    with MultiProcessHdf5File(bigfile_path, 'r') as bf:
    #with h5py.File(bigfile_path, 'r') as bf:

        def test_subvol( slicings ):
            for slicing in slicings:
                # Just read, don't check: 
                # We want the time for this test to be dominated by reading the data, not checking it.
                read_vol = bf['data'][slicing]
                #expected_vol = bigvol[slicing]
                #assert (read_vol == expected_vol).all()

        threads = []
        for i in range( 8 ):
            slicings = [ numpy.s_[i:i+5], 
                         numpy.s_[i+1:i+6],
                         numpy.s_[i+2:i+7],
                         numpy.s_[i+3:i+8],
                         numpy.s_[i+4:i+9] ]
            threads.append( threading.Thread(target=partial(test_subvol, slicings)))

        with Timer() as timer:
            for thread in threads:
                thread.start()
            
            for thread in threads:
                thread.join()

        print "Time: {} seconds".format( timer.seconds() )
