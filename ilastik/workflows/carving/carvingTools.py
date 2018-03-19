
import numpy

from multiprocessing import cpu_count
import threading
from concurrent.futures import ThreadPoolExecutor

import vigra

import nifty
import nifty.tools
import nifty.ufd
import nifty.graph.agglo
import nifty.graph.rag

import logging
logger = logging.getLogger(__name__)

# parallel watershed with hard block boarders
def simple_parallel_ws_impl(data, block_shape=None, max_workers=None):
        

    if max_workers is None:
        max_workers = cpu_count()

    labels_lock = threading.Lock()

    shape = data.shape
    ndim = len(shape)
    if block_shape is None:
        block_shape  = tuple([100]*ndim)
    roi_begin = tuple([0]*ndim)
    halo = [10]*ndim
    blocking = nifty.tools.blocking(roiBegin=roi_begin, roiEnd=shape, blockShape=block_shape)
    n_blocks = blocking.numberOfBlocks



    def to_slicing(begin, end):
        return [slice(b,e) for b,e in zip(begin, end)]


    labels = numpy.zeros(shape, dtype='int64')

    global_max_label = [0]
    global_min_label = [None]




    done_blocks = [0]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        for i in range(n_blocks):


            def per_block(block_index):
                
                # get block with halo
                block_with_halo = blocking.getBlockWithHalo(blockIndex=block_index, halo=halo)
                #print(block_with_halo)

                outer_block = block_with_halo.outerBlock
                inner_block = block_with_halo.innerBlock
                inner_block_local = block_with_halo.innerBlockLocal

                # get slicing
                inner_slicing = to_slicing(inner_block.begin, inner_block.end)
                outer_slicing = to_slicing(outer_block.begin, outer_block.end)
                inner_local_slicing = to_slicing(inner_block_local.begin, inner_block_local.end)

                # watershed input for block with margin/halo
                outer_block_data = data[outer_slicing]

                # do vigra watershed
                outer_block_data_vigra = numpy.require(outer_block_data, dtype='float32')
                outer_block_labels_vigra, nseg = vigra.analysis.watershedsNew(outer_block_data_vigra)
                outer_block_labels = outer_block_labels_vigra

                inner_block_labels = outer_block_labels[inner_local_slicing]
                inner_block_labels = vigra.analysis.labelMultiArray(inner_block_labels.astype('uint32'))

                inner_block_labels = inner_block_labels.astype('int64')
                # get the max
                inner_block_max_label = inner_block_labels.max()
                inner_block_min_label = inner_block_labels.min()

                with labels_lock:

                    gmax = global_max_label[0]
                    gmin = global_min_label[0]

                    new_global_max_label = gmax + inner_block_max_label
                    inner_block_labels += gmax

                    done_blocks[0] = done_blocks[0] +1
                    # print(done_blocks[0],n_blocks,  inner_block_labels.min(), inner_block_labels.max())
                    # print(done_blocks[0],n_blocks,  outer_block_labels.min(), outer_block_labels.max())

                    # print(inner_slicing, outer_slicing)
                    min_here = inner_block_min_label + gmax

                    if gmin is None:
                        global_min_label[0] = min_here

                    else:
                        global_min_label[0] = min(gmin, min_here)


                    global_max_label[0] = new_global_max_label


                    #print('g',labels[inner_slicing].shape, 'l', inner_block_labels.shape)

                    labels[inner_slicing] = inner_block_labels[:]
                        

        

            #per_block(i)
            future = executor.submit(per_block, block_index=i)

    labels -= int(global_min_label[0]-1)

    #print("labels ",labels.min())

    return labels
        


def simple_parallel_ws(data, block_shape=None, max_workers=None, reduce_to=0.2, size_regularizer=0.5):
    if max_workers is None:
        max_workers = cpu_count()

    logger.info(f"blockwise watershed with {max_workers} threads.")
    overseg = simple_parallel_ws_impl(data=data, block_shape=block_shape, max_workers=max_workers)

    #print("the overseg",overseg.min(), overseg.max())
    logger.info("bincount")
    res = bincount = numpy.bincount(overseg.ravel().astype('int64'))
    n_empty  = (res==0).sum() - 1

    logger.info("grid rag")
    rag = nifty.graph.rag.gridRag(overseg)
    logger.info("rag: %s"%str(rag))
    n_nodes = rag.numberOfNodes
    non_empty_nodes = n_nodes - n_empty

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

    n_stop = max(1,non_empty_nodes * reduce_to)
    n_stop = int(n_empty + n_stop)

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
    
    seg = numpy.take(nodeSeg, overseg.astype('int64'))



    seg -= seg.min()
    seg += 1

    #seg = vigra.analysis.labelVolume(seg.astype('uint32'))
    logger.info("agglomerative supervoxel creation is done")
    return seg
    
