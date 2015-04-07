import os
import copy
import h5py
from lazyflow.utility import PathComponents
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpInputDataReader, OpFormattedDataExport

from ilastik.applets.pixelClassification.opPixelClassification import OpEnsembleMargin
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet

def convert_predictions_to_uncertainties( input_path, parsed_export_args ):
    """
    Read exported pixel predictions and calculate/export the uncertainties.
    
    input_path: The path to the prediction output file. If hdf5, must include the internal dataset name.
    parsed_export_args: The already-parsed cmd-line arguments generated from a DataExportApplet-compatible ArgumentParser.
    """
    graph = Graph()
    opReader = OpInputDataReader(graph=graph)
    opReader.WorkingDirectory.setValue( os.getcwd() )
    opReader.FilePath.setValue(input_path)
    
    opUncertainty = OpEnsembleMargin( graph=graph )
    opUncertainty.Input.connect( opReader.Output )
        
    opExport = OpFormattedDataExport( graph=graph )
    opExport.Input.connect( opUncertainty.Output )

    # Apply command-line arguments.
    DataExportApplet._configure_operator_with_parsed_args(parsed_export_args, opExport)

    last_progress = [-1]
    def print_progress(progress_percent):
        if progress_percent != last_progress[0]:
            last_progress[0] = progress_percent
            sys.stdout.write( " {}".format(progress_percent) )
    
    print "Exporting results to : {}".format( opExport.ExportPath.value )    
    sys.stdout.write("Progress:")
    opExport.progressSignal.subscribe(print_progress)

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
    
    # Construct a parser with all the 'normal' export options, and add arg for input_path.
    parser = DataExportApplet.make_cmdline_parser( argparse.ArgumentParser() )
    parser.add_argument("input_path", help="Path to your exported predictions.")
    parsed_args = parser.parse_args()    
    
    # As a convenience, auto-determine the internal dataset path if possible.
    path_comp = PathComponents(parsed_args.input_path, os.getcwd())
    if path_comp.extension in PathComponents.HDF5_EXTS and path_comp.internalDatasetName == "":
        
        with h5py.File(path_comp.externalPath, 'r') as f:
            all_internal_paths = all_dataset_internal_paths(f)

        if len(all_internal_paths) == 1:
            path_comp.internalPath = all_internal_paths[0]
            parsed_args.input_path = path_comp.totalPath()
        elif len(all_internal_paths) == 0:
            sys.stderr.write("Could not find any datasets in your input file.")
            sys.exit(1)
        else:
            sys.stderr.write("Found more than one dataset in your input file.\n"
                             "Please specify the dataset name, e.g. /path/to/myfile.h5/internal/dataset_name")
            sys.exit(1)

    # As a convenience, if the user didn't explicitly specify an output file name, provide one for him.
    if not parsed_args.output_filename_format:
        output_path_comp = copy.copy(path_comp)
        output_path_comp.filenameBase += "_Uncertainties"
        parsed_args.output_filename_format = output_path_comp.externalPath
    if path_comp.extension in PathComponents.HDF5_EXTS and not parsed_args.output_internal_path:
        parsed_args.output_internal_path = "uncertainties"        

    sys.exit( convert_predictions_to_uncertainties( parsed_args.input_path, 
                                                    parsed_args ) )
