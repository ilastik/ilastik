from __future__ import absolute_import

import argparse
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
import os

import numpy

from ilastik.applets.base.applet import Applet
from ilastik.utility import OpMultiLaneWrapper
from ilastik.utility.commandLineProcessing import ParseListFromString
from .dataExportSerializer import DataExportSerializer
from .opDataExport import OpDataExport


class DataExportApplet( Applet ):
    """
    
    """
    def __init__( self, workflow, title, isBatch=False ):
        # Designed to be subclassed: If the subclass defined its own top-level operator,
        #  don't create one here.
        self.__topLevelOperator = None
        if self.topLevelOperator is None:
            self.__topLevelOperator = OpMultiLaneWrapper( OpDataExport, parent=workflow,
                                         promotedSlotNames=set(['RawData', 'Inputs', 'RawDatasetInfo']) )
        # Users can temporarily disconnect the 'transaction' 
        #  slot to force all slots to be applied atomically.
        self.topLevelOperator.TransactionSlot.setValue(True)
        super(DataExportApplet, self).__init__(title)

        self._gui = None
        self._title = title
        
        # This applet is designed to be subclassed.
        # If the user provided his own serializer, don't create one here.
        self.__serializers = None
        if self.dataSerializers is None:
            self.__serializers = [ DataExportSerializer(self.topLevelOperator, title) ]

        # This flag is set by the gui and checked by the workflow        
        self.busy = False
        
    @property
    def dataSerializers(self):
        return self.__serializers

    @property
    def topLevelOperator(self):
        return self.__topLevelOperator

    def includeTableOnlyOption(self):
        """
        Append Table-Only option to export csv or HDF5 table to operator selection names (without exporting volumes)
        """
        opDataExport = self.topLevelOperator
        names = opDataExport.SelectionNames.value
        names.append(opDataExport.TableOnlyName.value)
        opDataExport.SelectionNames.setValue(names)

    def getMultiLaneGui(self):
        if self._gui is None:
            from .dataExportGui import DataExportGui
            self._gui = DataExportGui( self, self.topLevelOperator )
        return self._gui

    @staticmethod
    def postprocessCanCheckForExistingFiles():
        '''
        While exporting, we can check whether files would be overwritten.
        This is handled by an additional parameter to post_process_lane_export called "checkOverwriteFiles",
        and that method should return True if the export files do NOT exist yet.

        By default we do not want to check for existing files,
        and most operators don't provide checkOverwriteFiles, so return False.
        '''
        return False

    # The following functions act as hooks for subclasses to override or clients to 
    # monkey-patch for custom behavior before/during/after an export is performed.
    # (The GUI and/or batch applet will call them at the appropriate time.)
    def prepare_for_entire_export(self):
        """Called before the entire export process starts"""
        pass
    def prepare_lane_for_export(self, lane_index):
        """Called before each lane is exported."""
        pass
    def post_process_lane_export(self, lane_index):
        """Called immediately after each lane is exported."""
        pass
    def post_process_entire_export(self):
        """Called after the entire export process finishes."""

    @classmethod
    def make_cmdline_parser(cls, starting_parser=None):
        arg_parser = starting_parser or argparse.ArgumentParser()
        arg_parser.add_argument(
            '--cutout_subregion',
            help=(
                'Subregion to export (start,stop), e.g. [(0,0,0,0,0),(1,100,200,20,3)]. '
                'Note, that the subregion has to be specified in 5D with the axisorder '
                '(t,c,z,y,x).'
            ),
            required=False,
            action=ParseListFromString,
        )

        arg_parser.add_argument(
            '--pipeline_result_drange',
            help='Pipeline result data range (min,max) BEFORE normalization, e.g. (0.0,1.0)',
            required=False,
            action=ParseListFromString,
        )
        arg_parser.add_argument(
            '--export_drange',
            help='Exported data range (min,max) AFTER normalization, e.g. (0,255)',
            required=False,
            action=ParseListFromString,
        )

        all_dtypes = ['uint8', 'uint16', 'uint32', 'int8', 'int16', 'int32', 'float32', 'float64']
        all_format_names = [fmt.name for fmt in OpDataExport.ALL_FORMATS]

        arg_parser.add_argument( '--export_dtype', help='Export data type', choices=all_dtypes, required=False )
        arg_parser.add_argument( '--output_axis_order', help='Axis indexing order of exported data, e.g. tzyxc', required=False )
        arg_parser.add_argument( '--output_format', help='Export file format', choices=all_format_names, required=False )
        arg_parser.add_argument( '--output_filename_format', help='Output file path, including special placeholders, e.g. /tmp/results_t{t_start}-t{t_stop}.h5', required=False )
        arg_parser.add_argument( '--output_internal_path', help='Specifies dataset name within an hdf5 dataset (applies to hdf5 output only), e.g. /volume/data', required=False )

        arg_parser.add_argument( '--export_source', help='The data to export.  See the dropdown list on the Data Export page for choices.', required=False )
        
        arg_parser.add_argument( '--table_only', help='Export only csv/HDF5 table.', action='store_true', default=False )

        return arg_parser

    @classmethod
    def parse_known_cmdline_args(cls, cmdline_args, parsed_args=None):
        """
        Helper function for headless workflows.
        Parses commandline args that can be used to configure the ``DataExportApplet`` top-level operator 
        and returns ``(parsed_args, unused_args)``, similar to ``argparse.ArgumentParser.parse_known_args()``
        See also: :py:meth:`configure_operator_with_parsed_args()`.
        
        parsed_args: Already-parsed args as returned from an ArgumentParser from make_cmdline_parser(), above.
                     If not provided, make_cmdline_parser().parse_known_args() will be used.
        """
        unused_args = []
        if parsed_args is None:
            arg_parser = cls.make_cmdline_parser()
            parsed_args, unused_args = arg_parser.parse_known_args(cmdline_args)

        # Replace '~' with home dir
        if parsed_args.output_filename_format is not None:
            parsed_args.output_filename_format = os.path.expanduser( parsed_args.output_filename_format )

        ### Convert from strings, check for obvious errors

        msg = "Error parsing command-line arguments for data export applet.\n"
        if parsed_args.cutout_subregion:
            roi = parsed_args.cutout_subregion
            assert isinstance(roi, list), "Expected a list"
            roi = tuple(map(tuple, roi))
            parsed_args.cutout_subregion = roi

            if len(roi) != 2:
                msg += "cutout_subregion must include separate start and stop tuples."
                raise Exception(msg)
            elif len(roi[0]) != len(roi[1]):
                msg += "cutout_subregion start and stop coordinates must have the same dimensionality!"
                raise Exception(msg)

        if parsed_args.pipeline_result_drange:

            input_drange = parsed_args.pipeline_result_drange
            assert isinstance(input_drange, list), "Expected a list"

            if len(input_drange) != 2:
                msg += "Didn't understand pipeline_result_drange: {}".format(parsed_args.pipeline_result_drange)
                raise Exception(msg)

            parsed_args.pipeline_result_drange = tuple(input_drange)

        if parsed_args.export_drange:
            if not parsed_args.pipeline_result_drange:
                raise Exception("Cannot renormalize to custom export_drange without a specified pipeline_result_drange.")

            export_drange = parsed_args.export_drange
            assert isinstance(export_drange, list), "Expected a list"

            if len(export_drange) != 2:
                msg += "Didn't understand export_drange: {}".format(parsed_args.export_drange)
                raise Exception(msg)

            parsed_args.export_drange = tuple(export_drange)

        if parsed_args.export_dtype:
            try:
                parsed_args.export_dtype = numpy.dtype(parsed_args.export_dtype).type
            except TypeError as e:
                msg += "Didn't understand export_dtype: {}".format(parsed_args.export_dtype)
                raise Exception(msg)

        if parsed_args.output_axis_order:
            output_axis_order = parsed_args.output_axis_order.lower()
            if any( [a not in 'txyzc' for a in output_axis_order] ):
                raise Exception( "Invalid axes specified output_axis_order: {}".format( parsed_args.output_axis_order ) )
            parsed_args.output_axis_order = output_axis_order

        return parsed_args, unused_args

    

    def configure_operator_with_parsed_args(self, parsed_args):
        """
        Helper function for headless workflows.
        Configures this applet's top-level operator according to the settings provided in ``parsed_args``.
        
        :param parsed_args: Must be an ``argparse.Namespace`` as returned by :py:meth:`parse_known_cmdline_args()`.
        """
        opDataExport = self.topLevelOperator
        self._configure_operator_with_parsed_args(parsed_args, opDataExport)

    @classmethod
    def _configure_operator_with_parsed_args(cls, parsed_args, opDataExport):
        """
        Helper function for headless workflows.
        Configures the given export operator according to the settings provided in ``parsed_args``.
        
        Unlike the function above, this function can be called from external scripts.
        The operator can be OpDataExport, OR OpFormattedDataExport
        
        :param parsed_args: Must be an ``argparse.Namespace`` as returned by :py:meth:`parse_known_cmdline_args()`.
        """
        
        # Disconnect the special 'transaction' slot to prevent these 
        #  settings from triggering many calls to setupOutputs.
        opDataExport.TransactionSlot.disconnect()

        if parsed_args.export_source is not None:
            source_choices = opDataExport.SelectionNames.value
            source_choices = list(map(str.lower, source_choices))
            export_source = parsed_args.export_source.lower()
            try:
                source_index = source_choices.index(export_source)
            except ValueError:
                raise Exception("Invalid option for --export_source: '{}'\n"
                                "Valid options are: {}".format( parsed_args.export_source, source_choices ))
            else:
                opDataExport.InputSelection.setValue( source_index )

        if parsed_args.cutout_subregion:
            opDataExport.RegionStart.setValue( parsed_args.cutout_subregion[0] )
            opDataExport.RegionStop.setValue( parsed_args.cutout_subregion[1] )

        if parsed_args.pipeline_result_drange and parsed_args.export_drange:
            opDataExport.InputMin.setValue( parsed_args.pipeline_result_drange[0] )
            opDataExport.InputMax.setValue( parsed_args.pipeline_result_drange[1] )
            opDataExport.ExportMin.setValue( parsed_args.export_drange[0] )
            opDataExport.ExportMax.setValue( parsed_args.export_drange[1] )

        if parsed_args.export_dtype:
            opDataExport.ExportDtype.setValue( parsed_args.export_dtype )
        
        if parsed_args.output_axis_order:
            opDataExport.OutputAxisOrder.setValue( parsed_args.output_axis_order )
            
        if parsed_args.output_filename_format:
            if hasattr(opDataExport, 'WorkingDirectory'):
                # By default, most workflows consider the project directory to be the 'working directory'
                #  for transforming relative paths (e.g. export locations) into absolute locations.
                # A user would probably expect paths to be relative to his cwd when he launches 
                #  ilastik from the command line.
                opDataExport.WorkingDirectory.disconnect()
                opDataExport.WorkingDirectory.setValue( os.getcwd() )
    
            opDataExport.OutputFilenameFormat.setValue( parsed_args.output_filename_format )
            
        if parsed_args.output_internal_path:
            opDataExport.OutputInternalPath.setValue( parsed_args.output_internal_path )

        if parsed_args.output_format:
            opDataExport.OutputFormat.setValue( parsed_args.output_format )
            
        if parsed_args.table_only:
            opDataExport.TableOnly.setValue(True)

        # Re-connect the 'transaction' slot to apply all settings at once.
        opDataExport.TransactionSlot.setValue(True)
