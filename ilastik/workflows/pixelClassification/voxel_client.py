import sys
import time
import httplib
import requests
import numpy as np

from PyQt4.QtCore import QObject, pyqtSignal, QString

from volumina.pixelpipeline.asyncabcs import RequestABC, SourceABC
from volumina.layer import GrayscaleLayer
from volumina.viewer import Viewer

from voxels_nddata_codec import VoxelsNddataCodec

class VoxelClientRequest(object):

    def __init__(self, hostname, dataset_name, source_name, dtype, start, stop):
        self.hostname = hostname
        self.dataset_name = dataset_name
        self.source_name = source_name
        self.dtype = dtype
        self.start = start
        self.stop = stop

    def wait( self ):
        start_str = '_'.join(map(str, self.start))
        stop_str = '_'.join(map(str, self.stop))
        r = requests.get("http://{hostname}/api/voxels/{dataset_name}/{source_name}".format(**self.__dict__),
                         params={'extents_min': start_str, 'extents_max': stop_str, 'format': 'raw'},
                         stream=True)

        r.raise_for_status()
        
        shape = np.array(self.stop) - self.start
        codec = VoxelsNddataCodec(self.dtype)
        arr = codec.decode_to_ndarray(r.raw, shape)
        return arr

class VoxelClientSource(QObject):
    
    isDirty = pyqtSignal( object )
    numberOfChannelsChanged = pyqtSignal(int)

    def __init__(self, hostname, dataset_name, source_name, initial_state):
        super(VoxelClientSource, self).__init__()
        self.hostname = hostname
        self.dataset_name = dataset_name # in ilastik terms, this is the 'lane'
        self.source_name = source_name # This is the slot/layer
        self.state = initial_state
        
    def update_state(self, new_state):
        old_state = self.state
        self.state = new_state
        
        old_channels = old_state['shape'][-1]
        new_channels = new_state['shape'][-1]
        if new_channels != old_channels:
            self.numberOfChannelsChanged(new_channels)

        if new_state != old_state:
            # Everything is dirty
            full_slicing = tuple(slice(a,b) for a,b in zip(5*(0,), self.state['shape']))
            self.setDirty( full_slicing )

    def numberOfChannels(self):
        return self.state['shape'][-1]

    def dtype(self):
        return np.dtype(self.state['dtype']).type

    def request( self, slicing ):
        # Convert slicing to (start, stop)
        start, stop = zip(*[(s.start, s.stop) for s in slicing])
        start = [0 if x is None else x for x in start]
        stop = [b if a is None else a for a,b in zip(stop, self.state['shape'])]

        return VoxelClientRequest( self.hostname, self.dataset_name, self.source_name, self.dtype(), start, stop )

    def setDirty( self, slicing ):
        self.isDirty.emit(slicing)

    def __eq__( self, other ):
        return  self.hostname == other.hostname and \
                self.dataset_name == other.dataset_name and \
                self.source_name == other.source_name

    def __ne__( self, other ):
        return not (self == other)
    
    def clean_up(self):
        pass


if __name__ == "__main__":
    from PyQt4.QtGui import QApplication
    
    DEBUG = False
    if DEBUG:
        print "DEBUGGING with localhost:8000"
        sys.argv += ["localhost:8000"]
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("hostname")
    args = parser.parse_args()

    hostname = args.hostname

    app = QApplication([])
        
    r = requests.get("http://{hostname}/api/list-datasets".format(hostname=hostname))
    if r.status_code != httplib.OK:
        raise RuntimeError("Could not fetch dataset list: {}".format(r.status_code))
    
    dset_names = r.json()
    print dset_names
    if len(dset_names) < 1:
        raise RuntimeError("No datasets listed.")
    
    # For now, just pick the first one.
    dataset_name = dset_names[0]
    r = requests.get("http://{hostname}/api/source-states/{dataset_name}".format(**locals()))
    r.raise_for_status()
    states = r.json()
    
    datasources = {}
    viewer = Viewer()
    for state in states:
        assert state['axes'] == 'txyzc', \
            "For now, sources must adhere to volumina's wacky axis order. (Got {})".format(state['axes'])
        source = VoxelClientSource(args.hostname, dataset_name, state['name'], state)
        datasources[state['name']] = source

        layer = GrayscaleLayer(source)
        layer.numberOfChannels = state['shape'][-1]
        layer.name = QString(state['name'])

        viewer.dataShape = state['shape']
        viewer.layerstack.append(layer)
    
    stopped = [False]
    def state_monitor_thread():
        # TODO: This detects changes to the datasources we already have,
        #       but doesn't handle sources disappearing or appearing.
        while not stopped[0]:
            r = requests.get("http://{hostname}/api/source-states/{dataset_name}"
                             .format(hostname=hostname, dataset_name=dataset_name))
            r.raise_for_status()
            new_states = { state['name'] : state for state in r.json() }
            for name, source in datasources.items():
                source.update_state(new_states[name])
            
            time.sleep(0.1)

    import threading
    th = threading.Thread(target=state_monitor_thread)
    th.daemon = True
    th.start()

    viewer.show()
    viewer.raise_()
    app.exec_()
