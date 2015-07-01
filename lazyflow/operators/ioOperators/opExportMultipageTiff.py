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
import os
import collections

import numpy
import psutil

import vigra
import tifffile

from lazyflow.graph import Operator, InputSlot
from lazyflow.utility import OrderedSignal
from lazyflow.operators.opReorderAxes import OpReorderAxes

import logging
logger = logging.getLogger(__name__)

class OpExportMultipageTiff(Operator):
    Input = InputSlot() # The last two non-singleton axes (except 'c') are the axes of the 'pages'.
                        # Re-order the axes yourself if you want an alternative slicing direction
    Filepath = InputSlot()

    DEFAULT_BATCH_SIZE = 4

    def __init__(self, *args, **kwargs):
        super(OpExportMultipageTiff, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
        self._opReorderAxes = OpReorderAxes(parent=self)
        self._opReorderAxes.Input.connect( self.Input )

    def setupOutputs(self):
        # Always export in tzcyx order (but omit missing axes)
        input_axes = self.Input.meta.getAxisKeys()
        export_axes = "".join( filter( lambda k: k in input_axes, 'tzcyx' ) )
        if not set("yx").issubset(set(export_axes)):
            # This could potentially be fixed...
            raise Exception("I don't know how to export data without both an X and Y axis")
        
        self._opReorderAxes.AxisOrder.setValue(export_axes)
        self._export_axes = export_axes

    def run_export(self):
        """
        Request the volume in slices (running in parallel), and write each slice to the correct page.
        Note: We can't use BigRequestStreamer here, because the data for each slice wouldn't be 
              guaranteed to arrive in the correct order.
        """
        # Delete existing image if present
        image_path = self.Filepath.value
        if os.path.exists(image_path):
            os.remove(image_path)

        tagged_shape = self.Input.meta.getTaggedShape()
        export_shape = self._opReorderAxes.Output.meta.shape
        shape_yx = export_shape[-2:]
        stacked_axes_shape = export_shape[:-2]
        num_pages = numpy.prod(stacked_axes_shape)

        def create_slice_req():
            for stacked_axes_ndindex in numpy.ndindex(*stacked_axes_shape):
                roi = numpy.zeros( (2,) + (len(export_shape),), dtype=int )
                roi[:, :-2] = stacked_axes_ndindex
                roi[1, :-2] += 1
                roi[1, -2:] = shape_yx
                yield self._opReorderAxes.Output(*roi)
        iter_slice_requests = create_slice_req()

        parallel_requests = self.DEFAULT_BATCH_SIZE
        
        # If ram usage info is available, make a better guess about how many requests we can launch in parallel
        ram_usage_per_requested_pixel = self.Input.meta.ram_usage_per_requested_pixel
        if ram_usage_per_requested_pixel is not None:
            pixels_per_slice = numpy.prod(shape_yx)
            if 'c' in tagged_shape:
                pixels_per_slice /= tagged_shape['c']
            
            ram_usage_per_slice = pixels_per_slice * ram_usage_per_requested_pixel

            # Fudge factor: Reduce RAM usage by a bit
            available_ram = psutil.virtual_memory().available
            available_ram *= 0.5

            parallel_requests = int(available_ram / ram_usage_per_slice)
        
        # Start with a batch of images
        reqs = collections.deque()
        for next_request_index in range( min(parallel_requests, num_pages) ):
            reqs.append( iter_slice_requests.next() )
        
        self.progressSignal(0)
        pages_written = 0
        while reqs:
            self.progressSignal( 100*next_request_index / num_pages )
            req = reqs.popleft()
            slice_data = req.wait()
            slice_data = vigra.taggedView(slice_data, self._export_axes)
            next_request_index += 1
            
            # Add a new request to the batch
            if next_request_index < num_pages:
                reqs.append( iter_slice_requests.next() )
            
            if pages_written == 0:
                xml_description = OpExportMultipageTiff.generate_ome_xml_description(
                                     self._opReorderAxes.Output.meta.getAxisKeys(),
                                     self._opReorderAxes.Output.meta.shape,
                                     self._opReorderAxes.Output.meta.dtype,
                                     os.path.split(image_path)[1] )
                # Write the first slice with tifffile, which allows us to write the tags.
                with tifffile.TiffWriter( image_path, software='ilastik', byteorder='<' ) as writer:
                    writer.save( slice_data.withAxes('yx'), description=xml_description, planarconfig='planar')
            else:
                # Append a slice to the multipage tiff file
                vigra.impex.writeImage( slice_data.withAxes('yx'), image_path, dtype='', compression='NONE', mode='a' )
            pages_written += 1

        self.progressSignal(100)

    # No output slots...
    def execute(self, slot, subindex, roi, result): pass 
    def propagateDirty(self, slot, subindex, roi): pass

    @classmethod
    def generate_ome_xml_description(cls, axes, shape, dtype, filename=''):
        """
        Generate an OME XML description of the data we're exporting,
        suitable for the image_description tag of the first page.

        axes and shape should be provided in C-order (will be reversed in the XML)
        """
        import uuid
        import xml.etree.ElementTree as ET

        # Normalize the inputs
        axes = "".join(axes)
        shape = tuple(shape)
        if not isinstance(dtype, type):
            dtype = dtype().type

        ome = ET.Element('OME')
        uuid_str = "urn:uuid:" + str(uuid.uuid1())
        ome.set('UUID', uuid_str)
        ome.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
        ome.set('xsi:schemaLocation', 
                "http://www.openmicroscopy.org/Schemas/OME/2015-01 "
                "http://www.openmicroscopy.org/Schemas/OME/2015-01/ome.xsd")
        
        image = ET.SubElement(ome, 'Image')
        image.set('ID', 'Image:0')
        image.set('Name', 'exported-data')
        
        pixels = ET.SubElement(image, 'Pixels')
        pixels.set('BigEndian', 'true')
        pixels.set('ID', 'Pixels:0')

        fortran_axes = "".join(reversed(axes)).upper()
        pixels.set('DimensionOrder', fortran_axes)

        for axis, dim in zip( axes.upper(), shape ):
            pixels.set('Size'+axis, str(dim))

        types = { numpy.uint8  : 'uint8', 
                  numpy.uint16 : 'uint16', 
                  numpy.uint32 : 'uint32', 
                  numpy.int8   : 'int8', 
                  numpy.int16  : 'int16', 
                  numpy.int32  : 'int32', 
                  numpy.float32  : 'float', 
                  numpy.float64  : 'double', 
                  numpy.complex64  : 'complex', 
                  numpy.complex128  : 'double-complex' }

        pixels.set('Type', types[dtype])
        
        # Omit channel information (is that okay?)
        # channel0 = ET.SubElement(pixels, "Channel")
        # channel0.set("ID", "Channel0:0")
        # channel0.set("SamplesPerPixel", "1")

        assert axes[-2:] == "yx"
        for page_index, page_ndindex in enumerate(numpy.ndindex(*shape[:-2])):
            tiffdata = ET.SubElement(pixels, "TiffData")
            for axis, index in zip(axes[:-2].upper(), page_ndindex):
                tiffdata.set("First"+axis, str(index))
            tiffdata.set("PlaneCount", "1")
            tiffdata.set("IFD", str(page_index))
            uuid_tag = ET.SubElement(tiffdata, "UUID")
            uuid_tag.text = uuid_str
            uuid_tag.set('FileName', filename)

        from textwrap import dedent
        from StringIO import StringIO
        xml_stream = StringIO()
        comment = ET.Comment(dedent('\
            <!-- Warning: this comment is an OME-XML metadata block, which contains crucial '
            'dimensional parameters and other important metadata. Please edit cautiously '
            '(if at all), and back up the original data before doing so. For more information, '
            'see the OME-TIFF web site: http://ome-xml.org/wiki/OmeTiff. -->'))

        tree = ET.ElementTree(ome)
        tree.write(xml_stream, encoding='utf-8', xml_declaration=True)
        
        if logger.isEnabledFor(logging.DEBUG):
            import xml.dom.minidom
            reparsed = xml.dom.minidom.parseString(xml_stream.getvalue())
            logger.debug("Generated OME-TIFF metadata:\n" + reparsed.toprettyxml())
        
        return xml_stream.getvalue()





        