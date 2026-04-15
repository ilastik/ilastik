# Not used for packaging other than for conda to load the setup data and
# determine the dynammic version.
# Modifying this file should have a good reason.
import setuptools
import setuptools_scm

_version = setuptools_scm.get_version()

# need to specify version here to play well with conda
setuptools.setup(version=_version)
