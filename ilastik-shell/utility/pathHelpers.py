import os

class PathComponents(object):
    """
    Provides a convenient access to path components of a combined external/internal path to a dataset.
    """
    def __init__(self, totalPath):
        # For hdf5 paths, split into external, extension, and internal paths
        h5Exts = ['.h5', '.hdf5', '.ilp']
        ext = None
        for x in h5Exts:
            if x in totalPath:
                ext = x

        # Comments below refer to this example path:
        # /some/path/to/file.h5/with/internal/dataset
        if ext is not None:
            self.extension = ext                              # .h5            
            self.externalPath = totalPath.split(ext)[0] + ext # /some/path/to/file.h5
            self.internalPath = totalPath.split(ext)[1]       # /with/internal/dataset

            self.internalDirectory = os.path.split( self.internalPath )[0]   # /with/internal
            self.internalDatasetName = os.path.split( self.internalPath )[1] # dataset
        else:
            # For non-hdf5 files, use normal path/extension (no internal path)
            (self.externalPath, self.extension) = os.path.splitext(totalPath)
            self.internalPath = None
            self.internalDatasetName = None
            self.internalDirectory = None

        self.externalDirectory = os.path.split( self.externalPath )[0] # /some/path/to
        self.filename = os.path.split( self.externalPath )[1]          # file.h5
        self.filenameBase = self.filename.split(ext)[0]                  # file

    def totalPath(self):
        return self.externalPath + self.extension + self.internalPath

def getPathVariants(originalPath, workingDirectory):
    """
    Take the given filePath (which can be absolute or relative, and may include an internal path suffix),
    and return a tuple of the absolute and relative paths to the file.
    """
    lastDotIndex = originalPath.rfind('.')
    extensionAndInternal = originalPath[lastDotIndex:]
    extension = extensionAndInternal.split('/')[0]

    relPath = originalPath
    
    if originalPath[0] == '/':
        absPath = originalPath
        relPath = os.path.relpath(absPath, workingDirectory)
    else:
        relPath = originalPath
        absPath = os.path.normpath( os.path.join(workingDirectory, relPath) )
        
    return (absPath, relPath)

if __name__ == "__main__":
    
    abs, rel = getPathVariants('/aaa/bbb/ccc/ddd.txt', '/aaa/bbb/ccc/eee')
    assert abs == '/aaa/bbb/ccc/ddd.txt'
    assert rel == '../ddd.txt'

    abs, rel = getPathVariants('../ddd.txt', '/aaa/bbb/ccc/eee')
    assert abs == '/aaa/bbb/ccc/ddd.txt'
    assert rel == '../ddd.txt'

    abs, rel = getPathVariants('ddd.txt', '/aaa/bbb/ccc')
    assert abs == '/aaa/bbb/ccc/ddd.txt'
    assert rel == 'ddd.txt'
    
    components = PathComponents('/some/external/path/to/file.h5/with/internal/path/to/data')
    assert components.externalPath == '/some/external/path/to/file.h5'
    assert components.extension == '.h5'
    assert components.internalPath == '/with/internal/path/to/data'


