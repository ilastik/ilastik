###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#           http://ilastik.org/license/
###############################################################################

import struct
import numpy as np

# Header IDs
FILE_HEADER_ID = 0xa3d2d45d
STACK_HEADER_ID = 0xbb67ca20
IMAGE_HEADER_ID = 0xf80921af

class MmfParser(object):
    # Initialize information to seek frames
    _frameSeekInfo = []
    
    # Constructor
    def __init__(self, fileName) :
        self._frameCount = None
        self._bkgImgSeekPos = None
        
        try:
            self.mmfFile = open(fileName, "rb")
        except FileNotFoundError:
            print "Wrong file or file path."
        
        # Find header id code (and skip ASCII description)
        while struct.unpack('1I',self.mmfFile.read(4))[0] != FILE_HEADER_ID :
                self.mmfFile.seek(-3,1)
        
        fileHeaderSize = struct.unpack('1i',self.mmfFile.read(4))[0]
        
        self.keyFrameInterval = struct.unpack('1i',self.mmfFile.read(4))[0]
        self.thresholdBelowBackground = struct.unpack('1i',self.mmfFile.read(4))[0]
        self.thresholdAboveBackground = struct.unpack('1i',self.mmfFile.read(4))[0]
        
        # Seek self.mmfFile by the number of self.mmfFile header bytes offset (10240?)
        self.mmfFile.seek(fileHeaderSize, 0)
        
        firstBkgImg = False
        
        # Loop through each background image
        while True :    
            stackStartPos = self.mmfFile.tell()
            
            # Reached end of file
            buf = self.mmfFile.read(4)
            if not buf :
                break
            
            stackIdCode = struct.unpack('1I',buf)[0]
            
            if  stackIdCode != STACK_HEADER_ID :
                print "Error: Background image header id code does not match."
            
            stackHeaderSize = struct.unpack('1i',self.mmfFile.read(4))[0]
            stackSize = struct.unpack('1i',self.mmfFile.read(4))[0]
            stackFrameNum = struct.unpack('1i',self.mmfFile.read(4))[0]
            
            # Got to end of stack header
            self.mmfFile.seek(stackStartPos + stackHeaderSize, 0)
            
            bkgHeaderSize = struct.unpack('1i',self.mmfFile.read(4))[0]
            
            # Read background image meta-data (only for the first frame)
            if not firstBkgImg :
                bkgIdCode =  struct.unpack('1I',self.mmfFile.read(4))[0] # <-- TO DO: This ID is not included in the docs
                
                bkgChannelNum =  struct.unpack('1i',self.mmfFile.read(4))[0]
                if bkgChannelNum != 1 :
                    print 'Cannot read multichannel data yet: TODO'
                
                bkgAlphaChannel =  struct.unpack('1i',self.mmfFile.read(4))[0]
                
                bkgDepth =  struct.unpack('1i',self.mmfFile.read(4))[0]
                if bkgDepth != 8 :
                    print 'Cannot read non-8-bit depth images yet: TODO'
                
                bkgColorModel =  struct.unpack('4c',self.mmfFile.read(4))[0]
                bkgChannelSeq =  struct.unpack('4c',self.mmfFile.read(4))[0]
                bkgDataOrder =  struct.unpack('1i',self.mmfFile.read(4))[0]
                bkgOrigin =  struct.unpack('1i',self.mmfFile.read(4))[0]
                bkgAlign = struct.unpack('1i',self.mmfFile.read(4))[0]
                self.bkgWidth =  struct.unpack('1i',self.mmfFile.read(4))[0]
                self.bkgHeight =  struct.unpack('1i',self.mmfFile.read(4))[0]
                
                # image ROI. if NULL, the whole image is selected
                bkgRoi =  struct.unpack('1I',self.mmfFile.read(4))[0]
                
                # must be NULL
                bkgMaskRoi = struct.unpack('1I',self.mmfFile.read(4))[0]
                
                # must be NULL
                bkgImageId = struct.unpack('1I',self.mmfFile.read(4))[0]
                
                # must be NULL
                bkgTileInfo = struct.unpack('1I',self.mmfFile.read(4))[0]
                
                # image data size in bytes (==image->height*image->widthStep in case of interleaved data)
                self.bkgImgSize = struct.unpack('1i',self.mmfFile.read(4))[0]
                bkgdim_imagedata = struct.unpack('1I',self.mmfFile.read(4))[0]
                # Size of aligned image row in bytes
                self.bkgImgWidthStep = struct.unpack('1i',self.mmfFile.read(4))[0]
                
                # ignored
                bkgBorderMode = struct.unpack('4i',self.mmfFile.read(4*4))[0]
                
                # ignored
                bkgBorderConst = struct.unpack('4i',self.mmfFile.read(4*4))[0]
                
                # pointer to something
                bkgImgDataOrigin = struct.unpack('1I',self.mmfFile.read(4))[0]
                
                bkgImgSeekPos = self.mmfFile.tell()
            else :
                # Skip reading background image meta-data
                self.mmfFile.seek(stackStartPos + stackHeaderSize + bkgHeaderSize, 0)
                bkgImgSeekPos = self.mmfFile.tell()
            
            self.mmfFile.seek(self.bkgImgSize, 1)
            
            # Read the diff image data (these are usually the tiles that contain the larvae/flies)
            for fri in range (stackFrameNum) : 
                imgStartPos = self.mmfFile.tell()
                
                imgIdCode = struct.unpack('1I',self.mmfFile.read(4))[0]
                
                if imgIdCode != IMAGE_HEADER_ID :
                    print "Image ID does not match."
                
                imgHeaderSize = struct.unpack('1i',self.mmfFile.read(4))[0]
                self.mmfFile.seek(8,1)
                imgBlockNum = struct.unpack('1i',self.mmfFile.read(4))[0]
                
                self.mmfFile.seek(imgStartPos + imgHeaderSize, 0)
        
                imgSeekPos = self.mmfFile.tell()
        
                self._frameSeekInfo.append( {"bkgImgSeekPos" : bkgImgSeekPos, "imgSeekPos" : imgSeekPos, "blockNum" :  imgBlockNum} )
        
                # Loop through each block        
                for bki in range(imgBlockNum) :
                    imgBlockRect = struct.unpack('4i',self.mmfFile.read(4*4))
                    self.mmfFile.seek(imgBlockRect[2]*imgBlockRect[3], 1)

    def seek(self, frameCount) :
        self._frameCount = frameCount

    def getFrame(self, frameCount) :
        self._frameCount = frameCount

        if self._bkgImgSeekPos != self._frameSeekInfo[self._frameCount]['bkgImgSeekPos'] :
            self._bkgImgSeekPos = self._frameSeekInfo[self._frameCount]['bkgImgSeekPos']
                
            self.mmfFile.seek(self._bkgImgSeekPos, 0)
            
            self._bkgImg = np.array(struct.unpack(str(self.bkgImgSize) + 'B', self.mmfFile.read(self.bkgImgSize)), dtype='uint8')
            self._bkgImg = np.reshape(self._bkgImg, (self.bkgHeight, self.bkgImgWidthStep))
            self._bkgImg = self._bkgImg[:, 0:self.bkgWidth]
            
        img = np.copy(self._bkgImg)
        
        self.mmfFile.seek(self._frameSeekInfo[self._frameCount]['imgSeekPos'], 0)
        
        blockNum = self._frameSeekInfo[self._frameCount]['blockNum'] 
        for bki in range(blockNum) :
            imgBlockRect = struct.unpack('4i',self.mmfFile.read(4*4))
                    
            byteNumStr = str(imgBlockRect[2]*imgBlockRect[3])
                        
            imgBlockData = np.array(struct.unpack(byteNumStr + 'B', self.mmfFile.read(imgBlockRect[2]*imgBlockRect[3])), dtype='uint8')
            imgBlockData = np.reshape(imgBlockData, (imgBlockRect[3],imgBlockRect[2]) )
                    
            img[imgBlockRect[1]:imgBlockRect[1]+imgBlockRect[3], imgBlockRect[0]:imgBlockRect[0]+imgBlockRect[2]] = imgBlockData  
            
        return img
            
    def getNextFrame(self):
        nextFrame = self._frameCount + 1
        return self.getFrame(nextFrame)

    def getNumberOfFrames(self):
        return len(self._frameSeekInfo)

    def close(self) :
        self.mmfFile.close()








