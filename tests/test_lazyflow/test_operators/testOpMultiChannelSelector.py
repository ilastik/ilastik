from lazyflow.operators import OpMultiChannelSelector
import numpy
import vigra

import pytest


@pytest.fixture
def random_data_5c():
    data = numpy.random.randint(0, 256, (10, 5, 5), dtype="uint8")
    return vigra.taggedView(data, "yxc")


def test_raises_channel_not_last(graph):
    data = numpy.random.randint(0, 256, (10, 5, 1), dtype="uint8")
    vdata = vigra.taggedView(data, "yxz")
    op = OpMultiChannelSelector(graph=graph)
    with pytest.raises(ValueError):
        op.Input.setValue(vdata)


def test_raises_selected_channel_not_in_data(graph):
    data = numpy.random.randint(0, 256, (10, 5, 1), dtype="uint8")
    vdata = vigra.taggedView(data, "yxc")

    op = OpMultiChannelSelector(graph=graph)
    op.Input.setValue(vdata)
    with pytest.raises(ValueError):
        op.SelectedChannels.setValue([1])


def test_trivial_operation(graph):
    data = numpy.random.randint(0, 256, (10, 5, 1), dtype="uint8")
    vdata = vigra.taggedView(data, "yxc")

    op = OpMultiChannelSelector(graph=graph)
    op.Input.setValue(vdata)
    op.SelectedChannels.setValue([0])

    output = op.Output[()].wait()

    numpy.testing.assert_array_equal(output, data)


@pytest.mark.parametrize(
    "selected_channel",
    [
        0,
        1,
        2,
        3,
        4,
    ],
)
def test_get_single_channel(graph, selected_channel, random_data_5c):

    op = OpMultiChannelSelector(graph=graph)
    op.Input.setValue(random_data_5c)
    op.SelectedChannels.setValue([selected_channel])

    output = op.Output[()].wait()

    numpy.testing.assert_array_equal(output, random_data_5c[..., (selected_channel,)])


def test_selected_channel_change(graph, random_data_5c):
    selected_channels = range(1, 5)

    is_dirty = False

    def set_dirty(*args, **kwargs):
        nonlocal is_dirty
        assert not is_dirty
        is_dirty = True

    op = OpMultiChannelSelector(graph=graph)
    op.Input.setValue(random_data_5c)
    # no change expected as its the default value
    op.SelectedChannels.setValue([0])

    assert not is_dirty

    for selected_channel in selected_channels:
        is_dirty = True
        op.SelectedChannels.setValue([selected_channel])
        assert is_dirty

        output = op.Output[()].wait()
        numpy.testing.assert_array_equal(output, random_data_5c[..., (selected_channel,)])


@pytest.mark.parametrize(
    "selected_channels",
    [
        (0, 1, 2, 3, 4),
        (1, 2),
        (2, 4),
        (5, 2),
        (3, 2, 4),
    ],
)
def test_select_multi_channels(graph, selected_channels, random_data_5c):
    selected_channels = (2, 4)
    op = OpMultiChannelSelector(graph=graph)
    op.SelectedChannels.setValue(selected_channels)
    op.Input.setValue(random_data_5c)

    output = op.Output[()].wait()
    numpy.testing.assert_array_equal(output, random_data_5c[..., selected_channels])
