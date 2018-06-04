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
"""
Some tools and helpers for command line processing
"""
import argparse
import json


def convertStringToList(some_string):
    """Helper function in order to parse lists encoded as strings

    This is often found for Rois, ranges...

    e.g.
      - [0, 1]
      - [(0, 0, ..), (1, 1, ...)]

    Note: in order to use json for safe parsing of values, round brackets `(, )`
    are replaced by square brackets `[, ]` during parsing. It is up to the user
    to convert lists to tuples where it is expected.

    e.g.
      - [(0, 0, ..), (1, 1, ...)] will be parse to [[0, 0 ...], [1, 1, ...]]
    """
    assert isinstance(some_string, str), "Expected a string!"

    # replace round brackets:
    replace_values = {
        '(': '[',
        ')': ']',
        'None': 'null',
    }
    to_parse = some_string
    for k, v in replace_values.items():
        to_parse = to_parse.replace(k, v)

    try:
        parsed = json.loads(to_parse)
    except json.JSONDecodeError as e:
        message = (
            f"Expected a list encoded as a string, e.g. '[0, 1]' but got '{some_string}'. "
            f"Encountered the following parsing problem: {e.msg} at pos {e.pos} in doc '{e.doc}'."
        )
        raise ValueError(message)

    if not isinstance(parsed, list):
        message = (
            f"Expected a list encoded as a string, e.g. '[0, 1]' but got '{some_string}' -> "
            f"type {type(parsed)}."
        )
        raise ValueError(message)

    return parsed


class ParseListFromString(argparse.Action):
    """Little helper action in order to parse lists encoded as strings
    """
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            parsed = convertStringToList(values)
        except ValueError as e:
            raise argparse.ArgumentError(self, str(e))

        setattr(namespace, self.dest, parsed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('this', action=ParseListFromString)
    args = parser.parse_args(["[0, 1]"])
    print(args)
    assert isinstance(args.this, list)

    args = parser.parse_args(["(0, 1)"])
    print(args)
    assert isinstance(args.this, list)

    # this will raise
    args = parser.parse_args(["(0, 1"])
