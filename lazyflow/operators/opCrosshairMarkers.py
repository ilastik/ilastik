import numpy
import vigra

from lazyflow.roi import TinyVector
from lazyflow.graph import Operator, InputSlot, OutputSlot

class OpCrosshairMarkers( Operator ):
    """
    Given a list of 3D coordinates and a volume with up to 5 dimensions,
    produces a volume with 3D 'crosshair' markers centered at each 
    coordinate, with zeros elsewhere.
    """
    Input = InputSlot() # Used for meta-data
    PointList = InputSlot() # list of 3d coordinates (dtype=object)
    CrosshairRadius = InputSlot(value=5)
    
    Output = OutputSlot()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.dtype = numpy.uint8

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown slot: {}".format( slot.name )
        radius = self.CrosshairRadius.value
        points = map(TinyVector, self.PointList.value)
        
        result[:] = 0
        result_view = result.view(vigra.VigraArray)
        result_view.axistags = self.Output.meta.axistags
        result_3d = result_view.withAxes(*'xyz')

        axiskeys = self.Output.meta.getAxisKeys()
        roi_start_3d = TinyVector(roi.start)
        roi_stop_3d = TinyVector(roi.stop)
        try:
            roi_start_3d.pop( axiskeys.index('c') )
            roi_stop_3d.pop( axiskeys.index('c') )
        except ValueError:
            pass

        try:        
            roi_start_3d.pop( axiskeys.index('t') )
            roi_stop_3d.pop( axiskeys.index('t') )
        except ValueError:
            pass

        for point3d in points:
            point3d -= roi_start_3d
            
            cross_min = point3d - radius
            cross_max = point3d + radius+1
            
            # If the cross would be entirely out-of-view, skip it.
            if (cross_max < [0,0,0]).any() or \
               (cross_min >= result_3d.shape).any():
                continue

            cross_min = numpy.maximum(cross_min, (0,0,0))
            cross_max = numpy.minimum(cross_max, result_3d.shape)

            x,y,z = point3d
            x1,y1,z1 = cross_min
            x2,y2,z2 = cross_max

            if 0 <= y < result_3d.shape[1] and 0 <= z < result_3d.shape[2]:
                result_3d[x1:x2, y,     z    ] = 1
            if 0 <= x < result_3d.shape[0] and 0 <= z < result_3d.shape[2]:
                result_3d[x,     y1:y2, z    ] = 1
            if 0 <= x < result_3d.shape[0] and 0 <= y < result_3d.shape[1]:
                result_3d[x,     y,     z1:z2] = 1

        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.PointList or slot == self.CrosshairRadius:
            self.Output.setDirty()
        else:
            assert slot == self.Input, "Unknown slot: {}".format( slot.name )
