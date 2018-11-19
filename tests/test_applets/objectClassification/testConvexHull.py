import numpy as np
import vigra
import unittest
from lazyflow.graph import Graph
from ilastik.applets.objectExtraction.opObjectExtraction import OpRegionFeatures


feats_2D = {'2D Convex Hull Features': {
'DefectDisplacementMean': {},
'Area': {}, 
'DefectCount': {},
'DefectVolumeVariance': {},
'DefectVolumeMean': {},
'Convexity': {},
'HullCenter': {},
'InputCenter': {},
'InputVolume': {}}}

feats_3D = {'3D Convex Hull Features': {
'DefectDisplacementMean': {},
'Area': {}, 
'DefectCount': {},
'DefectVolumeVariance': {},
'DefectVolumeMean': {},
'Convexity': {},
'HullCenter': {},
'InputCenter': {},
'InputVolume': {}}}

def segImage2D():

    img = np.zeros((2, 50, 50, 1, 1), dtype=np.int)
    img[0,  0:10,  0:10,  0, 0] = 1
    img[0, 20:25, 20:25, 0, 0] = 2
    img[1,  0:10,  0:10,  0, 0] = 1
    img[1, 10:20, 10:20, 0, 0] = 2
    img[1, 20:25, 20:25, 0, 0] = 3
    
    img = img.view(vigra.VigraArray)
    img.axistags = vigra.defaultAxistags('txyzc')    
    return img

def segImage3D():

    img = np.zeros((2, 50, 50, 50, 1), dtype=np.int)
    img[0,  0:10,  0:10,  0:10, 0] = 1
    img[0, 20:25, 20:25, 20:25, 0] = 2
    img[1,  0:10,  0:10,  0:10, 0] = 1
    img[1, 10:20, 10:20, 10:20, 0] = 2
    img[1, 20:25, 20:25, 20:25, 0] = 3
    
    img = img.view(vigra.VigraArray)
    img.axistags = vigra.defaultAxistags('txyzc')    
    return img


class TestConvexHull(unittest.TestCase):


    def test(self):
        # test 2D ConvexHull with 2D image
        segimg = segImage2D()
        feats = feats_2D

        feat_output = self.runConvexHull(segimg,feats)
        # print (feat_output[1]['2D Convex Hull Features'].values())

        self.assertTrue(bool(feat_output[1]['2D Convex Hull Features'].values()) == True)

        # test 2D ConvexHull with 3D image
        segimg = segImage3D()
        feats = feats_2D

        feat_output = self.runConvexHull(segimg,feats)
        # print (feat_output[1]['2D Convex Hull Features'].values())

        self.assertTrue(bool(feat_output[1]['2D Convex Hull Features'].values()) == False )

        # test 3D ConvexHull with 2D image
        segimg = segImage2D()
        feats = feats_3D

        feat_output = self.runConvexHull(segimg,feats)
        # print (feat_output[1]['3D Convex Hull Features'].values())

        self.assertTrue(bool(feat_output[1]['3D Convex Hull Features'].values()) == False)

        # test 3D ConvexHull with 3D image
        segimg = segImage3D()
        feats = feats_3D

        feat_output = self.runConvexHull(segimg,feats)
        # print (feat_output[1]['3D Convex Hull Features'].values())

        self.assertTrue(bool(feat_output[1]['3D Convex Hull Features'].values()) == True)



    def runConvexHull(self ,segimg ,feats):
        #testing 2D Convex Hull features on a 2D image

        rawimg = np.indices(segimg.shape).sum(0).astype(np.float32)
        rawimg = rawimg.view(vigra.VigraArray)
        rawimg.axistags = vigra.defaultAxistags('txyzc')


        g = Graph()
        self.featsop = OpRegionFeatures(graph=g)
        self.featsop.LabelVolume.setValue(segimg)
        self.featsop.RawVolume.setValue(rawimg)
        self.featsop.Features.setValue(feats)
        output = self.featsop.Output([]).wait()

        return output
