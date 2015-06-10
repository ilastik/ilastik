import os
import copy
import h5py
from lazyflow.utility import PathComponents
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpInputDataReader, OpFormattedDataExport

from ilastik.applets.pixelClassification.opPixelClassification import OpArgmaxChannel
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet

def convert_predictions_to_segmentation( input_paths, parsed_export_args ):
    """
    Read exported pixel predictions and calculate/export the segmentation.
    
    input_path: The path to the prediction output file. If hdf5, must include the internal dataset name.
    parsed_export_args: The already-parsed cmd-line arguments generated from a DataExportApplet-compatible ArgumentParser.
    """
    graph = Graph()
    opReader = OpInputDataReader(graph=graph)
    opReader.WorkingDirectory.setValue( os.getcwd() )

    opArgmaxChannel = OpArgmaxChannel( graph=graph )
    opArgmaxChannel.Input.connect( opReader.Output )
        
    opExport = OpFormattedDataExport( graph=graph )
    opExport.Input.connect( opArgmaxChannel.Output )

    # Apply command-line arguments.
    DataExportApplet._configure_operator_with_parsed_args(parsed_export_args, opExport)

    last_progress = [-1]
    def print_progress(progress_percent):
        if progress_percent != last_progress[0]:
            last_progress[0] = progress_percent
            sys.stdout.write( " {}".format(progress_percent) )
    opExport.progressSignal.subscribe(print_progress)

    for input_path in input_paths: 
        opReader.FilePath.setValue(input_path)

        input_pathcomp = PathComponents(input_path)
        opExport.OutputFilenameFormat.setValue(str(input_pathcomp.externalPath))

        output_path = opExport.ExportPath.value
        output_pathcomp = PathComponents( output_path )
        output_pathcomp.filenameBase += "_Segmentation"
        opExport.OutputFilenameFormat.setValue(str(output_pathcomp.externalPath))
        
        print "Exporting results to : {}".format( opExport.ExportPath.value )    
        sys.stdout.write("Progress:")
        # Begin export
        opExport.run_export()
        sys.stdout.write("\n")
    print "DONE."
    
def all_dataset_internal_paths(f):
    """
    Return a list of all the internal datasets in an hdf5 file.
    """
    allkeys = []
    f.visit(allkeys.append)
    dataset_keys = filter(lambda key: isinstance(f[key], h5py.Dataset), 
                          allkeys)
    return dataset_keys

if __name__ == "__main__":
    import sys
    import argparse
    #sys.argv += "/tmp/example_slice.h5/data /tmp/example_slice2.h5/data --export_drange=(0,255) --output_format=png --pipeline_result_drange=(1,2)".split()
    
    # Construct a parser with all the 'normal' export options, and add arg for prediction_image_paths.
    parser = DataExportApplet.make_cmdline_parser( argparse.ArgumentParser() )
    parser.add_argument("prediction_image_paths", nargs='+', help="Path(s) to your exported predictions.")
    parsed_args = parser.parse_args()
    parsed_args, unused_args = DataExportApplet.parse_known_cmdline_args( sys.argv[1:], parsed_args )
    
    # As a convenience, auto-determine the internal dataset path if possible.
    for index, input_path in enumerate(parsed_args.prediction_image_paths):
        path_comp = PathComponents(input_path, os.getcwd())        
        if not parsed_args.output_internal_path:
            parsed_args.output_internal_path = "segmentation"
        if path_comp.extension in PathComponents.HDF5_EXTS and path_comp.internalDatasetName == "":            
            with h5py.File(path_comp.externalPath, 'r') as f:
                all_internal_paths = all_dataset_internal_paths(f)
    
            if len(all_internal_paths) == 1:
                path_comp.internalPath = all_internal_paths[0]
                parsed_args.prediction_image_paths[index] = path_comp.totalPath()
            elif len(all_internal_paths) == 0:
                sys.stderr.write("Could not find any datasets in your input file:\n"
                                 "{}\n".format(input_path))
                sys.exit(1)
            else:
                sys.stderr.write("Found more than one dataset in your input file:\n"
                                 "{}\n".format(input_path) +
                                 "Please specify the dataset name, e.g. /path/to/myfile.h5/internal/dataset_name\n")
                sys.exit(1)

    sys.exit( convert_predictions_to_segmentation( parsed_args.prediction_image_paths, 
                                                   parsed_args ) )
