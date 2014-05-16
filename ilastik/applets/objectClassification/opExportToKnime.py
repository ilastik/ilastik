#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.stype import Opaque
from lazyflow.rtype import List
from lazyflow.operators.ioOperators import write_numpy_structured_array_to_HDF5

import h5py
import numpy
import numpy.lib.recfunctions as rfn

class OpExportToKnime(Operator):
    
    name = "Knime Export"
    
    RawImage = InputSlot()
    CCImage = InputSlot()
    
    ObjectFeatures = InputSlot(rtype=List, stype=Opaque)
    ImagePerObject = InputSlot(stype="bool")
    ImagePerTime = InputSlot(stype="bool")
    
    WriteImage = OutputSlot(stype='bool')
    
    def __init__(self, *args, **kwargs):
        super(OpExportToKnime, self).__init__(*args, **kwargs)
        self.outputFileName = "test_export_for_now.h5"
        self.imagePerObject = False
        self.imagePerTime = False
        
    def setupOutputs(self):
        self.imagePerObject = self.ImagePerObject.value
        self.imagePerTime = self.ImagePerTime.value
        
    def execute(self, slot, subindex, roi, result):
        pass
    def propagateDirty(self, slot, subindex, roi): 
        pass
    
    
    def join_struct_arrays(self, arrays):
        newdtype = sum((a.dtype.descr for a in arrays), [])
        print newdtype
        newrecarray = numpy.empty(len(arrays[0]), dtype = newdtype)
        for a in arrays:
            for name in a.dtype.names:
                newrecarray[name] = a[name]
        return newrecarray
    
    def run_export(self):
        
        if not self.RawImage.ready() or not self.CCImage.ready():
            print "NOT READY"
            return False
        
        table = self.ObjectFeatures.value
        
        image_paths = numpy.zeros(table.shape[0], dtype={"names":["raw", "labels"], "formats":['a50', 'a50']})
        
        #image_paths = numpy.zeros(table.shape[0], dtype=[('raw', 'S', 100),('labeled', 'S', 100)])
        
        with h5py.File(self.outputFileName, "w") as fout:
            gr_images = fout.create_group("images")
            if not self.imagePerObject and not self.imagePerTime:
                #one image for everything
                raw_image = self.RawImage[:].wait()
                cc_image = self.CCImage[:].wait()
                
                raw_name = "raw"
                cc_name = "labels"
                
                image_paths["raw"][:] = "images/0/"+raw_name
                image_paths["labels"][:] = "images/0/"+cc_name
                
                ri = gr_images.create_dataset("0/raw_name", data=raw_image.squeeze())
                cci = gr_images.create_dataset("0/cc_name", data=cc_image.squeeze())
                
                ri.attrs["type"] = "image"
                cci.attrs["type"] = "labeling"
                
            
            elif self.imagePerObject and not self.imagePerTime:
                minxs = table["Default features, Coord<Minimum>_ch_0"].astype(numpy.int32)
                minys = table["Default features, Coord<Minimum>_ch_1"].astype(numpy.int32)
                maxxs = table["Default features, Coord<Maximum>_ch_0"].astype(numpy.int32)
                maxys = table["Default features, Coord<Maximum>_ch_1"].astype(numpy.int32)
                
                try:
                    minzs = table["Default features, Coord<Minimum>_ch_2"].astype(numpy.int32)
                    maxzs = table["Default features, Coord<Maximum>_ch_2"].astype(numpy.int32)
                except ValueError:
                    minzs = None
                    maxzs = None    
                
                for i, minx in enumerate(minxs):
                    bbox = [slice(0, 1, None), slice(minx, maxxs[i], None), slice(minys[i], maxys[i], None)]
                    if minzs is not None:
                        bbox.append(slice(minzs[i], maxzs[i], None))
                    else:
                        bbox.append(slice(0, 1, None))
                        #FIXME: only 1 channel!!!!!!!
                    bbox.append(slice(0, 1, None))
                    
                    
                    raw_image = self.RawImage[bbox].wait()
                    cc_image = self.CCImage[bbox].wait()
                
                    
                    #print rawname, ccname
                    
                    #newtable["raw"][i] = rawname
                    #newtable["labeled"][i] = ccname
                    gr_images_obj = gr_images.create_group("{}".format(i))
                    rawname = "{}/raw".format(i)
                    ccname = "{}/labels".format(i)
                    
                    image_paths["raw"][i] = rawname
                    image_paths["labels"][i] = ccname
                    
                    ri = gr_images_obj.create_dataset("raw", data=raw_image.squeeze())
                    cci = gr_images_obj.create_dataset("labels", data=cc_image.squeeze())
                    
                    ri.attrs["type"] = "image"
                    cci.attrs["type"] = "labeling"
                    
                #print image_paths.shape, table.shape
                assert image_paths.shape[0] == table.shape[0]
                #newtable = self.join_struct_arrays((table, image_paths))
            
            write_numpy_structured_array_to_HDF5(fout, "tables/FeatureTable", table, True)
            write_numpy_structured_array_to_HDF5(fout, "tables/ImagePathTable", image_paths, True)
            #gr = fout.create_group("table")
            #gr.create_dataset("Table", data = table)
            #gr.create_dataset("Image_paths", data=image_paths)
            
            
        return True
            
        
        
    