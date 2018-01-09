###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
"""
Give the histogram of labels in a project file.
"""
from __future__ import print_function
from builtins import range
import sys
import os
import h5py
import numpy

if len(sys.argv) != 2 or not sys.argv[1].endswith(".ilp"):
    sys.stderr.write("Usage: {} <my_project.ilp>\n".format( sys.argv[0] ))
    sys.exit(1)

project_path = sys.argv[1]
if not os.path.exists(project_path):
    sys.stderr.write("Couldn't locate project file: {}\n".format( project_path ))
    sys.exit(2)
else:
    print("Counting labels in project: {}\n".format( project_path ))

def print_bincounts(label_names, bins_list, image_name):
    # Sum up the bincounts we got from each label block
    sum_bins = numpy.array( [0]*( len(label_names)+1 ), dtype=numpy.uint32)
    for bins in bins_list:
        zero_pad_bins = numpy.append( bins, [0]*(len(sum_bins)-len(bins)) )
        sum_bins += zero_pad_bins
    
    print("Counted a total of {} label points for {}.".format( sum_bins.sum(), image_name ))
    max_name_len = max( list(map(len, label_names )) )
    for name, count in zip( label_names, sum_bins[1:] ):
        print(("{:" + str(max_name_len) + "} : {}").format( name, count ))
    print("")

if __name__ == "__main__":
    all_bins = []
    num_bins = 0
    bins_by_image = []
    with h5py.File(project_path, 'r') as f:        
        # For each image
        for image_index, group in enumerate(f['PixelClassification/LabelSets'].values()):
            # For each label block
            this_img_bins = []
            for block in list(group.values()):
                data = block[:]
                nonzero_coords = numpy.nonzero(data)
                bins = numpy.bincount(data[nonzero_coords].flat)
                this_img_bins.append( bins )
                num_bins = max(num_bins, len(bins))
            all_bins += this_img_bins
            bins_by_image.append(this_img_bins)

        # Now print the findings for each image
        try:
            label_names = f['PixelClassification/LabelNames'].value
        except KeyError:
            label_names = [f"Label {n}" for n in range(1, num_bins)]

        for image_index, img_bins in enumerate(bins_by_image):
            print_bincounts( label_names, img_bins, "Image #{}".format( image_index+1 ) )
        
        # Finally, print the total results
        print_bincounts( label_names, all_bins, "ALL IMAGES")


