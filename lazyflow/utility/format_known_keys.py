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
# 		   http://ilastik.org/license/
###############################################################################
import string


def format_known_keys_strict(s, entries):
    """Strict version of format_known_keys()."""
    formatter = string.Formatter()
    pieces = []

    for text, name, fmt, _conv in formatter.parse(s):
        pieces.append(text)

        if name in entries:
            value = formatter.format_field(entries[name], fmt)
            pieces.append(value)
            continue

        # Replicate the original stub
        name = name or ""
        fmt = fmt or ""
        start, end, fmtsep = "", "", ""
        if name or fmt:
            start, end = "{", "}"
        if fmt:
            fmtsep = ":"
        pieces.append(start + name + fmtsep + fmt + end)

    return "".join(pieces)


def format_known_keys(s, entries, strict=True):
    """
    Like str.format(), but 
     (1) accepts only a dict and 
     (2) allows the dict to be incomplete, 
         in which case those entries are left alone.
    
    Setting strict to False returns the original format string
    if that string is malformed.

    Examples:
    
    >>> format_known_keys("Hello, {first_name}, my name is {my_name}", {'first_name' : 'Jim', 'my_name' : "Jon"})
    'Hello, Jim, my name is Jon'
    
    >>> format_known_keys("Hello, {first_name:}, my name is {my_name}!", {"first_name" : [1,2,2]})
    'Hello, [1, 2, 2], my name is {my_name}!'

    >>> format_known_keys("Hello, {first_name}, my name is {my_name", {'first_name' : 'Jim'})  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    ValueError: ...

    >>> format_known_keys("Hello, {first_name}, my name is {my_name", {'first_name' : 'Jim'}, strict=False)
    'Hello, {first_name}, my name is {my_name'
    """
    try:
        return format_known_keys_strict(s, entries)
    except ValueError:
        if strict:
            raise
        return s


if __name__ == "__main__":
    import doctest

    doctest.testmod()
