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
#		   http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.appletSerializer import AppletSerializer,\
    SerialDictSlot, SerialSlot, SerialHdf5BlockSlot, SerialPickleableSlot, SerialPickledValueSlot

try:
    import hytra
    WITH_HYTRA = True
except ImportError as e:
    WITH_HYTRA = False

class TrackingSerializer(AppletSerializer):
    VERSION = 1 # Make sure to bump the version in case you make any changes in the serialization
    
    def __init__(self, mainOperator, projectFileGroupName):
        # Serialization for the new pipeline (HyTra)
        if WITH_HYTRA:
            slots = [SerialDictSlot(mainOperator.Parameters, selfdepends=True),
                     SerialDictSlot(mainOperator.FilteredLabels, transform=str, selfdepends=True),
                     SerialPickledValueSlot(mainOperator.ExportSettings),                     
                     SerialPickleableSlot(mainOperator.HypothesesGraph, self.VERSION, None),
                     SerialPickleableSlot(mainOperator.ResolvedMergers, self.VERSION, None)
                     ]
       
        # Serialization for backward compatibility (for tracking with pgmlink)  
        # TODO: Remove this section when Windows supports the new pipeline (HyTra)
        else: 
            try:
                import pgmlink
            except:
                import pgmlinkNoIlpSolver as pgmlink
            
            slots = [SerialDictSlot(mainOperator.Parameters, selfdepends=True),
                     SerialHdf5BlockSlot(mainOperator.OutputHdf5,
                                         mainOperator.InputHdf5,
                                         mainOperator.CleanBlocks,
                                         name="CachedOutput"),
                     SerialDictSlot(mainOperator.EventsVector, transform=str, selfdepends=True),
                     SerialDictSlot(mainOperator.FilteredLabels, transform=str, selfdepends=True),
                     SerialPickledValueSlot(mainOperator.ExportSettings)
                     ]
            
    
            if 'MergerOutput' in mainOperator.outputs:
                slots.append(SerialHdf5BlockSlot(mainOperator.MergerOutputHdf5,
                                         mainOperator.MergerInputHdf5,
                                         mainOperator.MergerCleanBlocks,
                                         name="MergerCachedOutput"),
                              )
    
            if 'CoordinateMap' in mainOperator.outputs:
                slots.append(SerialPickleableSlot(mainOperator.CoordinateMap, 1, pgmlink.TimestepIdCoordinateMap()))

        super( TrackingSerializer, self ).__init__( projectFileGroupName, slots=slots )
        
