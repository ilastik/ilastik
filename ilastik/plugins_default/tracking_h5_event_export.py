from builtins import range
import os
import numpy as np
import h5py
from functools import partial
from lazyflow.request import Request, RequestPool

from ilastik.plugins import TrackingExportFormatPlugin

import logging
logger = logging.getLogger(__name__)

try:
    from hytra.core.jsongraph import getMappingsBetweenUUIDsAndTraxels, getMergersDetectionsLinksDivisions, \
                                     getMergersPerTimestep, getLinksPerTimestep, getDetectionsPerTimestep, \
                                     getDivisionsPerTimestep
except ImportError:
    logger.warning("Could not load hytra. Event exporting plugin not loaded.")
else:

    def writeEvents(timestep, activeLinks, activeDivisions, mergers, detections, fn, labelImage, verbose=False):
        '''
        Warning: every error in this function is somehow not thrown, not even as the logger warning.
        '''
        dis = []
        app = []
        div = []
        mov = []
        mer = []
        mul = []
    
        logging.getLogger(__name__).debug("-- Writing results to {}".format(fn))
        try:
            # convert to ndarray for better indexing
            dis = np.asarray(dis)
            app = np.asarray(app)
            div = np.asarray([[k, v[0], v[1]] for k,v in activeDivisions.items()])
            mov = np.asarray(activeLinks)
            mer = np.asarray([[k,v] for k,v in mergers.items()])
            mul = np.asarray(mul)
    
            with h5py.File(fn, 'w') as dest_file:
                # write meta fields and copy segmentation from project
                seg = dest_file.create_group('segmentation')
                seg.create_dataset("labels", data=labelImage, compression='gzip')
                meta = dest_file.create_group('objects/meta')
                ids = np.unique(labelImage)
                ids = ids[ids > 0]
                valid = np.ones(ids.shape)
                meta.create_dataset("id", data=ids, dtype=np.uint32)
                meta.create_dataset("valid", data=valid, dtype=np.uint32)
    
                tg = dest_file.create_group("tracking")
    
                # write associations
                if app is not None and len(app) > 0:
                    ds = tg.create_dataset("Appearances", data=app, dtype=np.int32)
                    ds.attrs["Format"] = "cell label appeared in current file"
    
                if dis is not None and len(dis) > 0:
                    ds = tg.create_dataset("Disappearances", data=dis, dtype=np.int32)
                    ds.attrs["Format"] = "cell label disappeared in current file"
    
                if mov is not None and len(mov) > 0:
                    ds = tg.create_dataset("Moves", data=mov, dtype=np.int32)
                    ds.attrs["Format"] = "from (previous file), to (current file)"
    
                if div is not None and len(div) > 0:
                    ds = tg.create_dataset("Splits", data=div, dtype=np.int32)
                    ds.attrs["Format"] = "ancestor (previous file), descendant (current file), descendant (current file)"
    
                if mer is not None and len(mer) > 0:
                    ds = tg.create_dataset("Mergers", data=mer, dtype=np.int32)
                    ds.attrs["Format"] = "descendant (current file), number of objects"
    
                if mul is not None and len(mul) > 0:
                    ds = tg.create_dataset("MultiFrameMoves", data=mul, dtype=np.int32)
                    ds.attrs["Format"] = "from (given by timestep), to (current file), timestep"
    
            logger.debug("-> results successfully written")
        except Exception as e:
            logger.warning("ERROR while writing events: {}".format(str(e)))
    
    
    class TrackingH5EventExportFormatPlugin(TrackingExportFormatPlugin):
        """H5 Sequence export"""
    
        exportsToFile = False
    
        def checkFilesExist(self, filename):
            ''' Check whether the files we want to export are already present '''
            return os.path.exists(filename)
    
        def export(self, filename, hypothesesGraph, pluginExportContext):
            """Export the tracking solution stored in the hypotheses graph as a sequence of H5 files,
            one per frame, containing the label image of that frame and which objects were part
            of a move or a division.
    
            :param filename: string of the FOLDER where to save the result
            :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
            :param pluginExportContext: instance of ilastik.plugins.PluginExportContext containing:
                labelImageSlot (required here) as well as objectFeaturesSlot, rawImageSlot, additionalPluginArgumentsSlot

            :returns: True on success, False otherwise
            """
            labelImageSlot = pluginExportContext.labelImageSlot
            traxelIdPerTimestepToUniqueIdMap, uuidToTraxelMap = hypothesesGraph.getMappingsBetweenUUIDsAndTraxels()
            timesteps = [t for t in traxelIdPerTimestepToUniqueIdMap.keys()]
    
            result = hypothesesGraph.getSolutionDictionary()
            mergers, detections, links, divisions = getMergersDetectionsLinksDivisions(result, uuidToTraxelMap)
    
            # group by timestep for event creation
            mergersPerTimestep = getMergersPerTimestep(mergers, timesteps)
            linksPerTimestep = getLinksPerTimestep(links, timesteps)
            detectionsPerTimestep = getDetectionsPerTimestep(detections, timesteps)
            divisionsPerTimestep = getDivisionsPerTimestep(divisions, linksPerTimestep, timesteps)
    
            # save to disk in parallel
            pool = RequestPool()
    
            timeIndex = labelImageSlot.meta.axistags.index('t')

            if not os.path.exists(filename):
                os.makedirs(filename)
    
            for timestep in traxelIdPerTimestepToUniqueIdMap.keys():
                # extract current frame lable image
                roi = [slice(None) for i in range(len(labelImageSlot.meta.shape))]
                roi[timeIndex] = slice(int(timestep), int(timestep)+1)
                roi = tuple(roi)
                labelImage = labelImageSlot[roi].wait()
    
                fn = os.path.join(filename, "{0:05d}.h5".format(int(timestep)))
                pool.add(Request(partial(writeEvents,
                                            int(timestep),
                                             linksPerTimestep[timestep],
                                             divisionsPerTimestep[timestep],
                                             mergersPerTimestep[timestep],
                                             detectionsPerTimestep[timestep],
                                             fn,
                                             labelImage)))
            pool.wait()
    
            return True
