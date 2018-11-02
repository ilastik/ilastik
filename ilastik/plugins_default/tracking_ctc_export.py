import os
import numpy as np
import vigra
from skimage.external import tifffile
from ilastik.plugins import TrackingExportFormatPlugin

import logging
logger = logging.getLogger(__name__)

class TrackingCTCExportFormatPlugin(TrackingExportFormatPlugin):
    """CTC export"""

    exportsToFile = False

    def checkFilesExist(self, filename):
        ''' Check whether the files we want to export are already present '''
        return os.path.exists(filename)

    def export(self, filename, hypothesesGraph, pluginExportContext):
        """
        Export the tracking model and result

        :param filename: string of the FOLDER where to save the result (will be filled with a res_track.txt and segmentation masks for each frame)
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param pluginExportContext: instance of ilastik.plugins.PluginExportContext containing:
            labelImageSlot (required here) as well as objectFeaturesSlot, rawImageSlot, additionalPluginArgumentsSlot

        :returns: True on success, False otherwise
        """
        if not os.path.exists(filename):
            os.makedirs(filename)

        mappings = {} # dictionary over timeframes, containing another dict objectId -> trackId per frame
        tracks = {} # stores a list of timeframes per track, so that we can find from<->to per track
        trackParents = {} # store the parent trackID of a track if known
        gapTrackParents = {}

        for n in hypothesesGraph.nodeIterator():
            frameMapping = mappings.setdefault(n[0], {})
            if 'trackId' not in hypothesesGraph._graph.node[n]:
                raise ValueError("You need to compute the Lineage of every node before accessing the trackId!")
            trackId = hypothesesGraph._graph.node[n]['trackId']
            if trackId is not None:
                frameMapping[n[1]] = trackId
            if trackId in tracks.keys():
                tracks[trackId].append(n[0])
            else:
                tracks[trackId] = [n[0]]
            if 'parent' in hypothesesGraph._graph.node[n]:
                assert(trackId not in trackParents)
                trackParents[trackId] = hypothesesGraph._graph.node[hypothesesGraph._graph.node[n]['parent']]['trackId']
            if 'gap_parent' in hypothesesGraph._graph.node[n]:
                assert(trackId not in trackParents)
                gapTrackParents[trackId] = hypothesesGraph._graph.node[hypothesesGraph._graph.node[n]['gap_parent']]['trackId']

        # write res_track.txt
        logger.debug("Writing track text file")
        trackDict = {}
        for trackId, timestepList in tracks.items():
            timestepList.sort()
            if trackId in trackParents.keys():
                parent = trackParents[trackId]
            else:
                parent = 0
            # jumping over time frames, so creating 
            if trackId in gapTrackParents.keys():
                if gapTrackParents[trackId] != trackId:
                    parent = gapTrackParents[trackId]
                    logger.info("Jumping over one time frame in this link: trackid: {}, parent: {}, time: {}".format(trackId, parent, min(timestepList)))
            trackDict[trackId] = [parent, min(timestepList), max(timestepList)]
        self._save_tracks(trackDict, filename)

        # load images, relabel, and export relabeled result
        logger.debug("Saving relabeled images")

        labelImage = pluginExportContext.labelImageSlot([]).wait()
        labelImage = np.swapaxes(labelImage, 1, 3) # do we need that?
        for timeframe in range(labelImage.shape[0]):
            labelFrame = labelImage[timeframe, ...]

            # check if frame is empty
            if timeframe in mappings.keys():
                remapped_label_image = self._remap_label_image(labelFrame, mappings[timeframe])
                self._save_frame_to_tif(timeframe, remapped_label_image, filename)
            else:
                self._save_frame_to_tif(timeframe, labelFrame, filename)

        return True


    def _save_frame_to_tif(self, timestep, label_image, output_dir, filename_zero_padding=3):
        """
        Save a single frame to a 2D or 3D tif
        """
        filename = os.path.join(output_dir, f"mask{timestep:0{filename_zero_padding}}.tif")
        # import ipdb; ipdb.set_trace()
        label_image = np.swapaxes(label_image.squeeze(), 0, 1)
        if len(label_image.shape) == 2: # 2d
            vigra.impex.writeImage(label_image.astype('uint16'), filename)
        elif len(label_image.shape) == 3: # 3D
            label_image = np.transpose(label_image, axes=[2, 0, 1])
            tifffile.imsave(filename, label_image.astype('uint16'))
        else:
            raise ValueError("Image had the wrong dimensions, can only save 2 or 3D images with a single channel")


    def _save_tracks(self, tracks, output_dir):
        """
        Take a dictionary indexed by TrackId which contains
        a list [parent, begin, end] per track, and save it 
        in the text format of the cell tracking challenge.
        """
        filename = os.path.join(output_dir, 'res_track.txt')
        with open(filename, 'wt') as f:
            for key, value in tracks.items():
                if key is  None:
                    continue
                # our track value contains parent, begin, end
                # but here we need begin, end, parent. so swap.
                # Also, ilastik uses trackIDs starting at 2, but CTC wants 1, so subtract 1
                f.write(f"{int(key) - 1} {value[1]} {value[2]} {max(0, int(value[0]) - 1)}\n")

    def _remap_label_image(self, label_image, mapping):
        """ 
        given a label image and a mapping, creates and 
        returns a new label image with remapped object pixel values 
        """
        remapped_label_image = np.zeros(label_image.shape, dtype=label_image.dtype)
        for src, dest in mapping.items():
            remapped_label_image[label_image == src] = dest - 1

        return remapped_label_image
