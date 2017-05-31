"""
Simple little utility to read a Carving project file and print out the object
names and their corresponding label values that would be used if the project
were opened and the "Completed segments" layer were exported.
"""
from __future__ import print_function
import sys
import h5py

if len(sys.argv) < 2 or sys.argv[1][-4:] != ".ilp":
    sys.stderr.write("Usage: {} project-file.ilp\n".format(sys.argv[0]))
    sys.exit(1)

project_path = sys.argv[1]

with h5py.File(project_path, 'r') as project_file:
    for i, name in enumerate(project_file['carving/objects'].keys(), start=1):
        print(i, ":", name)
