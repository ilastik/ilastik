import pytest
from hytra.core.hypothesesgraph import HypothesesGraph
from hytra.core.probabilitygenerator import Traxel
from ilastik.applets.tracking.structured.opStructuredTracking import (
    AnnotationHypothesisgraphMismatchException,
    OpStructuredTracking,
)


@pytest.fixture
def tracklet_graph():
    #               /  2    4
    #      0  ->  1       /
    #               \  3
    #                     \
    #                       5
    #
    #             6 -> 7 -> 8
    #
    # t:   0      1    2    3

    h = HypothesesGraph()
    h._graph.add_path([(0, 0), (1, 1), (2, 2)])
    h._graph.add_path([(1, 1), (2, 3), (3, 4)])
    h._graph.add_path([(2, 3), (3, 5)])
    h._graph.add_path([(1, 6), (2, 7), (3, 8)])
    for n in h._graph.nodes:
        h._graph.nodes[n]["id"] = n[1]
        h._graph.nodes[n]["traxel"] = Traxel()
        h._graph.nodes[n]["traxel"].Id = n[1]
        h._graph.nodes[n]["traxel"].Timestep = n[0]

    return h


@pytest.fixture
def annotations():
    """
    Annotations resulting in the following graph:

                   /  2    4
          0  ->  1        /
                   \  3 =
                          \
                           5

     t:   0      1    2    3

    = denote divisions

    annotations format:
        labels: {timeframe: {object_id: set(track_ids)}}
        divisions: {parent_track_id: ([child_track_id1, child_track_id2], timeframe)}
    """
    annotations = {
        "labels": {0: {0: {1, 2}}, 1: {1: {1, 2}}, 2: {2: {1}, 3: {2}}, 3: {4: {3}, 5: {4}}},
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


@pytest.fixture
def expected():
    expected = {
        "nodes": {
            (0, 0): {"id": 0, "traxel": InstantTraxel(timestep=0, uid=0), "value": 2, "divisionValue": False},
            (1, 1): {"id": 1, "traxel": InstantTraxel(timestep=1, uid=1), "value": 2, "divisionValue": False},
            (2, 2): {"id": 2, "traxel": InstantTraxel(timestep=2, uid=2), "value": 1, "divisionValue": False},
            (2, 3): {"id": 3, "traxel": InstantTraxel(timestep=2, uid=3), "value": 1, "divisionValue": True},
            (3, 4): {"id": 4, "traxel": InstantTraxel(timestep=3, uid=4), "value": 1, "divisionValue": False},
            (3, 5): {"id": 5, "traxel": InstantTraxel(timestep=3, uid=5), "value": 1, "divisionValue": False},
            (1, 6): {"id": 6, "traxel": InstantTraxel(timestep=1, uid=6), "value": 0, "divisionValue": False},
            (2, 7): {"id": 7, "traxel": InstantTraxel(timestep=2, uid=7), "value": 0, "divisionValue": False},
            (3, 8): {"id": 8, "traxel": InstantTraxel(timestep=3, uid=8), "value": 0, "divisionValue": False},
        },
        "edges": {
            ((0, 0), (1, 1)): {"value": 2, "gap": 1},
            ((1, 1), (2, 2)): {"value": 1, "gap": 1},
            ((1, 1), (2, 3)): {"value": 1, "gap": 1},
            ((2, 3), (3, 4)): {"value": 1, "gap": 1},
            ((2, 3), (3, 5)): {"value": 1, "gap": 1},
            ((1, 6), (2, 7)): {"value": 0, "gap": 1},
            ((2, 7), (3, 8)): {"value": 0, "gap": 1},
        },
    }

    return expected


def check_graph(graph, expected):
    assert graph.number_of_edges() == len(expected["edges"])
    for edge in graph.edges:
        assert edge in expected["edges"], f"at {edge!r}"
        assert graph.edges[edge] == expected["edges"][edge], f"at {edge!r}"

    assert graph.number_of_nodes() == len(expected["nodes"])
    for node in graph.nodes:
        assert node in expected["nodes"], f"at {node!r}"
        assert graph.nodes[node] == expected["nodes"][node], f"at {node!r}"


def test_annotations_insertion(tracklet_graph, annotations, expected):
    """reproduces ilastik/#2052"""
    annotated_graph = OpStructuredTracking.insertAnnotationsToHypothesesGraph(tracklet_graph, annotations)
    check_graph(annotated_graph._graph, expected)


def test_annotation_mismatch_raises(tracklet_graph, annotations):
    """add annotations that is not represented in the graph"""
    annotations["labels"][3][4] = {1, 3}
    with pytest.raises(AnnotationHypothesisgraphMismatchException):
        OpStructuredTracking.insertAnnotationsToHypothesesGraph(tracklet_graph, annotations)


def test_annotation_with_misdetection(tracklet_graph, annotations, expected):
    """add some annotations with misdetection:

                     6*-> 7 -> 8*
        * denote misdetections
    """
    annotations["labels"][1][6] = {-1, 5}
    annotations["labels"][2][7] = {5}
    annotations["labels"][3][8] = {-1, 5}

    # modify expected values accordingly:
    expected["nodes"][(2, 7)]["value"] = 1

    annotated_graph = OpStructuredTracking.insertAnnotationsToHypothesesGraph(tracklet_graph, annotations)

    check_graph(annotated_graph._graph, expected)
