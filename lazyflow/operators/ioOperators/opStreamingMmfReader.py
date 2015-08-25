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

'''
MMF reader adapted from JAABA's mmf header reader: https://github.com/kristinbranson/JAABA/blob/master/filehandling/mmf_read_header.m

mmf format documentation (Copied from JAABA's mmf_read_header.m):
Set of Image Stacks representing a movie. Beginning of file is a header, with this format:
10240 byte zero padded header beginning with a textual description of the file, followed by \0 then the following fields (all ints, except idcode)
4 byte unsigned long idcode = a3d2d45d, header size in bytes, key frame interval, threshold below background, threshold above background
Header is followed by a set of common background image stacks, with the following format:
Stack of common background images, beginning with this header:
512 byte zero-padded header, with the following fields (all 4 byte ints, except idcode):
4 byte unsigned long idcode = bb67ca20, header size in bytes, total size of stack on disk, nframes: number of images in stack
Then the background image, as an IplImage, starting with the 112 byte image header, followed by the image data
Then nframes background removed images containing only differences from the background, in this format:
BackgroundRemovedImage: header is a1024 byte zero padded header with the following data fields (all 4 byte ints, except id code)
4 byte unsigned long idcode = f80921af, headersize (number of bytes in header), depth (IplImage depth), nChannels (IplImage number of channels), numims (number of 
image blocks that differ from background) then metadata:
Name-Value MetaData: idcode (unsigned long) = c15ac674, int number of key-value pairs stored, then each pair
in the format \0-terminated string of chars then 8 byte double value
header is followed by numims image blocks of the following form:
(16 bytes) CvRect [x y w h] describing location of image data, then interlaced row ordered image data

TODO: handle multichannel data, non 8-bit data
'''

import logging
import time

import numpy
import vigra
import copy

import MmfParser

from lazyflow.utility import Timer

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility import Timer 

AXIS_ORDER = 'tyxc'

class OpStreamingMmfReader(Operator):
    """
    Imports videos in MMF format.
    """    
    name = "OpStreamingMmfReader"
    category = "Input"

    position = None
    
    FileName = InputSlot(stype='filestring')
    Output = OutputSlot()

    class DatasetReadError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super(OpStreamingMmfReader, self).__init__(*args, **kwargs)
        self._memmapFile = None
        self._rawVigraArray = None

    def setupOutputs(self):
        """
        Load the file specified via our input slot and present its data on the output slot.
        """
        fileName = self.FileName.value

        self.mmf = MmfParser.MmfParser(str(fileName))
        frameNum = self.mmf.getNumberOfFrames()
        
        #try:
        frame = self.mmf.getFrame(0)
        self.frame = frame[None, :, :, None]

        self.Output.meta.dtype = self.frame.dtype.type
        self.Output.meta.axistags = vigra.defaultAxistags(AXIS_ORDER)
        self.Output.meta.shape = (frameNum, self.frame.shape[1], self.frame.shape[2], self.frame.shape[3])

    def execute(self, slot, subindex, roi, result):
        start, stop = roi.start, roi.stop
        
        tStart, tStop = start[0], stop[0]
        yStart, yStop = start[1], stop[1]
        xStart, xStop = start[2], stop[2]
        cStart, cStop = start[3], stop[3]
            
        if self.position != tStart :
            self.position = tStart
            frame = self.mmf.getFrame(tStart)
            self.frame = frame[None, :, :, None]

          
        result[...] = self.frame[0:1, yStart:yStop, xStart:xStop, cStart:cStop]
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.FileName:
            self.Output.setDirty( slice(None) )
    
    def cleanUp(self):
        self.mmf.close()
        super(OpStreamingMmfReader, self).cleanUp()

