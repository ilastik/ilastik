import warnings

import numpy as np

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedArrayCache, OpValueCache
from lazyflow.utility import Timer

import nifty
from elf.segmentation.multicut import get_multicut_solver, get_available_solver_names

from .multicutLegacy import LEGACY_SOLVER_NAMES, legacy_nifty_fm_greedy_solver


import logging

logger = logging.getLogger(__name__)

DEFAULT_SOLVER_NAME = "kernighan-lin"

AVAILABLE_SOLVER_NAMES = list(get_available_solver_names()) + [DEFAULT_SOLVER_NAME]


class OpMulticut(Operator):
    Beta = InputSlot(value=0.5)
    SolverName = InputSlot(value=DEFAULT_SOLVER_NAME)
    FreezeCache = InputSlot(value=True)
    ProbabilityThreshold = InputSlot(value=0.5)

    Rag = InputSlot()  # value slot.  Rag object.
    Superpixels = InputSlot()
    EdgeProbabilities = InputSlot()
    # A dict of id_pair -> probabilities (used by the GUI)
    EdgeProbabilitiesDict = InputSlot()
    RawData = InputSlot(optional=True)  # Used by the GUI for display only

    Output = OutputSlot()  # Pixelwise output (not RAG, etc.)
    EdgeLabelDisagreementDict = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpMulticut, self).__init__(*args, **kwargs)

        self.opMulticutAgglomerator = OpMulticutAgglomerator(parent=self)
        self.opMulticutAgglomerator.Beta.connect(self.Beta)
        self.opMulticutAgglomerator.SolverName.connect(self.SolverName)
        self.opMulticutAgglomerator.Rag.connect(self.Rag)
        self.opMulticutAgglomerator.EdgeProbabilities.connect(self.EdgeProbabilities)
        self.opMulticutAgglomerator.ProbabilityThreshold.connect(self.ProbabilityThreshold)

        self.opNodeLabelsCache = OpValueCache(parent=self)
        self.opNodeLabelsCache.fixAtCurrent.connect(self.FreezeCache)
        self.opNodeLabelsCache.Input.connect(self.opMulticutAgglomerator.NodeLabels)
        self.opNodeLabelsCache.name = "opNodeLabelCache"

        self.opRelabel = OpProjectNodeLabeling(parent=self)
        self.opRelabel.Superpixels.connect(self.Superpixels)
        self.opRelabel.NodeLabels.connect(self.opNodeLabelsCache.Output)

        self.opDisagreement = OpEdgeLabelDisagreementDict(parent=self)
        self.opDisagreement.Rag.connect(self.Rag)
        self.opDisagreement.NodeLabels.connect(self.opNodeLabelsCache.Output)
        self.opDisagreement.EdgeProbabilities.connect(self.EdgeProbabilities)
        self.EdgeLabelDisagreementDict.connect(self.opDisagreement.EdgeLabelDisagreementDict)

        self.opSegmentationCache = OpBlockedArrayCache(parent=self)
        self.opSegmentationCache.fixAtCurrent.connect(self.FreezeCache)
        self.opSegmentationCache.Input.connect(self.opRelabel.Output)
        self.Output.connect(self.opSegmentationCache.Output)

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Unknown or unconnected output slot: {}".format(slot)

    def propagateDirty(self, slot, subindex, roi):
        pass


class OpProjectNodeLabeling(Operator):
    Superpixels = InputSlot()
    NodeLabels = InputSlot()  # 1D array, mapping superpixels to segment labels

    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Superpixels.meta)
        self.Output.meta.display_mode = "random-colortable"

    def execute(self, slot, subindex, roi, result):
        mapping_index_array = self.NodeLabels.value
        self.Superpixels(roi.start, roi.stop).writeInto(result).wait()
        result[:] = mapping_index_array[result]

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.Superpixels:
            self.Output.setDirty(roi.start, roi.stop)
        else:
            self.Output.setDirty()


class OpEdgeLabelDisagreementDict(Operator):
    Rag = InputSlot()
    NodeLabels = InputSlot()
    EdgeProbabilities = InputSlot()

    EdgeLabelDisagreementDict = OutputSlot()

    def setupOutputs(self):
        self.EdgeLabelDisagreementDict.meta.shape = (1,)
        self.EdgeLabelDisagreementDict.meta.dtype = object

    def execute(self, slot, subindex, roi, result):
        node_labels = self.NodeLabels.value
        if node_labels is None:
            # This can happen when the cache doesn't have data yet.
            result[0] = {}
            return

        edge_probabilities = self.EdgeProbabilities.value
        if edge_probabilities is None:
            # This can happen when the cache doesn't have data yet.
            result[0] = {}
            return

        rag = self.Rag.value
        edge_ids = rag.edge_ids

        # 0: edge is "inactive", nodes belong to the same segment
        # 1: edge is "active", nodes belong to separate segments
        edge_labels_from_nodes = (node_labels[rag.edge_ids[:, 0]] != node_labels[rag.edge_ids[:, 1]]).view(np.uint8)
        edge_labels_from_probabilities = edge_probabilities > 0.5

        conflicts = np.where(edge_labels_from_nodes != edge_labels_from_probabilities)
        conflict_edge_ids = edge_ids[conflicts]
        conflict_labels = edge_labels_from_nodes[conflicts]
        result[0] = dict(zip(map(tuple, conflict_edge_ids), conflict_labels))

    def propagateDirty(self, slot, subindex, roi):
        self.EdgeLabelDisagreementDict.setDirty()


class OpMulticutAgglomerator(Operator):
    SolverName = InputSlot()
    Beta = InputSlot()
    ProbabilityThreshold = InputSlot()

    Rag = InputSlot()
    EdgeProbabilities = InputSlot()
    NodeLabels = OutputSlot()  # 1D array, mapping superpixels to segment labels

    def setupOutputs(self):
        self.NodeLabels.meta.shape = (1,)
        self.NodeLabels.meta.dtype = object

    def execute(self, slot, subindex, roi, result):
        rag = self.Rag.value
        beta = self.Beta.value
        solver_name = self.SolverName.value
        edge_probabilities = self.EdgeProbabilities.value
        if edge_probabilities is None:
            # No probabilities cached yet. Merge everything
            result[0] = np.zeros((rag.max_sp + 1,), dtype=np.uint32)
            return

        with Timer() as timer:
            node_labeling = self.agglomerate_with_multicut(
                rag, edge_probabilities, beta, solver_name, self.ProbabilityThreshold.value
            )

        logger.info("'{}' Multicut took {} seconds".format(solver_name, timer.seconds()))

        # FIXME: Is it okay to produce 0-based supervoxels?
        # node_labeling[:] += 1 # RAG labels are 0-based, but we want 1-based

        result[0] = node_labeling

    def propagateDirty(self, slot, subindex, roi):
        self.NodeLabels.setDirty()

    @classmethod
    def agglomerate_with_multicut(cls, rag, edge_probabilities, beta, solver_name, threshold):
        """
        rag: ilastikrag.Rag

        edge_probabilities: 1D array, same order as rag.edge_ids.
                            Should indicate probability of each edge being ON.

        beta: The multicut 'beta' parameter (0.0 < beta < 1.0)

        solver_name: The multicut solver used. Format: library_solver (e.g. nifty_Exact)

        Returns: An index array [0,1,...,N] indicating the new labels for the N nodes of the RAG.
        """
        #
        # Check parameters
        #
        assert rag.edge_ids.shape == (rag.num_edges, 2)
        node_count = rag.max_sp + 1
        #
        # Solve
        #
        edge_weights = compute_edge_weights(rag.edge_ids, edge_probabilities, beta, threshold)
        assert edge_weights.shape == (rag.num_edges,)

        mapping_index_array = solve(rag.edge_ids, edge_weights, node_count, solver_name)

        return mapping_index_array


def compute_edge_weights(edge_ids, edge_probabilities, beta, threshold):
    """
    Convert edge probabilities to energies for the multicut problem.

    edge_ids:
        The list of edges in the graph. shape=(N, 2)
    edge_probabilities:
        1-D, float (1.0 means edge is CUT, disconnecting the two SPs)
    beta:
        scalar (float)
    threshold:
        scalar (float), moves the 0 of the edge weights (default threshold = 0.5)

    Special behavior:
        If any node has ID 0, all of it's edges will be given an
        artificially low energy, to prevent it from merging with its
        neighbors, regardless of what the edge_probabilities say.
    """

    def rescale(probabilities, threshold):
        """
        Given a threshold in the range (0,1), rescales the probabilities below and above
        the threshold to the ranges (0,0.5], and (0.5,1) respectively. This is needed
        to implement an effective 'moving' of the 0 weight, since the multicut algorithm
        implicitly calculates that weights change sign at p=0.5.

        :param probabilities: 1d array (float). Probability data within range (0,1)
        :param threshold: scalar (float). The new threshold for the algorithm.
        :return: Rescaled data to be used in algorithm.
        """
        out = np.zeros_like(probabilities)
        data_lower = probabilities[probabilities <= threshold]
        data_upper = probabilities[probabilities > threshold]

        data_lower = (data_lower / threshold) * 0.5
        data_upper = (((data_upper - threshold) / (1 - threshold)) * 0.5) + 0.5

        out[probabilities <= threshold] = data_lower
        out[probabilities > threshold] = data_upper
        return out

    p1 = edge_probabilities  # P(Edge=CUT)
    p1 = np.clip(p1, 0.001, 0.999)
    p1 = rescale(p1, threshold)
    p0 = 1.0 - p1  # P(Edge=NOT CUT)

    edge_weights = np.log(p0 / p1) + np.log((1 - beta) / beta)

    # See note special behavior, above
    edges_touching_zero = edge_ids[:, 0] == 0
    if edges_touching_zero.any():
        logger.warning("Volume contains label 0, which will be excluded from the segmentation.")
        MINIMUM_ENERGY = -1000.0
        edge_weights[edges_touching_zero] = MINIMUM_ENERGY

    return edge_weights


def solve(edge_ids, edge_weights, node_count, solver_method):
    """
    Solve the given multicut problem with the 'Nifty' library and return an
    index array that maps node IDs to segment IDs.

    edge_ids: The list of edges in the graph. shape=(N, 2)

    edge_weights: Edge energies. shape=(N,)

    node_count: Number of nodes in the model.
                Note: Must be greater than the max ID found in edge_ids.
                      If your superpixel IDs are not consecutive, node_count should be max_sp_id+1

    solver_method: see elf.segmentation.multicut.get_available_solver_names, also still supporting
                   NIFTY_FmGreedy, the previous default solver.
    """
    logging.debug(f"Using multicut solver {solver_method}")
    if solver_method in get_available_solver_names():
        solver = get_multicut_solver(solver_method)
    elif solver_method == "Nifty_FmGreedy":
        # for backwards compatibility:
        warnings.warn(
            f"Using legacy multicut {solver_method}. This is only expected in debug mode or with old project files."
        )
        solver = legacy_nifty_fm_greedy_solver
    elif solver_method in LEGACY_SOLVER_NAMES:
        ValueError(
            f"Multicut solver method {solver_method} not supported anymore. Please run the project in ilastik 1.3.3post3, or change the solver method in debug mode."
        )
    else:
        raise ValueError(f"Unsupported multicut solver method {solver_method}")

    g = nifty.graph.UndirectedGraph(int(node_count))
    g.insertEdges(edge_ids)

    ret = solver(g, edge_weights)
    mapping_index_array = ret.astype(np.uint32)
    return mapping_index_array
