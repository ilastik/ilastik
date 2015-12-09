###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
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
#		   http://ilastik.org/license/
###############################################################################

from __future__ import division

import os
import psutil
import platform
import logging


logger = logging.getLogger(__name__)
this_process = psutil.Process(os.getpid())


class Memory(object):
    """
    provides convenient access to memory-related functionality
    """

    _physically_available_ram = psutil.virtual_memory().total
    if "Darwin" in platform.system():
        # only Mac and BSD have the wired attribute, which we can use to
        # assess available RAM more precisely
        _physically_available_ram -= psutil.virtual_memory().wired

    # keep 1GiB reserved for other apps 
    # (systems with less than 1GiB RAM are not a target platform)
    _default_allowed_ram = max(_physically_available_ram - 1024.0**3, 0)
    _default_cache_fraction = .25
    _allowed_ram = _default_allowed_ram
    _user_limits_specified = {'total': False,
                              'caches': False}

    _magnitude_strings = {0: "B", 1: "KiB", 2: "MiB",
                          3: "GiB", 4: "TiB"}
    _magnitude_aliases = {"KB": "KiB", "kB": "KiB", "kiB": "KiB",
                          "MB": "MiB", "GB": "GiB", "TB": "TiB",
                          "B": "B", "KiB": "KiB", "MiB": "MiB",
                          "GiB": "GiB", "TiB": "TiB"}

    @classmethod
    def getMemoryUsage(cls):
        """
        get current memory usage in bytes
        """
        return this_process.memory_info().rss

    @classmethod
    def getAvailableRam(cls):
        """
        get the amount of memory, in bytes, that lazyflow is allowed to use

        Note: When a user specified setting (e.g. via .ilastikrc) is not available,
        the function will try to estimate how much memory is available after
        subtracting known overhead. Overhead estimation is currently only available
        on Mac.
        """
        return cls._allowed_ram

    @classmethod
    def setAvailableRam(cls, ram):
        """
        set the amount of memory, in bytes, that lazyflow is allowed to use

        If the argument ram is negative, lazyflow will not try to limit
        its RAM usage. Per default, lazyflow will use all of the available RAM.
        """

        if ram < 0:
            cls._user_limits_specified['total'] = False
            cls._allowed_ram = cls._default_allowed_ram
            logger.info("Available memory set to default")
        else:
            cls._user_limits_specified['total'] = True
            cls._allowed_ram = int(ram)
            logger.info("Available memory set to {}".format(
                Memory.format(cls._allowed_ram)))
            if cls._allowed_ram > cls._physically_available_ram:
                logger.warn("User specified memory exceeds memory "
                            "physically available. Please check the"
                            "configuration.")

        if cls._user_limits_specified['caches'] and \
                cls._allowed_ram_caches > cls._allowed_ram:
            logger.warn("User specified cache memory exceeds total RAM "
                        "available, resetting to default")
            cls._user_limits_specified['caches'] = False

    @classmethod
    def getAvailableRamCaches(cls):
        """
        get the amount of memory, in bytes, that lazyflow may use for caches
        """
        if cls._user_limits_specified['caches']:
            return cls._allowed_ram_caches
        else:
            return cls._allowed_ram * cls._default_cache_fraction

    @classmethod
    def setAvailableRamCaches(cls, ram):
        """
        set the amount of memory, in bytes, that lazyflow may use for caches

        If the argument ram is negative lazyflow will default to using
        25% of its available memory for caches.
        """

        if ram < 0:
            cls._user_limits_specified['caches'] = False
            logger.info("Memory for caches set to default")
        else:
            cls._user_limits_specified['caches'] = True
            cls._allowed_ram_caches = int(ram)
            logger.info("Memory for caches set to {}".format(
                Memory.format(cls._allowed_ram_caches)))
            if cls._allowed_ram_caches > cls.getAvailableRam():
                logger.warn("User specified memory for caches exceeds "
                            "memory available for the application. "
                            "Please check the configuration.")

    @classmethod
    def getAvailableRamComputation(cls):
        """
        shortcut for available_ram - ram_for_caches
        """
        available = cls.getAvailableRam()
        caches = cls.getAvailableRamCaches()
        comp = available - caches
        if comp < 0:
            comp = 0
        return comp

    @staticmethod
    def format(ram, trailing_digits=1):
        mant, exp = Memory.toScientific(ram)
        desc = Memory._magnitude_strings[exp]
        fmt_str = "{:.%uf}{}" % (trailing_digits,)
        return fmt_str.format(mant, desc)

    @staticmethod
    def toScientific(ram, base=1024, expstep=1, explimit=4):
        exp = 0
        mant = float(ram)
        step = base**expstep
        while mant >= step and exp + expstep <= explimit:
            mant /= step
            exp += expstep
        return mant, exp

    @staticmethod
    def parse(s):
        for i in (3, 2, 1):
            if len(s) < i:
                continue
            mag = s[-i:]
            try:
                x = float(s[:-i])
            except:
                # invalid float
                continue
            if mag not in Memory._magnitude_aliases:
                continue
            mag = Memory._magnitude_aliases[mag]
            for d in Memory._magnitude_strings:
                if Memory._magnitude_strings[d] == mag:
                    
                    return int(x*1024**d)
        raise FormatError("invalid format for memory string: "
                          "{}".format(s))


class FormatError(Exception):
    pass
