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
#          http://ilastik.org/license.html
###############################################################################
from __future__ import division
from __future__ import absolute_import
from builtins import range
import os
import sys
import glob
import argparse
import collections
import logging
from typing import List

logger = logging.getLogger(__name__)  # noqa

import vigra
from lazyflow.utility import PathComponents, isUrl
from ilastik.applets.base.applet import Applet
from .opDataSelection import OpMultiLaneDataSelectionGroup, FilesystemDatasetInfo
from .dataSelectionSerializer import DataSelectionSerializer, Ilastik05DataSelectionDeserializer


class DataSelectionApplet(Applet):
    """
    This applet allows the user to select sets of input data,
    which are provided as outputs in the corresponding top-level applet operator.
    """

    DEFAULT_INSTRUCTIONS = "Use the controls shown to the right to add image files to this workflow."

    def __init__(
        self,
        workflow,
        title,
        projectFileGroupName,
        supportIlastik05Import=False,
        batchDataGui=False,
        forceAxisOrder=None,
        instructionText=DEFAULT_INSTRUCTIONS,
        max_lanes=None,
        show_axis_details=False,
    ):
        self.__topLevelOperator = OpMultiLaneDataSelectionGroup(parent=workflow, forceAxisOrder=forceAxisOrder)
        super(DataSelectionApplet, self).__init__(title, syncWithImageIndex=False)

        self._serializableItems = [DataSelectionSerializer(self.topLevelOperator, projectFileGroupName)]
        if supportIlastik05Import:
            self._serializableItems.append(Ilastik05DataSelectionDeserializer(self.topLevelOperator))

        self._instructionText = instructionText
        self._gui = None
        self._batchDataGui = batchDataGui
        self._title = title
        self._max_lanes = max_lanes
        self.busy = False
        self.show_axis_details = show_axis_details

    #
    # GUI
    #
    def getMultiLaneGui(self):
        if self._gui is None:
            from .dataSelectionGui import DataSelectionGui, GuiMode

            guiMode = {True: GuiMode.Batch, False: GuiMode.Normal}[self._batchDataGui]
            self._gui = DataSelectionGui(
                self,
                self.topLevelOperator,
                self._serializableItems[0],
                self._instructionText,
                guiMode,
                self._max_lanes,
                self.show_axis_details,
            )
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

    @classmethod
    def get_arg_parser(cls, role_names):
        def user_expanded_existing_filename(path):
            if isUrl(path):
                return path
            expanded_path = os.path.expanduser(path)
            all_paths = glob.glob(PathComponents(expanded_path).externalPath)
            if len(all_paths) == 0:
                raise ValueError(f"No files found matching path {path}")
            for p in all_paths:
                if not os.path.exists(p):
                    raise ValueError(f"Input file does not exist: {p}")
            return path

        def make_trailing_args_action(role_names: List[str]):
            class ExtraTrailingArgumentsAction(argparse.Action):
                def __call__(self, parser, namespace, values, option_string):
                    role_arg_names = [DataSelectionApplet._role_name_to_arg_name(role_name) for role_name in role_names]
                    role_arg_values = [getattr(namespace, arg_name) for arg_name in role_arg_names]
                    named_configured_roles = {k: v for k, v in zip(role_arg_names, role_arg_values) if v}
                    if values:
                        if named_configured_roles:
                            raise ValueError(
                                "You can only have trailing file paths if no other role was set by name. "
                                f"You have set the following roles by name: {named_configured_roles}"
                            )
                        setattr(namespace, role_arg_names[0], values)

            return ExtraTrailingArgumentsAction

        arg_parser = argparse.ArgumentParser()
        for role_name in role_names or []:
            arg_name = cls._role_name_to_arg_name(role_name)
            arg_parser.add_argument(
                "--" + arg_name,
                nargs="+",
                help=f"List of input files for the {role_name} role",
                type=user_expanded_existing_filename,
            )

        # Finally, a catch-all for role 0 (if the workflow only has one role, there's no need to provide role names
        arg_parser.add_argument(
            "unspecified_input_files",
            nargs="*",
            help="List of input files to process.",
            action=make_trailing_args_action(role_names),
        )

        arg_parser.add_argument(
            "--preconvert_stacks",
            help="Convert image stacks to temporary hdf5 files before loading them.",
            action="store_true",
            default=False,
        )
        arg_parser.add_argument("--input_axes", help="Explicitly specify the axes of your dataset.", required=False)
        arg_parser.add_argument("--stack_along", help="Sequence axis along which to stack", type=str, default="z")
        return arg_parser

    @classmethod
    def parse_known_cmdline_args(cls, cmdline_args, role_names):
        """
        Helper function for headless workflows.
        Parses command-line args that can be used to configure the ``DataSelectionApplet`` top-level operator
        and returns ``(parsed_args, unused_args)``, similar to ``argparse.ArgumentParser.parse_known_args()``

        Relative paths are converted to absolute paths **according to ``os.getcwd()``**,
        not according to the project file location, since this more likely to be what headless users expect.

        .. note: If the top-level operator was configured with multiple 'roles', then the input files for
                 each role can be configured separately:
                 $ python ilastik.py [other workflow options] --my-role-A inputA1.png inputA2.png --my-role-B
                    inputB1.png, inputB2.png
                 If the workflow has only one role (or only one required role), then the role-name flag can be omitted:
                 # python ilastik.py [other workflow options] input1.png input2.png

        See also: :py:meth:`configure_operator_with_parsed_args()`.
        """
        arg_parser = cls.get_arg_parser(role_names)
        parsed_args, unused_args = arg_parser.parse_known_args(cmdline_args)
        return parsed_args, unused_args

    @staticmethod
    def _role_name_to_arg_name(role_name):
        return role_name.lower().replace(" ", "_").replace("-", "_")

    def role_paths_from_parsed_args(self, parsed_args):
        role_names = self.topLevelOperator.DatasetRoles.value
        role_paths = collections.OrderedDict()
        for role_index, role_name in enumerate(role_names):
            arg_name = self._role_name_to_arg_name(role_name)
            input_paths = getattr(parsed_args, arg_name)
            role_paths[role_index] = input_paths or []

        # As far as this parser is concerned, all roles except the first are optional.
        # (Workflows that require the other roles are responsible for raising an error themselves.)
        for role_index in range(1, len(role_names)):
            # Fill in None for missing files
            if role_index not in role_paths:
                role_paths[role_index] = []
            num_missing = len(role_paths[0]) - len(role_paths[role_index])
            role_paths[role_index] += [None] * num_missing
        return role_paths

    def configure_operator_with_parsed_args(self, parsed_args):
        """
        Helper function for headless workflows.
        Configures this applet's top-level operator according to the settings provided in ``parsed_args``.

        :param parsed_args: Must be an ``argparse.Namespace`` as returned by :py:meth:`parse_known_cmdline_args()`.
        """
        role_names = self.topLevelOperator.DatasetRoles.value
        role_paths = self.role_paths_from_parsed_args(parsed_args)

        for role_index, input_paths in list(role_paths.items()):
            # If the user doesn't want image stacks to be copied into the project file,
            #  we generate hdf5 volumes in a temporary directory and use those files instead.
            if parsed_args.preconvert_stacks:
                import tempfile

                input_paths = self.convertStacksToH5(input_paths, tempfile.gettempdir())

            input_infos = [FilesystemDatasetInfo(filepath=p) if p else None for p in input_paths]
            if parsed_args.input_axes:
                for info in [_f for _f in input_infos if _f]:
                    info.axistags = vigra.defaultAxistags(parsed_args.input_axes)

            opDataSelection = self.topLevelOperator
            existing_lanes = len(opDataSelection.DatasetGroup)
            opDataSelection.DatasetGroup.resize(max(len(input_infos), existing_lanes))
            for lane_index, info in enumerate(input_infos):
                if info:
                    opDataSelection.DatasetGroup[lane_index][role_index].setValue(info)

            need_warning = False
            for lane_index in range(len(input_infos)):
                output_slot = opDataSelection.ImageGroup[lane_index][role_index]
                if output_slot.ready() and output_slot.meta.prefer_2d and "z" in output_slot.meta.axistags:
                    need_warning = True
                    break

            if need_warning:
                logger.warning(
                    "*******************************************************************************************"
                )
                logger.warning(
                    "Some of your input data is stored in a format that is not efficient for 3D access patterns."
                )
                logger.warning("Performance may suffer as a result.  For best performance, use a chunked HDF5 volume.")
                logger.warning(
                    "*******************************************************************************************"
                )

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
            if not path or "*" not in path:
                continue
            globstring = path

            # Embrace paranoia:
            # We want to make sure we never re-use a stale cache file for a new dataset,
            #  even if the dataset is located in the same location as a previous one and has the same globstring!
            # Create a sha-1 of the file name and modification date.
            sha = hashlib.sha1()
            files = sorted([k.replace("\\", "/") for k in glob.glob(path)])
            for f in files:
                sha.update(f)
                sha.update(pickle.dumps(os.stat(f).st_mtime, 0))
            stackFile = sha.hexdigest() + ".h5"
            stackPath = os.path.join(stackVolumeCacheDir, stackFile).replace("\\", "/")

            # Overwrite original path
            filePaths[i] = stackPath + "/volume/data"

            # Generate the hdf5 if it doesn't already exist
            if os.path.exists(stackPath):
                logger.info("Using previously generated hdf5 volume for stack {}".format(path))
                logger.info("Volume path: {}".format(filePaths[i]))
            else:
                logger.info("Generating hdf5 volume for stack {}".format(path))
                logger.info("Volume path: {}".format(filePaths[i]))

                if not os.path.exists(stackVolumeCacheDir):
                    os.makedirs(stackVolumeCacheDir)

                with h5py.File(stackPath) as f:
                    # Configure the conversion operator
                    opWriter = OpStackToH5Writer(graph=Graph())
                    opWriter.hdf5Group.setValue(f)
                    opWriter.hdf5Path.setValue("volume/data")
                    opWriter.GlobString.setValue(globstring)

                    # Initiate the write
                    success = opWriter.WriteImage.value
                    assert success, "Something went wrong when generating an hdf5 file from an image sequence."

        return filePaths
