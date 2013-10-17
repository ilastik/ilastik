import os
import glob
import argparse
import logging
logger = logging.getLogger(__name__)

from lazyflow.utility import PathComponents
from ilastik.applets.base.applet import Applet
from opDataSelection import OpMultiLaneDataSelectionGroup, DatasetInfo
from dataSelectionSerializer import DataSelectionSerializer, Ilastik05DataSelectionDeserializer

class DataSelectionApplet( Applet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    
    DEFAULT_INSTRUCTIONS = "Use the controls shown to the right to add image files to this workflow."
    
    def __init__(self, workflow, title, projectFileGroupName, supportIlastik05Import=False, batchDataGui=False, force5d=False, instructionText=DEFAULT_INSTRUCTIONS, max_lanes=None):
        self.__topLevelOperator = OpMultiLaneDataSelectionGroup(parent=workflow, force5d=force5d)
        super(DataSelectionApplet, self).__init__( title, syncWithImageIndex=False )

        self._serializableItems = [ DataSelectionSerializer(self.topLevelOperator, projectFileGroupName) ]
        if supportIlastik05Import:
            self._serializableItems.append(Ilastik05DataSelectionDeserializer(self.topLevelOperator))

        self._instructionText = instructionText
        self._gui = None
        self._batchDataGui = batchDataGui
        self._title = title
        self._max_lanes = max_lanes
        self.busy = False

    #
    # GUI
    #
    def getMultiLaneGui( self ):
        if self._gui is None:
            from dataSelectionGui import DataSelectionGui, GuiMode
            guiMode = { True: GuiMode.Batch, False: GuiMode.Normal }[self._batchDataGui]
            self._gui = DataSelectionGui( self,
                                          self.topLevelOperator,
                                          self._serializableItems[0],
                                          self._instructionText,
                                          guiMode,
                                          self._max_lanes )
        return self._gui

    #
    # Top-level operator
    #
    @property
    def topLevelOperator(self):
        return self.__topLevelOperator 

    #
    # Project serialization
    #
    @property
    def dataSerializers(self):
        return self._serializableItems


    def parse_known_cmdline_args(self, cmdline_args):
        """
        Helper function for headless workflows.
        Parses command-line args that can be used to configure the ``DataSelectionApplet`` top-level operator 
        and returns ``(parsed_args, unused_args)``, similar to ``argparse.ArgumentParser.parse_known_args()``
        
        Relative paths are converted to absolute paths **according to ``os.getcwd()``**, 
        not according to the project file location, since this more likely to be what headless users expect.
        
        .. note: Currently, this command-line interface only supports workflows with a SINGLE dataset role.
                 Workflows that take multiple files per lane will need to configure the data selection applet 
                 by some other means.  :py:meth:`DatasetInfo.updateFromJson()` might be useful in that case.
        
        See also: :py:meth:`configure_operator_with_parsed_args()`.
        """
        # Currently, we don't support any special options -- just a list of files        
        arg_parser = argparse.ArgumentParser()
        arg_parser.add_argument('input_files', nargs='*', help='List of input files to process.')
        parsed_args, unused_args = arg_parser.parse_known_args(cmdline_args)
        
        # Check for errors: Do all input files exist?
        input_paths = parsed_args.input_files
        error = False
        for p in input_paths:
            p = PathComponents(p).externalPath
            if '*' in p:
                if len(glob.glob(p)) == 0:
                    logger.error("Could not find any files for globstring: {}".format(p))
                    logger.error("Check your quotes!")
                    error = True
            elif not os.path.exists(p):
                logger.error("Input file does not exist: " + p)
                error = True
        if error:
            raise RuntimeError("Could not find one or more input files.  See logged errors.")

        return parsed_args, unused_args

    def configure_operator_with_parsed_args(self, parsed_args):
        """
        Helper function for headless workflows.
        Configures this applet's top-level operator according to the settings provided in ``parsed_args``.
        
        :param parsed_args: Must be an ``argparse.Namespace`` as returned by :py:meth:`parse_known_cmdline_args()`.
        """
        # TODO: Support image stack inputs by checking for globstrings and converting to hdf5.
        input_paths = parsed_args.input_files
        input_infos = []
        for p in input_paths:
            info = DatasetInfo()
            info.location = DatasetInfo.Location.FileSystem
    
            # Convert all paths to absolute 
            # (otherwise they are relative to the project file, which probably isn't what the user meant)        
            comp = PathComponents(p)
            comp.externalPath = os.path.abspath(comp.externalPath)
            
            info.filePath = comp.totalPath()
            info.nickname = comp.filenameBase
            input_infos.append(info)

        opDataSelection = self.topLevelOperator
        opDataSelection.DatasetGroup.resize( len(input_infos) )
        for lane_index, info in enumerate(input_infos):
            # Only one dataset role in pixel classification
            opDataSelection.DatasetGroup[lane_index][0].setValue( info )
        
        
        
