#
# The Base_Ingester is a base class, because the Ingester class was becomming too big
#
# For Esa/lite dissemination project
#
# Serco 03/2016
# Lavaux Gilles
#
# 08/06/2016: V: 0.5
#
#
# -*- coding: cp1252 -*-

from abc import ABCMeta, abstractmethod
import os,sys,inspect
from cStringIO import StringIO
import time,datetime
import sys
import string
import traceback

#
import eoSip_converter.esaProducts.base_metadata as base_metadata
from eoSip_converter.esaProducts import metadata
from eoSip_converter.esaProducts import formatUtils
from eoSip_converter.esaProducts import definitions_EoSip

#
GENERATION_TIME_PATTERN='%Y-%m-%dT%H:%M:%SZ'

# default DEBUG value
DEBUG=0

class Base_Ingester():
        __metaclass__ = ABCMeta


        #
        #
        #
        def __init__(self):
            self.generationTime=None
            # DEBUG
            self.debug = DEBUG


        #
        def setDebug(self, d):
            if not isinstance( d, int ):
                print "ERROR setDebug: parameter is not an integer"
            self.debug=d
        #
        def getDebug(self):
            return self.debug


        #
        # generation time: now or a preset value
        #
        def getGenerationTime(self, met):
                # if not already set, set it to now
                tmp = met.getMetadataValue(metadata.METADATA_GENERATION_TIME)
                if tmp == base_metadata.VALUE_NOT_PRESENT:
                        tmp = time.strftime(GENERATION_TIME_PATTERN)
                        met.setMetadataPair(metadata.METADATA_GENERATION_TIME, tmp)
                        if self.debug != 0:
                            print "METADATA_GENERATION_TIME set to:'%s'" % tmp
                else:
                    if self.debug != 0:
                        print "METADATA_GENERATION_TIME already preset:'%s'" % tmp
                self.generationTime = int(time.mktime(formatUtils.timeFromDatePatterm(tmp).timetuple()))
                if self.debug != 0:
                    print "self.generationTime:'%s' type:%s" % (self.generationTime, type(self.generationTime))
                        
                
        
        #
        # check if the product already exists at destination
        # needed to handle duplicate
        #
        # if can not handle duplicate case: return False and -1
        # if it can, increase the filecounter
        #
        #
        def checkDestinationAlreadyExists(self, aProcessInfo):
            if self.debug != 0:
                print "checkDestinationAlreadyExists; aProcessInfo=%s" % aProcessInfo
            if not aProcessInfo.ingester.want_duplicate:
                # just test if destination exists
                firstPath=aProcessInfo.ingester.outputProductResolvedPaths[0]
                finalPath="%s%s" % (firstPath, aProcessInfo.destProduct.sipPackageName)
                if self.debug != 0:
                    print " ## checkDestinationAlreadyExists; finalPath=%s" % finalPath
                exists=os.path.exists(finalPath)
                return exists, -1, finalPath
            else:
                # check if destination exist, + get next counter if needed and < 10
                firstPath=aProcessInfo.ingester.outputProductResolvedPaths[0]
                finalPath="%s%s" % (firstPath, aProcessInfo.destProduct.sipPackageName)
                if self.debug != 0:
                    print " checkDestinationAlreadyExists; finalPath=%s" % finalPath
                if not aProcessInfo.ingester.can_autocorrect_filecounter:
                    if self.debug != 0:
                        print " checkDestinationAlreadyExists: return because can not correct duplicate case"
                    return False, -1, finalPath


                exists=os.path.exists(finalPath)
                n=1
                if exists:
                    # this method is called only if product_overwrite is False
                    if self.debug != 0:
                        print " checkDestinationAlreadyExists: finalPath exists, can autocorrect filecounter:%s" % aProcessInfo.ingester.can_autocorrect_filecounter
                        print " checkDestinationAlreadyExists: overwrite==false: need to increase METADATA_FILECOUNTER"
                    tmp=aProcessInfo.destProduct.metadata.getMetadataValue(metadata.METADATA_FILECOUNTER)
                    if self.debug != 0:
                        print " checkDestinationAlreadyExists: METADATA_FILECOUNTER=%s" % tmp
                    if tmp==None or tmp==base_metadata.VALUE_NOT_PRESENT:
                        if self.debug != 0:
                            print " case 1"
                        # assume is 1
                        n=2
                        if self.debug != 0:
                            print " case 1: new n=%s" % n
                    else:
                        if self.debug != 0:
                            print " case 2"
                        n=int(tmp)+1
                        if self.debug != 0:
                            print " case 2: new n=%s" % n
                    if n>=10:
                        raise Exception("checkDestinationAlreadyExists: fileCounter reach limit of 10:'%s'" % n)
                    if self.debug != 0:
                        print " checkDestinationAlreadyExists: METADATA_FILECOUNTER is now:%s"  % n
                else:
                    if self.debug != 0:
                        print " checkDestinationAlreadyExists: finalPath doesn't exists"
                return exists, n, finalPath
