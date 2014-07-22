###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
import unittest
import numpy as np
from countingsvr import SVR, SMO

class TestSMO(unittest.TestCase):
    def setUp(self):

        pMult = 100 #This is the penalty-multiplier for underestimating the density
        lMult = 100 #This is the penalty-multiplier for overestimating the density


       #ToyExample
        DENSITYBOUND = True
        img = np.ones((9,9,1),dtype=np.float32)
        dot = np.zeros((9,9))
        img = 1 * img
        #img[0,0] = 3
        #img[1,1] = 3
        img[3:6,3:6] = 50
        #img[:,:,1] = np.random.rand(*img.shape[:-1])
        #print img
        dot[3:5,3:5] = 2
        dot[0,0] = 1
        dot[1,1] = 1

        backup_image = np.copy(img)
        Counter = SVR(pMult, lMult, DENSITYBOUND, method = "dotprod")
        sigma = [0]
        self.img, self.dot, self.mapping, self.tags = Counter.prepareData(img,
                                                                          dot,
                                                                          sigma,
                                                                          False,
                                                                          False)
        self.upperBounds = [None,1000,1000]


        #newdot = Counter.predict(backup_image, normalize = False)
        
    def test(self):
        epsilon = 0.00
        smo = SMO(self.tags, self.img, self.dot, self.upperBounds, self.mapping,
                 epsilon)
        self.assertTrue(np.all(smo.alpha == [0,0,0,0,0,0,0,0,0,0]))
        print smo.I
        self.assertTrue(np.all(smo.I == [1,1,1,1,4,4,4,4,4,4]))
        #smo.takeStep(0,2)
        self.assertEqual(smo.examine(0), 0)
        self.assertEqual(smo.blow, 1 - epsilon)
        self.assertEqual(smo.examine(4), 0)
        self.assertEqual(smo.bup, 1 + epsilon)
        smo.examine(2)

        smo.mainLoop()
        print smo.blow, smo.bup
        print smo.alpha
        #print smo.b
        #print smo.w
        #self.assertTrue(np.all(smo.alpha == [1./49**2,0,1./49**2]))
        print "blub"


if __name__ == '__main__':
    unittest.main()
