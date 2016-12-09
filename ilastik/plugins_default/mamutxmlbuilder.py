import xml.etree.ElementTree as ET
import numpy as np

class MamutXmlBuilder(object):
    '''
    Class to construct XML files that can be loaded with Fiji's Mamut plugin.
    '''

    def __init__(self):
        self.tree = ET.parse('raw_input.xml')
        self.root = self.tree.getroot()
        self.allspots = ET.SubElement(self.root[0], 'AllSpots')
        self.alltracks = ET.SubElement(self.root[0], 'AllTracks')
        self.filteredTracks = ET.SubElement(self.root[0], 'FilteredTracks')
        self.cell_count = 0
        self.spotsPerFrame = {}
        self.trackElementById = {}

    def addFeatureName(self, featureName, featureDisplayName, shortName, isInt):
        '''
        Defines the used features at the beginning of the XML file.
        '''
        newfeature = ET.SubElement(self.root[0][0][0], 'Feature dimension="NONE" feature="{}" name="{}" shortname="{}"'.format(featureName, featureDisplayName, shortName))
        if isInt:
            newfeature.set('isint', 'true')
        else:
            newfeature.set('isint', 'false')

    def addSpot(self, timeframe, uuid, xpos, ypos, zpos, radius=1.0, featureDict=None):
        '''
        Adds spots and their features in the XML file
        '''
        if timeframe not in self.spotsPerFrame:
            spotsInFrame = ET.SubElement(self.allspots, 'SpotsInFrame')
            spotsInFrame.set('frame', str(timeframe))
            self.spotsPerFrame[timeframe] = spotsInFrame
        else:
            spotsInFrame = self.spotsPerFrame[timeframe]

        spot = ET.SubElement(spotsInFrame,
                            '''Spot ID="{}" name="center" VISIBILITY="1" POSITION_T="{}"
                               POSITION_Z="{}" POSITION_Y="{}" RADIUS="{}" FRAME="{}" 
                               POSITION_X="{}" QUALITY="3.0"'''.format(str(uuid), str(float(timeframe)), str(zpos), str(ypos), str(float(radius)),
                                                                        str(timeframe), str(xpos)))

        if featureDict is not None:
            for k, v in featureDict.iteritems():
                spot.set(k, str(np.nan_to_num(v)))

        self.cell_count += 1

    def getOrCreateTrackElement(self, trackId):
        '''
        Decides if a new track starts or an old one will be continoued
        '''
        if trackId not in self.trackElementById:
            track = ET.SubElement(self.alltracks, 'Track')
            track.set('TRACK_ID', str(trackId))
            track.set("name", 'Track_{}'.format(str(trackId)))
            track.set("TRACK_INDEX", str(trackId))
            ET.SubElement(self.filteredTracks, 'TrackID TRACK_ID="{}"'.format(str(trackId)))
            self.trackElementById[trackId] = track
            return track
        else:
            return self.trackElementById[trackId]

    def addSplit(self, trackId, parentId, childrenIds):
        '''
        writes splits from the split table in the XML tracking section
        '''
        trackElement = self.getOrCreateTrackElement(trackId)

        assert(len(childrenIds) == 2)

        for c in childrenIds:
            ET.SubElement(trackElement, '''Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}"
                         LINK_COST="-1.0" VELOCITY="0.0" DISPLACEMENT="0.0"'''.format(str(parentId), str(c)))

    def addLink(self, trackId, sourceId, targetId):
        '''
        writes moves from the move table in the XML tracking section
        '''
        trackElement = self.getOrCreateTrackElement(trackId)

        ET.SubElement(trackElement, '''Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}"
                                        LINK_COST="0.0" VELOCITY="0.0" DISPLACEMENT="0.0"'''.format(str(sourceId), str(targetId)))

    def printToConsole(self):
        '''
        FOR DEBUGGING ONLY! Print the full XML document to the console. 
        '''
        ET.dump(self.root)

    def setBigDataViewerImagePath(self, pathToFolder, filename):
        '''
        '''
        ET.SubElement(self.root[1], '''ImageData filename="{}" folder="{}" height ="0" nframes="0" nslices="0"
                    pixelheight="1.0" pixelwidth="1.0" timeinterval="1.0" voxeldepth="1.0" width="0" '''.format(filename, pathToFolder))

    def writeToFile(self, filename):
        '''
        saves the XML 
        '''
        for allspots in self.root.iter('AllSpots'):
            allspots.set('nspots', str(self.cell_count))

        MamutXmlBuilder.indent(self.root)
        self.tree.write(filename)

    @staticmethod
    def indent(elem, level=0):
        '''line indentation in the xml file '''
        i = "\n" + level*"  "
        j = "\n" + (level-1)*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for subelem in elem:
                MamutXmlBuilder.indent(subelem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = j
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = j
        return elem
