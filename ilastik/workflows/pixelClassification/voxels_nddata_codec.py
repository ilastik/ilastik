import numpy

class VoxelsNddataCodec(object):
    """
    Utiliy for "encoding" an ndarray as a stream of bytes, and vice-versa.
    (The array buffer is simply extracted.)
    
    This class was copied from the pydvid source code, but edited to use C-order instead of Fortran-order.
    """

    # Data is sent to/retrieved from the http response stream in chunks.
    STREAM_CHUNK_SIZE = 8192 # (bytes)

    # Defined here for clients to use.
    VOLUME_MIMETYPE = "application/octet-stream"
    
    def __init__(self, dtype):
        """
        dtype: The pixel type as a numpy dtype.
        """
        self.dtype = dtype
        
    def decode_to_ndarray(self, stream, full_roi_shape):
        """
        Decode the info in the given stream to a numpy.ndarray.
        
        full_roi_shape: Shape of the requested data. 
                        Roi must include the channel dimension, and all channels of data must be requested.
                        (For example, it's not valid to request channel 2 of an RGB image.  
                        You must request all channels 0-3.)
        """
        array = numpy.ndarray( full_roi_shape, dtype=self.dtype, order='C' )
        buf = numpy.getbuffer(array)
        self._read_to_buffer(buf, stream)
        return array

    def encode_from_ndarray(self, stream, array):
        """
        Encode the array to the given bytestream.
        
        Prerequisites:
        - array must be a numpy.ndarray
        - array must have the same dtype as this codec
        """
        buf = self._get_buffer(array)
        self._send_from_buffer(buf, stream)

    def create_encoded_stream_from_ndarray(self, array):
        """
        Create a stream object for the given array data.
        See VoxelsNddataCodec.EncodedStream for supported stream methods.

        Prerequisites:
        - array must be a numpy.ndarray
        - array must have the same dtype as this codec
        """
        buf = self._get_buffer(array)
        return VoxelsNddataCodec.EncodedStream(buf)

    def calculate_buffer_len(self, shape):
        return numpy.prod(shape) * self.dtype.type().nbytes
    
    def _get_buffer(self, array):
        """
        Obtain a buffer for the given array.

        Prerequisites:
        - array must be a numpy.ndarray
        - array must have the same dtype as this codec
        """
        # Check for bad input.
        assert isinstance( array, numpy.ndarray ), \
            "Expected a numpy.ndarray, not {}".format( type(array) )
        assert array.dtype == self.dtype, \
            "Wrong dtype.  Expected {}, got {}".format( self.dtype, array.dtype )

        # Unfortunately, if the array isn't C_CONTIGUOUS, we have to copy it.
        if not array.flags['C_CONTIGUOUS']:
            array_copy = numpy.empty_like(array, order='C')
            array_copy[:] = array[:]
            array = array_copy

        return numpy.getbuffer(array)
    
    @classmethod
    def _read_to_buffer(cls, buf, stream):
        """
        Read the data from the stream into the given buffer.
        """
        # We could read it in one step, but instead we'll read it in chunks to avoid big temporaries.
        # (See below.)
        # buf[:] = stream.read( len(buf) )

        # Read data from the stream in chunks
        remaining_bytes = len(buf)
        while remaining_bytes > 0:
            next_chunk_bytes = min( remaining_bytes, VoxelsNddataCodec.STREAM_CHUNK_SIZE )
            chunk_start = len(buf)-remaining_bytes
            chunk_stop = len(buf)-(remaining_bytes-next_chunk_bytes)
            buf[chunk_start:chunk_stop] = stream.read( next_chunk_bytes )
            remaining_bytes -= next_chunk_bytes

    @classmethod
    def _send_from_buffer(cls, buf, stream):
        """
        Write the given buffer out to the provided stream in chunks.
        """
        remaining_bytes = len(buf)
        while remaining_bytes > 0:
            next_chunk_bytes = min( remaining_bytes, VoxelsNddataCodec.STREAM_CHUNK_SIZE )
            chunk_start = len(buf)-remaining_bytes
            chunk_stop = len(buf)-(remaining_bytes-next_chunk_bytes)
            stream.write( buf[chunk_start:chunk_stop] )
            remaining_bytes -= next_chunk_bytes
        
    class EncodedStream(object):
        """
        A simple stream object returned by VoxelsNddataCodec.create_encoded_stream_from_ndarray()
        """
        def __init__(self, buf):
            assert buf is not None
            self._buffer = buf
            self._position = 0
        
        def seek(self, pos, whence):
            # This behavior of whence follows the standard python conventions for streams
            if whence == 0:
                self._position = pos # Absolute position
            if whence == 1:
                self._position += pos # Relative to current position
            if whence == 2:
                self._position = len(self._buffer) - pos # Relative to stream end
        
        def tell(self):
            return self._position
        
        def close(self):
            self._buffer = None
        
        def closed(self):
            return self._buffer is None
        
        @property
        def buf(self):
            return self._buffer

        def isatty(self):
            return False
        
        def getvalue(self):
            pos = self._position
            data = self.read()
            self._position = pos
            return data
        
        def peek(self, nbytes):
            return self._read(nbytes, True)
        
        def read(self, nbytes=None):
            return self._read(nbytes)

        def _read(self, nbytes=None, peeking=False):
            assert self._buffer is not None, "Can't read: stream is already closed."
            remaining_bytes = len(self._buffer) - self._position
            if nbytes is None:
                nbytes = remaining_bytes
            else:
                nbytes = min(remaining_bytes, nbytes)

            start = self._position
            stop = self._position + nbytes
            encoded_data = self._buffer[start:stop]
            
            if not peeking:
                self._position  += nbytes
            return encoded_data
    