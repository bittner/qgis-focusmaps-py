# -*- coding: utf-8 -*-
"""
/***************************************************************************
FocusMap
                                 QGIS FocusMap plugin
QGIS Normalization Plugin
                             -------------------
        begin                : 2014-07-03
        copyright            : (C) 2014 by GFZ
        email                : wangying220062@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This is the main dialog file.
"""

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import os

from ui_focusmap import Ui_FocusMap

class FocusMapDialog(QtGui.QDialog, Ui_FocusMap):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_FocusMap()
        self.ui.setupUi(self)
        
        layers=QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers: 
            if layer.type() == QgsMapLayer.RasterLayer:          
                self.ui.RasterLayers.addItem(layer.name())
        
        # set the weight input area as invisible at the beginning 
        self.ui.lineEdit_w1.setVisible(False)
        self.ui.lineEdit_w2.setVisible(False)
        self.ui.lineEdit_w3.setVisible(False)
        self.ui.lineEdit_w4.setVisible(False)
        self.ui.lineEdit_w5.setVisible(False)
        self.ui.lineEdit_w6.setVisible(False)

        # Connect the signals to the functions 
        QObject.connect(self.ui.ChooseLayerButton, SIGNAL("clicked()"), self.chooseLayer)
        QObject.connect(self.ui.UnchooseLayerButton, SIGNAL("clicked()"), self.unchooseLayer)
        QObject.connect(self.ui.OKButton, SIGNAL("clicked()"), self.ok)
        QObject.connect(self.ui.CancelButton, SIGNAL("clicked()"),self.reject)
        QObject.connect(self.ui.Button_path, SIGNAL("clicked()"), self.outputpath)
        QObject.connect(self.ui.helpButton, SIGNAL("clicked()"), self.show_help)
    
    # function chooseLayer, choose layers from the raster layer box,at the same time show the corresponding weight input area
    def chooseLayer(self):

        chosenitems = self.ui.RasterLayers.selectedItems()
        for item in chosenitems:
            self.ui.ChosenLayers.addItem(self.ui.RasterLayers.takeItem(self.ui.RasterLayers.row(item)))
        if self.ui.ChosenLayers.count()==1:
            self.ui.lineEdit_w1.setVisible(True)
        if self.ui.ChosenLayers.count()==2:
            self.ui.lineEdit_w2.setVisible(True)
        if self.ui.ChosenLayers.count()==3:
            self.ui.lineEdit_w3.setVisible(True)
        if self.ui.ChosenLayers.count()==4:
            self.ui.lineEdit_w4.setVisible(True)
        if self.ui.ChosenLayers.count()==5:
            self.ui.lineEdit_w5.setVisible(True)
        if self.ui.ChosenLayers.count()==6:
            self.ui.lineEdit_w6.setVisible(True)
            self.ui.ChooseLayerButton.setEnabled(False)

    # function unchooseLayer, delete layers from the chosen raster layers box and the corresponding weight
    def unchooseLayer(self):  
        unchosenitems = self.ui.ChosenLayers.selectedItems()
        for item in unchosenitems:
            self.ui.RasterLayers.addItem(self.ui.ChosenLayers.takeItem(self.ui.ChosenLayers.row(item)))
        if self.ui.ChosenLayers.count()==1:
            self.ui.lineEdit_w2.setVisible(False)
        if self.ui.ChosenLayers.count()==2:
            self.ui.lineEdit_w3.setVisible(False)
        if self.ui.ChosenLayers.count()==3:
            self.ui.lineEdit_w4.setVisible(False)
        if self.ui.ChosenLayers.count()==4:
            self.ui.lineEdit_w5.setVisible(False)
        if self.ui.ChosenLayers.count()==5:
            self.ui.lineEdit_w6.setVisible(False)
            self.ui.ChooseLayerButton.setEnabled(True)
        if self.ui.ChosenLayers.count()==0:
            self.ui.lineEdit_w1.setVisible(False)
    
    # function outputpath, to define the output image path
    def outputpath(self):
        fileName = QFileDialog.getSaveFileName(self,"Output Image", "~/","GeoTIFF (*.tiff *.tif)");
                
        if fileName !="":
            if  os.path.splitext(fileName)[1] :
                if  os.path.splitext(fileName)[1] == ".tif" or os.path.splitext(fileName)[1] == ".tiff":
                    self.ui.lineEdit_outputpath.setText(fileName)
                else:
                    self.ui.lineEdit_outputpath.setText(os.path.splitext(fileName)[0]+'.tif')
            else:
                self.ui.lineEdit_outputpath.setText(fileName+'.tif')

    # function show_help, helps to show help document to users
    def show_help(self):
        help_file = 'file:///%s/focushtml/help.html' % os.path.dirname(__file__)
        QDesktopServices.openUrl(QUrl(help_file))

    # set acceptance condition of ok button
    def ok(self):       
        if self.ui.pcomboBox.currentText()=='Selected':
            if self.ui.ChosenLayers.currentItem() is None:
                QMessageBox.information(None, "Warning", "Please choose a layer for match resolution!")
                return
        self.accept()