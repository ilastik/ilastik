from __future__ import print_function

from builtins import range
#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.stype import Opaque
from lazyflow.rtype import List
import logging
logger = logging.getLogger(__name__)

import os
import h5py
import vigra
import numpy
import math

def write_numpy_structured_array_to_HDF5(fid, internalPath, data, overwrite = False):
    """
        Serializes a NumPy structure array to an HDF5 file by creating a group that contains
        the individual keys as different array. Also, additional attributes are added to the
        group to store the shape and dtype of the NumPy structure array to allow for serialization
        out. Also, will handle normal NumPy arrays as well.
        
        Note:
            HDF5 does not support generic Python objects. So, serialization of objects to something
            else (perhaps strs of fixed size) must be performed first.
        
        Note:
            TODO: Write doctests.
        
        Args:
            fid(HDF5 file):         either an HDF5 file or an HDF5 filename.
            internalPath(str):      an internal path for the HDF5 file.
            data(numpy.ndarray):    the NumPy structure array to save (or normal NumPy array).
            overwrite(bool):        whether to overwrite what is already there.
    """
    
    close_fid = False
    
    if isinstance(fid, basestring):
        fid = h5py.File(fid, "a")
        close_fid = True
    
    
    dataset = None
    
    try:
        dataset = fid.create_dataset(internalPath, data.shape, data.dtype)
    except RuntimeError:
        if overwrite:
            del fid[internalPath]
            dataset = fid.create_dataset(internalPath, data.shape, data.dtype)
        else:
            raise
    
    dataset[:] = data
    
    if close_fid:
        fid.close()
    


def read_numpy_structured_array_from_HDF5(fid, internalPath):
    """
        Serializes a NumPy structure array from an HDF5 file by reading a group that contains
        all the arrays needed by the NumPy structure array. Also, additional attributes are
        added to the group to store the shape and dtype of the NumPy structure array to allow
        for serialization out. Also, it will handle normal NumPy arrays as well.
        
        Note:
            HDF5 does not support generic Python objects. So, serialization of objects to something
            else (perhaps strs of fixed size) must be performed first.
        
        Args:
            fid(HDF5 file):         either an HDF5 file or an HDF5 filename.
            
            internalPath(str):      an internal path for the HDF5 file.
        
        Note:
            TODO: Write doctests.
        
        Returns:
            data(numpy.ndarray):  the NumPy structure array.
    """
    
    close_fid = False
    
    if isinstance(fid, basestring):
        fid = h5py.File(fid, "r")
        close_fid = True
    
    data = fid[internalPath][:]
    
    if close_fid:
        fid.close()
    
    return(data)



class OpExportToKnime(Operator):
    
    name = "Knime Export"
    
    RawImage = InputSlot()
    CCImage = InputSlot()
    
    ObjectFeatures = InputSlot(rtype=List, stype=Opaque)
    ImagePerObject = InputSlot(stype="bool")
    ImagePerTime = InputSlot(stype="bool")
    FileType = InputSlot(value="h5", stype="str") #can be "csv" or "h5"
    OutputFileName = InputSlot(value="test_export_for_now.h5", stype="str")
    
    WriteData = OutputSlot(stype='bool', rtype=List)
    
    def __init__(self, *args, **kwargs):
        super(OpExportToKnime, self).__init__(*args, **kwargs)
        self.imagePerObject = False
        self.imagePerTime = False
        self.delim = "\t"
        
    def setupOutputs(self):
        self.imagePerObject = self.ImagePerObject.value
        self.imagePerTime = self.ImagePerTime.value
        
        self.WriteData.meta.shape = (1,)
        self.WriteData.meta.dtype = object
        
    
    def propagateDirty(self, slot, subindex, roi): 
        pass
    
    
    def join_struct_arrays(self, arrays):
        newdtype = sum((a.dtype.descr for a in arrays), [])
        print(newdtype)
        newrecarray = numpy.empty(len(arrays[0]), dtype = newdtype)
        for a in arrays:
            for name in a.dtype.names:
                newrecarray[name] = a[name]
        return newrecarray
    
    def write_to_h5(self, table, image_paths, roi):
        
        times = roi._l
        if len(times) == 0:
            # we assume that 0-length requests are requesting everything
            times = list(range(self.RawImage.meta.shape[0]))
        
        with h5py.File(self.OutputFileName.value, "w") as fout:
            print("Exporting to:", os.path.join(os.getcwd(), self.OutputFileName.value))
            gr_images = fout.create_group("images")
            if not self.imagePerObject and not self.imagePerTime:
                # One image for everything. 
                # FIXME: what if a subrange in time is requested? Stack different time
                # values on top of each other?
                
                raw_image = self.RawImage[:].wait()
                cc_image = self.CCImage[:].wait()
                
                raw_name = "raw"
                cc_name = "labels"
                
                image_paths["raw"][:] = "images/0/"+raw_name
                image_paths["labels"][:] = "images/0/"+cc_name
                
                ri = gr_images.create_dataset("0/raw_name", data=raw_image.squeeze())
                cci = gr_images.create_dataset("0/cc_name", data=cc_image.squeeze())
                
                ri.attrs["type"] = "image"
                ri.attrs["axistags"] = self.RawImage.meta.axistags.toJSON()
                
                cci.attrs["type"] = "labeling"
                cci.attrs["axistags"] = self.CCImage.meta.axistags.toJSON()                
            
            elif self.imagePerObject and not self.imagePerTime:
                # We export a bounding box image for every object individually
                raw_shape = self.RawImage.meta.getTaggedShape()
                nchannels = raw_shape['c']
                try:
                    minxs = table["Default features, Coord<Minimum>_ch_0"].astype(numpy.int32)
                    minys = table["Default features, Coord<Minimum>_ch_1"].astype(numpy.int32)
                    maxxs = table["Default features, Coord<Maximum>_ch_0"].astype(numpy.int32)
                    maxys = table["Default features, Coord<Maximum>_ch_1"].astype(numpy.int32)
                    time_values = table["Time"].astype(numpy.int32)
                except ValueError:
                    logger.info("Object bounding boxes are not passed as features. Object images will not be saved")
                    for i in range(table.shape[0]):
                        image_paths["raw"][i] = ""
                        image_paths["labels"][i] = ""
                else:
                    try:
                        minzs = table["Default features, Coord<Minimum>_ch_2"].astype(numpy.int32)
                        maxzs = table["Default features, Coord<Maximum>_ch_2"].astype(numpy.int32)
                    except ValueError:
                        minzs = None
                        maxzs = None
                        
                    for i, minx in enumerate(minxs):
                        bbox = [slice(time_values[i], time_values[i]+1, None), slice(minx, maxxs[i], None), slice(minys[i], maxys[i], None)]
                        if minzs is not None:
                            bbox.append(slice(minzs[i], maxzs[i], None))
                        else:
                            bbox.append(slice(0, 1, None))
                        cc_bbox = list(bbox)
                        bbox.append(slice(0, nchannels, None))
                        cc_bbox.append(slice(0, 1, None))
                        
                        raw_image = self.RawImage[bbox].wait()
                        cc_image = self.CCImage[cc_bbox].wait()
                        
                        #ensure the right order
                        ndigits = int(math.floor( math.log10( table.shape[0] ) ) + 1)
                        formatstring = "{:0>"+str(ndigits)+"d}"
                        numstring = formatstring.format(i)
                        
                        gr_images_obj = gr_images.create_group(numstring)
                        rawname = numstring+"/raw"
                        ccname = numstring+"/labels"
                        
                        image_paths["raw"][i] = rawname
                        image_paths["labels"][i] = ccname
                        
                        ri = gr_images_obj.create_dataset("raw", data=raw_image.squeeze())
                        cci = gr_images_obj.create_dataset("labels", data=cc_image.squeeze())                       
                        
                        valid_axistags = [self.RawImage.meta.axistags[j] for j, s in enumerate(raw_image.shape) if s > 1]
                        valid_axistags_cc = [self.CCImage.meta.axistags[j] for j, s in enumerate(cc_image.shape) if s > 1]
        
                        ri.attrs["type"] = "image"
                        ri.attrs["axistags"] = vigra.AxisTags(valid_axistags).toJSON()
                        
                        cci.attrs["type"] = "labeling"
                        cci.attrs["axistags"] = vigra.AxisTags(valid_axistags_cc).toJSON()
                        
                assert image_paths.shape[0] == table.shape[0]
            
            elif self.imagePerTime and not self.imagePerObject:
                for t in times:                                              
                    bbox = [slice(t, t+1, None), slice(None), slice(None), slice(None), slice(None)]
                    
                    raw_image = self.RawImage[bbox].wait()
                    cc_image = self.CCImage[bbox].wait()
                
                    gr_images_obj = gr_images.create_group("{}".format(t))
                    rawname = "{}/raw".format(t)
                    ccname = "{}/labels".format(t)
                    
                    image_paths["raw"][t-min(times)] = rawname
                    image_paths["labels"][t-min(times)] = ccname
                    
                    ri = gr_images_obj.create_dataset("raw", data=raw_image.squeeze())
                    cci = gr_images_obj.create_dataset("labels", data=cc_image.squeeze())
                    
                    valid_axistags = [self.RawImage.meta.axistags[i] for i, s in enumerate(raw_image.shape) if s > 1]
                    valid_axistags_cc = [self.CCImage.meta.axistags[i] for i, s in enumerate(cc_image.shape) if s > 1]
    
                    ri.attrs["type"] = "image"
                    ri.attrs["axistags"] = vigra.AxisTags(valid_axistags).toJSON()
                    
                    cci.attrs["type"] = "labeling"
                    cci.attrs["axistags"] = vigra.AxisTags(valid_axistags_cc).toJSON() 
                                        
                assert image_paths.shape[0] == table.shape[0]

            write_numpy_structured_array_to_HDF5(fout, "tables/FeatureTable", table, True)
            write_numpy_structured_array_to_HDF5(fout, "tables/ImagePathTable", image_paths, True)
        
    def write_to_csv(self, table):
        
        with open(self.OutputFileName.value, "w") as fout:
            names = table.dtype.names
            header = self.delim.join(names)

            fout.write(header+"\n")
            
            for sublist in table:
                fout.write(self.delim.join([str(item) for item in sublist])+"\n")
        
        
        
    def execute(self, slot, subindex, roi, result):
        assert slot==self.WriteData

        
        #request the right time values from the feature table? But then it has to be a slot!
        #the correct requesting has to happen before
        table = self.ObjectFeatures.value
        filetype = self.FileType.value
        if filetype=="h5":
            if not self.RawImage.ready() or not self.CCImage.ready():
                logger.info("Image slots are not ready for export!")
                result[0] = False
                return
            image_paths = numpy.zeros(table.shape[0], dtype={"names":["raw", "labels"], "formats":['a50', 'a50']})
            self.write_to_h5(table, image_paths, roi)
        elif filetype=="csv":
            self.write_to_csv(table)
        
        # We're finished.
        result[0] = True
    
    def run_export(self, constraints={}):
        #FIXME: constraints should be replaced by a real roi, like we 
        #usually do in execute() functions
        
        if not self.RawImage.ready() or not self.CCImage.ready():
            print("NOT READY")
            return False
        
        table = self.ObjectFeatures.value
        
        image_paths = numpy.zeros(table.shape[0], dtype={"names":["raw", "labels"], "formats":['a50', 'a50']})
        
        filetype = self.FileType.value
        
        if filetype=="h5":
            self.write_to_h5(table, image_paths, constraints)
        elif filetype=="csv":
            self.write_to_csv(table)
            
        return True
            
        
        
    
