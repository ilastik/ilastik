###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2021, the ilastik developers
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
class State:
    """
    Stores model state
    As opaque serialized tensors
    """

    model: bytes
    optimizer: bytes

    def __init__(self, *, model: bytes, optimizer: bytes) -> None:
        self.model = model
        self.optimizer = optimizer


class Model:
    code: bytes
    config: dict

    def __init__(self, *, code: bytes, config: dict) -> None:
        self.code = code
        self.config = config

    def __bool__(self) -> bool:
        return bool(self.code)


Model.Empty = Model(b"", {})
