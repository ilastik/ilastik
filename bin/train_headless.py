"""
Create a new project from scratch using a grayscale volume and label volume of the same shape.

At this time, this script does not provide a command-line API for selecting the features to train with.
Edit the feature matrix in the code below.

Also, this script's cmdline API supports only a single grayscale and label volume as input, 
so just write your own API that calls generate_trained_project_file() if you need more than that.

Note that this example makes no attempt to be careful with RAM usage. In particular, it loads each
label image in its entirety before pushing its data into the training pipeline.  This could be fixed,
but would obfuscate this example somewhat.

Example usage:
    # With 2D PNG input.
    # Label images must have pixel value 0 for non-labeled pixels, and values of 1,2,3, etc. for each label class.
    # Label images should *not* be RGB.
    ./ilastik-1.1.7-Linux/bin/python train_headless.py MyNewProject.ilp /tmp/cell-slide.png cell-labels.png

    # With HDF5 input:
    ./ilastik-1.1.7-Linux/bin/python train_headless.py MyNewProject.ilp "/tmp/grayscale_vol.h5/mydataset" /tmp/labels.h5/data

    # With 3D tiff input.
    ./ilastik-1.1.7-Linux/bin/python train_headless.py MyNewProject.ilp "/tmp/grayscale_sequence/*.tiff" "/tmp/label_img_sequence/*.tiff"

Note for Mac users: Use ./ilastik-1.1.7-OSX.app/Contents/ilastik-release/bin/python

Note: This script does not make any attempt to be efficient with RAM usage.
      (The entire label volume is loaded at once.)  As a result, each image volume you 
      train with must be significantly smaller than the available RAM on your machine.
"""
import os

def main():
    # Cmd-line args to this script.
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("new_project_name")
    parser.add_argument("raw_data")
    parser.add_argument("label_data")    
    parsed_args = parser.parse_args()

    # FIXME: This function returns hard-coded features for now.
    feature_selections = prepare_feature_selections()
    
    # Optional: Customize classifier settings
    classifier_factory = None
    #from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory
    #classifier_factory = ParallelVigraRfLazyflowClassifierFactory(100)
    
    # sklearn classifier:
    #from lazyflow.classifiers import SklearnLazyflowClassifier
    #classifier_factory = SklearnLazyflowClassifierFactory( AdaBoostClassifier, n_estimators=50 )

    generate_trained_project_file( parsed_args.new_project_name,
                                   [parsed_args.raw_data],
                                   [parsed_args.label_data],
                                   feature_selections,
                                   classifier_factory )
    print "DONE."

# Don't touch these constants!
ScalesList = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
FeatureIds = [ 'GaussianSmoothing',
               'LaplacianOfGaussian',
               'GaussianGradientMagnitude',
               'DifferenceOfGaussians',
               'StructureTensorEigenvalues',
               'HessianOfGaussianEigenvalues' ]

def prepare_feature_selections():
    """
    Returns a matrix of hard-coded feature selections.
    To change the features, edit the lines below.
    """
    import numpy

    # #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
    # selections = numpy.array( [[False, False, False, False, False, False, False],
    #                            [False, False, False, False, False, False, False],
    #                            [False, False, False, False, False, False, False],
    #                            [False, False, False, False, False, False, False],
    #                            [False, False, False, False, False, False, False],
    #                            [False, False, False, False, False, False, False]] )
    
    # Start with an all-False matrix and apply the features we want.
    selections = numpy.zeros( (len(FeatureIds), len(ScalesList)), dtype=bool )
    def set_feature(feature_id, scale):
        selections[ FeatureIds.index(feature_id), ScalesList.index(scale) ] = True
    
    set_feature('GaussianSmoothing',         0.3)
    set_feature('GaussianSmoothing',         1.0)
    set_feature('GaussianGradientMagnitude', 1.0)

    return selections

def generate_trained_project_file( new_project_path,
                                   raw_data_paths,
                                   label_data_paths,
                                   feature_selections,
                                   classifier_factory=None ):
    """
    Create a new project file from scratch, add the given raw data files,
    inject the corresponding labels, configure the given feature selections,
    and (if provided) override the classifier type ('factory').
    
    Finally, request the classifier object from the pipeline (which forces training),
    and save the project.
    
    new_project_path: Where to save the new project file
    raw_data_paths: A list of paths to the raw data images to train with
    label_data_paths: A list of paths to the label image data to train with
    feature_selections: A matrix of bool, representing the selected features
    classifier_factory: Override the classifier type.  Must be a subclass of either:
                        - lazyflow.classifiers.LazyflowVectorwiseClassifierFactoryABC
                        - lazyflow.classifiers.LazyflowPixelwiseClassifierFactoryABC
    """
    assert len(raw_data_paths) == len(label_data_paths), \
        "Number of label images must match number of raw images."
    
    import ilastik_main
    from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
    from lazyflow.graph import Graph
    from lazyflow.operators.ioOperators import OpInputDataReader
    from lazyflow.roi import roiToSlice, roiFromShape
    
    ##
    ## CREATE PROJECT
    ##
    
    # Manually configure the arguments to ilastik, as if they were parsed from the command line.
    # (Start with empty args and fill in below.)
    ilastik_args = ilastik_main.parser.parse_args([])
    ilastik_args.new_project = new_project_path
    ilastik_args.headless = True
    ilastik_args.workflow = 'Pixel Classification'
    
    shell = ilastik_main.main( ilastik_args )
    assert isinstance(shell.workflow, PixelClassificationWorkflow)
    
    ##
    ## CONFIGURE GRAYSCALE INPUT
    ##
    
    data_selection_applet = shell.workflow.dataSelectionApplet
    
    # To configure data selection, start with empty cmdline args and manually fill them in
    data_selection_args, _ = data_selection_applet.parse_known_cmdline_args([], PixelClassificationWorkflow.ROLE_NAMES)
    data_selection_args.raw_data = raw_data_paths
    data_selection_args.preconvert_stacks = True
    
    # Simplest thing here is to configure using cmd-line interface
    data_selection_applet.configure_operator_with_parsed_args(data_selection_args)
    
    ##
    ## APPLY FEATURE MATRIX (from matrix above)
    ##
    
    opFeatures = shell.workflow.featureSelectionApplet.topLevelOperator
    opFeatures.Scales.setValue( ScalesList )
    opFeatures.FeatureIds.setValue( FeatureIds )
    opFeatures.SelectionMatrix.setValue(feature_selections)
    
    ##
    ## CUSTOMIZE CLASSIFIER TYPE
    ##

    opPixelClassification = shell.workflow.pcApplet.topLevelOperator
    if classifier_factory is not None:
        opPixelClassification.ClassifierFactory.setValue( classifier_factory )
    
    ##
    ## READ/APPLY LABEL VOLUMES
    ##
    
    # Read each label volume and inject the label data into the appropriate training slot
    cwd = os.getcwd()
    max_label_class = 0
    for lane, label_data_path in enumerate(label_data_paths):
        graph = Graph()
        opReader = OpInputDataReader(graph=graph)
        try:
            opReader.WorkingDirectory.setValue( cwd )
            opReader.FilePath.setValue( label_data_path )
            
            print "Reading label volume: {}".format( label_data_path )
            label_volume = opReader.Output[:].wait()
        finally:
            opReader.cleanUp()

        raw_shape = opPixelClassification.InputImages[lane].meta.shape
        if label_volume.ndim != len(raw_shape):
            # Append a singleton channel axis
            assert label_volume.ndim == len(raw_shape)-1
            label_volume = label_volume[...,None]

        # Auto-calculate the max label value
        max_label_class = max(max_label_class, label_volume.max())
            
        print "Applying label volume to lane #{}".format(lane)
        entire_volume_slicing = roiToSlice(*roiFromShape(label_volume.shape))
        opPixelClassification.LabelInputs[lane][entire_volume_slicing] = label_volume

    assert max_label_class > 1, "Not enough label classes were found in your label data."
    label_names = map(str, range(max_label_class))
    opPixelClassification.LabelNames.setValue(label_names)
    
    ##
    ## TRAIN CLASSIFIER
    ##

    # Make sure the caches in the pipeline are not 'frozen'.
    # (This is the equivalent of 'live update' mode in the GUI.)
    opPixelClassification.FreezePredictions.setValue(False)

    # Request the classifier object from the pipeline.
    # This forces the pipeline to produce (train) the classifier.
    _ = opPixelClassification.Classifier.value
    
    ##
    ## SAVE PROJECT
    ##
    
    # save project file (includes the new classifier).
    shell.projectManager.saveProject(force_all_save=False)

if __name__ == "__main__":
    main()