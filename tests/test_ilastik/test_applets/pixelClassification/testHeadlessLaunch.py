"""
This is a minimal test to ensure that the app can be launched in headless mode, create a project, and exit cleanly.

In particular, this test should fail if a developer has accidentally added a GUI module import statement
(such as "import PyQt5") in a place that might be reached during "headless mode".
In headless mode, such import statements will fail, and so will this test.

NOTE: This test only works properly
"""
from __future__ import print_function
import sys
import os
import imp
import ilastik
import ilastik.utility
import pytest


@pytest.mark.skipif(__name__ != "__main__", reason=f"This test must be run independently: python {__file__}")
def test_headless_launch():
    print("looking for ilastik.py...")
    # Load the ilastik startup script as a module.
    # Do it here in setupClass to ensure that it isn't loaded more than once.
    import ilastik.__main__

    with ilastik.utility.autocleaned_tempdir() as tmpdir:
        sys.argv.append("--headless")
        sys.argv.append("--new_project=" + tmpdir + "/tempproj.ilp")
        sys.argv.append("--workflow")
        sys.argv.append("Pixel Classification")

        ilastik.__main__.main()


if __name__ == "__main__":
    sys.exit(test_headless_launch())
