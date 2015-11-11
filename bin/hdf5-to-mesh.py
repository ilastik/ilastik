"""
hdf5-to-mesh.py

Usage: python hdf5-to-mesh.py [--label=<N>] <input-file.h5>

Exports a mesh for the given hdf5 file, in .obj format, 
which is suitable for input into Blender.
If --label=N is provided, then only the pixels with value N will be converted into the mesh.
Otherwise, all nonzero pixels are used.
"""
import os
import sys
import argparse
from functools import partial
import shutil
import tempfile

import h5py
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QApplication
from vtk import vtkPolyDataWriter

from volumina.view3d.GenerateModelsFromLabels_thread import MeshExtractorDialog
from volumina.view3d.view3d import convertVTPtoOBJ

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", type=int, required=False)
    parser.add_argument("input_hdf5_file")
    parsed_args = parser.parse_args()

    output_file = os.path.splitext(parsed_args.input_hdf5_file)[0] + ".obj"

    print "Loading volume..."
    with h5py.File(parsed_args.input_hdf5_file, 'r') as f_input:
        dataset_names = []
        f_input.visit(dataset_names.append)
        if len(dataset_names) != 1:
            sys.stderr.write("Input HDF5 file should have exactly 1 dataset.\n")
            sys.exit(1)
        volume = f_input[dataset_names[0]][:].squeeze()

    if parsed_args.label:
        volume[:] = (volume == parsed_args.label)
    else:
        volume[:] = (volume != 0)
    
    app = QApplication([])

    dlg = MeshExtractorDialog()
    dlg.finished.connect( partial(onMeshesComplete, dlg, output_file) )
    dlg.show()
    dlg.raise_()

    QTimer.singleShot(0, partial(dlg.run, volume, [0]))
    app.exec_()
    print "DONE."

def onMeshesComplete(dlg, obj_filepath):
    """
    Called when mesh extraction is complete.
    Writes the extracted mesh to an .obj file
    """
    print "Mesh generation complete."
    mesh_count = len( dlg.extractor.meshes )

    # Mesh count can sometimes be 0 for the '<not saved yet>' object...
    if mesh_count > 0:
        assert mesh_count == 1, \
            "Found {} meshes. (Only expected 1)".format( mesh_count )
        mesh = dlg.extractor.meshes.values()[0]

        # Use VTK to write to a temporary .vtk file
        tmpdir = tempfile.mkdtemp()
        vtkpoly_path = os.path.join(tmpdir, 'meshes.vtk')
        w = vtkPolyDataWriter()
        w.SetFileTypeToASCII()
        w.SetInput(mesh)
        w.SetFileName(vtkpoly_path)
        w.Write()
        
        # Now convert the file to .obj format.
        print "Saving meshes to {}".format( obj_filepath )
        convertVTPtoOBJ(vtkpoly_path, obj_filepath)

        shutil.rmtree( tmpdir )

    # Cleanup: We don't need the window anymore.
    #dlg.setParent(None)


if __name__ == "__main__":
    main()
