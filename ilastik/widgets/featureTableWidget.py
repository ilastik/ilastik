# -*- coding: utf-8 -*-
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
from PyQt4.QtGui import QVBoxLayout, QLabel, QPixmap, QPainter, \
                        QTableWidgetItem, QItemDelegate, QStyle, QHBoxLayout, QIcon, QHeaderView, \
                        QAbstractItemView, QDialog, QToolButton, \
                        QTableWidget, QBrush, QColor, QPalette, \
                        QFont, QPen, QPolygon, QSlider, QImage
from PyQt4.QtCore import Qt, QRect, QSize, QEvent, QPoint, pyqtSignal

import numpy
from volumina.utility import decode_to_qstring

class FeatureEntry:
    def __init__(self, name):
        self.name = name

#===============================================================================
# FeatureTableWidgetVHeader
#===============================================================================
class FeatureTableWidgetVHeader(QTableWidgetItem):
    def __init__(self):
        QTableWidgetItem.__init__(self)
        # init
        # ------------------------------------------------
        self.isExpanded = True
        self.isRootNode = False
        self.feature = None
        self.vHeaderName = None
        self.children = []
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        self.setIcon(QIcon(pixmap))
            
    def setExpanded(self):
        self.isExpanded = True
        self._drawIcon()
        
    def setCollapsed(self):
        self.isExpanded = False
        self._drawIcon()
        
    def setIconAndTextColor(self, color):
        self._drawIcon(color)
    
    def setFeatureVHeader(self, feature):
        self.feature = feature
        self.vHeaderName = feature.name
        self.setText(self.vHeaderName)
#        self.featureID = feature.id
        
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        self.setIcon(QIcon(pixmap))
        
    def setGroupVHeader(self, name):
        self.vHeaderName = name
        self.setText(self.vHeaderName)
        self.isRootNode = True
        

    def _drawIcon(self, color=Qt.black):
        self.setForeground(QBrush(color))
        
        if self.isRootNode:
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.transparent)
            painter = QPainter()
            painter.begin(pixmap)
            pen = QPen(color)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(color)
            painter.setRenderHint(QPainter.Antialiasing)
            if not self.isExpanded:
                arrowRightPolygon = [QPoint(6,6), QPoint(6,14), QPoint(14, 10)]
                painter.drawPolygon(QPolygon(arrowRightPolygon))
            else:
                arrowDownPolygon = [QPoint(6,6), QPoint(15,6), QPoint(10, 14)]
                painter.drawPolygon(QPolygon(arrowDownPolygon))
            painter.end()
            self.setIcon(QIcon(pixmap))
        
        
#===============================================================================
# FeatureTableWidgetHHeader
#===============================================================================
class FeatureTableWidgetHHeader(QTableWidgetItem):
    def __init__(self, sigma, window_size, name=None):
        QTableWidgetItem.__init__(self)
        # init
        # ------------------------------------------------
        self.sigma = sigma
        self.window_size = window_size
        self.pixmapSize = QSize(61, 61)
        if not name:
            self.setNameAndBrush(self.sigma)
        else:
            self.setText(name)
    
    @property
    def brushSize(self):
        return int(3.0*self.sigma + 0.5)*2 + 1
        
    def setNameAndBrush(self, sigma, color=Qt.black):
        self.sigma = sigma
        self.setText(decode_to_qstring("σ=%.1fpx" % self.sigma, 'utf-8')) # This file is encoded as utf-8, so this string should be decoded as such.
        total_window = (1 + 2 * int(self.sigma * self.window_size + 0.5) )
        self.setToolTip( "sigma = {:.1f} pixels, window diameter = {:.1f}".format(self.sigma, total_window) )
        font = QFont() 
        font.setPointSize(10)
        font.setBold(True)
        self.setFont(font)
        self.setForeground(color)
                        
        pixmap = QPixmap(self.pixmapSize)
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(color)
        brush = QBrush(color)
        painter.setBrush(brush)
        painter.drawEllipse(QRect(self.pixmapSize.width()/2 - self.brushSize/2, self.pixmapSize.height()/2 - self.brushSize/2, self.brushSize, self.brushSize))
        painter.end()
        self.setIcon(QIcon(pixmap))
        self.setTextAlignment(Qt.AlignVCenter)
        
    def setIconAndTextColor(self, color):
        self.setNameAndBrush(self.sigma, color)
        
        

#===============================================================================
# ItemDelegate
#===============================================================================
class ItemDelegate(QItemDelegate):
    """"
     TODO: DOKU
    """
    def __init__(self, parent, width, height):
        QItemDelegate.__init__(self, parent)
        
        self.itemWidth = width
        self.itemHeight = height
        self.checkedIcon = None
        self.partiallyCheckedIcon = None
        self.uncheckedIcon = None
        self.pixmapUnckecked = QPixmap(self.itemWidth, self.itemHeight)
        self.drawPixmapForUnckecked()
        self.pixmapCkecked = QPixmap(self.itemWidth, self.itemHeight)
        self.drawPixmapForCkecked()
        self.pixmapPartiallyChecked = QPixmap(self.itemWidth, self.itemHeight)
        self.drawPixmapForPartiallyChecked()
        self.drawPixmapForDisabled()

    def drawPixmapForDisabled(self):
        self.pixmapDisabled = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmapDisabled.fill(Qt.white)

    def drawPixmapForUnckecked(self):
        self.pixmapUnckecked = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmapUnckecked.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(self.pixmapUnckecked)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5,5,self.itemWidth-10, self.itemHeight-10))
        painter.end()
        
    def drawPixmapForCkecked(self):
        self.pixmapCkecked = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmapCkecked.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(self.pixmapCkecked)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5,5,self.itemWidth-10, self.itemHeight-10))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawLine(self.itemWidth/2-5, self.itemHeight/2, self.itemWidth/2, self.itemHeight-9)
        painter.drawLine(self.itemWidth/2, self.itemHeight-9, self.itemWidth/2+10, 2)
        painter.end()
        
    def drawPixmapForPartiallyChecked(self):
        self.pixmapPartiallyChecked = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmapPartiallyChecked.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(self.pixmapPartiallyChecked)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5,5,self.itemWidth-10, self.itemHeight-10))
        pen.setWidth(4)
        pen.setColor(QColor(139,137,137))
        painter.setPen(pen)
        painter.drawLine(self.itemWidth/2-5, self.itemHeight/2, self.itemWidth/2, self.itemHeight-9)
        painter.drawLine(self.itemWidth/2, self.itemHeight-9, self.itemWidth/2+10, 2)
        painter.end()
    
    def paint(self, painter, option, index):
        
        tableWidgetCell = self.parent().item(index.row(), index.column())
        
        flags = tableWidgetCell.flags()
        if not (flags & Qt.ItemIsEnabled):
            painter.drawPixmap(option.rect, self.pixmapDisabled)
        elif tableWidgetCell.featureState == Qt.Unchecked:
            if not self.uncheckedIcon == None: 
                painter.drawImage(self.adjustRectForImage(option), self.uncheckedIcon)
            else:
                painter.drawPixmap(option.rect, self.pixmapUnckecked)
                option.state = QStyle.State_Off
        elif tableWidgetCell.featureState == Qt.PartiallyChecked:
            if not self.partiallyCheckedIcon == None:
                painter.drawImage(self.adjustRectForImage(option), self.partiallyCheckedIcon)
            else:
                painter.fillRect(option.rect.adjusted(3,3,-3,-3), QColor(220,220,220))
                painter.drawPixmap(option.rect, self.pixmapPartiallyChecked)
        else:
            if not self.checkedIcon == None:
                painter.drawImage(self.adjustRectForImage(option), self.checkedIcon)
            else:
                painter.fillRect(option.rect.adjusted(3,3,-3,-3), QColor(0,250,154))
                painter.drawPixmap(option.rect, self.pixmapCkecked)
        
        #Be careful with this! It may call itself recursively.
        #self.parent().update()
        
    def setCheckBoxIcons(self, checked, partiallyChecked, unchecked):
        self.checkedIcon = QImage(checked)
        self.partiallyCheckedIcon = QImage(partiallyChecked)
        self.uncheckedIcon = QImage(unchecked)
        
    def adjustRectForImage(self, option):
        if self.itemWidth > self.itemHeight:
            return option.rect.adjusted((self.itemWidth-self.itemHeight)/2+5, 5,-((self.itemWidth-self.itemHeight)/2)-5,-5 )
        else:
            return option.rect.adjusted(5, (self.itemHeight-self.itemWidth)/2+5, -((self.itemHeight-self.itemWidth)/2)-5,-5 )


#===============================================================================
# FeatureTableWidgetItem
#===============================================================================
class FeatureTableWidgetItem(QTableWidgetItem):
    def __init__(self, feature, parent=None, featureState=Qt.Unchecked):
        QTableWidgetItem.__init__(self, parent)

        self.isRootNode = False
        self.children = []
        self.featureState = featureState
        
    def setFeatureState(self, state):
        self.featureState = state
        
    def toggleState(self):
        if self.featureState == Qt.Unchecked:
            self.featureState = Qt.Checked
        else:
            self.featureState = Qt.Unchecked


#===============================================================================
# FeatureTableWidget
#===============================================================================
class FeatureTableWidget(QTableWidget):
    brushSizeChanged = pyqtSignal(float)
        
    def __init__(self, parent = None):
        QTableWidget.__init__(self, parent)
        # init
        # ------------------------------------------------
        #FIXME: move this somewhere else maybe?
        self.tmpSelectedItems = []
        #FIXME: what does this do? put a comment, why 30,30?
        self._sigmaList = None
        self._featureGroupMapping = None # Schema: [ (groupName1, [entry, entry...]),
                                         #           (groupName2, [entry, entry...]) ]
        #layout
        # ------------------------------------------------
        self.setCornerButtonEnabled(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setShowGrid(False)
        self.viewport().installEventFilter(self)
        self.setMouseTracking(1)
        self.verticalHeader().setHighlightSections(False)
        self.verticalHeader().setClickable(True)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setClickable(True)
        
        self.horizontalHeader().setMouseTracking(True)
        self.horizontalHeader().installEventFilter(self)
        self.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)
        
        self.itemSelectionChanged.connect(self._tableItemSelectionChanged)
        self.cellDoubleClicked.connect(self._featureTableItemDoubleClicked)
        self.verticalHeader().sectionClicked.connect(self._expandOrCollapseVHeader)
       
        #FIXME: this feature is disabled for now because it needs proper support
        #in the feature selection operator 
        #self.horizontalHeader().sectionDoubleClicked.connect(self._hHeaderDoubleclicked)
        
#        self.setFeatureGroups(featureMgr.ilastikFeatureGroups.groups)
#        self.setSigmas(self.defaultGroupScaleValues)
#        self.createTableForFeatureDlg()
                        
    # methods
    # ------------------------------------------------
        
        
    def setSelectedFeatureBoolMatrix(self, featureMatrix):
        r = 0
        for row in range(self.rowCount()):
            if self.verticalHeaderItem(row).isRootNode:
                continue
            for column in range(self.columnCount()):
                if featureMatrix[r][column]:
                    self.item(row, column).setFeatureState(Qt.Checked)
                else:
                    self.item(row, column).setFeatureState(Qt.Unchecked)
            r+=1
        self._updateParentCell()

    def setEnableItemMask(self, mask):
        """
        Selectively enable/disable specific items in the table.
        mask - a matrix with the same dimensions as the feature bool matrix.  True means enable, False means disable.
        
        Note: If a cell in a column is disabled, ALL of the cells under 
              that parent in the same column must be disabled.
              Categories of partially enabled cells are not supported yet.
        """
        featureMatrix = numpy.asarray(self.createSelectedFeaturesBoolMatrix())
        assert mask.shape == featureMatrix.shape
        r = 0
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                item = self.item(row, column)
                flags = item.flags()
                if self.verticalHeaderItem(row).isRootNode:
                    # Check all children
                    num_children = len(item.children)
                    child_status = mask[r:r+num_children, column]
                    enabled = child_status.any()
                else:
                    enabled = mask[r][column]
                if enabled:
                    flags |= Qt.ItemIsEnabled
                else:
                    flags &= ~Qt.ItemIsEnabled
                item.setFlags(flags)

            if not self.verticalHeaderItem(row).isRootNode:
                r+=1

        self._updateParentCell()

    def setSelectedFeatureList(self, featureList):
        for feature in featureList:
            for r,c in self._tableEntries():
                if feature[0] == self.verticalHeaderItem(r).vHeaderName and feature[1] == str(self.horizontalHeaderItem(c).sigma):
                    self.item(r,c).setFeatureState(Qt.Checked)
        self._updateParentCell()
    
    def createSelectedFeaturesBoolMatrix(self):
        i = 0
        for r in range(self.rowCount()):
            if not self.verticalHeaderItem(r).isRootNode:
                i+=1
        matrix = [[False for k in range(self.columnCount())] for j in range(i)]
        x=0
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                item = self.item(row,column)
                if not item.isRootNode: 
                    if item.featureState == Qt.Checked:
                        matrix[x][column] = True
            if not self.verticalHeaderItem(row).isRootNode:
                x+=1
        return matrix
    
    def createSelectedFeatureList(self):
        result = []
        for r,c in self._tableEntries():
            item = self.item(r,c)
            if not item.isRootNode:
                if item.featureState == Qt.Checked:
                    result.append([self.verticalHeaderItem(r).vHeaderName, str(self.horizontalHeaderItem(c).sigma)])
        return result
    
    def createTableForFeatureDlg(self, featureGroups, sigmas, window_size, text=None):
        """
        featureGroups: A list with schema: [ (groupName1, [entry, entry...]),
                                             (groupName2, [entry, entry...]), ... ]
        sigmas: List of sigmas (applies to all features)
        """
        self._sigmaList = sigmas
        self._featureGroupMapping = featureGroups
        if self._sigmaList is None:
            raise RuntimeError("No sigmas set!")
        self._addHHeader(window_size, text)
        if self._featureGroupMapping is None:
            raise RuntimeError("No featuregroups set!")
        self._addVHeader()
        self._setFixedSizeToHeaders()
        self._fillTabelWithItems()
        self._setSizeHintToTableWidgetItems()
        self.itemDelegate = ItemDelegate(self, self.horizontalHeader().sizeHint().width(), self.verticalHeader().sizeHint().height())
        self.setItemDelegate(self.itemDelegate)
        self._updateParentCell()

        # Hide fine-grain control by default
        self._collapsAllRows()

    def createSigmaList(self):
        result = []
        for c in range(self.columnCount()):
            result.append(self.horizontalHeaderItem(c).sigma)
        return result
    
    def _tableEntries(self):
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                yield row,column
            
    def sizeHint(self):
        height = super(FeatureTableWidget, self).sizeHint().height()
        width  = self.horizontalHeader().sizeHint().width() * self.columnCount() + self.verticalHeader().sizeHint().width() + 22
        return QSize(width, height)
    
    def _setSizeHintToTableWidgetItems(self):
        width = self.horizontalHeader().sizeHint().width()
        height = self.verticalHeader().sizeHint().height()
        for r,c in self._tableEntries():
            self.item(r,c).setSizeHint(QSize(width, height))
        
    
    def _setFixedSizeToHeaders(self):
        hHeaderSize = self.horizontalHeader().sizeHint()
        vHeaderSize = self.verticalHeader().sizeHint()
        for i in range(self.columnCount()):
            self.horizontalHeaderItem(i).setSizeHint(hHeaderSize)
        for j in range(self.rowCount()):
            self.verticalHeaderItem(j).setSizeHint(vHeaderSize)
    
    def _hHeaderDoubleclicked(self, col):
        sliderdlg = SliderDlg(self, self.horizontalHeaderItem(col).sigma)
#        self._highlightHeaders(col, -1)
        self.horizontalHeaderItem(col).setNameAndBrush(sliderdlg.exec_())
   
    def _fillTabelWithItems(self):
        for j in range(self.columnCount()):
            for i in range(self.rowCount()):
                item = FeatureTableWidgetItem(self, 0)
                if self.verticalHeaderItem(i).isRootNode:
                    item.isRootNode = True
                self.setItem(i,j, item)
        for j in range(self.columnCount()):
            for i in range(self.rowCount()):
                if self.verticalHeaderItem(i).isRootNode:
                    parent = self.item(i,j)
                    continue
                parent.children.append(self.item(i,j))
    
    def _expandOrCollapseVHeader(self, row):
        vHeader = self.verticalHeaderItem(row)
        if not vHeader.children == []:
            if vHeader.isExpanded == False:
                vHeader.setExpanded()
                for subRow in vHeader.children:
                    self.showRow(subRow)
            else:
                for subRow in vHeader.children:
                    self.hideRow(subRow)
                    vHeader.setCollapsed()
            self._deselectAllTableItems()
    
    def _collapsAllRows(self):
        for i in range(self.rowCount()):
            if not self.verticalHeaderItem(i).isRootNode:
                self.hideRow(i)
            else:
                self.verticalHeaderItem(i).setCollapsed()
    
    def _tableItemSelectionChanged(self):
        for item in self.selectedItems():
            if item in self.tmpSelectedItems:
                self.tmpSelectedItems.remove(item)
            else:
                if item.isRootNode and self.verticalHeaderItem(item.row()).isExpanded == False:
                    if item.featureState == Qt.Unchecked or item.featureState == Qt.PartiallyChecked:
                        state = Qt.Checked
                    else:
                        state = Qt.Unchecked
                    for child in item.children:
                        child.setFeatureState(state)
                else:
                    item.toggleState()
                
        for item in self.tmpSelectedItems:
            if item.isRootNode and not self.verticalHeaderItem(item.row()).isExpanded:
                if item.featureState == Qt.Unchecked or item.featureState == Qt.PartiallyChecked:
                    state = Qt.Checked
                else:
                    state = Qt.Unchecked
                for child in item.children:
                    child.setFeatureState(state)
            else:
                item.toggleState()
             
        self._updateParentCell()
        self.tmpSelectedItems = self.selectedItems()
                
        
    def _updateParentCell(self):
        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                item = self.item(i, j)
                if item.isRootNode:
                    x = 0
                    for child in item.children:
                        if child.featureState == Qt.Checked:
                            x += 1
                    if len(item.children) == x:
                        item.featureState = Qt.Checked
                    elif x == 0:
                        item.featureState = Qt.Unchecked
                    else:
                        item.featureState = Qt.PartiallyChecked
            self.viewport().update()


    def eventFilter(self, obj, event):
        if(event.type()==QEvent.MouseButtonPress):
            if event.button() == Qt.LeftButton:
                if self.itemAt(event.pos()):
                    self.setSelectionMode(2)
        if(event.type()==QEvent.MouseButtonRelease):
            if event.button() == Qt.LeftButton:
                self.setSelectionMode(0)
                self.tmpSelectedItems = []
                self._deselectAllTableItems()
        if event.type() == QEvent.MouseMove:
            if self.itemAt(event.pos()) and self.underMouse():
                item = self.itemAt(event.pos())
                hHeader = self.horizontalHeaderItem(item.column())
                self.brushSizeChanged.emit(hHeader.brushSize)
                self._highlightHeaders(item.column(), item.row())
        return super(FeatureTableWidget, self).eventFilter(obj, event)
        
    def _deselectAllTableItems(self):
        for item in self.selectedItems():
            item.setSelected(False)

    
    def _addHHeader(self, window_size, text=None):
        self.setColumnCount(len(self._sigmaList))
        for c in range(len(self._sigmaList)):
            if not text:
                hHeader = FeatureTableWidgetHHeader(self._sigmaList[c], window_size)
            else:
                hHeader = FeatureTableWidgetHHeader(self._sigmaList[c], window_size, text[c])
            self.setHorizontalHeaderItem(c, hHeader)

    
    def _addVHeader(self):
        row = 0
        for group, features in self._featureGroupMapping:
            self.insertRow(row)
            vGroupHeader = FeatureTableWidgetVHeader()
            vGroupHeader.setGroupVHeader(group)
            self.setVerticalHeaderItem(row, vGroupHeader)
            row += 1
            for feature in features:
                self.insertRow(row)
                vFeatureHeader = FeatureTableWidgetVHeader()
                vFeatureHeader.setFeatureVHeader(feature)
                self.setVerticalHeaderItem(row, vFeatureHeader)
                #Tooltip
                #self.verticalHeaderItem(row).setData(3, j.name)
                vGroupHeader.children.append(row)
                row += 1
                
                
    def _highlightHeaders(self, c, r):       
        p = QPalette()
        for i in range(self.columnCount()):
            col = self.horizontalHeaderItem(i)
            if i == c:
                col.setIconAndTextColor(p.link().color())
            else:
                col.setIconAndTextColor(p.text().color())
            
        for j in range(self.rowCount()):
            row = self.verticalHeaderItem(j)
            if j == r:
                row.setIconAndTextColor(p.link().color())
            else:
                row.setIconAndTextColor(p.text().color())
        
        
    def _featureTableItemDoubleClicked(self, row, column):
        item = self.item(row, column)
        if item.isRootNode and self.verticalHeaderItem(item.row()).isExpanded == True:
            if item.featureState == Qt.Unchecked or item.featureState == Qt.PartiallyChecked:
                state = Qt.Checked
            else:
                state = Qt.Unchecked
            for child in item.children:
                child.setFeatureState(state)
        self._updateParentCell()
                
                
                
#===============================================================================
# SliderDlg
#===============================================================================
class SliderDlg(QDialog):
    def __init__(self, parent, sigma):
        QDialog.__init__(self, parent, Qt.FramelessWindowHint)
        
        # init
        # ------------------------------------------------
        self.oldSigma = sigma
        self.sigma = sigma
        self.brushSize = 0
        self.setStyleSheet("background-color:window;")
        # widgets and layouts
        # ------------------------------------------------
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        labelsLayout =  QHBoxLayout()
        self.labelSigma = QLabel("Sigma: xx")
        self.labelBrushSize = QLabel("BrushSize: xx")
        labelsLayout.addWidget(self.labelSigma)
        labelsLayout.addWidget(self.labelBrushSize)
        self.layout.addLayout(labelsLayout)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(100)
        self.slider.sliderMoved.connect(self.on_sliderMoved)
        self.layout.addWidget(self.slider)
        
        self.buttonsLayout = QHBoxLayout()
        self.cancel = QToolButton()
        self.cancel.setText("cancel")
        self.cancel.clicked.connect(self.on_cancelClicked)
        self.buttonsLayout.addWidget(self.cancel)
        
        
        self.ok = QToolButton()
        self.ok.setText("OK")
        self.ok.clicked.connect(self.on_okClicked)
        self.buttonsLayout.addWidget(self.ok)

        self.layout.addLayout(self.buttonsLayout)
        
        self.layout.setContentsMargins(10, 0, 10, 0)
        labelsLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonsLayout.setContentsMargins(0, 0, 0, 0)
        
        self.setlabelSigma()
        self.setLabelBrushSize()
        self.setSliderPosition()
        
    def setlabelSigma(self):
        self.labelSigma.setText("Sigma: " + str(self.sigma))
        
    def setLabelBrushSize(self):
        self.brushSize = int(3.0*self.sigma + 0.5)*2 + 1
        self.labelBrushSize.setText("BrushSize: " + str(self.brushSize))
        
    def setSliderPosition(self):
        self.slider.setSliderPosition(self.sigma*10)
    
    def on_sliderMoved(self, i):
        self.sigma = float(i)/10
        self.setlabelSigma()
        self.setLabelBrushSize()
        self.parent().parent().parent().preView.setSizeToLabel(self.brushSize)
    
    def on_cancelClicked(self):
        self.reject()
        
    def on_okClicked(self):
        self.accept()
        
    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            return  self.sigma
        else:
            return self.oldSigma

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication

    app = QApplication([])
    t = FeatureTableWidget()
    t.createTableForFeatureDlg( \
        (("Color", [FeatureEntry("Banana")] ), ("Edge",  [FeatureEntry("Mango"), FeatureEntry("Cherry")] )),
        [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0],
        3.5)
    t.show()
    t.raise_()
    app.exec_()


        
