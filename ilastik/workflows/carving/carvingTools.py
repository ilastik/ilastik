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


def simple_parallel_ws(data, block_shape=None, max_workers=None, reduce_to=0.2, size_regularizer=0.5):
    if max_workers is None:
        max_workers = cpu_count()

    logger.info(f"blockwise watershed with {max_workers} threads.")
    overseg, _ = parallel_watershed(data=data, block_shape=block_shape, max_workers=max_workers)

    logger.info("grid rag")
    rag = nifty.graph.rag.gridRag(overseg,
                                  numberOfThreads=max_workers)
    logger.info("rag: %s"%str(rag))
    n_nodes = rag.numberOfNodes

    shape = data.shape
    ndim = len(shape)
    if block_shape is None:
        block_shape  = [100]*ndim

    data = numpy.require(data,dtype='float32')
    logger.info("accumulate along boundaries")
    edge_features, node_features = nifty.graph.rag.accumulateMeanAndLength(
        rag=rag, data=numpy.require(data,dtype='float32'),
        blockShape=list(block_shape),
        numberOfThreads=int(max_workers), saveMemory=True)

    meanEdgeStrength = edge_features[:,0]
    edgeSizes = edge_features[:,1]
    nodeSizes = node_features[:,1]


    node_features[:] = 1
    n_stop = reduce_to * n_nodes

    clusterPolicy = nifty.graph.agglo.nodeAndEdgeWeightedClusterPolicy(
        graph=rag, edgeIndicators=meanEdgeStrength,
        nodeFeatures=node_features,
        edgeSizes=edgeSizes,
        nodeSizes=nodeSizes,
        beta=0.0, numberOfNodesStop=n_stop,
        sizeRegularizer=size_regularizer)

    logger.info("run clustering")
    # run agglomerative clustering
    agglomerativeClustering = nifty.graph.agglo.agglomerativeClustering(clusterPolicy)
    agglomerativeClustering.run(True, 10000)
    nodeSeg = agglomerativeClustering.result()


    nodeSeg = numpy.require(nodeSeg, dtype='int64')
    nodeSeg -=(nodeSeg.min())
    nodeSeg += 1



    comp = nifty.graph.components(rag)
    comp.buildFromNodeLabels(nodeSeg)
    nodeSeg = comp.componentLabels()+1

    logger.info("project back")
    # convert graph segmentation
    # to pixel segmentation

    seg = nifty.graph.rag.projectScalarNodeDataToPixels(rag, nodeSeg,
                                                        numberOfThreads=max_workers)



    seg -= seg.min()
    seg += 1

    #seg = vigra.analysis.labelVolume(seg.astype('uint32'))
    logger.info("agglomerative supervoxel creation is done")
    return seg
