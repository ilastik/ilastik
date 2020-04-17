###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2019, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
"""
Test that pixel + object classification files created in 1.3.3, 1.3.3post1 can
still be read.

1.3.3 introduced new axisorder (always 5D) for saved data in the combined
workflow. Previously (and after), pixel annotations are saved in the original
axis order.

For more details see
original issue: https://github.com/ilastik/ilastik/issues/2152
pull request: https://github.com/ilastik/ilastik/pull/2160
"""
import pathlib
import pytest
import sys

from ilastik import app


@pytest.fixture
def project_path() -> pathlib.Path:
    """Pixel + Object Classification project file created with ilastik 1.3.3post1

    Created following instructions here:
    https://github.com/ilastik/ilastik/issues/2152#issuecomment-552926381
    """
    tests_root = pathlib.Path(__file__).parents[1]
    project_path = tests_root / "data" / "inputdata" / "pc-oc-133.ilp"
    return project_path


def test_133_pc_oc_loading(project_path: pathlib.Path):
    args = ["--headless", f"--project={project_path}"]
    # Clear the existing commandline args so it looks like we're starting fresh.
    sys.argv = ["ilastik.py"]
    sys.argv.extend(args)

    # Start up the ilastik.py entry script as if we had launched it from the command line
    parsed_args, workflow_cmdline_args = app.parse_known_args()

    shell = app.main(parsed_args=parsed_args, workflow_cmdline_args=workflow_cmdline_args, init_logging=False)

    shell.closeCurrentProject()
    # this would raise an error in case of a problem
