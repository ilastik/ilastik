###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2017, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#                 http://ilastik.org/license/
###############################################################################

import unittest
from ilastik.utility.commandLineProcessing import ParseListFromString
import argparse
import sys

import logging
logger = logging.getLogger(__name__)


class Stdout2Log(object):
    def write(self, msg):
        logger.debug(msg)


class CommandLineHelperTests(unittest.TestCase):
    def setUp(self):
        self.parser = argparse.ArgumentParser()

    def test_expected_failures(self):
        self.parser.add_argument('this', action=ParseListFromString)

        values_to_test = [
            '123',
            '{123}',
            '[a, b]',
            '[1',
            '1]',
            '',
            '(1, 2, 3'
        ]

        stderr_original = sys.stderr

        # redirect sdout, because it clogs the console with expected failure messages
        sys.stderr = Stdout2Log()
        for value in values_to_test:
            self.assertRaises(SystemExit, self.parser.parse_args, [value])
        sys.stderr = stderr_original

    def test_allowed_string(self):
        self.parser.add_argument('this', action=ParseListFromString)

        values_to_test = {
            '[123]': [123],
            '(123)': [123],
            '[(1, 2)]': [[1, 2]],
            '[(1, 2), (3, 4)]': [[1, 2], [3, 4]],
            '[(0, 0, 0), (0, None, None)]': [[0, 0, 0], [0, None, None]],
        }

        for value, expected in values_to_test.items():
            parsed = self.parser.parse_args([value]).this
            self.assertEqual(parsed, expected)
