import nifty
import numpy
import vigra
from multiprocessing import cpu_count
import threading
from concurrent.futures import ThreadPoolExecutor


# parallel watershed with hard block boarders
def simple_parallel_ws(data, block_shape=None, max_workers=None):
        

    if max_workers is None:
        max_workers = cpu_count()

    labels_lock = threading.Lock()

    shape = data.shape
    ndim = len(shape)
    if block_shape is None:
        block_shape  = tuple([100]*ndim)
    roi_begin = tuple([0]*ndim)
    halo = [20]*ndim
    blocking = nifty.tools.blocking(roiBegin=roi_begin, roiEnd=shape, blockShape=block_shape)
    n_blocks = blocking.numberOfBlocks



    def to_slicing(begin, end):
        return [slice(b,e) for b,e in zip(begin, end)]


    labels = numpy.zeros(shape, dtype='uint64')
    global_max_label = 0
    with ThreadPoolExecutor(max_workers=8) as executor:

        for i in range(n_blocks):


            def per_block(block_index):
                # get block with halo
                block_with_halo = blocking.getBlockWithHalo(blockIndex=block_index, halo=halo)
                print(block_with_halo)

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
                outer_block_data_vigra = numpy.require(outer_block_data, dtype='float32').T
                outer_block_labels_vigra, nseg = vigra.analysis.watershedsNew(outer_block_data_vigra)
                outer_block_labels = outer_block_labels_vigra.T

                # extract inner labels
                inner_block_labels = outer_block_labels[inner_local_slicing]

                # get the max
                inner_block_max_label = inner_block_labels.max()


                with labels_lock:
                    new_global_max_label = global_max_label + inner_block_max_label
                    inner_block_labels += global_max_label

                labels[inner_slicing] = inner_block_labels
                        


            # per_block(i)
            future = executor.submit(per_block, block_index=i)

    return labels
        


# # reduce the number of segments 
# # based on agglomerative clustering
# def reduce_overseg(overseg, edge_indicator, size_regularizer, factor):
#     pass


# # data = numpy.random.rand(20,20)
# # simple_parallel_ws(data)


# data = numpy.random.rand(400,400,20)
# simple_parallel_ws(data)