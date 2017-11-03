###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2017, the ilastik developers
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
"""Basic tests that can be applied to _all_ workflows in headless mode

This is meant as a sanity check to make sure that workflows can be at least
started after changes are committed.

Also this can be used as a basis for further headless-mode testing.
"""
from ilastik.workflow import getAvailableWorkflows


class TestHeadlessWorkflowStartupProjectCreation(object):
    """Start a headless shell and create a project for each workflow"""
    @classmethod
    def setupClass(cls):
        cls.workflow_list = list(getAvailableWorkflows())
