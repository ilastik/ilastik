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
#                  http://ilastik.org/license.html
###############################################################################

import vigra
import h5py
import numpy
import sys
import time
import os
from threading import Thread

from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory
from lazyflow.classifiers import ParallelVigraRfLazyflowClassifier

from lazyflow.request import Request
     
def difference_of_gaussians(data, scale):
    return ( vigra.filters.gaussianSmoothing(data, scale) -
             vigra.filters.gaussianSmoothing(data, scale*0.66) )
  
def gaussian_gradient_magnitude(data, scale):
    return vigra.filters.gaussianGradientMagnitude(data, scale)
  
def structure_tensor_eigenvalues(data, scale):
    return vigra.filters.structureTensorEigenvalues(data, scale, 0.5*scale)
    
filter_funcs = { "Gaussian Smoothing" : vigra.filters.gaussianSmoothing,
                 "Gaussian Gradient Magnitude" : gaussian_gradient_magnitude, #vigra.filters.gaussianGradientMagnitude,
                 "Laplacian of Gaussian" : vigra.filters.laplacianOfGaussian,
                 "Hessian of Gaussian EVs" :  vigra.filters.hessianOfGaussianEigenvalues,
                 "Difference of Gaussians" : difference_of_gaussians,
                 "Structure Tensor EVs" : structure_tensor_eigenvalues }

class Timer(object):
    def __init__(self):
        self.start_time = None
        self.stop_time = None
        self.elapsed_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        self.stop_time = time.time()
        self.elapsed_time = self.stop_time - self.start_time 

def compute_features(data, sigma, filter_name, stacked_feature_images, t, current_channel, filter_channels):        
    features = filter_funcs[filter_name](data, sigma)
    stacked_feature_images[t,:,:, current_channel:current_channel+filter_channels] = features

# This code is used to isolate feature calculation and prediction in order to profile the running time speratelly and identify any unexpected sources of time consumption
def main(project_file_path, input_file_path, thread_num):
    
    # Set number of threads for feature calculation and prediction
    if thread_num > 0 :
        Request.reset_thread_pool(thread_num)
        print "Threads enabled\n"
    else:
        Request.reset_thread_pool(0)
        print "Threads disabled\n"
       
    total_time = 0.0
    filter_time = 0.0
 
    # Load RF classification parameters from project file
    #projectFile = h5py.File("/opt/local/cx_JRC_SS03500_Pixel_Classification_2_classes.ilp", "r")
    projectFile = h5py.File(project_file_path, "r")
    
    classifierForests = projectFile['/PixelClassification/ClassifierForests']
    classifier = ParallelVigraRfLazyflowClassifier.deserialize_hdf5(classifierForests) 
 
    projectFile.close()
    
    # Define features (filters)
    filter_specs = [ ("Gaussian Smoothing", 0.3, 1),
                    ("Gaussian Smoothing", 0.7, 1),
                    ("Gaussian Smoothing", 1.0, 1),
                    ("Gaussian Smoothing", 1.6, 1),
                    ("Laplacian of Gaussian", 0.7, 1),
                    ("Laplacian of Gaussian", 5.0, 1),
                    ("Gaussian Gradient Magnitude", 1.0, 1),
                    ("Structure Tensor EVs", 5.0, 2), 
                    ("Structure Tensor EVs", 10.0, 2),                    
                    ("Hessian of Gaussian EVs", 3.5, 2),
                    ("Hessian of Gaussian EVs", 5.0, 2),
                    ("Hessian of Gaussian EVs", 10.0, 2) ]  
    
    with h5py.File(input_file_path, 'r') as f:
        dset = f.values()[0]
        print "Reading from {}/{}".format( input_file_path, dset.name )
        with Timer() as t:
            data = dset[:].astype(numpy.float32)
            if 'axistags' in dset.attrs:
                tags = vigra.AxisTags.fromJSON(dset.attrs['axistags'])
                data = vigra.taggedView(data, tags)
                assert [tag.key for tag in tags] == list('txyc')
        print "Reading Data took: {} seconds".format( t.elapsed_time )
        total_time += t.elapsed_time;
        
    total_channels = sum( [spec[2] for spec in filter_specs] )
    stacked_feature_images = numpy.zeros( data.shape[:-1] + (total_channels,), dtype=numpy.float32 )
    
    threads = [None] * thread_num 
    
    current_channel = 0
    
    # Calculate features
    for filter_name, sigma, filter_channels in filter_specs:
        with Timer() as timer:

            if thread_num > 0 :
                for t in xrange(0, data.shape[0], thread_num):
                    for i in range(thread_num):
                        if t + i < data.shape[0] :
                            threads[i] = Thread(target=compute_features, args=(data[t+i], sigma, filter_name, stacked_feature_images, t+i, current_channel, filter_channels))
                            threads[i].start()
                    
                    for i in range(thread_num):
                        if t + i < data.shape[0] :
                            threads[i].join()
                           
            else : 
                for t in range(data.shape[0]):
                    features = filter_funcs[filter_name](data[t], sigma)
                    stacked_feature_images[t,:,:, current_channel:current_channel+filter_channels] = features
            
        current_channel += filter_channels
        print "{} (s={}) took: {} ({} secs/vox el)"\
              .format( filter_name, 
                       sigma, 
                       timer.elapsed_time, 
                       timer.elapsed_time/numpy.prod(data.shape) )
              
        total_time += timer.elapsed_time
        filter_time += timer.elapsed_time
                   
    print "Filter time: ", filter_time

    output_file_path = os.path.split(input_file_path)[0] + '/features.h5'
    with h5py.File( output_file_path, 'w' ) as output_file:
        output_file.create_dataset('data', data=stacked_feature_images, chunks=True)

    feature_matrix = stacked_feature_images[:]
    feature_matrix.shape = (numpy.prod(stacked_feature_images.shape[:-1]), stacked_feature_images.shape[-1])
    #print "feature_matrix.strides =", feature_matrix.strides

    # RF predict        
    with Timer() as timer:
        prediction_matrix = classifier.predict_probabilities(feature_matrix)

    print "Predicting time: ",  timer.elapsed_time
    total_time += timer.elapsed_time
                
    print "Total elapsed time: ", total_time    

    prediction_vol_shape = (stacked_feature_images.shape[:-1] + (prediction_matrix.shape[-1],))
    prediction_volume = prediction_matrix.reshape( prediction_vol_shape )

    # Save predictions to output HDF5 file
    output_file_path = os.path.split(input_file_path)[0] + '/output.h5'
    with h5py.File( output_file_path, 'w' ) as output_file:
        output_file.create_dataset('predictions', data=prediction_volume, chunks=True)
                  
    print "DONE."

if __name__ == "__main__":
    
    if len(sys.argv) < 3:
        print "Usage: {} <project-file> <data-file> <thread-number>".format( sys.argv[0] )
        sys.exit(1)

    sys.exit( main(sys.argv[1], sys.argv[2], int(sys.argv[3]) ) )
