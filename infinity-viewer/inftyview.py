#!/usr/bin/env python
#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import argparse
import sys
import os.path as path
import h5py
from PyQt4.QtGui import QApplication

import volumina.api as vol
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedArrayCache, OpArrayPiper

class OpH5StackReader5d( Operator ):
    name = "H5StackReader5d"
    description = "represent stack of h5 files as 5d array"
       
    inputSlots = [InputSlot('h5fns'), InputSlot('dataset')]
    outputSlots = [OutputSlot("array5d")]
    
    def notifyConnectAll(self):
        h5fns = self.inputs["h5fns"].value
        dataset_name = self.inputs["dataset"].value
        timesteps = len(h5fns)
        # probe one file
        with h5py.File(h5fns[0], 'r') as f:
            dataset = f[dataset_name]
            shape3d = dataset.shape
            assert(len(shape3d) == 3), 'only 3d datasets supported right now'
            dtype = dataset.dtype
        self.inputs["h5fns"].shape = shape3d
        shape = (timesteps,) + shape3d + (1,) 
            
        self.outputs["array5d"]._dtype = dtype
        self.outputs["array5d"]._shape = shape
        # self.outputs["Output"]._axistags = copy.copy(inputSlot.axistags)

    def execute(self, slot, roi, result):
        fns = self.inputs["h5fns"].value
        assert key[-1] == slice(0,1,None)
        temporal = key[0]
        dataset_name = self.inputs["dataset"].value
        start = temporal.start if temporal.start else 0
        stop = temporal.stop if temporal.stop else len(fns)
        step = temporal.step if temporal.step else 1
        assert(step == 1)
        for file_idx in xrange(start, stop):
            h5fn = self.inputs["h5fns"].value[file_idx]
            with h5py.File(h5fn, 'r') as f:
                assert(f[dataset_name].shape == self.inputs['h5fns'].shape)
                result[file_idx - start,...,0] = f[dataset_name][key[1:-1]]



if __name__=='__main__':
    parser = argparse.ArgumentParser(description='View large volumetric images.')
    parser.add_argument('-d', '--dataset', default='raw/volume', help='[default: %(default)s]')
    parser.add_argument('h5file', nargs='+')
    args = parser.parse_args()

    h5fn = args.h5file[0]
    dataset_name = args.dataset
    h5f = h5py.File(h5fn, 'r')
    dataset = h5f[dataset_name]
    print dataset.shape
    assert(len(dataset.shape) == 3), "only 3d datasets supported so far"

    ###
    ### setup a lazyflow
    ###
    graph = Graph()

    stack_reader = OpH5StackReader5d(graph)

    stack_reader.inputs["h5fns"].setValue( args.h5file )
    stack_reader.inputs["dataset"].setValue( args.dataset )

    array = OpArrayPiper(graph)
    array.inputs["Input"].setValue(dataset)
    #print "shape", array.inputs["Input"].shape

    fiver = vol.Op5ifyer(graph)
    fiver.inputs['Input'].connect(array.outputs["Output"])

    cache = OpBlockedArrayCache(graph)
    cache.inputs['outerBlockShape'].setValue((1,128,128,128,1))
    cache.inputs['innerBlockShape'].setValue((1,64,64,64,1))
    cache.inputs['fixAtCurrent'].setValue(False)
    cache.inputs["Input"].connect(stack_reader.outputs['array5d'])


    qapp = QApplication([])
    viewer = vol.Viewer()
    viewer.title = "Infinity Viewer"

    #viewer.addLayer(stack_reader.outputs['array5d'], name=path.basename(h5fn[0]))
    #print cache.outputs['Output'].shape
    viewer.addLayer(cache.outputs['Output'], name=path.basename(h5fn[0]))

    viewer.showMaximized()
    qapp.exec_()
    h5f.close()
