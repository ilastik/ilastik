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
from collections import defaultdict, OrderedDict

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

        # for slot in observedSlots:
          #  print slot
        # data = self.op.LabelNames.value
        # print data
        # data = self.op.Input.get(slice(None)).wait()
        # print data.shape, 'SADD'

        # subscribe to dirty notifications of input data
        # TODO

        # set variables
        # TODO

        self._availablePlots = OrderedDict()
        self._availablePlots['Volume'] = 'volume'
        self._availablePlots['Relative Composition'] = 'percentage'
        self._availablePlots['Volume Change (previous)'] = 'delta'
        self._availablePlots['Volume Change (baseline)'] = 'baseline'
        
        # load and initialize user interfaces
        self._initCentralUic()
        self._initAppletDrawerUic()

        self._isReportStatusDirty = True
        self.op.Input.notifyDirty( self._reportStatus )

    def _reportStatus(self, *args, **kwargs):
        print 'Report input has changed'
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

        # Volume fig 1-3
        self._vol_fig1 = Figure()
        self._vol_canvas1 = FigureCanvas(self._vol_fig1)
        self._vol_canvas1.setParent(self)
        self._vol_canvas1.setSizePolicy(expandingPolicy)
        # create and initialize plot axis
        self._vol_axis1 = self._vol_fig1.add_subplot(111)#, aspect='equal')
        self.set_axis_properties(self._vol_axis1)

        self._vol_fig2 = Figure()
        self._vol_canvas2 = FigureCanvas(self._vol_fig2)
        self._vol_canvas2.setParent(self)
        self._vol_canvas2.setSizePolicy(expandingPolicy)
        # create and initialize plot axis
        self._vol_axis2 = self._vol_fig2.add_subplot(111)#, aspect='equal')
        self.set_axis_properties(self._vol_axis2)

        self._vol_fig3 = Figure()
        self._vol_canvas3 = FigureCanvas(self._vol_fig3)
        self._vol_canvas3.setParent(self)
        self._vol_canvas3.setSizePolicy(expandingPolicy)
        # create and initialize plot axis
        self._vol_axis3 = self._vol_fig3.add_subplot(111)#, aspect='equal')
        self.set_axis_properties(self._vol_axis3)

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

        self.topLeft.insertWidget(0,self._vol_canvas1)
        self.topRight.insertWidget(0,self._vol_canvas2)

        self.bottomLeft.insertWidget(0,self._vol_canvas3)
        self.bottomRight.insertWidget(0,self._vol_table)

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
        pass
        '''
        if self._isReportStatusDirty:
            print 'ReportStatus Dirty' , event
            # self._get_data()
            # self._compute_values()
            self._isReportStatusDirty = False
        else:
            print 'ReportStatus Clean'
        '''
    def _get_data(self):
        # TODO only ask for data if it is dirty HOW? 
        # connect this function to notifydirty of input data
        self._active_channels = np.nonzero(self.op.ActiveChannels.value)[0]
        self._mask = self.op.Input[...].wait()
        # self._raw = self.op.RawInput[...].wait().squeeze()
        # print self._raw.shape
        print self._mask.shape
        self._labels = self.op.LabelNames.value

    def _compute_values(self):
        """
        Function computes 'volume', percentage change of volume ('delta'), 
        'total' volume (all foreground classes combined) and 
        relative contribution ('percentage') of the tumor classes
        for each timepoint
        """
        assert len(self._mask.shape) == 5, 'Data is not 5D (txyzc)'
        timepoints = self._mask.shape[0]
        total = []
        colors = {}
        values = defaultdict(list)
        for t in range(timepoints):
            counts = np.bincount(self._mask[t].ravel())
            tmp_total = 0.0
            for i in range(counts.size):
                if i in self._active_channels:
                    # print self._labels[i], counts[i+1]
                    values[self._labels[i]].append(counts[i+1])
                    colors[self._labels[i]]= self._channelColors[i]
                    tmp_total += counts[i+1]
            total.append(tmp_total)
        total = np.array(total)

        self._values = defaultdict(dict) 
        for k,v in values.iteritems():
            self._values[k].update({'volume': np.array(v)})
            self._values[k].update({'percentage':np.array(v)/total})
            self._values[k].update({'color':colors[k]})
            if timepoints > 1:
                delta_total = (np.array(v)[1:]/ \
                               np.array(v,dtype=np.float32)[:-1])*100.0-100.0
                delta_total = np.insert(delta_total,0,0.0)
                self._values[k].update({'delta':delta_total})
                baseline = np.array([100.*(i/v[0])-100.0 for i in np.array(v,
                                        dtype=np.float32)],dtype=np.float32)
                self._values[k].update({'baseline':baseline})
        self._values['Total'].update({'volume' : np.array(total)})
        self._values['Total'].update({'color':(0.0, 0.0, 0.0, 1.0)}) #black
        if timepoints > 1:
            delta_total = (total[1:]/total[:-1])*100.0-100.0
            delta_total = np.insert(delta_total,0,0.0)
            self._values['Total'].update({'delta':delta_total})
            baseline = np.array([100.*(i/total[0])-100.0 for i in total], 
                                dtype=np.float32)
            self._values['Total'].update({'baseline':baseline})
        print self._values 

    def plot_timecourse(self, axis, canvas, mode='volume'):
        # TODO If only one timepoint make pie chart
        self.clear_figure(axis)
        for k,v in self._values.iteritems():
            if mode == 'volume':
                data = v[mode].astype(np.float32)/1000.
                axis.plot(data,'o-', color = v['color'],
                          label=k, lw=2.5)
            elif mode == 'percentage':
                if k != 'Total':
                    data = v[mode].astype(np.float32)
                    axis.plot(data,'o-', color = v['color'],
                              label=k, lw=2.5)
            elif mode == 'delta' or mode == 'baseline':
                data = v[mode].astype(np.float32)
                axis.plot(data,'o-', color = v['color'],
                          label=k, lw=2.5)
                

        if mode == 'volume':
            axis.set_title('Volume', fontweight='bold')
            axis.set_xlabel(str('Timepoint'), fontweight='bold')
            axis.set_ylabel(str('Volume [ml]'), fontweight='bold')
        elif mode == 'delta':
            axis.set_title('$\Delta$ Volume (previous)', 
                           fontweight='bold')
            axis.set_xlabel(str('Timepoint'), fontweight='bold')
            axis.set_ylabel(str('Volume [%]'), fontweight='bold')
            axis.axhline(y=25,color='Gray',ls='dashed')
            axis.axhline(y=-25,color='Gray',ls='dashed')
            axis.fill_between(range(len(data)), -25, 25, 
                                  facecolor='Gray', alpha=0.1)
            ticks = list(axis.yaxis.get_majorticklocs())
            axis.yaxis.set_ticks(ticks + [-25, 25])
        elif mode == 'baseline':
            axis.set_title('$\Delta$ Volume (baseline)', 
                           fontweight='bold')
            axis.set_xlabel(str('Timepoint'), fontweight='bold')
            axis.set_ylabel(str('Volume [%]'), fontweight='bold')
            axis.axhline(y=25,color='Gray',ls='dashed')
            axis.axhline(y=-25,color='Gray',ls='dashed')
            axis.fill_between(range(len(data)), -25, 25, 
                                  facecolor='Gray', alpha=0.1)
            ticks = list(axis.yaxis.get_majorticklocs())
            axis.yaxis.set_ticks(ticks + [-25, 25])
        elif mode == 'percentage':
            axis.set_title('Relative Composition', fontweight='bold')
            axis.set_xlabel(str('Timepoint'), fontweight='bold')
            axis.set_ylabel(str('Composition [%]'), fontweight='bold')

        canvas.draw()


        # Pie chart
        '''
        explode = (0.1,)*len(labels) 

        self.clear_figure(self._vol_axis)
        self._vol_axis.pie(percentage, 
                           labels=labels,explode=explode, 
                           colors=colors, autopct='%1.1f%%', 
                           shadow=True, 
                           textprops=self._fnt_props) #  startangle=90)

        self._vol_canvas.draw()
        self.update_table(data_list)
        '''

    def _onApplyButtonClicked(self):
        if self._isReportStatusDirty:
            self._get_data()
            self._compute_values()
            self._isReportStatusDirty = False 

        mode = str(self._drawer.comboBoxPlot1.currentText())
        self.plot_timecourse(self._vol_axis1, self._vol_canvas1, 
                             mode=self._availablePlots[mode])
        mode = str(self._drawer.comboBoxPlot2.currentText())
        self.plot_timecourse(self._vol_axis2, self._vol_canvas2, 
                             mode=self._availablePlots[mode])
        mode = str(self._drawer.comboBoxPlot3.currentText())
        self.plot_timecourse(self._vol_axis3, self._vol_canvas3, 
                             mode=self._availablePlots[mode])



    def _initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer
        """
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/report_drawer.ui")
        
        self._drawer.applyButton.clicked.connect( self._onApplyButtonClicked )

        for k in self._availablePlots.keys():
            self._drawer.comboBoxPlot1.addItem(k)
            self._drawer.comboBoxPlot2.addItem(k)
            self._drawer.comboBoxPlot3.addItem(k)
        
        self._drawer.comboBoxPlot1.setCurrentIndex(0)
        self._drawer.comboBoxPlot2.setCurrentIndex(1)
        self._drawer.comboBoxPlot3.setCurrentIndex(2)

        self._drawer.comboBoxPlot1.currentIndexChanged.connect( \
                                                self._plot1Changed )
        self._drawer.comboBoxPlot2.currentIndexChanged.connect( \
                                                self._plot2Changed )
        self._drawer.comboBoxPlot3.currentIndexChanged.connect( \
                                                self._plot3Changed )

    def _plot1Changed(self):
        if not self._isReportStatusDirty:
            mode = str(self._drawer.comboBoxPlot1.currentText())
            self.plot_timecourse(self._vol_axis1, self._vol_canvas1, 
                                 mode=self._availablePlots[mode])

    def _plot2Changed(self):
        if not self._isReportStatusDirty:
            mode = str(self._drawer.comboBoxPlot2.currentText())
            self.plot_timecourse(self._vol_axis2, self._vol_canvas2, 
                                 mode=self._availablePlots[mode])

    def _plot3Changed(self):
        if not self._isReportStatusDirty:
            mode = str(self._drawer.comboBoxPlot3.currentText())
            self.plot_timecourse(self._vol_axis3, self._vol_canvas3, 
                                 mode=self._availablePlots[mode])

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
