# -*- coding: cp1252 -*-
#
# this class implement access to an http service that send back browse images
#
#
from abc import ABCMeta, abstractmethod
import os, sys, inspect
import logging
import traceback
import urllib2
import urllib

from client import Client


#
SERVICE_LUZRESOLVER="luzResolver"
# 

# properties that are known in service configuration file
SETTING_URL_PATTERN="URL_PATTERN"


class LuzResolverClient(Client):
    service=None
    urlPattern=None
    layer=None
    lastCalledUrl=None

    #
    # class init
    #
    def __init__(self, processInfo, otherServiceName=None):
        Client.__init__(self)
        #self.DEBUG=1
        if otherServiceName is None:
            self.clientName=SERVICE_LUZRESOLVER
            if self.debug != 0:
                print " init class LuzResolverClient"
            #
            self.service = processInfo.ingester.getService(SERVICE_LUZRESOLVER)
        else:
            self.clientName = otherServiceName
            if self.debug != 0:
                print " init class LuzResolverClient using otherServiceName=%s" % otherServiceName
            #
            self.service = processInfo.ingester.getService(otherServiceName)
        
        if self.debug!=0:
            print " @@ LuzResolverClient: got service luzResolver (%s):%s" % (self.clientName, self.service)

        self.urlPattern=self.service.getProperty(SETTING_URL_PATTERN)
        if self.debug!=0:
            print " @@ LuzResolverClient: got urlPattern (%s):%s" % (self.clientName, self.urlPattern)


    #
    # query server
    # param will be the 5 points footprint:
    #
    def callWfsService(self, processInfo, params):
        # url to be completed will be like: http://localhost:7001/

        if len(params)!=1:
            raise Exception("params has to be list with 1 values: footprint")

        footprint=urllib.quote(params[0])

        
        dash='%2c'
        self.lastCalledUrl="%s?FOOTPRINT=%s" % (self.urlPattern, footprint)
        params=None
        if self.debug!=0:
            print " ## service params: Url=%s; params=%s" % (self.lastCalledUrl, params)
        #
        #self.service.setDebug(self.DEBUG)
        data=None
        try:
            data=self.service.processRequest(self.lastCalledUrl, params, False, False) # dont use post, dont decode
            if self.debug!=0:
                print " ## service result: length=%s" % len(data)
            
        except urllib2.HTTPError, e:
            print "HTTPError: %s" % e
            
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            errorMsg="Error:%s  %s\n%s" %  (exc_type, exc_obj, traceback.format_exc())
            

        return data


