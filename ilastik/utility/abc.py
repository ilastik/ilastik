###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################

import abc


class StrictABCMeta(abc.ABCMeta):
    """ABCMeta that validates methods during virtual subclass registration.

    In most cases it's better to derive from :cls:`abc.ABC` to achieve the same effect.
    However, this class could be useful if implementing classes have parents with
    complex metaclass machinery that prevents you from doing that (e.g. PyQt).

    See Also:
        :cls:`StrictABC`
    """

    def register(cls, subclass: type) -> type:
        """Register subclass as a "virtual subclass" of this ABC.

        Virtual subclass validity is based only on attribute membership.
        That is, registering an ABC subclass with abstract methods
        behaves identical to registering a non-ABC subclass.

        Can be used as a class decorator::

            @MyABC.register
            class MyCls:
                ...

        Returns:
            The registered subclass.

        Raises:
            TypeError: The subclass does not have all the methods required by this ABC.
        """
        missing = ", ".join(sorted(name for name in cls.__abstractmethods__ if not hasattr(subclass, name)))
        if missing:
            raise TypeError(f"Can't register class {subclass.__name__} with missing methods {missing}")

        return super().register(subclass)


class StrictABC(metaclass=StrictABCMeta):
    """ABC that validates methods during virtual subclass registration.

    See Also:
        :cls:`StrictABCMeta`
    """
