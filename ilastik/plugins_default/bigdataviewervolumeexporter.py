import xml.etree.ElementTree as ET
import numpy as np
import h5py
import mamutxmlbuilder

class BigDataViewerVolumeExporter(object):
    '''
    Set up a BigDataViewer xml containing size information of the dataset, reference the raw HDF5, 
    and add a transformation for every time point. 
    '''
    def __init__(self, rawH5Filename, rawH5path, datasetDimensions=None):
        self.listOfTimePoints = []
        self.root = ET.Element('SpimData')
        self.tree = ET.ElementTree(self.root)

        if datasetDimensions is None:
            with h5py.File(rawH5Filename, 'r') as f:
                datasetDimensions = f[rawH5path].shape
                datasetDimensions = datasetDimensions[1:3]
        else:
            assert(len(datasetDimensions) == 3)

        # general setup
        self.root.set('version', '0.2')
        bp = ET.SubElement(self.root, 'BasePath')
        bp.set('type', 'relative')
        bp.text = '.'
        self.viewRegistrations = ET.SubElement(self.root, 'ViewRegistrations')
        self.sequenceDescription = ET.SubElement(self.root, 'SequenceDescription')

        # image loader
        il = ET.SubElement(self.sequenceDescription, 'ImageLoader')
        il.set('format', 'ilastik.hdf5') # use OUR format for loading!
        hdf = ET.SubElement(il, 'hdf5')
        hdf.set('type', 'absolute')
        hdf.text = rawH5Filename
        ds = ET.SubElement(il, 'dataset')
        ds.text = rawH5path

        # View Setup
        vss = ET.SubElement(self.sequenceDescription, 'ViewSetups')
        vs = ET.SubElement(vss, 'ViewSetup')
        i = ET.SubElement(vs, 'id')
        i.text = '0'
        n = ET.SubElement(vs, 'name')
        n.text = 'channel 1'
        s = ET.SubElement(vs, 'size')
        s.text = '{} {} {}'.format(*datasetDimensions)
        a = ET.SubElement(vs, 'attributes')
        c = ET.SubElement(a, 'channel')
        c.text = '1'
        vos = ET.fromstring('''<voxelSize><unit>micrometer</unit><size>1.0 1.0 1.0</size></voxelSize>''')
        vs.append(vos)

        a = ET.SubElement(vss, 'Attributes')
        a.set('name', 'channel')
        c = ET.SubElement(a, 'Channel')
        i = ET.SubElement(c, 'id')
        i.text = '1'
        n = ET.SubElement(c, 'name')
        n.text = '1'

    def addTimePoint(self, time):
        assert(len(self.listOfTimePoints) == 0 or time > max(self.listOfTimePoints)) # timepoints need to be given in ascending order
        self.listOfTimePoints.append(time)
        vr = ET.SubElement(self.viewRegistrations, 'ViewRegistration')
        vr.set('setup', '0')
        vr.set('timepoint', str(time))
        vt = ET.SubElement(vr, 'ViewTransform')
        vt.set('type', 'affine')
        affine = ET.SubElement(vt, 'affine')
        affine.text = "1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0"
    
    def _finalizeTimepoints(self):
        assert(self.listOfTimePoints == sorted(self.listOfTimePoints))
        tp = ET.SubElement(self.sequenceDescription, 'Timepoints')
        tp.set('type', 'range')
        f = ET.SubElement(tp, 'first')
        f.text = str(min(self.listOfTimePoints))
        l = ET.SubElement(tp, 'last')
        l.text = str(max(self.listOfTimePoints))
            
    def writeToFile(self, filename):
        self._finalizeTimepoints() 
        self.tree.write(filename)

if __name__ == '__main__':
    bve = BigDataViewerVolumeExporter('myhdf5File.h5', 'exported_data', [123, 654, 789])
    bve.addTimePoint(0)
    bve.addTimePoint(1)
    bve.addTimePoint(2)
    bve._finalizeTimepoints()
    mamutxmlbuilder.MamutXmlBuilder.indent(bve.root)
    print(ET.dump(bve.root))
