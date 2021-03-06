# -*- coding: cp1252 -*-
#
# this class implement access to an http apercu service
#
#
from abc import ABCMeta, abstractmethod
import os, sys
import logging

#
SERVICE_APERCU="apercu"
# 

# properties that are known in service configuration file
SETTING_URL_PATTERN="URL_PATTERN"

class ApercuServiceClient:
    debug=0
    service=None
    urlPattern=None

    #
    # class init
    #
    def __init__(self, processInfo):
        self.clientName=SERVICE_APERCU 
        if self.debug!=0:
            print " init class ApercuServiceClient"
        self.service = processInfo.ingester.getService(SERVICE_APERCU)
        if self.debug!=0:
            print "@@@@@@@@@@@@@@@@ ApercuServiceClient: got service apercu:%s" % self.service
        self.urlPattern=self.service.getProperty(SETTING_URL_PATTERN)
        if self.debug!=0:
            print "@@@@@@@@@@@@@@@@ ApercuServiceClient: got urlPattern:%s" % self.urlPattern


    #
    # send report using http
    #
    #def useHttp(self, processInfo, params):
    #    self.reportToApercuService(processInfo, params)
        

    #
    # send report to apercu
    # data to be sent are already url encoded
    #
    def reportToApercuService(self, processInfo, params):
        # build correct url + data
        pos = self.urlPattern.index('?')
        url=self.urlPattern[0:pos]
        if self.debug!=0:
            print "############## service params:url=%s; params=%s" % (url, params)
        #
        self.service.debug=True
        res=self.service.processRequest(url, params, False) # dont use post
        if self.debug!=0:
            print "############## service result:%s" % res

        return res


