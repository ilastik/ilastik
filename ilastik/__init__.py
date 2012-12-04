##################
## Version info ##
##################

def _format_version(t):
    """converts a tuple to a string"""
    return '.'.join(str(i) for i in t)

__version_info__ = (0, 6)
__version__ = _format_version(__version_info__)

def convertVersion(vstring):
    if not isinstance(vstring, str):
        raise Exception('tried to convert non-string version: {}'.format(vstring))
    return tuple(int(i) for i in vstring.split('.'))


def isVersionCompatible(version):
    """Return True if the current project file format is
    backwards-compatible with the format used in this version of
    ilastik.

    """
    # Currently we aren't forwards or backwards compatible with any
    # other versions.

    # for now, also allow old-style floats as version numbers
    if isinstance(version, float):
        return float(__version__) == version
    return convertVersion(version) == __version_info__

#######################
## Dependency checks ##
#######################

def _do_check(fnd, rqd, msg):
    if fnd < rqd:
        fstr = _format_version(fnd)
        rstr = _format_version(rqd)
        raise Exception(msg.format(fstr, rstr))

def _check_depends():
    import h5py

    _do_check(h5py.version.version_tuple,
              (2, 1, 0),
              "h5py version {0} too old; versions of h5py before {1} are not threadsafe.")

    _do_check(h5py.version.hdf5_version_tuple,
              (1, 8, 7),
              "hdf5 version {0} is too old; version {1} or newer required")

_check_depends()
