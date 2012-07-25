class VersionManager(object):
    CurrentIlastikVersion = 0.6
    
    @classmethod
    def isProjectFileVersionCompatible(cls, ilastikVersion):
        """
        Return True if the current project file format is backwards-compatible with the format used in ilastikVersion.
        """
        # Currently we aren't forwards or backwards compatible with any other versions.
        return ilastikVersion == cls.CurrentIlastikVersion
