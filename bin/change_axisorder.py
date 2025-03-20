#!/usr/bin/env python3
"""
HDF5 Axis Order Modifier for ILASTIK Projects

This script modifies the axis order in ILASTIK Project (.ilp) files.
ILASTIK is an interactive learning and segmentation toolkit, and its
project files use HDF5 format to store configuration and data.

The script changes the axis order of a dataset and removes any existing
classifier to force retraining with the new axis configuration.

Usage:
    python modify_axis_order.py project_file.ilp new_axisorder

Example:
    python modify_axis_order.py segmentation.ilp "txyzc"
"""

from __future__ import print_function
import sys
import h5py


def modify_axis_order(projectfile, axisorder):
    """
    Modify the axis order in an ILASTIK project file.
    
    Args:
        projectfile (str): Path to the ILASTIK project file (.ilp)
        axisorder (str): New axis order string (e.g., "txyzc")
        
    Returns:
        bool: True if modification was successful
    """
    try:
        with h5py.File(projectfile, "r+") as f:
            # Paths to important elements in the HDF5 structure
            raw_data_path = "Input Data/infos/lane0000/Raw Data"
            classifier_path = "PixelClassification/ClassifierForests"
            
            # Delete the old axisorder and replace it with our new one
            try:
                del f[f"{raw_data_path}/axisorder"]
                print(f"Removed existing axis order")
            except KeyError:
                print(f"No existing axis order found")
                pass
            
            # Set the new axis order
            f[f"{raw_data_path}/axisorder"] = axisorder
            print(f"Set new axis order to: {axisorder}")
            
            # If 'axistags' field is present, it overrides axisorder.
            # Delete it to ensure our axisorder is used.
            try:
                del f[f"{raw_data_path}/axistags"]
                print(f"Removed axistags which would override axisorder")
            except KeyError:
                print(f"No axistags found")
                pass
            
            # Delete any existing classifier to force retraining with new axis configuration
            try:
                del f[classifier_path]
                print(f"Removed existing classifier (retraining will be required)")
            except KeyError:
                print(f"No existing classifier found")
                pass
        
        return True
        
    except Exception as e:
        sys.stderr.write(f"Error modifying project file: {str(e)}\n")
        return False


if __name__ == "__main__":
    # Check if correct number of arguments were provided
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: {} project_file.ilp axisorder\n".format(sys.argv[0]))
        sys.stderr.write("Example: {} segmentation.ilp txyzc\n".format(sys.argv[0]))
        sys.exit(1)
    
    # Parse command line arguments
    projectfile = sys.argv[1]
    axisorder = sys.argv[2]
    
    # Validate inputs (basic validation)
    if not projectfile.endswith('.ilp'):
        sys.stderr.write("Warning: Project filename doesn't end with .ilp extension\n")
    
    if not all(c in 'txyzc' for c in axisorder):
        sys.stderr.write("Warning: Axis order typically uses only t,x,y,z,c characters\n")
    
    # Execute the modification function
    success = modify_axis_order(projectfile, axisorder)
    
    if success:
        print("Done. Project file successfully modified.")
    else:
        sys.stderr.write("Failed to modify project file.\n")
        sys.exit(1)
