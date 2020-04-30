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

"""Some tools and helpers for command line processing."""

import argparse
import configparser
import json
from typing import Optional
import vigra


class OptionalFlagAction(argparse.Action):
    """Similar to store_true or store_false actions, but also allows an optional argument.

    This action is typically used with ``default`` and ``const`` in :meth:`argparse.ArgumentParser.add_argument`.
      * If the option is not supplied, value of ``default`` will be used (usually left out since it is None by default).
      * If the option is supplied without an argument, value of ``const`` will be used (usually True or False).
      * If the option is supplied with an argument, that argument will be converted to boolean.

    Valid arguments are the same as in :meth:`configparser.ConfigParser.getboolean`.
    """

    def __init__(self, nargs=argparse.OPTIONAL, **kwargs):
        if nargs != argparse.OPTIONAL:
            raise ValueError(f"action {self.__class__.__name__} can only be used with nargs={argparse.OPTIONAL!r}")

        if not isinstance(kwargs.get("const"), bool):
            raise ValueError(f"action {self.__class__.__name__} can only be used with const=True or const=False")

        super().__init__(nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            value = self.default

        elif isinstance(values, bool):
            value = values

        else:
            states = configparser.ConfigParser.BOOLEAN_STATES
            try:
                value = states[str(values).lower()]
            except KeyError:
                parser.error(f"invalid value {values!r} for {option_string}; try one of: {', '.join(states)}")
                return

        setattr(namespace, self.dest, value)


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
    replace_values = {"(": "[", ")": "]", "None": "null"}
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
            f"Expected a list encoded as a string, e.g. '[0, 1]' but got '{some_string}' -> " f"type {type(parsed)}."
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

def parse_axiskeys(axiskeys: str, dataset_dims: int = 0) -> Optional[vigra.AxisTags]:
        if axiskeys == "None":
            return None
        dataset_dims = dataset_dims or len(axiskeys)
        if len(axiskeys) in range(1, dataset_dims):
            raise ValueError(f"Dataset has {dataset_dims} dimensions, so you need to provide that many axes keys")
        if not set(axiskeys).issubset(set("xyztc")):
            raise ValueError(f'Axes must be a combination of "xyztc"')
        if len(set(axiskeys)) < len(axiskeys):
            raise ValueError(f"Repeated axis keys: {axiskeys}")
        if not set("xy").issubset(set(axiskeys)):
            raise ValueError(f"x and y need to be present. Provided value was {axiskeys}")
        return vigra.defaultAxistags(axiskeys)
