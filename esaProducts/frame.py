# -*- coding: cp1252 -*-
#
# represent one frame for a stripline product
#
# For Esa/lite dissemination project
#
# Serco 10/2015
# Lavaux Gilles
#
#
#


import os, sys, inspect
from datetime import datetime, timedelta
from cStringIO import StringIO
import traceback

import eoSip_converter.esaProducts.formatUtils as formatUtils
from eoSip_converter.esaProducts import metadata as metadata
from eoSip_converter.esaProducts.product_EOSIP import Product_EOSIP
from eoSip_converter.esaProducts.eosip_product_helper import Eosip_product_helper
import eoSip_converter.xmlHelper as xmlHelper, eoSip_converter.geomHelper as geomHelper


SSM_FRAME_MAPPING='EarthObservation'


debug=0

#
# frame:
#
class Frame:

    xmlMapping={
        metadata.METADATA_WRS_LONGITUDE_GRID_NORMALISED:'/procedure/EarthObservationEquipment/acquisitionParameters/Acquisition/wrsLongitudeGrid',
        metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED:'/procedure/EarthObservationEquipment/acquisitionParameters/Acquisition/wrsLatitudeGrid',
        metadata.METADATA_START_DATE_TIME:'/phenomenonTime/TimePeriod/beginPosition',
        metadata.METADATA_STOP_DATE_TIME:'/phenomenonTime/TimePeriod/endPosition',
        metadata.METADATA_ORBIT:'/procedure/EarthObservationEquipment/acquisitionParameters/Acquisition/orbitNumber',
        metadata.METADATA_ORBIT_DIRECTION:'/procedure/EarthObservationEquipment/acquisitionParameters/Acquisition/orbitDirection',
        metadata.METADATA_WRS_LONGITUDE_GRID_NORMALISED:'/procedure/EarthObservationEquipment/acquisitionParameters/Acquisition/wrsLongitudeGrid',
        metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED:'/procedure/EarthObservationEquipment/acquisitionParameters/Acquisition/wrsLatitudeGrid',
        metadata.METADATA_START_TIME_FROM_ASCENDING_NODE:'/procedure/EarthObservationEquipment/acquisitionParameters/Acquisition/startTimeFromAscendingNode',
        metadata.METADATA_COMPLETION_TIME_FROM_ASCENDING_NODE:'/procedure/EarthObservationEquipment/acquisitionParameters/Acquisition/completionTimeFromAscendingNode',
        metadata.METADATA_FOOTPRINT:'/featureOfInterest/Footprint/multiExtentOf/MultiSurface/surfaceMember/Polygon/exterior/LinearRing/posList',
        metadata.METADATA_SCENE_CENTER:'/featureOfInterest/Footprint/centerOf/Point/pos',
        metadata.METADATA_IDENTIFIER:'/metaDataProperty/EarthObservationMetaData/identifier'
        }
    #
    def __init__(self, num):
        self.num=num
        self.id=None
        self.first=False
        self.last=False
        # readed from node
        self.properties = {}
        #
        self.footprint=None
        self.center=None # lat lon string
        self.distance=None # in meters
        #
        self.browseName=None
        self.browseSrcPath=None
        self.srcObject=None
        # start stop time in msec
        self.startTimeMsec=None
        self.stopTimeMsec=None
        self.durationMsec=None
        #
        self.debug=debug

    #
    def info(self):
        out=StringIO()
        print >>out, " frame num:%s" % self.num
        print >>out, " id:%s" % self.id
        print >>out, " first?:%s" % self.first
        print >>out, " last?:%s" % self.last
        print >>out, " browseName:%s" % self.browseName
        print >>out, " browseSrcPath:%s" % self.browseSrcPath
        print >>out, " footprint:%s" % self.footprint
        print >>out, " center:%s" % self.center
        print >>out, " distance:%s" % self.distance
        print >>out, " srcObject:%s" % self.srcObject
        print >>out, " startTimeFloatMsec:%s" % self.startTimeMsec
        print >>out, " stopTimeFloatMsec:%s" % self.stopTimeMsec
        print >>out, " durationMsec:%s" % self.durationMsec
        if len(self.properties.keys()):
            print >>out, " properties"
            for key in self.properties.keys():
                print >>out, " %s=%s" % (key, self.properties[key])
        return out.getvalue()


    #
    # expand the frame at the beggining: move backward the point 0 and 3
    #
    def expandBeginning(self):
        pass
        
    #
    # expand the frame at the beggining: move forward the point 1 and 2
    #
    def expandEnd(self):
        pass

    #
    def getDurationMsec(self):
        if self.stopTimeMsec != None and  self.startTimeMsec != None:
            return self.stopTimeMsec - self.startTimeMsec
        else:
            return None

    #
    def getStartTimeMsec(self):
        return self.startTimeMsec

    #
    def setStartTimeMsec(self, t):
        self.startTimeMsec = t

    #
    def getStopTimeMsec(self):
        return self.stopTimeMsec

    #
    def setStopTimeMsec(self, t):
        self.stopTimeMsec = t
        
    #
    def getFootprint(self):
        return self.footprint

    #
    def setFootprint(self,f):
        self.footprint = f

    #
    def getCenter(self):
        return self.center

    #
    def setCenter(self,s):
        self.center = s

    #
    def getDistance(self):
        return self.distance

    #
    def setDistance(self,d):
        self.distance = d

    #
    def setProperty(self, key, value):
        self.properties[key]=value

    #
    def getProperty(self, key):
        return self.properties[key]

    #
    def setProperty(self, key, value):
        self.properties[key]=value

    #
    def getBrowseName(self):
        return self.browseName

    #
    def setBrowseName(self, name):
        self.browseName=name

    #
    def getBrowseSrcPath(self):
        return self.browseSrcPath

    #
    def setBrowsePathe(self, path):
        self.browseSrcPath=path

    #
    def getPropertyKeys(self):
        return self.properties.keys()

    #
    def hasPropertyKey(self, key):
        return self.properties.has_key(key)

    #
    def parseNode(self, node, helper):
        n=0
        for field in self.xmlMapping:
            #print "################################################ parseNode: do field[%s]:%s" % (n, field)
            mapping = self.xmlMapping[field]
            #print "################################################ parseNode: mapping[%s]:%s" % (n, mapping)
            aData = helper.getFirstNodeByPath(node, mapping, None)
            if self.debug!=0:
                print "################################################ eoSip_stripline.Frame.parseNode:   aData[%s]:%s" % (n, aData)
            if aData is None:
                aValue=None
                self.properties[field]=metadata.VALUE_UNKNOWN
            else:
                aValue=helper.getNodeText(aData)
                self.properties[field]=aValue
            if self.debug!=0:
                print "################################################ eoSip_stripline.Frame.parseNode:   aValue[%s]:%s" % (n, aValue)
            n=n+1

        # decompose metadata.METADATA_START_DATE and metadata.METADATA_STOP_DATE (mapping used to retrieve beginPosition and endPosition)
        #   that are DATE+TIME into DATE + TIME
        #   + get duration
        #
        # DATE_TIME is like: 2007-01-07T10:26:25.485Z
        #

        # use msec
        start = self.getProperty(metadata.METADATA_START_DATE_TIME)
        pos = start.find('.')
        startMs=0
        if pos>0:
            startMs = start[pos+1:-1]
            start = "%sZ" % start[0:pos]
        #
        stop = self.getProperty(metadata.METADATA_STOP_DATE_TIME)
        pos = stop.find('.')
        stopMs=0
        if pos>0:
            stopMs = stop[pos+1:-1]
            stop = "%sZ" % stop[0:pos]

        # store in DATE and TIME
        pos2 = start.find('T')
        startDate=start[0:pos2]
        startTime=start[pos2+1:].replace('Z','')

        pos2 = stop.find('T')
        stopDate=stop[0:pos2]
        stopTime=stop[pos2+1:].replace('Z','')
        
        if self.debug!=0:
            print " frame and msec: start:%s ms:%s;  stop:%s ms:%s\n  start date:%s; start time:%s\n  stop date:%s; stop time:%s" % (start, startMs, stop, stopMs, startDate, startTime, stopDate, stopTime)
        self.setProperty(metadata.METADATA_START_DATE, startDate)
        self.setProperty(metadata.METADATA_START_TIME, startTime)
        self.setProperty(metadata.METADATA_STOP_DATE, stopDate)
        self.setProperty(metadata.METADATA_STOP_TIME, stopTime)

        
        d1=datetime.strptime(start, formatUtils.DEFAULT_DATE_PATTERN)
        startMsF=float(startMs)
        d1=d1+timedelta(milliseconds=startMsF)

        
        d2=datetime.strptime(stop, formatUtils.DEFAULT_DATE_PATTERN)
        stopMsF=float(stopMs)
        d2=d2+timedelta(milliseconds=stopMsF)
        
        duration = d2-d1
        # duration in HH:MN:SS.msec
        self.setProperty(metadata.METADATA_DURATION_HMS, "%s" % duration)

        # duration in sec
        dt = formatUtils.dateDiffmsec(start, int(startMs), stop, int(stopMs), formatUtils.DEFAULT_DATE_PATTERN)
        self.setProperty(metadata.METADATA_DURATION, dt)

        # check that footprint has 5 pairs of coordinates
        tmp = self.getProperty(metadata.METADATA_FOOTPRINT)
        numCoords=len(tmp.split(' '))
        if numCoords != 10:
            raise Exception("footprint[%s] has not 10 coordinates (5 vertex) but:%s" % (self.num, numCoords))

            
