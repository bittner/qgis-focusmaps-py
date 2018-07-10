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
 This is the main plugin file.
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from gdalconst import *
import numpy as np
import gdal
import string
import osr
import ogr
import sys
import os

from osgeo import gdal, gdalconst, ogr, osr

# Initialize Qt resources from file resources.py
import resources_rc

# Import the code for the dialog
from maindialog import FocusMapDialog

# Import the python processing function
from library.functions import getMapLayerByName, addtocanva, mask_from_geometry

gdal.AllRegister()

class Main:   
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        
    def initGui(self):
        self.toolBar = self.iface.addToolBar("FocusMap")
        # Create action that will start plugin configuration
        self.action_focus = QAction(QIcon(":/plugins/FocusMap/icons/focus.png"), "Focus", self.iface.mainWindow())
        # Connect the action to the run method
        self.action_focus.triggered.connect(self.focus)
        # Add toolbar button and menu item
        self.toolBar.addAction(self.action_focus)
        self.iface.addPluginToMenu(u"&FocusMap", self.action_focus)
   
    def unload(self):
        self.iface.removePluginMenu(u"&FocusMap", self.action_focus)
        self.iface.removeToolBarIcon(self.action_focus)
                        
    # function check helps to check if the input layers fulfill all the conditions,
    #check if SRS, pixel resulotions match, and if input layers have overlapped area.
    def check(self):
        # get the amount of chosen layers        
        countn=self.dlg.ui.ChosenLayers.count()

        layer=[]
        origX=[]
        origY=[]
        maxX=[]
        maxY=[]
        SRS=[]
        we=[]
        ns=[]
        cols=[]
        rows=[]
        noDataValue=[]

        ######### with this loop, store all the corresponding information into these arrays#########
        for i in range(0,countn):
            # get the layername
            layername_i=self.dlg.ui.ChosenLayers.item(i).text()

            #get layer by its layername and store it in the array 'layer'
            layer_i=getMapLayerByName(layername_i)
            layer.append(layer_i)

            # get the original layer_i source's path 
            source_i=layer_i.source()
            # get source image 
            image_i=gdal.Open(source_i)
            # get the geo-transform
            geotransform_i=image_i.GetGeoTransform()
            # get the pixel resolutions 
            we_i=geotransform_i[1]
            ns_i=geotransform_i[5]
            # get the projection
            Ri=image_i.GetProjection()
            # get the spatial reference system
            SRS_i=osr.SpatialReference(Ri)
            # get Numbers of rows and columns of layer source 
            cols_i=image_i.RasterXSize
            rows_i=image_i.RasterYSize

            # get the origin x and origin y
            origX_i=geotransform_i[0]
            origY_i=geotransform_i[3]
            # calculate the max x and max y
            maxX_i = origX_i + (cols_i*we_i)
            maxY_i = origY_i + (rows_i*ns_i)
            # get the nodatavalue
            nodatavalue=image_i.GetRasterBand(1).GetNoDataValue()
            
            # store all the information got from above into arrays
            origX.append(origX_i) 
            origY.append(origY_i)
            maxX.append(maxX_i)
            maxY.append(maxY_i)
            SRS.append(str(SRS_i))
            we.append(we_i)
            ns.append(ns_i)
            cols.append(cols_i)
            rows.append(rows_i)
            noDataValue.append(nodatavalue)
        
        path=os.path.dirname(unicode(layer[0].source()).encode('utf-8')) 
           
        ######### check if the SRSs of input images match ###########
        for j in range(1,countn):           
            if str(SRS[j])!=str(SRS[0]):
                QMessageBox.information(None, "Warning", "SRSs don't match!")
                break 

        ########## check if images overlapped, if so, get the overlapped part from each image ###########                   
        # find out the overlapping part 
        rastergeom=[]
        # find bounding rectangle of each layer/image
        for j in range(0,countn):
            if cols[j]!=cols[0] or rows[j]!=rows[0] or origX[j]!=origX[0] or origY[j]!=origY[0]:               
                for k in range(0,countn):               
                    ring = ogr.Geometry(ogr.wkbLinearRing)
                    ring.AddPoint(origX[k], origY[k])
                    ring.AddPoint(maxX[k], origY[k])
                    ring.AddPoint(maxX[k], maxY[k])
                    ring.AddPoint(origX[k], maxY[k])
                    ring.CloseRings()
                    raster_geom = ogr.Geometry(ogr.wkbPolygon)
                    raster_geom.AddGeometry(ring)
                    rastergeom.append(raster_geom)
                # find the overlapping part of these rectangles                              
                for k in range(1,countn):
                    check_intersect = rastergeom[0].Intersect(rastergeom[k])
                    if (check_intersect is True):
                        #intersect raster extent with clip-vector
                        isect_geom = rastergeom[0].Intersection(rastergeom[k])
                        rastergeom[0]=isect_geom
                    else:
                        QMessageBox.information(None, "Warning", "images are not overlapping!") 
                        break            
                break  
        # save the final rectangle into a shapefile               
        spatialReference = osr.SpatialReference()
        spatialReference.ImportFromEPSG(4326)    #get srs from clip-shapefile
        driver1 = ogr.GetDriverByName('ESRI Shapefile')
        tmpVectorDataset = driver1.CreateDataSource(path+'/clip_tmp.shp')
        tmpVectorLayer = tmpVectorDataset.CreateLayer('clip_tmp', spatialReference, geom_type=ogr.wkbPolygon)
        featureDefn = tmpVectorLayer.GetLayerDefn()
        tmpVectorFeature = ogr.Feature(featureDefn)
        tmpVectorFeature.SetGeometry(rastergeom[0])    #set geometry to intersection
        tmpVectorLayer.CreateFeature(tmpVectorFeature)
        tmpVectorFeature.Destroy()
        tmpVectorDataset.Destroy()
        
        # cut the overlapping part from each layer/image
        for j in range(0,countn):                
            com= 'gdalwarp -q -cutline '+path+'/clip_tmp.shp -crop_to_cutline -of GTiff -multi -wm 500000 -dstnodata ' + '-9999'+' '+unicode(layer[j].source()).encode('utf-8') + ' ' + path +'/cutting'+ str(j) + '.tif'
            os.system(com)  
        # delete the shapefile for cutting 
        driver1.DeleteDataSource(path+'/clip_tmp.shp')
        
        ########### check the pixel resolutions, if not match, resample them ###########
        #initialize max pixel resolutions
        wemax=wemin=we[0]
        nsmax=nsmin=ns[0]
        imageNowemax=0
        imageNonsmax=0
        imageNowemin=0
        imageNonsmin=0
        for j in range(1,countn):
            # get the largest pixel resolutions by comparing all of them in the loop
            if we[j]!=we[0] or ns[j]!=ns[0]:
                for i in range(1,countn):
                    if abs(we[j])>abs(wemax):
                        wemax=we[j]
                        imageNowemax=j
                    if abs(ns[j])>abs(nsmax):
                        nsmax=ns[j]
                        imageNonsmax=j
                    if abs(we[j])<abs(wemin):
                        wemin=we[j]
                        imageNowemin=j
                    if abs(ns[j])<abs(nsmin):
                        nsmin=ns[j]
                        imageNonsmin=j
            break

        # choose the lowest resolution as target resolution 
        if self.dlg.ui.pcomboBox.currentText()=='Lowest':
            # find out the cutting layers/images with the lowest X and Y resolution
            imagewe=gdal.Open(path+'/cutting'+ str(imageNowemax) + '.tif')
            imagens=gdal.Open(path+'/cutting'+ str(imageNonsmax) + '.tif')
            # calculate the X and Y raster size
            colsfinal=imagewe.RasterXSize
            rowsfinal=imagens.RasterYSize
            # if not equal to the target resolution, resample all the cutting images' resolution to the target one
            for j in range(0,countn):
                if we[j]==wemax and ns[j]==nsmax:
                    os.renames(path +'/cutting'+ str(j) + '.tif', path +'/cuttingresampling'+ str(j) + '.tif')
                else:
                    # resampling
                    com= 'gdalwarp -r near -ts ' +str(colsfinal)+ ' ' +str(rowsfinal)+ ' ' + '-multi -wm 500000 -of GTiff -dstnodata ' + str(noDataValue[j]) +' '+path +'/cutting'+ str(j) + '.tif' + ' ' + path +'/cuttingresampling'+ str(j) + '.tif'                    
                    os.system(com)
        # choose the highest resolution as target resolution 
        if self.dlg.ui.pcomboBox.currentText()=='Highest':
            # find out the cutting layers/images with the highest X and Y resolution
            imagewe=gdal.Open(path+'/cutting'+ str(imageNowemin) + '.tif')
            imagens=gdal.Open(path+'/cutting'+ str(imageNonsmin) + '.tif')
            colsfinal=imagewe.RasterXSize
            rowsfinal=imagens.RasterYSize
            for j in range(0,countn):
                if we[j]==wemin and ns[j]==nsmin:
                    os.renames(path +'/cutting'+ str(j) + '.tif', path +'/cuttingresampling'+ str(j) + '.tif')
                else:
                    com= 'gdalwarp -r near -ts ' +str(colsfinal)+ ' ' +str(rowsfinal)+ ' ' + '-multi -wm 500000 -of GTiff -dstnodata ' + str(noDataValue[j]) +' '+path +'/cutting'+ str(j) + '.tif' + ' ' + path +'/cuttingresampling'+ str(j) + '.tif'                    
                    os.system(com)  
        # choose one layer's resolution as target resolution 
        if self.dlg.ui.pcomboBox.currentText()=='Selected':
            # get the layer from the selected name from chosen layers box
            sel_layer = getMapLayerByName(self.dlg.ui.ChosenLayers.currentItem().text())
            No=0               
            for j in range(0,countn):
                if sel_layer==layer[j]:
                    No=j  
            # open the corresponding cutting image of the selected layer
            image=gdal.Open(path+'/cutting'+ str(No) + '.tif')         
            # get Numbers of rows and columns of selected layer source 
            colsfinal = image.RasterXSize
            rowsfinal = image.RasterYSize
            for j in range(0,countn):
                if j==No:
                    os.renames(path +'/cutting'+ str(j) + '.tif', path +'/cuttingresampling'+ str(j) + '.tif')
                else:
                    com= 'gdalwarp -r near -ts ' +str(colsfinal)+ ' ' +str(rowsfinal)+ ' ' + '-multi -wm 500000 -of GTiff -dstnodata ' + str(noDataValue[j]) +' '+path +'/cutting'+ str(j) + '.tif' + ' ' + path +'/cuttingresampling'+ str(j) + '.tif'                    
                    os.system(com) 
      
###################calculation part######################
        #TODO:check if it is possible to dynamically adjust ui based on number of input layers
        # get the weights from input and store them into a array 'weight'
        weight=[]
        if self.dlg.ui.lineEdit_w1.text():
            weight.append(string.atof(self.dlg.ui.lineEdit_w1.text()))
        if self.dlg.ui.lineEdit_w2.text():
            weight.append(string.atof(self.dlg.ui.lineEdit_w2.text()))
        if self.dlg.ui.lineEdit_w3.text():
            weight.append(string.atof(self.dlg.ui.lineEdit_w3.text()))
        if self.dlg.ui.lineEdit_w4.text():
            weight.append(string.atof(self.dlg.ui.lineEdit_w4.text()))
        if self.dlg.ui.lineEdit_w5.text():
            weight.append(string.atof(self.dlg.ui.lineEdit_w5.text()))
        if self.dlg.ui.lineEdit_w6.text():
            weight.append(string.atof(self.dlg.ui.lineEdit_w6.text()))
 

        # get the original layer source's path 
        sourcepath=path +'/cuttingresampling0.tif'      
        # get layer source
        datasource=gdal.Open(sourcepath)
        # get No. of rows of layer source
        rows=datasource.RasterYSize
        # get No. of columns of layer source
        cols=datasource.RasterXSize
        # get projection of layer source
        proj=datasource.GetProjection()        
        # get Geo Transform of layer source 
        transform=datasource.GetGeoTransform()
        # get no datavalue of layer source
        nodatavalue=datasource.GetRasterBand(1).GetNoDataValue()        
         
        layerarray=[]            
         
        # give all the cutted and resampled image parts names cuttingresampling[i]
        for i in range(0,countn): 
            cal_layersource = path +'/cuttingresampling'+ str(i) + '.tif'            
            cal_layerarray=gdal.Open(cal_layersource) 
            layerarray.append(cal_layerarray.ReadAsArray(0,0,cols,rows))
           
        focusarray=0
       
        # focus calculating with Linear method
        if self.dlg.ui.fcomboBox.currentText()=='Linear':
            for i in range(0,countn):
                focusarray=focusarray+np.ma.masked_equal(layerarray[i],nodatavalue)*weight[i]
        # focus calculating with LogLinear method            
        if self.dlg.ui.fcomboBox.currentText()=='LogLinear':
            for i in range(0,countn):
                focusarray=focusarray+np.log(np.ma.masked_equal(layerarray[i],nodatavalue)+0.00001)*weight[i]
            focusarray=np.exp(focusarray)
        

        lsource=self.dlg.ui.lineEdit_outputpath.text()
        # get driver for the input file
        driver=datasource.GetDriver()                
        # create output file with driver
        output=driver.Create(lsource,cols,rows,1,GDT_Float32)                
        # get the band to write to 
        outBand=output.GetRasterBand(1)
        # write array into the band
        outBand.WriteArray(focusarray,0,0)
        # set the output geo transform
        output.SetGeoTransform(transform)
        # set the output projection
        output.SetProjection(proj)
        # set nodata value 
        outBand.SetNoDataValue(nodatavalue)
        # close gdal dataset
        output = None        
        # add result to map canvas with function addtocanva, which is located in library.functions.py
        if self.dlg.ui.checkBox.checkState():
            addtocanva(lsource)  

        # delete all the image parts created in the mean time
        for j in range(0,countn):
            if os.path.isfile(path +'/cuttingresampling'+ str(j) + '.tif') :
                os.remove(path +'/cuttingresampling'+ str(j) + '.tif')
            if os.path.isfile(path +'/cutting'+ str(j) + '.tif') :
                os.remove(path +'/cutting'+ str(j) + '.tif')

        
    def focus(self):
        # Create the dialog (after translation) and keep reference
        self.dlg = FocusMapDialog()        
        # Show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            ui = self.dlg.ui
            self.check()

  