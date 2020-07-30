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
from typing import List, Dict, Optional, Union, Sequence
import itertools
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)  # noqa

import vigra
import h5py
from lazyflow.utility import PathComponents, isUrl
from ilastik.utility.commandLineProcessing import parse_axiskeys
from ilastik.applets.base.applet import Applet
from .opDataSelection import (
    OpMultiLaneDataSelectionGroup,
    DatasetInfo,
    RelativeFilesystemDatasetInfo,
    UrlDatasetInfo,
    FilesystemDatasetInfo,
    OpDataSelectionGroup,
)
from .dataSelectionSerializer import DataSelectionSerializer, Ilastik05DataSelectionDeserializer


class RoleMismatchException(Exception):
    pass


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
                "--" + arg_name.replace("_", "-"),
                nargs="+",
                help=f"List of input files for the {role_name} role",
            )

        # Finally, a catch-all for role 0 (if the workflow only has one role, there's no need to provide role names
        arg_parser.add_argument(
            "unspecified_input_files",
            nargs="*",
            help="List of input files to process.",
            action=make_trailing_args_action(role_names),
        )

        arg_parser.add_argument(
            "--preconvert-stacks",
            "--preconvert_stacks",
            help="Convert image stacks to temporary hdf5 files before loading them.",
            action="store_true",
            default=False,
        )

        def parse_input_axes(raw_input_axes: str) -> List[Optional[vigra.AxisTags]]:
            input_axes = [axes.strip() for axes in raw_input_axes.split(",")]
            if len(input_axes) > len(role_names):
                raise ValueError("Specified input axes exceed number of data roles ({role_names})")
            if len(input_axes) == 1:
                input_axes = input_axes * len(role_names)
            else:
                input_axes += ["None"] * (len(role_names) - len(input_axes))
            return [parse_axiskeys(keys) for keys in input_axes]

        arg_parser.add_argument(
            "--input-axes",
            "--input_axes",
            help=(
                "Dataset axes names; a list of comma-separated axis names, representing how datasets are to be "
                "interpreted in each workflow role e.g.: 'xyz,xyz' ."
                " If a single value is provided, it is assumed to apply to all roles ({role_names}). If more than "
                "one value is provided but less than the total number of roles, the missing roles will have their "
                "axistags defined by the training data axistags. If --ignore-training-axistags is set, dataset axistags "
                "will be inferred from the file conventions, e.g.: 'axes' in .n5, and not from the "
                "training data axistags. Defaults to using the training data axistags"
            ),
            required=False,
            type=parse_input_axes,
            default=[None] * len(role_names),
        )

        arg_parser.add_argument(
            "--ignore-training-axistags",
            "--ignore_training_axistags",
            help="Do not use training data to guess input data axis on headless runs. Can still use file axis conventions",
            action="store_true",
        )

        arg_parser.add_argument(
            "--stack-along",
            "--stack_along",
            help=(
                "Axis along which stack datasets (e.g.: my_yx_slices*.tiff) are to be stacked. If the axis is not "
                "present in the input files, it will appear prepended to the input files axis (e.g.: when stacking "
                "'yxc' files along the 'z' axis, the resulting axis order will be zyxc). Otherwise, the stack axis "
                "remain in the same order as the input images, but with with size equal to the sum of the sizes of "
                "all images, in that dimension"
            ),
            type=str,
            default="z",
        )
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

    def create_dataset_info(
        self, url: Union[Path, str], axistags: Optional[vigra.AxisTags] = None, sequence_axis: str = "z"
    ) -> DatasetInfo:
        url = str(url)
        if isUrl(url):
            return UrlDatasetInfo(url=url, axistags=axistags)
        else:
            return RelativeFilesystemDatasetInfo.create_or_fallback_to_absolute(
                filePath=url, axistags=axistags, sequence_axis=sequence_axis
            )

    def convert_info_to_h5(self, info: DatasetInfo) -> DatasetInfo:
        tmp_path = tempfile.mktemp() + ".h5"
        inner_path = "volume/data"
        full_path = Path(tmp_path) / inner_path
        with h5py.File(tmp_path, mode="w") as tmp_h5:
            logger.info(f"Converting info {info.effective_path} to h5 at {full_path}")
            info.dumpToHdf5(h5_file=tmp_h5, inner_path=inner_path)
            return self.create_dataset_info(url=full_path)

    def create_lane_configs(
        self,
        role_inputs: Dict[str, List[str]],
        input_axes: Sequence[Optional[vigra.AxisTags]] = (),
        preconvert_stacks: bool = False,
        ignore_training_axistags: bool = False,
        stack_along: str = "z",
    ) -> List[Dict[str, DatasetInfo]]:
        if not input_axes or not any(input_axes):
            if ignore_training_axistags or self.num_lanes == 0:
                input_axes = [None] * len(self.role_names)
                logger.info(f"Using axistags from input files")
            else:
                input_axes = list(self.get_lane(-1).get_axistags().values())
                logger.info(f"Using axistags from previous lane: {input_axes}")
        else:
            logger.info(f"Forcing input axes to {input_axes}")

        rolewise_infos: Dict[str, List[DatasetInfo]] = {}
        for role_name, axistags in zip(self.role_names, input_axes):
            role_urls = role_inputs.get(role_name, [])
            infos = [self.create_dataset_info(url, axistags=axistags, sequence_axis=stack_along) for url in role_urls]
            if preconvert_stacks:
                infos = [self.convert_info_to_h5(info) if info.is_stack() else info for info in infos]
            rolewise_infos[role_name] = infos

        lane_configs: List[Dict[str, Optional[DatasetInfo]]] = []
        for info_group in itertools.zip_longest(*rolewise_infos.values()):
            lane_configs.append(dict(zip(self.role_names, info_group)))

        main_role = self.role_names[0]
        if any(lane_conf[main_role] is None for lane_conf in lane_configs):
            message = f"You must provide values for {main_role} for every lane. Provided was {lane_configs}"
            raise RoleMismatchException(message)
        return lane_configs

    def lane_configs_from_parsed_args(self, parsed_args: argparse.Namespace) -> List[Dict[str, Optional[DatasetInfo]]]:
        role_inputs: Dict[str, List[str]] = {}
        for role_name in self.role_names:
            role_arg_name = self._role_name_to_arg_name(role_name)
            role_inputs[role_name] = getattr(parsed_args, role_arg_name) or []
        return self.create_lane_configs(
            role_inputs=role_inputs,
            input_axes=parsed_args.input_axes,
            preconvert_stacks=parsed_args.preconvert_stacks,
            ignore_training_axistags=parsed_args.ignore_training_axistags,
            stack_along=parsed_args.stack_along,
        )

    def pushLane(self, role_infos: Dict[str, DatasetInfo]):
        return self.topLevelOperator.pushLane(role_infos)

    def dropLastLane(self):
        return self.topLevelOperator.dropLastLane()

    @property
    def num_lanes(self) -> int:
        return self.topLevelOperator.num_lanes

    def get_lane(self, lane_idx: int) -> OpDataSelectionGroup:
        return self.topLevelOperator.get_lane(lane_idx)

    @property
    def project_file(self) -> Optional[h5py.File]:
        return self.topLevelOperator.ProjectFile.value if self.topLevelOperator.ProjectFile.ready() else None

    @property
    def role_names(self) -> List[str]:
        return self.topLevelOperator.role_names

    def configure_operator_with_parsed_args(self, parsed_args: argparse.Namespace):
        for lane_config in self.lane_configs_from_parsed_args(parsed_args):
            self.pushLane(lane_config)
