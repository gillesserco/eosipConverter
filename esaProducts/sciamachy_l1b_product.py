# -*- coding: cp1252 -*-
#
# this class represent a worldview directory product
#
#  - 
#  - 
#
#
import os, sys, inspect
import logging
import zipfile
import xmlHelper
from product import Product
from directory_product import Directory_Product
from definitions_EoSip import sipBuilder
from browseImage import BrowseImage
import metadata
import browse_metadata
import formatUtils
import imageUtil
from definitions_EoSip import sipBuilder
import geomHelper
import re
from subprocess import call,Popen, PIPE
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# import parent
parentdir = os.path.dirname(currentdir)
#print "##### eoSip converter dir:%s" % parentdir
try:
    sys.path.index(parentdir)
except:
    sys.path.insert(0,parentdir)
import fileHelper



class TEMPLATE_Product(Product):


    xmlMapping={}

    #
    #
    #
    def __init__(self, path=None):
        Product.__init__(self, path)
        if self.debug!=0:
        	print " init class TEMPLATE_Product"

        
    #
    # called at the end of the doOneProduct, before the index/shopcart creation
    #
    def afterProductDone(self):
        pass


    #
    # read matadata file
    #
    def getMetadataInfo(self):
        pass

    #
    #
    #
    def makeBrowses(self, processInfo):
		pass

    #
    # extract the product
    #
    def extractToPath(self, folder=None, dont_extract=False):
        if not os.path.exists(folder):
            raise Exception("destination fodler does not exists:%s" % folder)
        if self.debug!=0:
            print " will exttact directory product '%s' to path:%s" % (self.path, folder)

        self.contentList=[]
        self.EXTRACTED_PATH=folder


    #
    #
    #
    def buildTypeCode(self):
        pass


    #
    #
    #
    def extractMetadata(self, met=None):
        pass


    #
    # refine the metada
    #
    def refineMetadata(self):
        pass

        
    #
    # extract quality
    #
    def extractQuality(self, helper, met):
        pass


    #
    # extract the footprint posList point, ccw, lat lon
    #
    def extractFootprint(self, helper, met):
        pass
        

    #
    #
    #
    def toString(self):
        res="path:%s" % self.path
        return res


    #
    #
    #
    def dump(self):
        res="path:%s" % self.path
        print res


