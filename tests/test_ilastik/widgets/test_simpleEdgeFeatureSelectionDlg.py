import pytest
from PyQt5.QtCore import Qt

from ilastik.applets.edgeTraining.simpleEdgeFeatSelection import FeatureGroup, SimpleEdgeFeatureSelection


def test_to_feature_dict():
    state_dict = {
        "group 1": {"state": False, "features": {"ch 1": ["grp1_ch1_f1", "grp1_f2", "grp1_f3"]}},
        "group 2": {"state": True, "features": {"ch 2": ["grp2_ch2_f1", "grp2_ch2_f2", "grp2_ch2_f3"]}},
        "group 3": {"state": True, "features": {"ch 1": ["grp3_ch1_f1"], "ch 2": ["grp3_ch2_f1"]}},
    }

    assert SimpleEdgeFeatureSelection._to_feature_dict(state_dict) == {
        "ch 1": ["grp3_ch1_f1"],
        "ch 2": ["grp2_ch2_f1", "grp2_ch2_f2", "grp2_ch2_f3", "grp3_ch2_f1"],
    }


def test_defaultFeaturesStateDict():
    state_dict = SimpleEdgeFeatureSelection._defaultFeaturesStateDict(["raw_data"], ["edge_data"], data_is_3d=False)

    assert all(x in state_dict for x in FeatureGroup)
    assert "edgeregion_edge_regionradii_2" not in state_dict[FeatureGroup.shape]["features"]["edge_data"]

    state_dict = SimpleEdgeFeatureSelection._defaultFeaturesStateDict(["raw_data"], ["edge_data"], data_is_3d=True)

    assert all(x in state_dict for x in FeatureGroup)
    assert "edgeregion_edge_regionradii_2" in state_dict[FeatureGroup.shape]["features"]["edge_data"]


@pytest.fixture
def supported_features():
    return [
        "edgeregion_edge_area",
        "edgeregion_edge_regionradii_0",
        "edgeregion_edge_regionradii_1",
        "edgeregion_edge_test" "standard_edge_mean",
        "standard_edge_quantiles_10",
        "standard_edge_quantiles_90",
        "standard_edge_test",
        "standard_sp_mean",
        "standard_sp_quantiles_10",
        "standard_sp_quantiles_90",
        "standard_sp_test",
    ]


@pytest.mark.parametrize(
    "selection, expected_groups",
    [
        ({}, []),
        ({"boundary_data": ["edgeregion_edge_regionradii_0", "edgeregion_edge_regionradii_1"]}, [FeatureGroup.shape]),
        (
            {
                "boundary_data": [
                    "edgeregion_edge_regionradii_0",
                    "edgeregion_edge_regionradii_1",
                    "standard_sp_mean",
                    "standard_sp_quantiles_10",
                    "standard_sp_quantiles_90",
                ]
            },
            [FeatureGroup.shape, FeatureGroup.boundary_sp],
        ),
        (
            {
                "raw_data": [
                    "standard_sp_mean",
                    "standard_sp_quantiles_10",
                    "standard_sp_quantiles_90",
                ],
                "boundary_data": [
                    "standard_sp_mean",
                    "standard_sp_quantiles_10",
                    "standard_sp_quantiles_90",
                ],
            },
            [FeatureGroup.boundary_sp, FeatureGroup.raw_sp],
        ),
        (
            {
                "raw_data": [
                    "standard_sp_mean",
                    "standard_sp_quantiles_10",
                    "standard_sp_quantiles_90",
                    "standard_edge_mean",
                    "standard_edge_quantiles_10",
                    "standard_edge_quantiles_90",
                ],
                "boundary_data": [
                    "standard_sp_mean",
                    "standard_sp_quantiles_10",
                    "standard_sp_quantiles_90",
                ],
            },
            [FeatureGroup.boundary_sp, FeatureGroup.raw_sp, FeatureGroup.raw_edge],
        ),
        (
            {
                "raw_data": [],
                "boundary_data": [
                    "edgeregion_edge_regionradii_0",
                    "edgeregion_edge_regionradii_1",
                    "standard_edge_mean",
                    "standard_edge_quantiles_10",
                    "standard_edge_quantiles_90",
                ],
            },
            [FeatureGroup.shape, FeatureGroup.boundary_edge],
        ),
    ],
)
def test_checkmarks(qtbot, supported_features, selection, expected_groups):
    raw_channels = ["raw_data"]
    boundary_channels = ["boundary_data"]

    w = SimpleEdgeFeatureSelection(
        raw_channels=raw_channels,
        boundary_channels=boundary_channels,
        probability_channels=["probability_data"],
        selection=selection,
        supported_features=supported_features,
        data_is_3d=False,
    )

    qtbot.addWidget(w)
    qtbot.waitExposed(w)

    assert w.intensityGroupBox.isEnabled()
    assert w.shapeGroupBox.isEnabled()

    for grp in FeatureGroup:
        assert grp in w.checkboxes, grp
        expected_checkstate = Qt.Checked if grp in expected_groups else Qt.Unchecked
        assert w.checkboxes[grp].checkState() == expected_checkstate, grp


@pytest.mark.parametrize(
    "selection",
    [
        {"raw_data": ["feature_does_not_exist"]},
        {"channel_does_not_exist": ["edgeregion_edge_regionradii_0", "edgeregion_edge_regionradii_1"]},
    ],
)
def test_incompatible_selection(qtbot, supported_features, selection):
    raw_channels = ["raw_data"]
    boundary_channels = ["boundary_data"]

    w = SimpleEdgeFeatureSelection(
        raw_channels=raw_channels,
        boundary_channels=boundary_channels,
        probability_channels=["probability_data"],
        selection=selection,
        supported_features=supported_features,
        data_is_3d=False,
    )

    qtbot.addWidget(w)
    qtbot.waitExposed(w)

    assert not w.intensityGroupBox.isEnabled()
    assert not w.shapeGroupBox.isEnabled()


def test_reset_to_defaults(qtbot, supported_features):
    raw_channels = ["raw_data"]
    boundary_channels = ["boundary_data"]

    w = SimpleEdgeFeatureSelection(
        raw_channels=raw_channels,
        boundary_channels=boundary_channels,
        probability_channels=["probability_data"],
        selection={
            "raw_data": [
                "standard_edge_mean",
                "standard_edge_quantiles_10",
                "standard_edge_quantiles_90",
            ],
        },
        supported_features=supported_features,
        data_is_3d=False,
    )

    qtbot.addWidget(w)
    qtbot.waitExposed(w)

    for grp in FeatureGroup:
        assert grp in w.checkboxes, grp
        expected_checkstate = Qt.Checked if grp == FeatureGroup.raw_edge else Qt.Unchecked
        assert w.checkboxes[grp].checkState() == expected_checkstate, grp

    qtbot.mouseClick(w._resetButton, Qt.MouseButton.LeftButton)

    state_dict = SimpleEdgeFeatureSelection._defaultFeaturesStateDict(
        raw_channels=raw_channels, boundary_channels=boundary_channels, data_is_3d=False
    )

    for grp in state_dict:
        assert grp in w.checkboxes, grp
        expected_checkstate = Qt.Checked if state_dict[grp]["state"] else Qt.Unchecked
        assert w.checkboxes[grp].checkState() == expected_checkstate, grp
