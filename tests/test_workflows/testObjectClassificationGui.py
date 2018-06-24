###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2018, the ilastik developers
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
import logging
import os
import shutil
import sys
import tempfile

from ilastik.workflows import ObjectClassificationWorkflowPixel

from lazyflow.utility.timer import Timer
from tests.helpers import ShellGuiTestCaseBase


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


class TestObjectClassificationGui(ShellGuiTestCaseBase):
    """
    Run a set of GUI-based tests on the object classification workflow.

    Note: These tests are named (prefixed with `test_%02d`) in order to impose
        an order. Tests simulate interaction with a ilastik and depend on
        the earlier ones.
    """
    @classmethod
    def workflowClass(cls):
        return ObjectClassificationWorkflowPixel

    @classmethod
    def setupClass(cls):
        # Base class first
        super().setupClass()

        # input files:
        current_dir = os.path.split(__file__)[0]
        cls.sample_data_raw = os.path.join(current_dir, '../data/inputdata/3d.h5')
        cls.sample_data_prob = os.path.join(current_dir, '../data/inputdata/3d_Probabilities.h5')

        # output files:
        cls.tmp_dir = tempfile.mkdtemp()
        cls.project_file = os.path.join(cls.tmp_dir, 'test_project_oc.ilp')
        cls.output_file = os.path.join(cls.tmp_dir, '3d_Object_Probabilities_out.h5')

        # Start the timer
        cls.timer = Timer()
        cls.timer.unpause()

    @classmethod
    def teardownClass(cls):
        cls.timer.pause()
        logger.debug(f"Total Time: {cls.timer.seconds()} seconds.")

        # Call our base class so the app quits!
        super().teardownClass()

        # Clean up: Delete any test files we generated
        shutil.rmtree(cls.tmp_dir)

    def test_00_check_preconditions(self):
        """Make sure the needed files exist"""
        needed_files = [
            self.sample_data_raw,
            self.sample_data_prob
        ]
        for f in needed_files:
            assert os.path.exists(f), f"File {f} does not exist!"


if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_nosetest
    run_shell_nosetest(__file__)
