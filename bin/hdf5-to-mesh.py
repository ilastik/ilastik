"""
hdf5-to-mesh.py

Usage: python hdf5-to-mesh.py [--label=<N>] <input-file.h5>

Exports a mesh for the given hdf5 file, in .obj format, 
which is suitable for input into Blender.
If --label=N is provided, then only the pixels with value N will be converted into the mesh.
Otherwise, all nonzero pixels are used.
"""
from __future__ import print_function
#import os
#import sys
#import argparse
#from functools import partial
#import shutil
#import tempfile

from os.path import splitext
from sys import stderr, exit as sysexit
from argparse import ArgumentParser
from numpy import unique

#import h5py
#from PyQt5.QtCore import QTimer
#from PyQt5.QtWidgets import QApplication

from h5py import File
from volumina.view3d.meshgenerator import labeling_to_mesh, mesh_to_obj


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--label", type=int, required=False)
    parser.add_argument("input_hdf5_file")
    parsed_args = parser.parse_args()

    output_file = os.path.splitext(parsed_args.input_hdf5_file)[0] + ".obj"

    print("Loading volume...")
    with File(parsed_args.input_hdf5_file, 'r') as f_input:
        dataset_names = []
        f_input.visit(dataset_names.append)
        if len(dataset_names) != 1:
            stderr.write("Input HDF5 file should have exactly 1 dataset.\n")
            sysexit(1)
        volume = f_input[dataset_names[0]][:].squeeze()

    if parsed_args.label:
        volume[:] = (volume == parsed_args.label)
        labels = [parsed_args.label]
    else:
        volume[:] = (volume != 0)
        labels = [label for label in unique(volume) if label != 0]

    for label, mesh in labeling_to_mesh(volume, labels):
        mesh_to_obj(mesh, "{}_{}.obj".format(output_file, label), label)

