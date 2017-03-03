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
import argparse
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.plugins import pluginManager

class TrackingBaseDataExportApplet( DataExportApplet ):
    """
    This a specialization of the generic data export applet that
    provides a special viewer for trackign output.
    """
    def __init__(self, *args, **kwargs):
        if 'default_export_filename' in kwargs:
            default_export_filename = kwargs['default_export_filename']
            del kwargs['default_export_filename']
        else:
            default_export_filename = ""

        super(TrackingBaseDataExportApplet, self).__init__(*args, **kwargs)
        self.export_op = None
        self._default_export_filename = default_export_filename
        self._cmdline_selected_export_plugin = ''
        self._cmdline_selected_export_source = ''

    def set_exporting_operator(self, op):
        self.export_op = op

    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from trackingBaseDataExportGui import TrackingBaseDataExportGui
            self._gui = TrackingBaseDataExportGui( self, self.topLevelOperator )

            assert self.export_op is not None, "Exporting Operator must be set!"
            self._gui.set_exporting_operator(self.export_op)
            self._gui.set_default_export_filename(self._default_export_filename)
        return self._gui

    def getSelectedExportSourceName(self):
        # TODO: read this parameter from the command line by implementing make_cmdline_parser and parse_known_cmdline_args!
        if self._gui is not None:
            return self._gui.selectedExportSource
        else:
            return self._cmdline_selected_export_source

    def getSelectedExportPluginName(self):
        # TODO: read this parameter from the command line by implementing make_cmdline_parser and parse_known_cmdline_args!

        if self._gui is not None:
            return self._gui.selectedPlugin
        else:
            return self._cmdline_selected_export_plugin

    def includePluginOnlyOption(self):
        """
        Append Plugin-Only option to export tracking result using a plugin (without exporting volumes)
        """
        opDataExport = self.topLevelOperator
        names = opDataExport.SelectionNames.value
        names.append(opDataExport.PluginOnlyName.value)
        opDataExport.SelectionNames.setValue(names)

    @classmethod
    def make_cmdline_parser(cls, starting_parser=None):
        arg_parser = DataExportApplet.make_cmdline_parser(starting_parser)
        arg_parser.add_argument('--export_plugin',
                                help='Plugin name for exporting tracking results',
                                required=False,
                                default=None)
        return arg_parser

    @classmethod
    def parse_known_cmdline_args(cls, cmdline_args, parsed_args=None):
        """
        Helper function for headless workflows.
        Parses commandline args that can be used to configure the ``TrackingBaseDataExportApplet`` top-level operator
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

        # configure parent applet
        DataExportApplet.parse_known_cmdline_args(cmdline_args, parsed_args)

        return parsed_args, unused_args

    def configure_operator_with_parsed_args(self, parsed_args):
        """
        Helper function for headless workflows.
        Configures this applet's top-level operator according to the settings provided in ``parsed_args``.

        :param parsed_args: Must be an ``argparse.Namespace`` as returned by :py:meth:`parse_known_cmdline_args()`.
        """
        opDataExport = self.topLevelOperator
        self._configure_operator_with_parsed_args(parsed_args, opDataExport)

        # Todo derive the data export operator so we can put these things there, Applet should be stateless!
        if parsed_args.export_plugin is not None:
            self._cmdline_selected_export_plugin = parsed_args.export_plugin

        if parsed_args.export_source is not None:
            self._cmdline_selected_export_source = parsed_args.export_source

    @classmethod
    def _configure_operator_with_parsed_args(cls, parsed_args, opDataExport):
        """
        Helper function for headless workflows.
        Configures the given export operator according to the settings provided in ``parsed_args``.

        Unlike the function above, this function can be called from external scripts.
        The operator can be OpDataExport, OR OpFormattedDataExport

        :param parsed_args: Must be an ``argparse.Namespace`` as returned by :py:meth:`parse_known_cmdline_args()`.
        """

        DataExportApplet._configure_operator_with_parsed_args(parsed_args, opDataExport)





