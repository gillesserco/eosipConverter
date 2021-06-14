# -*- coding: cp1252 -*-
#
# represent the strip of frames for a stripline product
# used to create MDP files
#
# the idea is:
# - load the MD footprint
# - load the SSM frames. Do the vertex matching to find the frames separations
# - calculate frame distances and heading
# Then aloows:
# - frame expansion or moving. time based
# - handle corresponding colr row list ?
#
#
# 
#
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
import math
import decimal


import eoSip_converter.esaProducts.formatUtils as formatUtils
from eoSip_converter.esaProducts import metadata as metadata
from eoSip_converter.esaProducts.product_EOSIP import Product_EOSIP
from eoSip_converter.esaProducts.browseImage import BrowseImage
from eoSip_converter.esaProducts.frame import Frame
from eoSip_converter.esaProducts.eosip_product_helper import Eosip_product_helper
import eoSip_converter.xmlHelper as xmlHelper, eoSip_converter.geomHelper as geomHelper


LIMIT_DELTA_TIME_PERCENT=0.02


debug = 0
#
#
#
#
#
#
class FrameStrip:

    #
    def __init__(self):
        #self.frames={}
        self.framesFromFootprint={} # key is numerical index starting 0
        self.start=None
        self.stop=None
        self.debug=debug
        #
        self.showCHANGED=False

    #
    # get number of frames
    #
    def getNumFootprintFrames(self):
        return len(self.framesFromFootprint)

    #
    def info(self):
        out=StringIO()
        print >>out, "framestrip:"
        print >>out, " number of frames:%s" % len(self.framesFromFootprint.keys())
        for frameId in self.framesFromFootprint.keys():
            frame = self.framesFromFootprint[frameId]
            print >>out, "\n  frame[%s]:\n%s" % (frameId, frame.info())
            
        return out.getvalue()

    #
    def getFrameFromFootprint(self, n):
        return self.framesFromFootprint[n]

    #
    # expand the first frame:
    #
    def expandFirstFrameFootprint(self, refLength):
        if len(self.framesFromFootprint.keys())<0: # expand using the second frame as ref. Has to be good of course
            return self.expandFirstFrameFootprintUsingNext(refLength)
        else:
            #
            out=StringIO()
            print >>out, " expandFirstFrameFootprint: refLength=%s" % (refLength)
            nextFrame = self.framesFromFootprint[1]
            durationMsec=nextFrame.stopTimeMsec - nextFrame.startTimeMsec
            delta = math.fabs(durationMsec - (refLength*1000))/1000
            if delta/refLength < LIMIT_DELTA_TIME_PERCENT: # next frame has ok duration
                result,log =  self.expandFirstFrameFootprintUsingNext(refLength)
                print >>out, " expandFirstFrameFootprint: durationMsec=%s; delta=%s, error=%s" % (durationMsec, delta, (delta/refLength))
                return result, "%s\n%s" % (log, out.getvalue())
            else:
                result,log =  self.expandFirstFrameFootprintUsingNext(refLength)
                print >>out, " expandFirstFrameFootprint: durationMsec=%s; delta=%s, error=%s" % (durationMsec, delta, (delta/refLength))
                return result, "%s\n%s" % (log, out.getvalue())
            #raise Exception("Expand with just 2 frames not implemented") 


    #
    # expand the first frame: will be up to second frame 
    #
    def expandFirstFrameFootprintUsingNext(self, reflength, percent=100.0):

        out=StringIO()
        print >>out, "### expandFirstFrameFootprint; reflength=%s; percent=%s" % (reflength, percent)
        
        firstFrame = self.framesFromFootprint[0]
        nextFrame = self.framesFromFootprint[1]
        if self.debug!=0:
            print " expandFirstFrameFootprint"
            print "   first frame:%s" % firstFrame.info()
            print "   next frame:%s" % nextFrame.info()
        print " @@@@@@@@@@@@@@@@@@@  first frame:%s" % firstFrame.info()
        print " @@@@@@@@@@@@@@@@@@@  next frame:%s" % nextFrame.info()

        # calculate the frame length (in meter)
        firstFootprint = firstFrame.getFootprint()
        atoks = firstFootprint.split(' ')
        btoks = nextFrame.getFootprint().split(' ')
        # get forward percent
        firstDistance = geomHelper.metersDistanceBetween(float(atoks[0]), float(atoks[1]), float(atoks[2]), float(atoks[3]))
        if self.debug!=0:
            print " first frame length in meter:%s" % firstDistance
        print >>out, " first frame length in meter:%s" % firstDistance
        secondDistance = geomHelper.metersDistanceBetween(float(btoks[0]), float(btoks[1]), float(btoks[2]), float(btoks[3]))
        if self.debug!=0:
            print " second frame length in meter:%s" % secondDistance
        print >>out, " second frame length in meter:%s" % secondDistance

        # test if frame need to be expanded
        #if firstDistance>=secondDistance:
        #    if self.DEBUG!=0:
        #        print " don't modify first frame because is big enough"
        #    print >>out, " don't modify first frame because is big enough"
        #    return -1, out.getvalue()

        # calculate expand percent needed on first frame
        # NOTE: this is useless because first frame has incorrect distance/time ratio (i.e. ground velocity is wrong)
        firstFramePercent = firstDistance*100/secondDistance
        firstFrameMissingPercent = 100 - firstFramePercent
        firstFrameMultPercent = (firstFrameMissingPercent/firstFramePercent) * 100
        print >>out, " first frame/second frame percentage=%s; first frame missing percentage:%s; first frame mult percentage=%s" % (firstFramePercent, firstFrameMissingPercent, firstFrameMultPercent)

        
        # move forward point 1 and 2 of first frame 
        # get intermidiate point from nextFrame point 0 to nextFrame point 1; and nextFrame point 3 to nextFrame point 2
        alat, alon = geomHelper.getIntermediatePoint(float(btoks[0]), float(btoks[1]), float(btoks[2]), float(btoks[3]), firstFrameMissingPercent/100)
        blat, blon = geomHelper.getIntermediatePoint(float(btoks[6]), float(btoks[7]), float(btoks[4]), float(btoks[5]), firstFrameMissingPercent/100)
        if self.debug!=0:
            print " changed coords of vertex 1 and 2: %s %s %s %s" % (alat, alon, blat, blon)
        print >>out, "\n changed coord of vertex 1 and 2: %s %s %s %s" % (alat, alon, blat, blon)

        changedFootprint = "%s %s %s %s %s %s %s %s %s %s" % (atoks[0], atoks[1], alat, alon, blat, blon, atoks[6], atoks[7], atoks[0], atoks[1])
        print >>out, " expanded footprint: %s" % changedFootprint
        firstFrame.setFootprint(changedFootprint)
        if self.showCHANGED:
            firstFrame.setProperty(metadata.METADATA_FOOTPRINT, "%s CHANGED: %s" % (firstFootprint, changedFootprint))
        else:
            firstFrame.setProperty(metadata.METADATA_FOOTPRINT, "%s" % changedFootprint)
        
        # verify distance
        distanceBis = self.getFrameDistance(0)
        print >>out, " new first frame length in meter :%s" % distanceBis
        
        # recalculate center
        firstCenter = firstFrame.getCenter()
        browse = BrowseImage()
        browse.setFootprint(firstFrame.getFootprint())
        browse.calculateCenter()
        lat, lon = browse.getCenter()
        changedCenter = "%s %s" % (lat, lon)
        firstFrame.setCenter(changedCenter)
        print >>out, " old scene center:%s; new center:%s\n" % (firstCenter, changedCenter)
        if self.showCHANGED:
            firstFrame.setProperty(metadata.METADATA_SCENE_CENTER, "%s CHANGED: %s" % (firstCenter, changedCenter))
        else:
            firstFrame.setProperty(metadata.METADATA_SCENE_CENTER, "%s" % changedCenter)

        startFromAscending = firstFrame.getProperty(metadata.METADATA_START_TIME_FROM_ASCENDING_NODE)
        completionFromAscending = firstFrame.getProperty(metadata.METADATA_COMPLETION_TIME_FROM_ASCENDING_NODE)


        # recalculate stop time msec + stop time; set it in src.product.frame[0].properties
        # using the mult percentag
        # UNUSED NOW
        durationMsec=firstFrame.stopTimeMsec - firstFrame.startTimeMsec
        newDurationMsec=durationMsec*(1+(firstFrameMultPercent/100))
        deltaDurationMsec = newDurationMsec - durationMsec
        print >>out, "  UNUSED NOW: using mult percentag: first frame delta: durationMsec=%s; newDurationMsec=%s; deltaDurationMsec=%s" % (durationMsec, newDurationMsec, deltaDurationMsec)
        # UNUSED NOW: test that duration using mult if ok
        # check that it is standard 15/60 sec duration
        delta = math.fabs(newDurationMsec - (reflength * 1000))
        print >>out, "  delta on duration 0:%s" % delta
        delta = delta/(reflength * 1000)
        print >>out, "  delta on duration 1:%s\n  END UNUSED NOW" % delta
        # UNUSED NOW: don't use the above result but the frame reference duration
        if 1==1: # math.fabs(delta) > LIMIT_DELTA_TIME_PERCENT:
            newDurationMsec = reflength * 1000
            newStopTimeMsec = firstFrame.startTimeMsec+newDurationMsec
            deltaDurationMsec = newDurationMsec - durationMsec
            #print >>out, "  duration delta too big; newDurationMsec set to:%s; new deltaDurationMsec:%s" % (newDurationMsec, deltaDurationMsec)
            print >>out, " newDurationMsec using frame length ref set to:%s; new deltaDurationMsec:%s" % (newDurationMsec, deltaDurationMsec)
        else:
            newStopTimeMsec = firstFrame.stopTimeMsec+deltaDurationMsec
            print >>out, " newDurationMsec using mult set to:%s; new deltaDurationMsec:%s" % (newDurationMsec, deltaDurationMsec)

        if self.showCHANGED:
            firstFrame.stopTimeMsec = "%s CHANGED: %s" % (firstFrame.stopTimeMsec, newStopTimeMsec)
        else:
            firstFrame.stopTimeMsec = "%s" % (newStopTimeMsec)
        firstFrame.durationMsec = "%s" % (newDurationMsec/1000)
        oldStop = firstFrame.getProperty(metadata.METADATA_STOP_DATE_TIME)
        decimalStop = decimal.Decimal(newStopTimeMsec/1000.0)
        newStop = formatUtils.secsDecimalToDateTimeMsecsString(decimalStop)
        if self.showCHANGED:
            firstFrame.setProperty(metadata.METADATA_STOP_DATE_TIME, "%s CHANGED: %s" % (oldStop, newStop))
        else:
            firstFrame.setProperty(metadata.METADATA_STOP_DATE_TIME, "%s" % newStop)
        pos2=newStop.index('T')
        adate=newStop[0:pos2]
        atime=newStop[pos2+1:].replace('Z','')
        firstFrame.setProperty(metadata.METADATA_STOP_DATE, adate)
        firstFrame.setProperty(metadata.METADATA_STOP_TIME, atime)
        print >>out, " first frame newStopTimeMsec=%s; oldStopDateTime=%s; newStopDateTime=%s\n" % (newStopTimeMsec, oldStop, newStop)


        # recalculate frame; set it in src.product.frame[0].properties
        # frame numbers changes every 0.84 seconds
        # CHANGE: first frame number is wrong, can not use it. use next frame
        frame = firstFrame.getProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED)
        deltaFrame = math.fabs(deltaDurationMsec/(840.0*2.0))
        direction = firstFrame.getProperty(metadata.METADATA_ORBIT_DIRECTION)
        newFrame = int(round(float(frame) + deltaFrame))
        print >>out, " calculate new frame number based on frame itself: frame=%s; deltaFrame=%s; direction=%s; newFrame=%s" % (frame, deltaFrame, direction, newFrame)
        if self.showCHANGED:
            firstFrame.setProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, "%s CHANGED: %s" % (frame, newFrame))
        else:
            firstFrame.setProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, "%s" % newFrame)

        # CHANGED: first frame number is wrong, can not use it. use next frame:
        nextFrameNum = nextFrame.getProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED)
        deltaFrame2 = durationMsec / 840.0
        newFrame = int(round(float(nextFrameNum) - deltaFrame2))
        print >>out, " calculate new frame number based on next frame: next frame=%s; frame:%s; deltaFrame2=%s; direction=%s; newFrame=%s" % (nextFrameNum, frame, deltaFrame2, direction, newFrame)
        if self.showCHANGED:
            firstFrame.setProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, "%s CHANGED: %s" % (frame, newFrame))
        else:
            firstFrame.setProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, "%s" % newFrame)

        # recalculate completionFromAscending; set it in src.product.frame[0].properties
        old=completionFromAscending
        #if direction=='ASCENDING':
        completionFromAscending = int(float(completionFromAscending) + deltaDurationMsec)
        #else:
        #    completionFromAscending = int(float(completionFromAscending) - deltaDurationMsec)
        print >>out, " calculate completionFromAscending old=%s; new=%s" % (old, completionFromAscending)
        if self.showCHANGED:
            firstFrame.setProperty(metadata.METADATA_COMPLETION_TIME_FROM_ASCENDING_NODE, "%s CHANGED: %s" % (old, completionFromAscending))
        else:
            firstFrame.setProperty(metadata.METADATA_COMPLETION_TIME_FROM_ASCENDING_NODE, "%s" % completionFromAscending)


        print >>out, "### end expandFirstFrameFootprint"
        return firstFrameMultPercent, out.getvalue()


    #
    # get frame distance in meter. calculated on one side (right one)
    #
    def getFrameDistance(self, numFrame):
        frame = self.framesFromFootprint[numFrame]
        atoks = frame.getFootprint().split(' ')
        distance = geomHelper.metersDistanceBetween(float(atoks[0]), float(atoks[1]), float(atoks[2]), float(atoks[3]))
        return distance

    #
    # expand the last frame:
    #
    def expandLastFrameFootprint(self, refLength):
        if len(self.framesFromFootprint.keys())>2: # expand using the n-1 frame as ref
            return self.expandLastFrameFootprintUsingPrevious(refLength)
        else:
            #
            num = len(self.framesFromFootprint.keys())
            previousFrame = self.framesFromFootprint[num-1]
            durationMsec=previousFrame.stopTimeMsec - previousFrame.startTimeMsec
            delta = math.fabs(durationMsec - (refLength*1000))
            if delta/refLength < LIMIT_DELTA_TIME_PERCENT: # previous frame has ok duration
                result,log =  self.expandLastFrameFootprintUsingPrevious(refLength)
                return result, "expandLastFrameFootprint: delta=%s\n\n%s" % (delta, log)
            else:
                result,log =  self.expandLastFrameFootprintUsingPrevious(refLength)
                return result, "expandLastFrameFootprint: delta=%s\n\n%s" % (delta, log)
            #raise Exception("Expand with just 2 frames not implemented")
        
    #
    # expand the last frame: will be up to previous frame
    #
    def expandLastFrameFootprintUsingPrevious(self, reflength, percent=100.0):

        out=StringIO()
        print >>out, "### expandLastFrameFootprintUsingPrevious; reflength=%s; percent=%s" % (reflength, percent)

        num = len(self.framesFromFootprint.keys())
        lastFrame = self.framesFromFootprint[num-1]
        previousFrame = self.framesFromFootprint[num-2]
        if self.debug!=0:
            print " expandLastFrameFootprint"
            print "   last frame:%s" % lastFrame.info()
            print "   previous frame:%s" % previousFrame.info()
        print " @@@@@@@@@@@@@@@@@@@  last frame:%s" % lastFrame.info()
        print " @@@@@@@@@@@@@@@@@@@  previous frame:%s" % previousFrame.info()

        # calculate the frame length (in meter)
        lastFootprint = lastFrame.getFootprint()
        atoks = lastFootprint.split(' ')
        btoks = previousFrame.getFootprint().split(' ')
        # get forward percent
        lastDistance = geomHelper.metersDistanceBetween(float(atoks[0]), float(atoks[1]), float(atoks[2]), float(atoks[3]))
        if self.debug!=0:
            print " last frame length in meter:%s" % lastDistance
        print >>out, " last frame length in meter:%s" % lastDistance
        previousDistance = geomHelper.metersDistanceBetween(float(btoks[0]), float(btoks[1]), float(btoks[2]), float(btoks[3]))
        if self.debug!=0:
            print " previous frame length in meter:%s" % previousDistance
        print >>out, " previous frame length in meter:%s" % previousDistance

        # test if frame need to be expanded
        #if lastDistance>=previousDistance:
        #    print " don't modify last frame because is big enough"
        #    print >>out, " don't modify last frame because is big enough"
        #    return -1, out.getvalue()
        
        # calculate expand percent needed on last frame
        # NOTE: this is useless because first frame has incorrect distance/time ratio (i.e. ground velocity is wrong)
        lastFramePercent = lastDistance*100/previousDistance
        print >>out, " lastFramePercent:%s" % lastFramePercent
        lastFrameMissingPercent = 100 - lastFramePercent
        lastFrameMultPercent = (lastFrameMissingPercent/lastFramePercent) * 100
        print >>out, " lastFramePercent=%s; lastFrameMissingPercent:%s; lastFrameMultPercent=%s" % (lastFramePercent, lastFrameMissingPercent, lastFrameMultPercent)

        # move backward point 0 and 3 of lastFrame
        # get intermidiate point from previousFrame point 1 to previousFrame point 0; and previousFrame point 2 to previousFrame point 3
        alat, alon = geomHelper.getIntermediatePoint(float(btoks[2]), float(btoks[3]), float(btoks[0]), float(btoks[1]), lastFrameMissingPercent/100)
        blat, blon = geomHelper.getIntermediatePoint(float(btoks[4]), float(btoks[5]), float(btoks[6]), float(btoks[7]), lastFrameMissingPercent/100)
        if self.debug!=0:
            print " expandLastFrameFootprint, changed coords: %s %s %s %s" % (alat, alon, blat, blon)
        print >>out, " expandLastFrameFootprint, changed coord: %s %s %s %s" % (alat, alon, blat, blon)

        changedFootprint = "%s %s %s %s %s %s %s %s %s %s" % (alat, alon, atoks[2], atoks[3],  atoks[4], atoks[5], blat, blon, alat, alon)
        print >>out, " expanded footprint: %s" % changedFootprint
        lastFrame.setFootprint(changedFootprint)
        if self.showCHANGED:
            lastFrame.setProperty(metadata.METADATA_FOOTPRINT, "%s CHANGED: %s" % (lastFootprint, changedFootprint))
        else:
            lastFrame.setProperty(metadata.METADATA_FOOTPRINT, "%s" % changedFootprint)      

        
        # verify distance
        distanceBis = self.getFrameDistance(num-1)
        print >>out, " distanceBis :%s" % distanceBis
        
        # recalculate center
        lastCenter = lastFrame.getCenter()
        browse = BrowseImage()
        browse.setFootprint(lastFrame.getFootprint())
        browse.calculateCenter()
        lat, lon = browse.getCenter()
        changedCenter = "%s %s" % (lat, lon)
        print >>out, " old scene center:%s; new center:%s" % (lastCenter, changedCenter)
        lastFrame.setCenter(changedCenter)
        if self.showCHANGED:
            lastFrame.setProperty(metadata.METADATA_SCENE_CENTER, "%s CHANGED: %s" % (lastCenter, changedCenter))
        else:
            lastFrame.setProperty(metadata.METADATA_SCENE_CENTER, "%s" % changedCenter)

        startFromAscending = lastFrame.getProperty(metadata.METADATA_START_TIME_FROM_ASCENDING_NODE)
        completionFromAscending = lastFrame.getProperty(metadata.METADATA_COMPLETION_TIME_FROM_ASCENDING_NODE)

        # recalculate stop time msec + stop time; set it in src.product.frame[n-1].properties
        durationMsec=lastFrame.stopTimeMsec - lastFrame.startTimeMsec
        newDurationMsec=durationMsec*(1+(lastFrameMultPercent/100))
        deltaDurationMsec = newDurationMsec - durationMsec
        print >>out, " last frame delta: durationMsec=%s; newDurationMsec=%s; deltaDurationMsec=%s" % (durationMsec, newDurationMsec, deltaDurationMsec)
        # check that it is standard 15/60 sec duration
        delta = math.fabs(newDurationMsec - (reflength*1000))
        print >>out, " delta on duration 2:%s" % delta
        delta = delta/(reflength * 1000)
        print >>out, " delta on duration 3:%s" % delta
        if 1==1: #math.fabs(delta) > LIMIT_DELTA_TIME_PERCENT:
            newDurationMsec = reflength * 1000
            newStartTimeMsec = lastFrame.stopTimeMsec-newDurationMsec
            deltaDurationMsec = newDurationMsec - durationMsec
            print >>out, " duration delta too big; newDurationMsec set to:%s; new deltaDurationMsec:%s" % (newDurationMsec, deltaDurationMsec)
        else:
            newStartTimeMsec = lastFrame.startTimeMsec-deltaDurationMsec
            
        if self.showCHANGED:
            lastFrame.startTimeMsec = "%s CHANGED: %s" % (lastFrame.startTimeMsec, newStartTimeMsec)
        else:
            lastFrame.startTimeMsec = "%s" % (newStartTimeMsec)
        lastFrame.durationMsec = "%s" % (newDurationMsec/1000)
            
        oldStart = lastFrame.getProperty(metadata.METADATA_START_DATE_TIME)
        decimalStart = decimal.Decimal(newStartTimeMsec/1000.0)
        newStart = formatUtils.secsDecimalToDateTimeMsecsString(decimalStart)
        if self.showCHANGED:
            lastFrame.setProperty(metadata.METADATA_START_DATE_TIME, "%s CHANGED: %s" % (oldStart, newStart))
        else:
            lastFrame.setProperty(metadata.METADATA_START_DATE_TIME, "%s" % newStart)

        pos2=newStart.index('T')
        adate=newStart[0:pos2]
        atime=newStart[pos2+1:].replace('Z','')
        lastFrame.setProperty(metadata.METADATA_START_DATE, adate)
        lastFrame.setProperty(metadata.METADATA_START_TIME, atime)
        print >>out, " last frame newStartTimeMsec=%s; oldStartDateTime=%s; newStartDateTime=%s" % (newStartTimeMsec, oldStart, newStart)


        # recalculate frame; set it in src.product.frame[0].properties
        # frame numbers changes every 0.84 seconds
        # last frame number is wrong, can not use it. use previous frame:
        frame = lastFrame.getProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED)
        deltaFrame = math.fabs(deltaDurationMsec/(840.0*2.0))
        direction = lastFrame.getProperty(metadata.METADATA_ORBIT_DIRECTION)
        #if direction=='ASCENDING':
        newFrame = int(round(float(frame) - deltaFrame))
        #else:
        #    newFrame = int(round(float(frame) - deltaFrame))
        print >>out, " frame=%s; deltaFrame=%s; direction=%s; newFrame=%s" % (frame, deltaFrame, direction, newFrame)
        if self.showCHANGED:
            lastFrame.setProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, "%s CHANGED: %s" % (frame, newFrame))
        else:
            lastFrame.setProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, "%s" % newFrame)
        # last frame number is wrong, can not use it. use previous frame:
        previousFrameNum = previousFrame.getProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED)
        deltaFrame2 = durationMsec / 840.0
        newFrame = int(round(float(previousFrameNum) + deltaFrame2))
        print >>out, " based on previous frame: previous frame=%s; frame:%s; deltaFrame2=%s; direction=%s; newFrame=%s" % (previousFrameNum, frame, deltaFrame2, direction, newFrame)
        if self.showCHANGED:
            lastFrame.setProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, "%s CHANGED: %s" % (frame, newFrame))
        else:
            lastFrame.setProperty(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, "%s" % newFrame)
            
        # recalculate startFromAscending; set it in src.product.frame[n-1].properties
        old=startFromAscending
        #if direction=='ASCENDING':
        startFromAscending = int(float(startFromAscending) - deltaDurationMsec)
        #else:
        #    startFromAscending = int(float(startFromAscending) - deltaDurationMsec)
        print >>out, " startFromAscending old=%s; new=%s" % (old, startFromAscending)
        if self.showCHANGED:
            lastFrame.setProperty(metadata.METADATA_START_TIME_FROM_ASCENDING_NODE, "%s CHANGED: %s" % (old, startFromAscending))
        else:
            lastFrame.setProperty(metadata.METADATA_START_TIME_FROM_ASCENDING_NODE, "%s" % startFromAscending)
            
        print >>out, "### end expandLastFrameFootprint"
        return lastFrameMultPercent, out.getvalue()
    
    #
    #
    #
    def getAverageDistance(self):
        totalDistance=0
        for frameId in self.framesFromFootprint.keys():
            aFrame = self.framesFromFootprint[frameId]
            totalDistance=totalDistance+aFrame.getDistance()
        return totalDistance/len(self.framesFromFootprint.keys())


    #
    # get the strip footprint
    #
    def getFootprintString(self):
        side0=''
        side1=''
        vertex0=None
        vertex1=None
        first=None
        for frameId in self.framesFromFootprint.keys():
            frame = self.framesFromFootprint[frameId]
            afootprint = frame.getFootprint()
            print "   getFootprintString n=%s; afootprint=%s;" % (frameId, afootprint)
            toks = afootprint.split(' ')
            if first==None:
                first="%s %s" % (toks[0], toks[1])
            if len(side0)>0:
                side0="%s " % side0
            side0="%s%s %s" % (side0, toks[0], toks[1])
            vertex0="%s %s" % (toks[2], toks[3])

            if len(side1)>0:
                side1=" %s" % side1
            side1="%s %s%s" % (toks[6], toks[7], side1)
            vertex1="%s %s" % ( toks[4], toks[5])
            print "   getFootprintString n=%s; side0=%s; side1=%s;" % (frameId, side0, side1)
        # add lest side vertex
        side0="%s %s" % (side0, vertex0)
        side1="%s %s" % (vertex1, side1)
        print " getFootprintString side0=%s; side1=%s; first=%s;" % (side0, side1, first)
        return "%s %s %s" % (side0, side1, first)
        
    #
    # set the footprint from a footprint string, lat lon pair,
    # like the poslist in the MD file
    # - create the Frame
    #
    def setFootprintString(self, mess):
        if self.debug!=0:
            print 'setFootprintString:%s' % mess
        toks=mess.split(" ")
        nPair=1
        numFrames=(len(toks)-3)/4
        if self.debug!=0:
            print " numCoords=%s" % (len(toks)/2)
            print " numFrames=%s" % numFrames

        aframe=None
        for frameNum in range(numFrames):
            if self.debug:
                print " doing frame=%s" % frameNum
            firstPoint=frameNum
            secondPoint=frameNum+1
            tirdPoint=(len(toks)-2)/2-frameNum-2;
            fourthPoint=(len(toks)-2)/2-frameNum-1;
            if self.debug:
                print "  frame[%s] points=%s %s %s %s" % (frameNum, firstPoint, secondPoint, tirdPoint, fourthPoint)
            point0="%s %s" % (toks[firstPoint*2], toks[firstPoint*2+1])
            point1="%s %s" % (toks[secondPoint*2], toks[secondPoint*2+1])
            point2="%s %s" % (toks[tirdPoint*2], toks[tirdPoint*2+1])
            point3="%s %s" % (toks[fourthPoint*2], toks[fourthPoint*2+1])
            coords="%s %s %s %s %s" % (point0, point1, point2, point3, point0)
            if self.debug:
                print "  frame[%s] coords=%s" % (frameNum, coords)
            aframe = Frame(frameNum)
            # calculate center
            browseImage = BrowseImage()
            browseImage.setFootprint(coords)
            browseImage.calculateCenter()
            aframe.setFootprint(coords)
            aframe.setCenter("%s %s" % (browseImage.getCenter()[0], browseImage.getCenter()[1]))
            # frame distance
            # get first line intermediate point
            topLat, topLon = geomHelper.getIntermediatePoint(float(toks[firstPoint*2]), float(toks[firstPoint*2+1]), float(toks[fourthPoint*2]), float(toks[fourthPoint*2+1]), .5)
            bottomLat, bottomLon = geomHelper.getIntermediatePoint(float(toks[secondPoint*2]), float(toks[secondPoint*2+1]), float(toks[tirdPoint*2]), float(toks[tirdPoint*2+1]), .5)
            if self.debug!=0:
                print "  top center lat:%s lon:%s" % (topLat, topLon)
                print "  bottom center lat:%s lon:%s" % (bottomLat, bottomLon)
            aframe.setDistance(geomHelper.metersDistanceBetween(bottomLat, bottomLon, topLat, topLon))
            self.framesFromFootprint[frameNum]=aframe
            if frameNum==0:
                aframe.first=True
        aframe.last=True

        if self.debug!=0:
            print 'done'








if __name__ == '__main__':
    print "start"

    frameStrip = FrameStrip()
    #frameStrip.setFootprintString('81.16 -11.74 80.92 -12.88 80.20 -16.12 79.45 -18.94 78.68 -21.37 77.89 -23.53 77.09 -25.42 76.28 -27.11 75.47 -28.62 74.85 -29.65 74.45 -26.31 75.04 -25.17 75.84 -23.50 76.63 -21.66 77.41 -19.59 78.16 -17.28 78.90 -14.67 79.61 -11.70 80.30 -8.34 80.51 -7.17 81.16 -11.74')
    frameStrip.setFootprintString('38.09 -5.63 37.32 -5.81 36.43 -6.01 35.54 -6.22 34.65 -6.42 33.76 -6.62 32.87 -6.82 31.98 -7.02 31.09 -7.22 30.19 -7.41 29.30 -7.60 28.41 -7.79 27.52 -7.99 26.73 -8.16 26.57 -7.25 27.36 -7.07 28.25 -6.87 29.14 -6.67 30.03 -6.46 30.94 -6.26 31.83 -6.06 32.72 -5.85 33.61 -5.64 34.50 -5.43 35.39 -5.22 36.28 -5.00 37.16 -4.78 37.93 -4.60 38.09 -5.63')
    print "\n\nDUMP:%s\n" % frameStrip.info()

    print "getAverageDistance=%s" % frameStrip.getAverageDistance()
    frameStrip.expandFirstFrameFootprint()
    frameStrip.expandLastFrameFootprint()

























    
