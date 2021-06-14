# -*- coding: cp1252 -*-
#
# this class is a specialisation of the netCdf based product, used to create by-cycle EoSips
#
#
import os, sys
import re
import logging
import traceback
import metadata
import browse_metadata
import formatUtils
import valid_values
from product_netCDF_reaper import Product_netCDF_reaper





class Product_netCDF_reaper_cycle(Product_netCDF_reaper):
    

    def __init__(self, path):
        Product_netCDF_reaper.__init__(self, path)
        print " init class Product_netCDF_reaper_cycle"
        self.debug=1
        


    #
    #
    #
    def extractMetadata(self, met=None):
        if met==None:
            raise Exception("metadate is None")

        # set some evident values
        met.setMetadataPair(metadata.METADATA_PRODUCTNAME, self.origName)
        

        #get fields
        num_added=0
        
        return num_added


    #
    # refine the metada, should perform in order:
    #
    def refineMetadata(self):
        # processing time: suppress microsec
        tpass

        
    #
    # ERS_ALT_2_ lat variable: lat, in
    # ERS_ALT_2_ lat variable: lat, in
    #
    def getFootprint(self, number=0, reduce=50):
        return
    
    #
    #
    #
    def buildTypeCode(self):
        pass
        

if __name__ == '__main__':
    print "start1"
    try:
        p=Product_netCDF_reaper_cycle(None)
        p.getMetadataInfo()
        met=metadata.Metadata()
        p.extractMetadata(met)
        p.refineMetadata()
        
    except Exception, e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print "Error:%s  %s\n%s" %  (exc_type, exc_obj, traceback.format_exc())


