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
from PyQt5.QtCore import Qt

from ilastik.applets.dataSelection.datasetInfoEditorWidget import DatasetInfoEditorWidget
from ilastik.applets.dataSelection import DatasetInfo


def download_test_image(url, suffix:str):
    resp = requests.get(url)
    _, image_path = tempfile.mkstemp(suffix='-' + suffix)
    with open(image_path, 'wb') as f:
        f.write(resp.content)
    return image_path

@pytest.fixture(scope='function')
def image_yxc_path():
    path =  download_test_image("http://data.ilastik.org/pixel-classification/2d/c_cells_1.png", "c_cells_1.png")
    yield path
    os.remove(path)

@pytest.fixture(scope='function')
def image_yxc_info(image_yxc_path):
    return DatasetInfo(filepath=image_yxc_path)

@pytest.fixture(scope='function')
def another_image_yxc_path():
    path =  download_test_image("http://data.ilastik.org/pixel-classification/2d/c_cells_2.png", "c_cells_2.png")
    yield path
    os.remove(path)

@pytest.fixture(scope='function')
def image_zyxc_stack_path(image_yxc_path, another_image_yxc_path):
    return image_yxc_path + os.path.pathsep + another_image_yxc_path

@pytest.fixture
def empty_project_file() -> h5py.File:
    return h5py.File(tempfile.mkstemp()[1], 'r+')

DONT_SET_NORMALIZE = object()

def create_and_modify_widget(
    qtbot,
    infos:List[DatasetInfo],
    project_file:h5py.File,
    nickname:str=None,
    axiskeys:str='',
    normalizeDisplay:bool=DONT_SET_NORMALIZE,
    drange:Tuple[Number, Number]=None,
    display_mode:str=None,
    location:DatasetInfo.Location=None
):
    widget = DatasetInfoEditorWidget(None, infos, project_file)
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

def accept_widget(qtbot, widget:DatasetInfoEditorWidget) -> List[DatasetInfo]:
    qtbot.mouseClick(widget.okButton, Qt.LeftButton)
    return widget.edited_infos

def test_datasetinfo_editor_widget_shows_correct_data_on_single_info(qtbot, image_yxc_path, empty_project_file):
    info = DatasetInfo(filepath=image_yxc_path, project_file=empty_project_file)
    assert info.axiskeys == 'yxc'
    assert info.laneDtype == numpy.uint8
    assert info.laneShape == (520, 697, 3)

    editor_widget = DatasetInfoEditorWidget(None, [info], empty_project_file)
    qtbot.addWidget(editor_widget)
    editor_widget.show()

    assert editor_widget.axesEdit.maxLength() == 3
    assert "".join(tag.key for tag in editor_widget.get_new_axes_tags()) == 'yxc'
    assert editor_widget.nicknameEdit.text() == Path(image_yxc_path).stem
    assert editor_widget.nicknameEdit.isEnabled()
    assert editor_widget.normalizeDisplayComboBox.isVisible()
    assert editor_widget.storageComboBox.isVisible()

    edited_info = accept_widget(qtbot, editor_widget)[0]
    assert editor_widget.edited_infos[0].axistags == info.axistags

def test_datasetinfo_editor_widget_modifies_single_info(qtbot, image_yxc_path, empty_project_file):
    info = DatasetInfo(filepath=image_yxc_path, project_file=empty_project_file)
    widget = create_and_modify_widget(qtbot,
                                      [info],
                                      project_file=empty_project_file,
                                      nickname="SOME_NICKNAME",
                                      axiskeys="xyc",
                                      normalizeDisplay=True,
                                      drange=(10,20),
                                      display_mode="alpha-modulated",
                                      location=DatasetInfo.Location.FileSystemRelativePath)
    edited_info = accept_widget(qtbot, widget)[0]
    assert edited_info.axiskeys == "xyc"
    assert edited_info.nickname == "SOME_NICKNAME"
    assert edited_info.normalizeDisplay == True
    assert edited_info.drange == (10, 20)
    assert edited_info.display_mode == 'alpha-modulated'
    assert edited_info.location == DatasetInfo.Location.FileSystemRelativePath
    assert edited_info.filePath == str(Path(image_yxc_path).absolute())

def test_datasetinfo_editor_widget_shows_correct_data_on_multiple_info(qtbot, image_yxc_path, another_image_yxc_path, empty_project_file):
    info = DatasetInfo(filepath=image_yxc_path, project_file=empty_project_file)
    info_2 = DatasetInfo(filepath=another_image_yxc_path, project_file=empty_project_file)

    widget = create_and_modify_widget(qtbot=qtbot,
                                     infos=[info, info_2],
                                     project_file=empty_project_file)

    assert widget.axesEdit.maxLength() == 3
    assert "".join(tag.key for tag in widget.get_new_axes_tags()) == 'yxc'
    assert not widget.nicknameEdit.isEnabled()
    assert widget.nicknameEdit.text() == Path(image_yxc_path).stem + ', ' + Path(another_image_yxc_path).stem

def test_datasetinfo_editor_widget_shows_edits_data_on_multiple_infos_with_same_dimensionality(qtbot, image_yxc_path, another_image_yxc_path, empty_project_file):
    info_1 = DatasetInfo(filepath=image_yxc_path, project_file=empty_project_file)
    info_2 = DatasetInfo(filepath=another_image_yxc_path, project_file=empty_project_file)
    project_file_dir = str(Path(image_yxc_path).parent)

    widget = create_and_modify_widget(qtbot,
                                     [info_1, info_2],
                                     project_file=empty_project_file,
                                     axiskeys='cxy',
                                     display_mode='binary-mask',
                                     normalizeDisplay=True,
                                     drange=(20,40))

    edited_infos = accept_widget(qtbot, widget)
    assert all(info.axiskeys == 'cxy' for info in edited_infos)
    assert all(info.display_mode == 'binary-mask' for info in edited_infos)
    assert all(info.normalizeDisplay == True for info in edited_infos)
    assert all(info.drange == (20,40) for info in edited_infos)

def test_cannot_edit_axis_tags_on_images_of_different_dimensionality(qtbot, image_yxc_path, image_zyxc_stack_path, empty_project_file):
    info_1 = DatasetInfo(filepath=image_yxc_path)
    info_2 = DatasetInfo(filepath=image_zyxc_stack_path, sequence_axis="z")

    widget = create_and_modify_widget(qtbot, [info_1, info_2], project_file=empty_project_file)
    assert not widget.axesEdit.isEnabled()

    edited_infos = accept_widget(qtbot, widget)
    assert edited_infos[0].axiskeys == info_1.axiskeys  and edited_infos[1].axiskeys == info_2.axiskeys

def test_immediate_accept_does_not_change_values(qtbot, image_yxc_path, image_zyxc_stack_path, empty_project_file):
    info_1 = DatasetInfo(filepath=image_yxc_path,
                         normalizeDisplay=False)
    info_2 = DatasetInfo(filepath=image_zyxc_stack_path,
                         sequence_axis="z",
                         normalizeDisplay=True,
                         drange=(56, 78))
    project_file_dir = str(Path(image_yxc_path).parent)

    widget = create_and_modify_widget(qtbot, [info_1, info_2], project_file=empty_project_file)
    edited_infos = accept_widget(qtbot, widget)

    assert info_1.axiskeys == edited_infos[0].axiskeys == "yxc"
    assert info_2.axiskeys == edited_infos[1].axiskeys == "zyxc"

    assert info_1.normalizeDisplay == edited_infos[0].normalizeDisplay == False
    assert info_2.normalizeDisplay == edited_infos[1].normalizeDisplay == True
    assert info_2.drange == edited_infos[1].drange == (56, 78)


def test_too_few_axeskeys_shows_error(qtbot, image_yxc_info, empty_project_file):
    widget = create_and_modify_widget(qtbot, [image_yxc_info], empty_project_file, axiskeys="xy")
    assert widget.axes_error_display.text() != ''

def test_garbled_axeskeys_shows_error(qtbot, image_yxc_info):
    widget = create_and_modify_widget(qtbot, [image_yxc_info], empty_project_file, axiskeys="ab")
    assert widget.axes_error_display.text() != ''

def test_repeated_axeskeys_shows_error(qtbot, image_yxc_info):
    widget = create_and_modify_widget(qtbot, [image_yxc_info], empty_project_file, axiskeys="yy")
    assert widget.axes_error_display.text() != ''
