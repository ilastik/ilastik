**ilastik-based splitting tool for FlyEM proofreading**
=============================================

This tool was developed to split false merges in FlyEM volumes.  
It is a modified version of the standard ilastik Carving workflow, 
with some features added and some intentionally removed.

Data Selection
--------------

The tool requires 3 input files:

- Raw grayscale data (typically imported as a volume from a stack of .png images).
- Pixel Probability maps (generated during the gala segmentation pipeline, which uses the ilastik pixel classifier)
 * The first channel must be the membrane probabilities.
- Label volume .h5 file, referred to here as the "Raveler Labels"

![Raw Data](http://stuarteberg.github.io/images/split-tool/data_selection_raw.png)
![Pixel Probabilities](http://stuarteberg.github.io/images/split-tool/data_selection_pixel_probabilities.png)
![Raveler Labels](http://stuarteberg.github.io/images/split-tool/data_selection_raveler_labels.png)

Note: Label volumes in the gala/Raveler pipeline are usually stored in z-y-x order.  
After selecting your data, ensure it is oriented correctly in the viewer by changing 
the axis ordering in the dataset properties editor window.

![Raveler Labels Axisorder](http://stuarteberg.github.io/images/split-tool/data_selection_raveler_labels_axisorder.png)

Preprocessing
-------------

The split tool workflow uses the same preprocessing tab as the standard Carving workflow.
The workflow uses the pixel probabilities (channel 0) as the input to carving.
(The Raw data layer is not used by the algorithm. It is provided for display only.)

For best results, choose "original image" with a sigma of 1.0.  The default "WS Input" setting (Filter Output) is fine.

![Preprocessing](http://stuarteberg.github.io/images/split-tool/preprocessing.png)


Labeling
--------

The "Labeling" tab is main UI of the split tool.  It is a modified version of the standard ilastik Carving tool.
To get started, click the "Annotations" button to open the Annotations window.
Then click the "Load Split Annotation File" button to load your Raveler bookmarks, 
which is usually named bookmarks-annotations.json

![Annotations Window](http://stuarteberg.github.io/images/split-tool/annotations_window_1.png)

As you can see, the split annotations from your Raveler bookmarks file are shown on the right-hand side of the window.
Each body that appears in your bookmarks list also appears on the left-hand side of the window, along with a progress 
bar indicating how many fragments you are likely to produce once you have finished splitting the body.  For example, 
a body with two split annotations on it is likely to need splitting into three fragments.

The next step is to select a raveler body to split.  Double click on one of the annotations.  
The viewer will auto-navigate to the bookmark coordinates, and the original body will be highlighed in red.
The bookmark coordinates will be indicated by a light-colored crosshair icon.

![Navigate to Bookmark](http://stuarteberg.github.io/images/split-tool/navigate_to_bookmark.png)

In this example, it looks like a mitochondria was incorrectly included in a neighboring neuron.
We need to split it away from the neuron.

In the split tool, you must create a "fragment" before you can edit anything.
Now that we've chosen a body to work with, a "New Fragment" button appeared in the annotations window.  
Click it.

![New Fragment Button](http://stuarteberg.github.io/images/split-tool/annotations_window_2.png)

The brushing controls are now enabled.  Use them to segment your fragment of interest.  
Hit the "Update Split" button (shortcut: '3') to see the results of each brushstroke on your fragment.
In the 3D view, your editing fragment is shown in green.
To toggle quickly between the raw data view and the segmentation, hit the 'F' key.

![Initial Brushstrokes](http://stuarteberg.github.io/images/split-tool/initial_brushstrokes.png)

When you have finished refining your fragment segmentation, save it by clicking the "Save" button.

![Annotations Window](http://stuarteberg.github.io/images/split-tool/annotations_window_3.png)

Your saved fragment now appears in a different color.  
If you notice that your fragment still needs refinement, click the "Edit" button in the annotation window. 

![First Fragment](http://stuarteberg.github.io/images/split-tool/first_fragment_complete.png)

Before you can move on to the next body, you must create another fragment out of the 
remaining red pixels from the original body.  Use the same procedure: 
Click "New Fragment", make some brush strokes, and save it.

![Editing Second Fragment](http://stuarteberg.github.io/images/split-tool/edit_second_fragment.png)

You may notice some small "speckles" of incorrect segmentation on fragment edges.  That's okay.  
They will be removed during post-processing, once you have finished splitting all bodies in the volume.

![Speckles](http://stuarteberg.github.io/images/split-tool/speckles.png)

You are free to split a body into as many fragments as you wish.  The "progress" indicator is only shown as a guidline.

![Progress Complete](http://stuarteberg.github.io/images/split-tool/progress_complete.png)

When you are ready to move on to a different body, simply double-click a different bookmark in the list.

Post-processing
--------------

Once you have split all necessary bodies, navigate to the "Split-body post-processing" tab.  
Hit the "Export Final Segmentation" button, and select an output file name.  The post-processing algorithm may take a 
few minutes, depending on how many bodies you had to split.

Once the post-processing is complete, the final results are shown in the "Final Segmentation" layer.  
Other layers are also available, but mostly for debugging purposes.

If you still have the Annotation window open, double-click on a bookmark to navigate to those 
coordinates in the post-processing viewer.

![Post-processing Results](http://stuarteberg.github.io/images/split-tool/postprocessing_results.png)

Command-line Interface
----------------------

Since preprocessing a raveler volume is time-consuming and does not require user interaction, it may be convenient create 
a new pre-processed ilastik project automatically using the command-line interface.  All input files and settings 
are specified in a json file.  Developers: See the json schema description in splitBodyCarvingWorkflow.py 
for details.

    ./ilastik.py --headless --new_project=my_split_project.ilp --workflow=SplitBodyCarvingWorkflow --split_tool_param_file=my_split_params.json


Here's an example split tool parameter file:

```
{
    "_schema_name" : "split-body workflow params",
    "_schema_version" : 0.1,
    
    "raw_data_info" :
    {
        "_schema_name" : "dataset-info",
        "_schema_version" : 0.1,
        
        "filepath" : "/groups/flyem/data/medulla-FIB-Z1211-25-production/align2/substacks/00076_4508-5007_3259-3758_2000-2499/grayscale_maps/*.png",
        "nickname" : "raw"
    },
    "pixel_probabilities_info" :
    {
        "_schema_name" : "dataset-info",
        "_schema_version" : 0.1,
        
        "filepath" : "STACKED_prediction.h5/volume/predictions",
        "drange" : [0.0, 1.0],
        "nickname" : "predictions"
    },
    "raveler_labels_info" :
    {
        "_schema_name" : "dataset-info",
        "_schema_version" : 0.1,
        
        "filepath" : "seg-0.0-21d65a67f14d2c3be1c7495a8542aec4-v4.h5/stack",
        "nickname" : "raveler_labels",
        "axistags" : "zyx"
    },    
    "raveler_bookmarks_file" : "/groups/flyem/data/medulla-FIB-Z1211-25-production/align2/substacks/00076_4508-5007_3259-3758_2000-2499/focused-980-exports/annotations-bookmarks.json"
}
```




