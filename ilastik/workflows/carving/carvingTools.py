from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor

import numpy
import vigra

import nifty
import nifty.tools
import nifty.graph.agglo
import nifty.graph.rag

import logging
logger = logging.getLogger(__name__)


# TODO it would make sense to apply an additional size filter here
def parallel_watershed(data, block_shape=None, halo=None, max_workers=None):
    """ Parallel watershed with hard block boundaries.
    """

    logger.info(f"blockwise watershed with {max_workers} threads.")
    shape = data.shape
    ndim = len(shape)

    # check for None arguments and set to default values
    block_shape = (100,) * ndim if block_shape is None else block_shape
    # NOTE nifty expects a list for the halo parameter although a tuple would be more logical
    halo = [10] * ndim if halo is None else halo
    max_workers = cpu_count() if max_workers is None else max_workers

    # build the nifty blocking object
    roi_begin = (0,) * ndim
    blocking = nifty.tools.blocking(roiBegin=roi_begin, roiEnd=shape, blockShape=block_shape)
    n_blocks = blocking.numberOfBlocks

    # small helper function to cast nifty.tools.Block to a slice
    def to_slicing(block):
        return tuple(slice(b, e) for b, e in zip(block.begin, block.end))

    # initialise the output labels
    labels = numpy.zeros(shape, dtype='int64')

    # watershed for a single block
    def ws_block(block_index):

        # get the block with halo and the slicings corresponding to
        # the block with halo, the block without halo and the
        # block without halo in loocal coordinates
        block = blocking.getBlockWithHalo(blockIndex=block_index, halo=halo)
        inner_slicing = to_slicing(block.innerBlock)
        outer_slicing = to_slicing(block.outerBlock)
        inner_local_slicing = to_slicing(block.innerBlockLocal)

        # perform watershed on the data for the block with halo
        outer_block_data = numpy.require(data[outer_slicing], dtype='float32')
        outer_block_labels, _ = vigra.analysis.watershedsNew(outer_block_data)

        # extract the labels of the inner block and perform connected components
        inner_block_labels = vigra.analysis.labelMultiArray(outer_block_labels[inner_local_slicing])

        # write watershed result to the label array
        labels[inner_slicing] = inner_block_labels

        # return the max-id for this block, that will be used as offset
        return inner_block_labels.max()

    # run the watershed blocks in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [executor.submit(ws_block, block_index) for block_index in range(n_blocks)]
        offsets = numpy.array([t.result() for t in tasks], dtype='int64')

    # compute the block offsets and the max id
    last_max_id = offsets[-1]
    offsets = numpy.roll(offsets, 1)
    offsets[0] = 1
    offsets = numpy.cumsum(offsets)
    # the max_id is the offset of the last block + the max id in the last block
    max_id = last_max_id + offsets[-1]

    # add the offset to blocks to make ids unique
    def add_offset_block(block_index):
        block = to_slicing(blocking.getBlock(block_index))
        labels[block] += offsets[block_index]

    # add offsets in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [executor.submit(add_offset_block, block_index) for block_index in range(n_blocks)]
        [t.result() for t in tasks]

    return labels, max_id


def agglomerate_labels(data, labels, block_shape=None, max_workers=None,
                       reduce_to=0.2, size_regularizer=0.5):
    """ Agglomerate labels based on edge features.
    """

    logger.info("computing region adjacency graph")
    rag = nifty.graph.rag.gridRag(labels, numberOfThreads=max_workers)
    n_nodes = rag.numberOfNodes

    shape = data.shape
    ndim = len(shape)
    block_shape = [100] * ndim if block_shape is None else block_shape
    max_workers = cpu_count() if max_workers is None else max_workers

    logger.info("accumulate edge strength along boundaries")

    # extract edge features over the boundaries and sizes of edges and nodes
    edge_features, node_features = nifty.graph.rag.accumulateMeanAndLength(
        rag=rag, data=numpy.require(data, dtype='float32'),
        blockShape=list(block_shape),
        numberOfThreads=max_workers, saveMemory=True)
    edge_strength = edge_features[:, 0]
    edge_sizes = edge_features[:, 1]
    node_sizes = node_features[:, 1]

    # we don't use node features in the agglomeration,
    # so we set all of them to one
    node_features[:] = 1

    # calculate the number of nodes at which to stop agglomeration
    # = number of nodes times reduction factor
    n_stop = int(reduce_to * n_nodes)

    policy = nifty.graph.agglo.nodeAndEdgeWeightedClusterPolicy(
        graph=rag,
        edgeIndicators=edge_strength,
        edgeSizes=edge_sizes,
        nodeFeatures=node_features,
        nodeSizes=node_sizes,
        beta=0.0,
        numberOfNodesStop=n_stop,
        sizeRegularizer=size_regularizer)

    logger.info("run agglomeration")
    agglomerative_clustering = nifty.graph.agglo.agglomerativeClustering(policy)
    agglomerative_clustering.run(True, 10000)
    node_labels = agglomerative_clustering.result()

    logger.info("project node labels to segmentation")

    # numpy.take throws a memory error for too large inputs
    # nifty.rag has a function to project node labels back to pixels,
    # however in the nifty version used by ilastik it is not exported
    # for the correct combination of datatypes to just use it here.
    # so for now, we compute a new rag with uint32 labels and then use it,
    # only if numpy.take throws a mem error
    try:
        seg = numpy.take(node_labels, labels)
    except MemoryError:
        # TODO expose this for the right combination of dtypes in nifty and then use
        # it by default
        rag2 = nifty.graph.rag.gridRag(labels.astype('uint32'), numberOfThreads=max_workers)
        seg = nifty.graph.rag.projectScalarNodeDataToPixels(rag2, node_labels.astype('uint32'),
                                                            numberOfThreads=max_workers)

    # the ids in the output segmentation need to start at 1, otherwise
    # the graph watershed will fail
    vigra.analysis.relabelConsecutive(seg, start_label=1, keep_zeros=False, out=seg)
    logger.info("agglomerative supervoxel creation is done")
    return numpy.require(seg, dtype='int64')


def watershed_and_agglomerate(data, block_shape=None, max_workers=None,
                              reduce_to=0.2, size_regularizer=0.5):
    """ Run parallel watershed and agglomerate the resulting labels.
    """

    labels, _ = parallel_watershed(data=data, block_shape=block_shape, max_workers=max_workers)
    labels = agglomerate_labels(data, labels, block_shape=block_shape,
                                max_workers=max_workers, reduce_to=reduce_to,
                                size_regularizer=size_regularizer)
    return labels
