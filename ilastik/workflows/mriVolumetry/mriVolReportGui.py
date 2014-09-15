import os
import csv

from PyQt4 import uic
from PyQt4.QtCore import Qt, QAbstractTableModel, QVariant, QModelIndex
from PyQt4.QtGui import QWidget, QListWidget, QLabel, QPainter, QColor, \
    QPixmap, QSizePolicy, QTableView, QFileDialog

from matplotlib.backends.backend_qt4agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties

import numpy as np

class MriVolReportGui( QWidget ):
    """
    Gui for visualizing Report for MriVolumetry
    based on code from Christoph Decker
    """
    def centralWidget( self ):
        return self
    def menus( self ):
        return []
    def appletDrawer( self ):
        return self._drawer
    def reset( self ):
        print "MriVolReportGui.reset(): not implemented"
    def viewerControlWidget(self):
        return self._viewerControlWidgetStack
    def stopAndCleanUp(self):
        pass


    def __init__(self, parentApplet, topLevelOperatorView, 
                 title="MRI Volumetry Report"):
        super(MriVolReportGui, self).__init__()

        self.title = title
        self.parentApplet = parentApplet
        # self.parentApplet.topLevelOperator.parent.mriVolFilterApplet.topLevelOperator.Output.setDirty()
        # Region in the lower left
        self._viewerControlWidgetStack = QListWidget(self)
        self.op = topLevelOperatorView

        self._channelColors = self._createDefault16ColorColorTable()
        observedSlots = []

        for slot in self.op.inputs.values() + self.op.outputs.values():
            if slot.level == 0 or slot.level == 1:
                observedSlots.append(slot)

        for slot in observedSlots:
            print slot
        # data = self.op.LabelNames.value
        # print data
        # data = self.op.Input.get(slice(None)).wait()
        # print data.shape, 'SADD'

        # subscribe to dirty notifications of input data
        # TODO

        # set variables
        # TODO

        # load and initialize user interfaces
        self._initCentralUic()
        self._initAppletDrawerUic()

        self._isReportStatusDirty = False
        self.op.ReportStatus.notifyDirty(self._reportStatus)


    def _reportStatus(self, *args, **kwargs):
        self._isReportStatusDirty = True

    def _initCentralUic(self):
        """
        Load the ui for the main window
        """
        # create layout
        localDir = os.path.split(__file__)[0]
        uic.loadUi(localDir+"/report_main.ui", self)
        
        self._fnt_props = {'fontweight':'bold','fontsize':'small'}
        expandingPolicy = QSizePolicy(QSizePolicy.Expanding, 
                                      QSizePolicy.Expanding)

        # Volume pie chart
        self._vol_fig = Figure()
        self._vol_canvas = FigureCanvas(self._vol_fig)
        self._vol_canvas.setParent(self)
        self._vol_canvas.setSizePolicy(expandingPolicy)
        # create and initialize plot axis
        self._vol_axis = self._vol_fig.add_subplot(111, aspect='equal')
        self.set_axis_properties(self._vol_axis)

        # Scatter plot
        self._scatter_fig = Figure()
        self._scatter_canvas = FigureCanvas(self._scatter_fig)
        self._scatter_canvas.setParent(self)
        self._scatter_canvas.setSizePolicy(expandingPolicy)
        # create and initialize plot axis
        self._scatter_axis = self._scatter_fig.add_subplot(111)
        self.set_axis_properties(self._scatter_axis)
        

        # Histogram plot
        self._histo_fig = Figure()
        self._histo_canvas = FigureCanvas(self._histo_fig)
        self._histo_canvas.setParent(self)
        self._histo_canvas.setSizePolicy(expandingPolicy)
        # create and initialize plot axis
        self._histo_axis = self._histo_fig.add_subplot(111)
        self.set_axis_properties(self._histo_axis)
        self._bins = 64

        # result summary table
        # TODO
        self._vol_table = QTableView()
        self._vol_table.setSizePolicy(expandingPolicy)
        header = ['Label','Voxel Count', 'Relative [%]']
        # data_list = [('Dummy', 0, 0)]
        data_list = [()]
        table_model = MriTableModel(self, data_list, header)
        self._vol_table.setModel(table_model)
        # font = QFont("Courier New", 14)
        # table_view.setFont(font)
        # set column width to fit contents (set font first!)

        self.bottomLeft.insertWidget(0,self._vol_canvas)
        self.bottomRight.insertWidget(0,self._vol_table)

        self.topLeft.insertWidget(0,self._scatter_canvas)
        self.topRight.insertWidget(0,self._histo_canvas)

        self.pushButtonCSV.clicked.connect(self.exportToCSV)
        # self.label.setText('adasdad')

    def exportToCSV(self):
        # TODO write header
        path = QFileDialog.getSaveFileName(
            self, 'Save File', '', 'CSV(*.csv)')
        if not path.isEmpty():
            with open(unicode(path), 'wb') as stream:
                writer = csv.writer(stream)
                for row in range(self._vol_table.model().rowCount()):
                    rowdata = []
                    for column in range(self._vol_table.model().columnCount()):
                        entry = self._vol_table.model().data[row][column]
                        if entry is not None:
                            rowdata.append( unicode(entry).encode('utf8') )
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)

    def update_table(self, data_list):
        self._vol_table.model().setData(data_list)
        self._vol_table.resizeColumnsToContents()


    def set_axis_properties(self, axis, ftsize='small', ftweight='bold'):
        for tick in axis.xaxis.get_major_ticks():
            tick.label1.set_fontsize(ftsize)
            tick.label1.set_fontweight(ftweight)
        for tick in axis.yaxis.get_major_ticks():
            tick.label1.set_fontsize(ftsize)
            tick.label1.set_fontweight(ftweight)

        for ax in ['top','bottom','left','right']:
             axis.spines[ax].set_linewidth(1.5)
       
    def clear_figure(self, axis):
        axis.clear()
        axis.grid(True)

    def showEvent(self, event):
        if self._isReportStatusDirty:
            print 'ReportStatus Dirty' , event
            self._get_data()
            self._plot_volume()
            self._isReportStatusDirty = False
        else:
            print 'ReportStatus Clean'

    def _get_data(self):
        # TODO only ask for data if it is dirty
        self._active_channels = np.nonzero(self.op.ActiveChannels.value)[0]
        self._mask = self.op.Input[...].wait().squeeze()
        self._raw = self.op.RawInput[...].wait().squeeze()
        self._labels = self.op.LabelNames.value

    def _plot_volume(self):
        counts = np.bincount(self._mask.ravel())

        abs_counts = []
        labels = []
        colors = []
        data_list = []
        for i in range(counts.size):
            if i in self._active_channels:
                print self._labels[i], counts[i+1]
                labels.append(self._labels[i])
                abs_counts.append(counts[i+1])
                colors.append(self._channelColors[i])
                data_list.append((self._labels[i], str(counts[i+1])))
        abs_counts = np.array(abs_counts, dtype=np.uint32)
        percentage = abs_counts/np.float(abs_counts.sum())

        data_list = [x + ('{0:.2f}'.format(percentage[idx]*100),) for idx,x in enumerate(data_list)]

        print '##################################################'
        print percentage, 'Perc'
        print abs_counts, 'ABS'
        print labels
        print colors

        explode = (0.1,)*len(labels) 

        self.clear_figure(self._vol_axis)
        self._vol_axis.pie(percentage, 
                           labels=labels,explode=explode, 
                           colors=colors, autopct='%1.1f%%', 
                           shadow=True, 
                           textprops=self._fnt_props) #  startangle=90)

        self._vol_canvas.draw()
        self.update_table(data_list)

    def _scatter_plot(self):
        # TODO x- and y- labels according to channel name
        chX = self._drawer.scatterXComboBox.currentIndex()
        chY = self._drawer.scatterYComboBox.currentIndex()
        print self._raw.shape

        self.clear_figure(self._scatter_axis)

        # counts = np.bincount(self._mask.ravel())
        for i in self._active_channels:
            tmp_mask = self._mask==i+1
            print tmp_mask.shape
            X_ = self._raw[...,chX][tmp_mask]
            Y_ = self._raw[...,chY][tmp_mask]
            print self._labels[i]
            print 'X_', X_.size
            print 'Y_', Y_.size
            self._scatter_axis.scatter(X_,Y_,color=self._channelColors[i])

        self._scatter_canvas.draw()

    def _histo_plot(self):
        idx = self._drawer.histogramComboBox.currentIndex()
        self.clear_figure(self._histo_axis)
        min_= 1e6
        max_= -1e6
        for i in self._active_channels:
            tmp_mask = self._mask==i+1
            if self._raw[...,idx][tmp_mask].min() < min_:
                min_ = self._raw[...,idx][tmp_mask].min()
            if self._raw[...,idx][tmp_mask].max() > max_:
                max_ = self._raw[...,idx][tmp_mask].max()
                
        handels = [None]*len(self._active_channels)
        for x,i in enumerate(self._active_channels):
            tmp_mask = self._mask==i+1
            n, bins, patches = \
                        self._histo_axis.hist(self._raw[...,idx][tmp_mask],
                                              self._bins, normed=1, 
                                              histtype='stepfilled',
                                              color=self._channelColors[i],
                                              alpha=0.4)
            '''
            bins,edges = np.histogram(self._raw[...,idx][tmp_mask],
                                      bins=self._bins,
                                      density=True,
                                      range=[min_,max_])
            left,right = edges[:-1],edges[1:]
            X = np.array([left,right]).T.flatten()
            Y = np.array([bins,bins]).T.flatten()
            handels[x], = self._histo_axis.plot(X,Y,'-',
                                            color=self._channelColors[i],
                                                lw=1.5)
            '''
        self._histo_canvas.draw()

    def _onApplyButtonClicked(self):
        '''
        if self.op.Input.ready():
            print self.op.Input.meta.getTaggedShape()
            data = self.op.Input[...].wait()
            print data.shape
        '''
        # test = self.op.ReportStatus.value
        # When the output slot is called the execute method is triggered
        # self.op.computeVolume()
        self._get_data()
        self._plot_volume()
        self._scatter_plot()
        self._histo_plot()


    def _initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer
        """
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/report_drawer.ui")
        
        self._drawer.applyButton.clicked.connect( self._onApplyButtonClicked )

        ts = self.op.RawInput.meta.getTaggedShape()
        for i in range(ts['c']):
            ch_ = 'MRI Channel {}'.format(i)
            self._drawer.histogramComboBox.addItem( ch_ )
            self._drawer.scatterXComboBox.addItem( ch_ )
            self._drawer.scatterYComboBox.addItem( ch_ )

        self._drawer.histogramComboBox.currentIndexChanged.connect( \
                                                self._histoChannelChanged )
        self._drawer.scatterXComboBox.currentIndexChanged.connect( \
                                                self._scatterXChannelChanged )
        self._drawer.scatterYComboBox.currentIndexChanged.connect( \
                                                self._scatterYChannelChanged )

    def _histoChannelChanged(self):
        idx = self._drawer.histogramComboBox.currentIndex()
        print 'Histogram channel changed to {}'.format(idx)

    def _scatterXChannelChanged(self):
        idx = self._drawer.scatterXComboBox.currentIndex()
        print 'ScatterX channel changed to {}'.format(idx)

    def _scatterYChannelChanged(self):
        idx = self._drawer.scatterYComboBox.currentIndex()
        print 'ScatterY channel changed to {}'.format(idx)

    def _createDefault16ColorColorTable(self):
        colors = []

        # SKIP: Transparent for the zero label
        # colors.append(QColor(0,0,0,0))

        # ilastik v0.5 colors
        colors.append( QColor( Qt.red ) )
        colors.append( QColor( Qt.green ) )
        colors.append( QColor( Qt.yellow ) )
        colors.append( QColor( Qt.blue ) )
        colors.append( QColor( Qt.magenta ) )
        colors.append( QColor( Qt.darkYellow ) )
        colors.append( QColor( Qt.lightGray ) )

        # Additional colors
        colors.append( QColor(255, 105, 180) ) #hot pink
        colors.append( QColor(102, 205, 170) ) #dark aquamarine
        colors.append( QColor(165,  42,  42) ) #brown
        colors.append( QColor(0, 0, 128) )     #navy
        colors.append( QColor(255, 165, 0) )   #orange
        colors.append( QColor(173, 255,  47) ) #green-yellow
        colors.append( QColor(128,0, 128) )    #purple
        colors.append( QColor(240, 230, 140) ) #khaki

        colors.append( QColor(192, 192, 192) ) #silver

#        colors.append( QColor(69, 69, 69) )    # dark grey
#        colors.append( QColor( Qt.cyan ) )

        assert len(colors) == 16
        return [c.getRgbF() for c in colors]


class MriTableModel( QAbstractTableModel ):
    def __init__(self, parent, data, header, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.data = data
        self.header = header

    def rowCount(self, parent=QModelIndex()):
        return len(self.data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.data[0])

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            return QVariant(self.data[index.row()][index.column()])
        elif role == Qt.TextAlignmentRole:
           return QVariant(Qt.AlignLeft | Qt.AlignCenter | Qt.AlignCenter)
        
        return QVariant() 
    
    def setData(self, newData):
        print 'Updating Model'
        print newData
        self.layoutAboutToBeChanged.emit()
        self.data = newData
        self.layoutChanged.emit()

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None
