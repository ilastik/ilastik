__version_info__ = (0, 6)
__version__ = '.'.join(str(i) for i in __version_info__)


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
