###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
import os

class PathComponents(object):
    """
    Provides a convenient access to path components of a combined external/internal path to a dataset.
    Also, each of the properties listed below is writable, in which case ALL properties are updated accordingly.
    """
    
    # Only files with these extensions are allowed to have an 'internal' path
    HDF5_EXTS = ['.ilp', '.h5', '.hdf5']
    
    def __init__(self, totalPath, cwd=None):
        """
        Initialize the path components.
        
        :param totalPath: The entire path to the dataset, including any internal path (e.g. the path to an hdf5 dataset).
                          For example, ``totalPath='/some/path/to/file.h5/with/internal/dataset'``

        :param cwd: If provided, relative paths will be converted to absolute paths using this arg as the working directory.
        """
        self._externalPath = None
        self._externalDirectory = None
        self._filename = None            
        self._filenameBase = None
        self._extension = None
        self._internalPath = None
        self._internalDatasetName = None
        self._internalDirectory = None
        
        self._cwd = cwd
        self._init(totalPath, cwd)
        self._initialized = True

    def _init(self, totalPath, cwd):
        ext = None
        extIndex = -1
        
        if cwd is not None:
            absPath, relPath = getPathVariants( totalPath, cwd )
            totalPath = absPath
        
        #convention for Windows: use "/"
        totalPath = totalPath.replace("\\","/")
        
        # For hdf5 paths, split into external, extension, and internal paths
        for x in self.HDF5_EXTS:
            if totalPath.find(x) > extIndex:
                extIndex = totalPath.find(x)
                ext = x

        # Comments below refer to this example path:
        # /some/path/to/file.h5/with/internal/dataset
        if ext is not None:
            self._extension = ext                              # .h5
            parts = totalPath.split(ext)
            
            # Must deal with pathological filenames such as /path/to/file.h5_with_duplicate_ext.h5
            while len(parts) > 2:
                parts[0] = parts[0] + ext + parts[1]
                del parts[1]
            self._externalPath = parts[0] + ext # /some/path/to/file.h5
            self._internalPath = parts[1].replace('\\', '/') # /with/internal/dataset

            self._internalDirectory = os.path.split( self.internalPath )[0]   # /with/internal
            self._internalDatasetName = os.path.split( self.internalPath )[1] # dataset
        else:
            # For non-hdf5 files, use normal path/extension (no internal path)
            (self._externalPath, self._extension) = os.path.splitext(totalPath)
            self._externalPath += self._extension
            self._internalPath = None
            self._internalDatasetName = None
            self._internalDirectory = None

        self._externalDirectory = os.path.split( self._externalPath )[0] # /some/path/to
        self._filename = os.path.split( self._externalPath )[1]          # file.h5
        self._filenameBase = os.path.splitext(self._filename)[0]         # file
    
    def __setattr__(self, attr, value):
        """
        This prevents us from accidentally writing to a non-existant attribute.
        e.g. if the user tries to say components.fIlEnAmE = 'newfile.h5', raise an error.
        """
        if hasattr( self, '_initialized' ):
            # Attempt to get the old attribute first
            oldval = getattr(self, attr)
        object.__setattr__( self, attr, value )

    def totalPath(self):
        """
        Return the (reconstructed) totalPath to the dataset.
        """
        total = self.externalPath 
        if self.internalPath:
            total += self.internalPath
        return total
    
    #
    # Getters
    #
    
    @property
    def externalPath(self):
        """
        Example: ``/some/path/to/file.h5``
        """
        return self._externalPath

    @property
    def externalDirectory(self):
        """
        Example: ``/some/path/to``
        """
        return self._externalDirectory

    @property
    def filename(self):
        """
        Example: ``file.h5``
        """
        return self._filename

    @property
    def filenameBase(self):
        """
        Example: ``file``
        """
        return self._filenameBase

    @property
    def extension(self):
        """
        Example: ``.h5``
        """
        return self._extension

    @property
    def internalPath(self):
        """
        Example: ``/with/internal/dataset``
        """
        return self._internalPath

    @property
    def internalDatasetName(self):
        """
        Example: ``/dataset``
        """
        return self._internalDatasetName

    @property
    def internalDirectory(self):
        """
        Example: ``/with/internal``
        """
        return self._internalDirectory

    #
    # Setters
    #

    @externalPath.setter
    def externalPath(self, new):
        assert new[-1] != '/'
        if self._internalPath:
            self._init( new + self._internalPath, self._cwd )
        else:
            self._init( new, self._cwd ) 

    @externalDirectory.setter
    def externalDirectory(self, new):
        new_external = os.path.join(new, self._filename)
        self.externalPath = new_external

    @filename.setter
    def filename(self, new):
        new_external = os.path.join( self._externalDirectory, new )
        self.externalPath = new_external

    @filenameBase.setter
    def filenameBase(self, new):
        new_external = os.path.join( self._externalDirectory, new + self._extension )
        self.externalPath = new_external

    @extension.setter
    def extension(self, new):
        assert (not self._internalPath) or (new in self.HDF5_EXTS), \
            "This PathComponents has an internal path ({}), but you are "\
            "attempting to assign a non-hdf5 extension to it ({})"\
            .format( self._internalPath, new )
        new_external = os.path.join( self._externalDirectory, self._filenameBase + new )
        self.externalPath = new_external        

    @internalPath.setter
    def internalPath(self, new):
        assert self._extension in self.HDF5_EXTS, \
            "Can't set an internal path on a filename with extension {}".format( self._extension )
        if new:
            self._init( self._externalPath + new, self._cwd )
        else:
            self._init( self._externalPath, self._cwd )

    @internalDatasetName.setter
    def internalDatasetName(self, new):
        new_internal = os.path.join(self._internalDirectory, new)
        self.internalPath = new_internal

    @internalDirectory.setter
    def internalDirectory(self, new):
        if new and new[0] != '/':
            new = '/' + new
        new_internal = os.path.join( new, self._internalDatasetName )
        self.internalPath = new_internal

def areOnSameDrive(path1,path2):
    #if one path is relative, assume they are on same drive
    if isUrl(path1) or isUrl(path2):
        return False
    if not os.path.isabs(path1) or not os.path.isabs(path2):
        return True
    drive1,path1 = os.path.splitdrive(path1)
    drive2,path2 = os.path.splitdrive(path2)
    return drive1==drive2

def compressPathForDisplay(pathstr,maxlength):
    '''Add alternatingly parts of the start and the end of the path
    until the length s increased. Result: Drive/Dir1/.../Dirn/file'''
    if len(pathstr)<=maxlength:
        return pathstr
    suffix = ""
    prefix = ""
    component_list = pathstr.split("/")
    while component_list:
        c = component_list.pop(-1)
        newlength = len(suffix)+1+len(c)+len(prefix)
        if newlength>maxlength:
            suffix = c[-min(len(c)-3,maxlength-3):]
            break
        suffix="/"+c+suffix
        if not component_list:
            break
        c = component_list.pop(0)
        if len(suffix)+len(prefix)+1+len(prefix)>maxlength:
            break
        prefix=prefix+c+"/"
    return prefix+"..."+suffix

def isUrl(path):
    # For now, the simplest rule will work.
    return '://' in path

def getPathVariants(originalPath, workingDirectory):
    """
    Take the given filePath (which can be absolute or relative, and may include an internal path suffix),
    and return a tuple of the absolute and relative paths to the file.
    """
    # urls are considered absolute
    if isUrl(originalPath):
        return originalPath, None
    
    if len(originalPath) > 0 and originalPath[0] == '~':
        originalPath = os.path.expanduser(originalPath)
    
    relPath = originalPath
    
    if os.path.isabs(originalPath):
        absPath = originalPath
        if areOnSameDrive(originalPath,workingDirectory):
            relPath = os.path.relpath(absPath, workingDirectory).replace("\\","/")
        else:
            # Relative path does not always exist.  Caller must check for None.
            relPath = None
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

    assert getPathVariants('', '/abc') == ('/abc', '')
    
    components = PathComponents('/some/external/path/to/file.h5/with/internal/path/to/data')
    assert components.externalPath == '/some/external/path/to/file.h5'
    assert components.extension == '.h5'
    assert components.internalPath == '/with/internal/path/to/data'

    components = PathComponents('/some/external/path/to/file.h5_crazy_ext.h5/with/internal/path/to/data')
    assert components.externalPath == '/some/external/path/to/file.h5_crazy_ext.h5'
    assert components.extension == '.h5'
    assert components.internalPath == '/with/internal/path/to/data'

    # Everything should work for URLs, too.
    components = PathComponents('http://somehost:8000/path/to/data/with.ext')
    assert components.externalPath == 'http://somehost:8000/path/to/data/with.ext'
    assert components.extension == '.ext'    
    assert components.internalPath is None
    assert components.externalDirectory == 'http://somehost:8000/path/to/data'
    assert components.filenameBase == 'with'
    
    # Try modifying the properties and verify that the total path is updated.
    components = PathComponents('/some/external/path/to/file.h5/with/internal/path/to/data')
    components.extension = '.hdf5'
    assert components.externalPath == '/some/external/path/to/file.hdf5'
    assert components.totalPath() == '/some/external/path/to/file.hdf5/with/internal/path/to/data'
    components.filenameBase = 'newbase'
    assert components.totalPath() == '/some/external/path/to/newbase.hdf5/with/internal/path/to/data'
    components.internalDirectory = 'new/internal/dir'
    assert components.totalPath() == '/some/external/path/to/newbase.hdf5/new/internal/dir/data'
    components.internalDatasetName = 'newdata'
    assert components.totalPath() == '/some/external/path/to/newbase.hdf5/new/internal/dir/newdata'
    components.externalDirectory = '/new/extern/dir/'
    assert components.totalPath() == '/new/extern/dir/newbase.hdf5/new/internal/dir/newdata'
    components.externalDirectory = '/new/extern/dir'
    assert components.totalPath() == '/new/extern/dir/newbase.hdf5/new/internal/dir/newdata'
    components.externalPath = '/new/externalpath/somefile.h5'
    assert components.totalPath() == '/new/externalpath/somefile.h5/new/internal/dir/newdata'
    components.filename = 'newfilename.h5'
    assert components.totalPath() == '/new/externalpath/newfilename.h5/new/internal/dir/newdata'
    components.internalPath = '/new/internal/path/dataset'
    assert components.totalPath() == '/new/externalpath/newfilename.h5/new/internal/path/dataset'
