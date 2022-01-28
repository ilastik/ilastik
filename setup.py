import setuptools
import setuptools_scm

_version = setuptools_scm.get_version(write_to="ilastik/_version.py")


# need to specify version here to play well with conda
setuptools.setup(version=_version)
