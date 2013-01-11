"""
This module defines a set of global settings that can be used to "hack in" special features, 
particularly one-off features that it's not worth redesigning the architecture for.
"""

class ImportOptions(object):
    # Used in the DataSelection applet serializer for importing.
    default_axis_order = None
