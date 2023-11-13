###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2023, the ilastik developers
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
from typing import Iterator, Type, Union


def exception_chain(exc: Union[BaseException, None]) -> Iterator[BaseException]:
    """
    Iterate through an Exception chain

    in order to capture potential `raise from` chains of exceptions.
    """
    while exc:
        yield exc
        exc = exc.__cause__ or exc.__context__


def root_cause(exc: BaseException) -> BaseException:
    """
    Traverses the Exception chain and returns the root cause Exception
    """
    *_, root_cause = exception_chain(exc)
    return root_cause


def is_root_cause(root_class: Type[BaseException], exc: BaseException) -> bool:
    return isinstance(root_cause(exc), root_class)
