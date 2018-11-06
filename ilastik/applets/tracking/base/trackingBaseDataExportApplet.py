from __future__ import absolute_import
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
from ilastik.applets.base.appletSerializer import SerialSlot, SerialDictSlot
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.dataExport.dataExportSerializer import DataExportSerializer
from ilastik.applets.tracking.base.opTrackingBaseDataExport import OpTrackingBaseDataExport
from ilastik.utility import OpMultiLaneWrapper
import os

class TrackingBaseDataExportApplet( DataExportApplet ):
    """
    This a specialization of the generic data export applet that
    provides a special viewer for tracking output.
    """
    def __init__(self, workflow, title, is_batch=False, default_export_filename=''):
        self.export_op = None
        self._default_export_filename = default_export_filename

        self.__topLevelOperator = OpMultiLaneWrapper(OpTrackingBaseDataExport, parent=workflow,
                                                     promotedSlotNames=set(['RawData', 'Inputs', 'RawDatasetInfo']))

        extra_serial_slots = [
            SerialSlot(self.topLevelOperator.SelectedPlugin),
            SerialSlot(self.topLevelOperator.SelectedExportSource),
            SerialDictSlot(self.topLevelOperator.AdditionalPluginArguments)
        ]
        self._serializers = [DataExportSerializer(self.topLevelOperator, title, extra_serial_slots)]

        super(TrackingBaseDataExportApplet, self).__init__(workflow, title, isBatch=is_batch)

    @property
    def dataSerializers(self):
        return self._serializers

    def set_exporting_operator(self, op):
        self.export_op = op

    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from .trackingBaseDataExportGui import TrackingBaseDataExportGui
            self._gui = TrackingBaseDataExportGui( self, self.topLevelOperator )

            assert self.export_op is not None, "Exporting Operator must be set!"
            self._gui.set_exporting_operator(self.export_op)
            self._gui.set_default_export_filename(self._default_export_filename) # remove once the PGMLINK version is gone
        return self._gui

    @staticmethod
    def postprocessCanCheckForExistingFiles():
        '''
        While exporting, we can check whether files would be overwritten.
        This is handled by an additional parameter to post_process_lane_export called "checkOverwriteFiles",
        and that method should return True if the export files do NOT exist yet.

        In Tracking export we want to check for existing files, so return True.
        '''
        return True

    @property
    def topLevelOperator(self):
        return self.__topLevelOperator

    @classmethod
    def make_cmdline_parser(cls, starting_parser=None):
        """
        Returns a command line parser that includes all parameters from the parent applet and adds export_plugin.
        """
        arg_parser = DataExportApplet.make_cmdline_parser(starting_parser)
        arg_parser.add_argument('--export_plugin',
                                help='Plugin name for exporting tracking results',
                                required=False,
                                default=None)
        arg_parser.add_argument('--big_data_viewer_xml_file',
                                help='Path to BigDataViewer XML file. Required if export_plugin=Fiji-MaMuT',
                                required=False,
                                default=None)
        return arg_parser

    @classmethod
    def parse_known_cmdline_args(cls, cmdline_args, parsed_args=None):
        """
        Helper function for headless workflows.
        Parses commandline args that can be used to configure the ``TrackingBaseDataExportApplet`` top-level operator
        as well as its parent, the ``DataExportApplet``,
        and returns ``(parsed_args, unused_args)``, similar to ``argparse.ArgumentParser.parse_known_args()``
        See also: :py:meth:`configure_operator_with_parsed_args()`.

        parsed_args: Already-parsed args as returned from an ArgumentParser from make_cmdline_parser(), above.
                     If not provided, make_cmdline_parser().parse_known_args() will be used.
        """
        unused_args = []
        if parsed_args is None:
            arg_parser = cls.make_cmdline_parser()
            parsed_args, unused_args = arg_parser.parse_known_args(cmdline_args)

        msg = "Error parsing command-line arguments for tracking data export applet.\n"
        if parsed_args.export_plugin is not None:
            if parsed_args.export_source is None or parsed_args.export_source.lower() != "plugin":
                msg += "export_plugin should only be specified if export_source is set to Plugin."
                raise Exception(msg)

        if parsed_args.export_source is not None and parsed_args.export_source.lower() == "plugin" and parsed_args.export_plugin is None:
                msg += "export_plugin MUST be specified if export_source is set to Plugin!"
                raise Exception(msg)

        if parsed_args.export_plugin == 'Fiji-MaMuT':
            if parsed_args.big_data_viewer_xml_file is None:
                msg += "'big_data_viewer_xml_file' MUST be specified if 'export_plugin' is set to 'Fiji-MaMuT'"
                raise Exception(msg)

        # configure parent applet
        DataExportApplet.parse_known_cmdline_args(cmdline_args, parsed_args)

        return parsed_args, unused_args

    def configure_operator_with_parsed_args(self, parsed_args):
        """
        Helper function for headless workflows.
        Configures this applet's top-level operator according to the settings provided in ``parsed_args``.

        :param parsed_args: Must be an ``argparse.Namespace`` as returned by :py:meth:`parse_known_cmdline_args()`.
        """
        opTrackingDataExport = self.topLevelOperator
        self._configure_operator_with_parsed_args(parsed_args, opTrackingDataExport)

    @classmethod
    def _configure_operator_with_parsed_args(cls, parsed_args, opTrackingDataExport):
        """
        Helper function for headless workflows.
        Configures the given export operator according to the settings provided in ``parsed_args``,
        and depending on the chosen export source it also configures the parent operator opDataExport

        :param parsed_args: Must be an ``argparse.Namespace`` as returned by :py:meth:`parse_known_cmdline_args()`.
        """
        if parsed_args.export_source is not None:
            opTrackingDataExport.SelectedExportSource.setValue(parsed_args.export_source)

            if parsed_args.export_source == OpTrackingBaseDataExport.PluginOnlyName:
                opTrackingDataExport.SelectedPlugin.setValue(parsed_args.export_plugin)
                if parsed_args.export_plugin == 'Fiji-MaMuT':
                    if opTrackingDataExport.AdditionalPluginArguments.ready():
                        additional_plugin_args = opTrackingDataExport.AdditionalPluginArguments.value
                    else:
                        additional_plugin_args = {}
                    additional_plugin_args['bdvFilepath'] = parsed_args.big_data_viewer_xml_file
                    opTrackingDataExport.AdditionalPluginArguments.setValue(additional_plugin_args)

                # if a plugin was selected, the only thing we need is the export name
                if parsed_args.output_filename_format:
                    if hasattr(opTrackingDataExport, 'WorkingDirectory'):
                        # By default, most workflows consider the project directory to be the 'working directory'
                        #  for transforming relative paths (e.g. export locations) into absolute locations.
                        # A user would probably expect paths to be relative to his cwd when he launches
                        #  ilastik from the command line.
                        opTrackingDataExport.WorkingDirectory.disconnect()
                        opTrackingDataExport.WorkingDirectory.setValue(os.getcwd())

                    opTrackingDataExport.OutputFilenameFormat.setValue(parsed_args.output_filename_format)

                return # We don't want to configure the super operator so we quit now!
            else:
                # set some value to the SelectedPlugin slot so that it is ready
                opTrackingDataExport.SelectedPlugin.setValue("None")

        # configure super operator
        DataExportApplet._configure_operator_with_parsed_args(parsed_args, opTrackingDataExport)


