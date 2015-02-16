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
 This file contains two functions: function getMapLayerByName helps users get a map layer by its name;
 Function addtocanva helps add the new layer to the project;Function mask_from_geometry create mask from polygon
"""

# Import the PyQt and QGIS libraries
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import gdal
import ogr
import osr
import numpy

# function to get layer by name, parameter layername passes the layer name into this function
def getMapLayerByName(layerName):
    # get all the map layers from project
    layermap = QgsMapLayerRegistry.instance().mapLayers()
    # for loop checking all the layers from the project
    for name,layer in layermap.iteritems():
        # check if the name of one layer is the same with the incoming layer name 
        if layer.name() == layerName:
            # check if the layer is valid
            if layer.isValid():
                # if yes, return this layer
                return layer
            else:
                # if not, return false
                return None
    # release
    return None
# function to add normalized layer to project, parameter normedimage passes the normalized image into this function
def addtocanva(normedimage):
    # get the file info of the incoming image
    file_info = QFileInfo(normedimage)
    # check if the file info exists
    if file_info.exists():
        # if exists, set the name in file info to be layer name
        layer_name = file_info.completeBaseName()
    else:
        # if not, return false
        return False
    # create a raster layer based on the incoming normalized image
    rlayer_new = QgsRasterLayer(normedimage,layer_name)
    # check if the new created raster layer is valid
    if rlayer_new.isValid():
        # if yes, add this raster layer to the project
        QgsMapLayerRegistry.instance().addMapLayer(rlayer_new)
        return True
    else:
        # if not, return false
        return False
 
    
def mask_from_geometry(ndarray_shape, geometry, projection, transform, all_touched=False):
    """
    Create a boolean numpy mask from a Shapely geometry.  Data must be projected to match prior to calling this function.
    Areas are coded as 1 inside the geometry, and 0 outside.  Invert this to use as a numpy.ma mask.

    :param ndarray_shape: (rows, cols)
    :param geometry: Shapely geometry object
    :param projection: the projection of the geometry and target numpy array, as WKT
    :param transform: the GDAL transform object representing the spatial domain of the target numpy array
    :param all_touched: if true, any pixel that touches geometry will be included in mask.
    If false, only those with centroids within or selected by Brezenhams line algorithm will be included.
    See http://www.gdal.org/gdal__alg_8h.html#adfe5e5d287d6c184aab03acbfa567cb1 for more information.
    """

    assert len(ndarray_shape) == 2

    sr = osr.SpatialReference()
    sr.ImportFromEPSG(projection)
    target_ds = gdal.GetDriverByName("MEM").Create("", ndarray_shape[1], ndarray_shape[0], gdal.GDT_Byte)
    target_ds.SetProjection(sr.ExportToWkt())
    target_ds.SetGeoTransform(transform)
    temp_features = ogr.GetDriverByName("Memory").CreateDataSource("")
    lyr = temp_features.CreateLayer("poly", srs=sr)
    feature = ogr.Feature(lyr.GetLayerDefn())
    feature.SetGeometryDirectly(ogr.Geometry(wkb = geometry.wkb))
    lyr.CreateFeature(feature)
    kwargs = {}
    if all_touched:
        kwargs['options'] = ["ALL_TOUCHED=TRUE"]
    gdal.RasterizeLayer(target_ds, [1], lyr, burn_values=[1], **kwargs)
    return target_ds.GetRasterBand(1).ReadAsArray(0, 0, ndarray_shape[1], ndarray_shape[0]).astype(numpy.bool)
    