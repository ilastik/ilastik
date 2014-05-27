#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.stype import Opaque
from lazyflow.rtype import List

import h5py
import numpy
import numpy.lib.recfunctions as rfn

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
    
    if type(fid) is str:
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
    
    if type(fid) is str:
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
    
    def run_export(self, constraints={}):
        
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
            
            elif self.imagePerTime and not self.imagePerObject:
                # check for constraints passed with function call
                try:
                    if 't' in constraints:                    
                        tmin = constraints['t']['min']
                        tmax = constraints['t']['max']
                    else:
                        raise Exception("Constraints on an axis have to be defined by 'min' and 'max' value")
                except:
                    tmin, tmax = (-1, -1)
                
                # sanity check given constraint values
                tmax = max(min(tmax, self.RawImage.meta.getTaggedShape()['t']), 0)
                tmin = min(max(tmin, 0), tmax)
                
                for t in range(tmin, tmax):                                              
                    bbox = [slice(t, t+1, None), slice(None), slice(None), slice(None), slice(None)]      
                    
                    raw_image = self.RawImage[bbox].wait()
                    cc_image = self.CCImage[bbox].wait()
                
                    gr_images_obj = gr_images.create_group("{}".format(t))
                    rawname = "{}/raw".format(t)
                    ccname = "{}/labels".format(t)
                    
                    image_paths["raw"][t] = rawname
                    image_paths["labels"][t] = ccname
                    
                    ri = gr_images_obj.create_dataset("raw", data=raw_image.squeeze())
                    cci = gr_images_obj.create_dataset("labels", data=cc_image.squeeze())
                    
                    ri.attrs["type"] = "image"
                    cci.attrs["type"] = "labeling"
                                        
                assert image_paths.shape[0] == table.shape[0]

            write_numpy_structured_array_to_HDF5(fout, "tables/FeatureTable", table, True)
            write_numpy_structured_array_to_HDF5(fout, "tables/ImagePathTable", image_paths, True)
            #gr = fout.create_group("table")
            #gr.create_dataset("Table", data = table)
            #gr.create_dataset("Image_paths", data=image_paths)
            
            
        return True
            
        
        
    