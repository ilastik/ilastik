import pytest
from hytra.core.hypothesesgraph import HypothesesGraph
from hytra.core.probabilitygenerator import Traxel
from ilastik.applets.tracking.structured.opStructuredTracking import (
    OpStructuredTracking,
)


@pytest.fixture
def tracklet_graph():
    #               /  2   4
    #      0  ->  1       /
    #               \  3  division
    #                     \
    #                      5
    #
    # t:   0      1    2    3
    h = HypothesesGraph()
    h._graph.add_path([(0, 0), (1, 1), (2, 2)])
    h._graph.add_path([(1, 1), (2, 3), (3, 4)])
    h._graph.add_path([(2, 3), (3, 5)])
    for n in h._graph.nodes:
        h._graph.nodes[n]["id"] = n[1]
        h._graph.nodes[n]["traxel"] = Traxel()
        h._graph.nodes[n]["traxel"].Id = n[1]
        h._graph.nodes[n]["traxel"].Timestep = n[0]

    return h


@pytest.fixture
def annotations():
    """
        labels: {timeframe: {object_id: set(track_ids)}}
        divisions: {parent_track_id: ([child_track_id1, child_track_id2], timeframe)}
    """
    annotations = {
        "labels": {
            0: {0: {1, 2}},
            1: {1: {1, 2}},
            2: {2: {1}, 3: {2}},
            3: {4: {3}, 5: {4}},
        },
        "divisions": {2: ([3, 4], 2)},
    }
    return annotations


class InstantTraxel(Traxel):
    """Convenience, instantiate Traxel with timestep and id, add __eq__"""

    def __init__(self, timestep, uid):
        super().__init__()
        self.Timestep = timestep
        self.Id = uid

    def __eq__(self, other):
        if not isinstance(other, Traxel):
            return False
        if self.Timestep == other.Timestep:
            if self.Id == other.Id:
                return True

        return False


def test_annotations_insertion(tracklet_graph, annotations):
    """reproduces ilastik/#2052"""
    expected = {
        "nodes": {
            (0, 0): {
                "id": 0,
                "traxel": InstantTraxel(timestep=0, uid=0),
                "value": 2,
                "divisionValue": False,
            },
            (1, 1): {
                "id": 1,
                "traxel": InstantTraxel(timestep=1, uid=1),
                "value": 2,
                "divisionValue": False,
            },
            (2, 2): {
                "id": 2,
                "traxel": InstantTraxel(timestep=2, uid=2),
                "value": 1,
                "divisionValue": False,
            },
            (2, 3): {
                "id": 3,
                "traxel": InstantTraxel(timestep=2, uid=3),
                "value": 1,
                "divisionValue": True,
            },
            (3, 4): {
                "id": 4,
                "traxel": InstantTraxel(timestep=3, uid=4),
                "value": 1,
                "divisionValue": False,
            },
            (3, 5): {
                "id": 5,
                "traxel": InstantTraxel(timestep=3, uid=5),
                "value": 1,
                "divisionValue": False,
            },
        },
        "edges": {
            ((0, 0), (1, 1)): {"value": 2, "gap": 1},
            ((1, 1), (2, 2)): {"value": 1, "gap": 1},
            ((1, 1), (2, 3)): {"value": 1, "gap": 1},
            ((2, 3), (3, 4)): {"value": 1, "gap": 1},
            ((2, 3), (3, 5)): {"value": 1, "gap": 1},
        },
    }

    annotated_graph = OpStructuredTracking.insertAnnotationsToHypothesesGraph(
        tracklet_graph, annotations
    )

    assert annotated_graph._graph.number_of_edges() == len(expected["edges"])
    for edge in annotated_graph._graph.edges:
        assert edge in expected["edges"]
        assert annotated_graph._graph.edges[edge] == expected["edges"][edge]

    assert annotated_graph._graph.number_of_nodes() == len(expected["nodes"])
    for node in annotated_graph._graph.nodes:
        assert node in expected["nodes"]
        assert annotated_graph._graph.nodes[node] == expected["nodes"][node]


def test_annotation_mismatch_raises(tracklet_graph, annotations):
    # add annotations that is not represented in the graph:
    annotations['labels'][3][4] = {1, 3}
    with pytest.raises(AssertionError):
        OpStructuredTracking.insertAnnotationsToHypothesesGraph(
            tracklet_graph, annotations
        )
