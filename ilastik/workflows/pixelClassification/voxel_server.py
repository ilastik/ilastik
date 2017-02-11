import os
import json
import atexit
import signal
import logging
from textwrap import dedent
from functools import partial
from collections import namedtuple, OrderedDict

import numpy as np
from flask import Flask, request, redirect, url_for, send_file, jsonify

from lazyflow.graph import OperatorWrapper
from lazyflow.operators.opReorderAxes import OpReorderAxes

from voxels_nddata_codec import VoxelsNddataCodec

app = Flask(__name__)

VoxelSourceState = namedtuple("VoxelSourceState", "name axes shape dtype version") # also: drange?

# For now, one global slot tracker for the server
SLOT_TRACKER = None
class SlotTracker(object):
    
    def __init__(self, image_name_multislot, multislots, forced_axes=None):
        self.image_name_multislot = image_name_multislot
        self._slot_versions = {} # { dataset_name : { slot_name : [slot, version] } }
        
        self.multislot_names = [s.name for s in multislots]
        if forced_axes is None:
            self.multislots = multislots
        else:
            self.multislots = []
            for multislot in multislots:
                op = OperatorWrapper(OpReorderAxes, parent=multislot.getRealOperator().parent, broadcastingSlotNames=['AxisOrder'])
                op.AxisOrder.setValue(forced_axes)
                op.Input.connect( multislot )
                self.multislots.append( op.Output )
    
    def get_dataset_names(self):
        names = []
        for lane_index, name_slot in enumerate(self.image_name_multislot):
            if name_slot.ready():
                name = name_slot.value
            else:
                name = "dataset-{}".format(lane_index)
            names.append(name)
        return names

    def get_slot_versions(self, dataset_name):
        found = False
        lane_index = None
        for lane_index, name_slot in enumerate(self.image_name_multislot):
            if name_slot.value == dataset_name:
                found = True
                break
        if not found:
            raise RuntimeError("Dataset name not found: {}".format(dataset_name))

        if dataset_name not in self._slot_versions:
            for multislot in self.multislots:
                slot = multislot[lane_index]
                # TODO: Unsubscribe to these signals on shutdown...
                slot.notifyDirty( partial(self._increment_version, dataset_name) )
                slot.notifyMetaChanged( partial(self._increment_version, dataset_name) )
            
            self._slot_versions[dataset_name] = { self.multislot_names[self.multislots.index(multislot)] : [multislot[lane_index], 0] for multislot in self.multislots }

        return self._slot_versions[dataset_name]

    def _increment_version(self, dataset_name, slot, *args):
        for name in self._slot_versions[dataset_name].keys():
            if self._slot_versions[dataset_name][name][0] == slot:
                self._slot_versions[dataset_name][name][1] += 1
                return
        assert False, "Couldn't find slot"

    def get_states(self, dataset_name):
        states = OrderedDict()
        slot_versions = self.get_slot_versions(dataset_name)
        for slot_name, (slot, version) in slot_versions.items():
            axes = ''.join(slot.meta.getAxisKeys())
            states[slot_name] = VoxelSourceState( slot_name,
                                                  axes,
                                                  slot.meta.shape,
                                                  slot.meta.dtype.__name__,
                                                  version)
        return states
    
    def get_slot(self, dataset_name, slot_name):
        slot_versions = self.get_slot_versions(dataset_name)
        return slot_versions[slot_name][0]

@app.route('/')
def index():
    return redirect(url_for('status_page'))

@app.route('/status')
def status_page():
    page = dedent("""\
    <html>
      <head>
        <title>Status</title>
      </head>
    <body>
    Up and running...<br>
    <a href="{list_datasets}">Dataset List</a><br>
    </body>
    </html>
    """.format(list_datasets=url_for('list_datasets'), 
               debug_link="localhost:8000/api/voxels/002cell/InputImages?extents_min=0_0_0&extents_max=256_256_1"))
    return page
        
@app.route('/api/list-datasets')
def list_datasets():
    return jsonify(SLOT_TRACKER.get_dataset_names())

@app.route('/api/source-states/<dataset_name>')
def source_states(dataset_name):
    # TODO: Error handling
    json_states = []
    states = SLOT_TRACKER.get_states(dataset_name)
    for state in states.values():
        json_states.append( OrderedDict( zip(state._fields, state) ) )
    return jsonify(json_states)

@app.route('/api/voxels/<dataset_name>/<source_name>')
def voxels(dataset_name, source_name):
    start = map(int, request.args['extents_min'].split('_'))
    stop = map(int, request.args['extents_max'].split('_'))
    slot = SLOT_TRACKER.get_slot(dataset_name, source_name)
    
    format = 'raw'
    if 'format' in request.args:
        format = str(request.args['format'])

    data = slot(start, stop).wait()

    if format == 'raw':
        data = np.asarray(data, order='C')
        stream = VoxelsNddataCodec(data.dtype).create_encoded_stream_from_ndarray(data)
        return send_file(stream, mimetype=VoxelsNddataCodec.VOLUME_MIMETYPE)
    elif format in ('tiff', 'png'):
        import vigra
        fname = '/tmp/data.' + format
        vigra.impex.writeImage(data.squeeze(), fname, dtype='NBYTE')
        return send_file(fname)
    else:
        raise RuntimeError("unsupported format: {}".format(format))

def start_server(image_name_multislot, multislots, port=8000, debug_mode=False, use_thread=False):
    assert not debug_mode or not use_thread, "Can't use debug_mode and use_thread simultaneously"
    
    global SLOT_TRACKER
    SLOT_TRACKER = SlotTracker(image_name_multislot, multislots, forced_axes='txyzc') # for now, force wacky volumina order
    
    # Don't log ordinary GET, POST, etc.
    # logging.getLogger('werkzeug').setLevel(logging.ERROR)

    # Shutdown functions
    # atexit.register(cleanup)
    
    # Terminate results in normal shutdown
    signal.signal(signal.SIGTERM, lambda signum, stack_frame: exit(1))

    def start():    
        print "Starting server on 0.0.0.0:{}".format(port)
        app.run(host='0.0.0.0', port=port, debug=False)
    
    if use_thread:
        import threading
        server_thread = threading.Thread(target=start)
        server_thread.daemon = True
        server_thread.start()
        return server_thread
    else:
        return start()

