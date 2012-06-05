from setuptools import setup, find_packages
setup(
    name = "lazyflow",
#    version = "0.1",
    packages = find_packages(),
    scripts = [],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['greenlet'],

    package_data = {
        'lazyflow': ['*.txt', '*.py'],
    },

    include_package_data = True,    # include everything in source control


    # metadata for upload to PyPI
    author = "Christoph Straehle",
    author_email = "christoph.straehle@iwr.uni-heidelberg.de",
    description = "Lazyflow - graph based lazy numpy data flows",
    license = "BSD",
    keywords = "graph numpy dataflow",
    url = "http://ilastik.org/lazyflow",
)
