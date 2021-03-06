#!/usr/bin/env python
#
# 
# Lavaux Gilles 2014
#
# This class is used to get product metadata from various sources 
#
#
#
from abc import ABCMeta, abstractmethod
import os,sys,inspect
import traceback
import csv
#from data import *

# import needed to be able to load the data package
dataDir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
if dataDir not in sys.path:
    sys.path.insert(0, dataDir)

class DataProvider():
    initString=None
    dataReader=None

    #
    debug=0


    #
    # initString is like: METADATA_ORBIT@Kompsat|csvData@csvFile@filePath|Orbit@New_Filename
    # - METADATA_ORBIT@Kompsat: name of the metadata we look at, for Product Kompsat
    # - class@module@properties that will be used to retrieve the value
    # - key|name pair that will be used to build the query
    #
    def __init__(self, init):
        print "init DataProvider with init string:'%s'" % init
        #print "\n\n\ncurrent path:%s\n\n\n" % sys.path
        self.initString = init
        toks=init.split("|")
        if len(toks[1].split("@"))!= 3:
            raise Exception("token 1 of provider source has not 3 '@' separated fields:'%s'" % toks[1])
            
        aClass,aPackage,aPath=toks[1].split("@")
        if self.debug!=0:
            print "  will instanciate class:'%s' in package:'%s' with init:'%s'" % (aClass,aPackage,aPath)
            
        name,key=toks[2].split("@")
        if self.debug!=0:
            print " key;'%s' name;'%s'" % (key,name)

        # create it:
        module = __import__(aPackage)
        if self.debug!=0:
            print " module loaded:%s" % module
        class_ = getattr(module, aClass)
        self.dataReader = class_()
        if self.debug!=0:
            print " got class"
        self.dataReader.openFile(aPath, key, name)
        if self.debug!=0:
            print " dataReader ready"
        
          

    #
    # get a value
    #
    def getRowValue(self, k):
        if self.debug>=1:
            print " DataProvider.getRowValue for:%s" % k
        return self.dataReader.getRowValue(k)

    #
    # get valuea
    #
    def getRowValues(self, k):
        if self.debug>=1:
            print " DataProvider.getRowValues for:%s" % k
        return self.dataReader.getRowValues(k)

        
if __name__ == '__main__':
    try:
        provider = DataProvider('METADATA_ORBIT@Kompsat|csvData@csvFile@C:/Users/glavaux/Shared/LITE/testData/TropForest/status_AVNIR_qc_Final.csv|Orbit@New_Filename')
        
    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
