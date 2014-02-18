# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

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
        arg_parser.add_argument('--preconvert_stacks', help="Convert image stacks to temporary hdf5 files before loading them.", action='store_true', default=False)
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
        input_paths = parsed_args.input_files

        # If the user doesn't want image stacks to be copied inte the project file,
        #  we generate hdf5 volumes in a temporary directory and use those files instead.        
        if parsed_args.preconvert_stacks:
            import tempfile
            input_paths = self.convertStacksToH5( input_paths, tempfile.gettempdir() )
        
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
        
    @classmethod
    def convertStacksToH5(cls, filePaths, stackVolumeCacheDir):
        """
        If any of the files in filePaths appear to be globstrings for a stack,
        convert the given stack to hdf5 format.
        
        Return the filePaths list with globstrings replaced by the paths to the new hdf5 volumes.
        """
        import hashlib
        import pickle
        import h5py
        from lazyflow.graph import Graph
        from lazyflow.operators.ioOperators import OpStackToH5Writer
        
        filePaths = list(filePaths)
        for i, path in enumerate(filePaths):
            if '*' in path:
                globstring = path
    
                # Embrace paranoia:
                # We want to make sure we never re-use a stale cache file for a new dataset,
                #  even if the dataset is located in the same location as a previous one and has the same globstring!
                # Create a sha-1 of the file name and modification date.
                sha = hashlib.sha1()
                files = [k.replace('\\', '/') for k in glob.glob( path )]
                for f in files:
                    sha.update(f)
                    sha.update(pickle.dumps(os.stat(f).st_mtime))
                stackFile = sha.hexdigest() + '.h5'
                stackPath = os.path.join( stackVolumeCacheDir, stackFile ).replace('\\', '/')
                
                # Overwrite original path
                filePaths[i] = stackPath + "/volume/data"
    
                # Generate the hdf5 if it doesn't already exist
                if os.path.exists(stackPath):
                    logger.info( "Using previously generated hdf5 volume for stack {}".format(path) )
                    logger.info( "Volume path: {}".format(filePaths[i]) )
                else:
                    logger.info( "Generating hdf5 volume for stack {}".format(path) )
                    logger.info( "Volume path: {}".format(filePaths[i]) )
    
                    if not os.path.exists( stackVolumeCacheDir ):
                        os.makedirs( stackVolumeCacheDir )
                    
                    with h5py.File(stackPath) as f:
                        # Configure the conversion operator
                        opWriter = OpStackToH5Writer( graph=Graph() )
                        opWriter.hdf5Group.setValue(f)
                        opWriter.hdf5Path.setValue("volume/data")
                        opWriter.GlobString.setValue(globstring)
                        
                        # Initiate the write
                        success = opWriter.WriteImage.value
                        assert success, "Something went wrong when generating an hdf5 file from an image sequence."
            
        return filePaths
            
