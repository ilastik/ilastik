############################################################
# for pixel value displaying
############################################################
from PyQt4.Qt import pyqtSlot
import logging
logger = logging.getLogger(__name__)

class PixelValueDisplaying(object):
    """
    class for showing the pixel-value of one slot with a particular channel

    inherit from object to make the @property and the @X.setter work correctly

    """

    def __init__(self, slot, pixelValue, pixelValueCheckBox, quadViewStatusBar, channel=0):
        """
        :param slot:       InputSlot or OutputSlot  for which the value will be displayed
        :param pixelValue: where you can set the text for the pixelvalue
            e.g. self._labelControlUi.pixelValue 
        :type pixelValue: QLabel
        :param pixelValueCheckBox: 
            QCheckbox for controlling whether to show the pixel value or whether to not show the value
            e.g. self._labelControlUi.pixelValueCheckBox 
        :type pixelValueCheckBox: QCheckbox
        :param quadViewStatusBar: 
            the status bar from ilastik, where you can find the coordinates 
            e.g. self.volumeEditorWidget.quadViewStatusBar
        (self can be the class: WatershedSegmentationGui)
        :param channel:  the channel which shall be displayed 
        :type channel: int
        """
        #variable initialization
        self.data               = slot
        self._pixelValue        = pixelValue
        self._pixelValueCheckBox= pixelValueCheckBox
        self._statusBar         = quadViewStatusBar
        #check channel for validation
        if self._checkChannelIndex(channel):
            self._channel       = channel
        else:
            self._channel       = 0
            logger.info("Init channel as zero = 0")

        # pixel value functionality
        self._pixelValueCheckBox.stateChanged.connect(self.toggleConnectionPixelValue)
        





    @property
    def Label(self):
        return self._pixelValueCheckBox.text()

    @Label.setter
    def Label(self, text):
        """
        set the label of the checkbox to a new value
        :param text: str new label for the checkbox
        """
        self._pixelValueCheckBox.setText(text)

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, c):
        """
        only set channel, if number of channel is valid
        :param c: int new channel value
        """
        if self._checkChannelIndex(c):
            self._channel = c
        else:
            logger.info("Leave the channel-value as it is")



    def _checkChannelIndex(self, channelToCheck):
        """
        Checks whether the channel-number fits together with the slot-metadata-shape 
        :returns: True if channelToCheck is a valid channel-number; False else
        :rtype: bool
        """
        # zero is always possible
        if (channelToCheck == 0) :
            return True
        channelIndex = self.data.meta.axistags.index('c')
        maxChannel = self.data.meta.shape[channelIndex]
        if ( channelToCheck < maxChannel):
            return True
        else:
            logger.info("Given channel is out of range")
            return False

    def __del__(self):
        #FIXME does this work here? or is it even needed?
        #self._pixelValueCheckBox.stateChanged.disconnect(self.toggleConnectionPixelValue)
        #TODO disconnect connections in toggleConnectionPixelValue
        pass



    #slightly faster with pyqtSlot
    @pyqtSlot(int)
    def on_SpinBox_valueChanged(self, i):
        """
        executed when x,y,z or t is changed
        get the current values and change the view for the pixel-value
        The spinbox has updated its value, 
        so the new value i (of signal) == x.SpinBox.value() (for y,z as well)
        i remains unused
        :param i: is not used
        :type i: int

        """
        x = self._statusBar.xSpinBox.value()
        y = self._statusBar.ySpinBox.value()
        z = self._statusBar.zSpinBox.value()
        t = self._statusBar.timeSpinBox.value()
        c = self.channel
        self._changeToNewPixelValue(x, y, z, t, c)



    def _changeToNewPixelValue(self, x, y, z, t, c):
        """
        get the coord. information and get the value of the array-coord
        set the text of the gui to that value
        handles all dimension combinations
        :param x:   get the coordinate of the x axis
        :param y:   get the coordinate of the y axis
        :param z:   get the coordinate of the z axis
        :param t:   get the coordinate of the time axis
        :param c:   get the channel to use
        """
        tags = self.data.meta.axistags
        if self.data.ready():
            count = 0
            array = [0,0,0,0,0]
            # rearrangement of the indices of x,y,z,t,c to have the correct axis-order
            # indices always start with 0,1,...
            # if the dimensions are tagged, then they are ordered like: 0,1,2
            # and not like 1, 2, 3
            # so that the section with e.g. count == 3 makes sense
            tupl = (('x', x, tags.index('x')),
                    ('y', y, tags.index('y')),
                    ('z', z, tags.index('z')),
                    ('t', t, tags.index('t')),
                    ('c', c, tags.index('c')))

            #copy the axis-value into the array at the right index for all axes
            for (letter, value, index) in tupl:
                if (letter in tags):
                    count+=1
                    array[index] = value


            """ worse performance than if..elif..
            def f(count, self.data, array):
                for i in range(count):
                    self.data = self.data[array[i]]
                return self.data
            newValue = f(count, self.data.value, array)
            """
            # search the value of the data depending on how many dimensions used
            if (count == 2):
                newValue = self.data.value[array[0],array[1]]
            elif (count == 3):
                newValue = self.data.value[array[0],array[1],array[2]]
            elif (count == 4):
                newValue = self.data.value[array[0],array[1],array[2],array[3]]
            elif (count == 5):
                newValue = self.data.value[array[0],array[1],array[2],array[3],array[4]]

            #show the value of the pixel under the curser on the gui
            self._pixelValue.setText(str(newValue))

            """print infos
            print xIndex, ":", yIndex, ":", zIndex, ":", tIndex
            print tags
            print self.data
            print "array:", array
            print "pixelValue:", newValue
            """


    @pyqtSlot()
    def toggleConnectionPixelValue(self):
        """
        connect or disconnect the valueChanged signals from 
        coordinates x,y,z,t,c with the slot: on_SpinBox_valueChanged
        so that changes can be registered or not
        Additionally: change the label of the pixelValue

        Explanation for the x,y,z,timeSpinBox:
        # Connect the standard signal, that is emitted, when a QSpinBox changes its value, 
        # 'valueChanged' with the function that handles this change
        # to compute the changed value of the pixel with the new coordinates
        # Origin for better understanding:
        # volumina/volumina/sliceSelctorHud.py:
        # QuadStatusBar.xSpinBox (and y,z)
        # with standard signal: valueChanged
        # /volumina/volumina/volumeEditorWidget.py
        # self=VolumneEditorWidget
        # self.quadViewStatusBar = QuadStatusBar()
        # e.g. 
        #self.volumeEditorWidget.quadViewStatusBar.zSpinBox.valueChanged.connect( self.on_SpinBox_valueChanged )
        """

        #tuple with x,y,z,t and their spinBoxes
        # the channel is a memberVariable and can be changed seperately
        sBar = self._statusBar
        tupl = (sBar.xSpinBox,  sBar.ySpinBox, sBar.zSpinBox, sBar.timeSpinBox)
        if self._pixelValueCheckBox.isChecked():
            #connect x,y,z,t,c
            for box in tupl:
                box.valueChanged.connect(self.on_SpinBox_valueChanged)

            #emit signal (of local widget) to read in the pixel values immediately 
            #number is irrelevant, see on_SpinBox_valueChanged
            sBar.xSpinBox.valueChanged.emit(0)

        else:
            #disconnect x,y,z,t,c
            for box in tupl:
                box.valueChanged.disconnect(self.on_SpinBox_valueChanged)
            #reset pixelValue-Label
            self._pixelValue.setText("unused")

