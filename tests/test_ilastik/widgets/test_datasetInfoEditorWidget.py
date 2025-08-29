import os
from typing import List, Tuple
from numbers import Number
from pathlib import Path
import pytest
import requests
import tempfile
import uuid
import h5py

import numpy
from qtpy.QtCore import Qt

from ilastik.applets.dataSelection.datasetInfoEditorWidget import DatasetInfoEditorWidget
from ilastik.applets.dataSelection.dataSelectionSerializer import DataSelectionSerializer
from ilastik.applets.dataSelection.opDataSelection import OpDataSelectionGroup
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo, FilesystemDatasetInfo, FilesystemDatasetInfo
from ilastik.applets.dataSelection.opDataSelection import RelativeFilesystemDatasetInfo, ProjectInternalDatasetInfo
from lazyflow.graph import Graph


@pytest.fixture(scope="function")
def image_yxc_fs_info(png_image, empty_project_file):
    return FilesystemDatasetInfo(filePath=str(png_image), project_file=empty_project_file)


@pytest.fixture(scope="function")
def image_zyxc_stack_path(png_image, another_png_image):
    return str(png_image) + os.path.pathsep + str(another_png_image)


DONT_SET_NORMALIZE = object()
TOP_GROUP_NAME = "my_group"


def create_and_modify_widget(
    qtbot,
    infos: List[DatasetInfo],
    project_file: h5py.File,
    nickname: str = None,
    axiskeys: str = "",
    normalizeDisplay: bool = DONT_SET_NORMALIZE,
    drange: Tuple[Number, Number] = None,
    display_mode: str = None,
    location: type = None,
):
    project_file = project_file or empty_project_file()

    opDataSelectionGroup = OpDataSelectionGroup(graph=Graph())
    opDataSelectionGroup.ProjectFile.setValue(project_file)
    opDataSelectionGroup.ProjectDataGroup.setValue(TOP_GROUP_NAME)

    serializer = DataSelectionSerializer(opDataSelectionGroup, TOP_GROUP_NAME)
    widget = DatasetInfoEditorWidget(None, infos, serializer)
    qtbot.addWidget(widget)
    widget.show()

    assert widget.multi_axes_display.text() == "Current: " + ", ".join(info.axiskeys for info in infos)

    if axiskeys:
        assert widget.axesEdit.isVisible()
        assert widget.axesEdit.isEnabled()
        widget.axesEdit.setText(axiskeys)

    if nickname:
        assert widget.nicknameEdit.isEnabled()
        widget.nicknameEdit.setText("SOME_NICKNAME")

    if normalizeDisplay is not DONT_SET_NORMALIZE:
        widget.normalizeDisplayComboBox.setCurrentIndex(widget.normalizeDisplayComboBox.findData(normalizeDisplay))

    if drange is not None:
        widget.rangeMinSpinBox.setValue(drange[0])
        widget.rangeMaxSpinBox.setValue(drange[1])

    if display_mode is not None:
        index = widget.displayModeComboBox.findData(display_mode)
        widget.displayModeComboBox.setCurrentIndex(index)

    if location is not None:
        comboIndex = widget.storageComboBox.findData(location)
        widget.storageComboBox.setCurrentIndex(comboIndex)

    return widget


def accept_widget(qtbot, widget: DatasetInfoEditorWidget) -> List[DatasetInfo]:
    qtbot.mouseClick(widget.okButton, Qt.LeftButton)
    return widget.edited_infos


def test_datasetinfo_editor_widget_shows_correct_data_on_single_info(qtbot, png_image, empty_project_file):
    info = FilesystemDatasetInfo(filePath=str(png_image), project_file=empty_project_file)
    assert info.axiskeys == "yxc"
    assert info.laneDtype == numpy.uint8
    assert info.laneShape == (100, 200, 1)

    editor_widget = create_and_modify_widget(qtbot, [info], empty_project_file)

    assert editor_widget.axesEdit.maxLength() == 3
    assert "".join(tag.key for tag in editor_widget.get_new_axes_tags()) == "yxc"
    assert editor_widget.nicknameEdit.text() == Path(png_image).stem
    assert editor_widget.nicknameEdit.isEnabled()
    assert editor_widget.normalizeDisplayComboBox.isVisible()
    assert editor_widget.storageComboBox.isVisible()

    edited_info = accept_widget(qtbot, editor_widget)[0]
    assert editor_widget.edited_infos[0].axistags == info.axistags


def test_datasetinfo_editor_widget_modifies_single_info(qtbot, png_image, empty_project_file):
    info = FilesystemDatasetInfo(filePath=str(png_image), project_file=empty_project_file)
    widget = create_and_modify_widget(
        qtbot,
        [info],
        project_file=empty_project_file,
        nickname="SOME_NICKNAME",
        axiskeys="xyc",
        normalizeDisplay=True,
        drange=(10, 20),
        display_mode="alpha-modulated",
        location=RelativeFilesystemDatasetInfo,
    )
    edited_info = accept_widget(qtbot, widget)[0]
    assert edited_info.axiskeys == "xyc"
    assert edited_info.nickname == "SOME_NICKNAME"
    assert edited_info.normalizeDisplay == True
    assert edited_info.drange == (10, 20)
    assert edited_info.display_mode == "alpha-modulated"
    assert isinstance(edited_info, RelativeFilesystemDatasetInfo)
    assert edited_info.filePath == Path(png_image).absolute().as_posix()


def test_datasetinfo_editor_widget_shows_correct_data_on_multiple_info(
    qtbot, png_image, another_png_image, empty_project_file
):
    info = FilesystemDatasetInfo(filePath=str(png_image), project_file=empty_project_file)
    info_2 = FilesystemDatasetInfo(filePath=str(another_png_image), project_file=empty_project_file)

    widget = create_and_modify_widget(qtbot=qtbot, infos=[info, info_2], project_file=empty_project_file)

    assert widget.axesEdit.maxLength() == 3
    assert "".join(tag.key for tag in widget.get_new_axes_tags()) == "yxc"
    assert not widget.nicknameEdit.isEnabled()
    assert widget.nicknameEdit.text() == Path(png_image).stem + ", " + Path(another_png_image).stem


def test_datasetinfo_editor_widget_shows_edits_data_on_multiple_infos_with_same_dimensionality(
    qtbot, png_image, another_png_image, empty_project_file
):
    info_1 = FilesystemDatasetInfo(filePath=str(png_image), project_file=empty_project_file)
    info_2 = FilesystemDatasetInfo(filePath=str(another_png_image), project_file=empty_project_file)
    project_file_dir = str(Path(png_image).parent)

    widget = create_and_modify_widget(
        qtbot,
        [info_1, info_2],
        project_file=empty_project_file,
        axiskeys="cxy",
        display_mode="binary-mask",
        normalizeDisplay=True,
        drange=(20, 40),
    )

    edited_infos = accept_widget(qtbot, widget)
    assert all(info.axiskeys == "cxy" for info in edited_infos)
    assert all(info.display_mode == "binary-mask" for info in edited_infos)
    assert all(info.normalizeDisplay == True for info in edited_infos)
    assert all(info.drange == (20, 40) for info in edited_infos)


def test_cannot_edit_axis_tags_on_images_of_different_dimensionality(
    qtbot, png_image, image_zyxc_stack_path, empty_project_file
):
    info_1 = FilesystemDatasetInfo(filePath=str(png_image), project_file=empty_project_file)
    info_2 = FilesystemDatasetInfo(
        filePath=str(image_zyxc_stack_path), sequence_axis="z", project_file=empty_project_file
    )

    widget = create_and_modify_widget(qtbot, [info_1, info_2], project_file=empty_project_file)
    assert not widget.axesEdit.isEnabled()

    edited_infos = accept_widget(qtbot, widget)
    assert edited_infos[0].axiskeys == info_1.axiskeys and edited_infos[1].axiskeys == info_2.axiskeys


def test_immediate_accept_does_not_change_values(qtbot, png_image, image_zyxc_stack_path, empty_project_file):
    info_1 = FilesystemDatasetInfo(filePath=str(png_image), normalizeDisplay=False, project_file=empty_project_file)
    info_2 = FilesystemDatasetInfo(
        filePath=str(image_zyxc_stack_path),
        project_file=empty_project_file,
        sequence_axis="z",
        normalizeDisplay=True,
        drange=(56, 78),
    )
    project_file_dir = str(Path(png_image).parent)

    widget = create_and_modify_widget(qtbot, [info_1, info_2], project_file=empty_project_file)
    edited_infos = accept_widget(qtbot, widget)

    assert info_1.axiskeys == edited_infos[0].axiskeys == "yxc"
    assert info_2.axiskeys == edited_infos[1].axiskeys == "zyxc"

    assert info_1.normalizeDisplay == edited_infos[0].normalizeDisplay == False
    assert info_2.normalizeDisplay == edited_infos[1].normalizeDisplay == True
    assert info_2.drange == edited_infos[1].drange == (56, 78)


def test_too_few_axeskeys_shows_error(qtbot, image_yxc_fs_info, empty_project_file):
    widget = create_and_modify_widget(qtbot, [image_yxc_fs_info], empty_project_file, axiskeys="xy")
    assert widget.axes_error_display.text() != ""


def test_garbled_axeskeys_shows_error(qtbot, image_yxc_fs_info, empty_project_file):
    widget = create_and_modify_widget(qtbot, [image_yxc_fs_info], empty_project_file, axiskeys="ab")
    assert widget.axes_error_display.text() != ""


def test_repeated_axeskeys_shows_error(qtbot, image_yxc_fs_info, empty_project_file):
    widget = create_and_modify_widget(qtbot, [image_yxc_fs_info], empty_project_file, axiskeys="yy")
    assert widget.axes_error_display.text() != ""


def test_switch_to_project_internal_saves_data_to_project(qtbot, image_yxc_fs_info, empty_project_file):
    widget = create_and_modify_widget(
        qtbot, infos=[image_yxc_fs_info], project_file=empty_project_file, location=ProjectInternalDatasetInfo
    )
    new_info = accept_widget(qtbot, widget)[0]
    assert new_info.inner_path in empty_project_file


def test_switch_from_absolute_to_relative(qtbot, image_yxc_fs_info, empty_project_file):
    widget = create_and_modify_widget(
        qtbot, infos=[image_yxc_fs_info], project_file=empty_project_file, location=RelativeFilesystemDatasetInfo
    )
    new_info = accept_widget(qtbot, widget)[0]
    assert isinstance(new_info, RelativeFilesystemDatasetInfo)
    relative_path = Path(image_yxc_fs_info.filePath).relative_to(Path(empty_project_file.filename).parent)
    assert new_info.effective_path == str(relative_path)


def test_modify_project_internal_datasetinfo(qtbot, image_yxc_fs_info, empty_project_file):
    widget = create_and_modify_widget(
        qtbot, infos=[image_yxc_fs_info], project_file=empty_project_file, location=ProjectInternalDatasetInfo
    )
    new_info = accept_widget(qtbot, widget)[0]
    assert isinstance(new_info, ProjectInternalDatasetInfo)
    assert new_info.inner_path in empty_project_file

    widget = create_and_modify_widget(
        qtbot, infos=[new_info], project_file=empty_project_file, display_mode="grayscale"
    )
    new_info = accept_widget(qtbot, widget)[0]

    assert isinstance(new_info, ProjectInternalDatasetInfo)
    assert new_info.display_mode == "grayscale"


def test_modify_axistags_in_stack(qtbot, png_image, another_png_image, empty_project_file):
    info = FilesystemDatasetInfo(filePath=str(png_image) + os.path.pathsep + str(another_png_image), sequence_axis="t")
    widget = create_and_modify_widget(qtbot, infos=[info], project_file=empty_project_file, axiskeys="zxyc")
    new_info = accept_widget(qtbot, widget)[0]
    assert new_info.axiskeys == "zxyc"

    widget2 = create_and_modify_widget(
        qtbot, infos=[new_info], project_file=empty_project_file, axiskeys="txyc", location=ProjectInternalDatasetInfo
    )
    new_info2 = accept_widget(qtbot, widget2)[0]
    assert new_info2.axiskeys == "txyc"
