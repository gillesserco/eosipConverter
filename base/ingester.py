#
# The Ingester class is a base classe that can be used to convert Eo-Products into Eo-Sip packaged products
#
# For Esa/lite dissemination project
#
# Serco 04/2014
# Lavaux Gilles
#
# 30/05/2016: V: 0,8
#
#
# -*- coding: cp1252 -*-

    
from abc import ABCMeta, abstractmethod
import os,sys,inspect
import logging
from cStringIO import StringIO
from logging.handlers import RotatingFileHandler
import time,datetime
import sys
import zipfile
import re
import string
import traceback
import subprocess
import urllib
from collections import namedtuple
import errors
import ConfigParser



#
#
#
VERSION_INFO="""EoSip converter V:0.8.5  Lavaux Gilles - Serco 2018-08
 last changes:
  - compatible with Luigi scheduler
  - added workflow option: can just extract metadata
"""
VERSION="base converter V:1.0.2"

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# parentDir is needed to find the service ressource file, look at line ~413
parentdir = os.path.dirname(currentdir)

from eoSip_converter.esaProducts.ipfIcd import jobOrder_product
from eoSip_converter.base.footprintAgregator import FootprintAgregator

#
# display useful message if definitions EoSip by version is not available
#
try:
        from eoSip_converter.esaProducts import product_EOSIP
except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print "\n can not import EoSip definitions: %s %s" % (exc_type, exc_obj)
        traceback.print_exc(file=sys.stdout)
        print "\n  possible causes are:"
        print "  - specialized ingester not up to date"
        print "  - incorrect system path or PYTHONPATH"
        os._exit(-9)


import eoSip_converter.base.processInfo as processInfo
import eoSip_converter.fileHelper as fileHelper
from eoSip_converter.esaProducts import metadata
from eoSip_converter.esaProducts import definitions_EoSip
from eoSip_converter.esaProducts import formatUtils
import eoSip_converter.statsUtil as statsUtil
from eoSip_converter.data import dataProvider
from eoSip_converter.services import serviceProvider
from eoSip_converter.ressources import ressourceProvider
#
from eoSip_converter.serviceClients import remoteLoggerServiceClient, GraphiteEventsClient
#
from xml_nodes import sipBuilder
import eoSip_converter.base.infoKeeper as infoKeeper
import eoSip_converter.base.reportMaker as reportMaker
import eoSip_converter.sysim as sysim
from eoSip_converter.sysim import sysItem
from eoSip_converter.base.errors import Error
from eoSip_converter.base.base_ingester import Base_Ingester
from eoSip_converter.sysPathTool import SysPathTool
import eoSip_converter.kmz as kmz


# should be True in normal operation
STOP_DATAPROVIDER_PROBLEM=True
STOP_SERVICEPROVIDER_PROBLEM=True
STOP_RESSOURCEPROVIDER_PROBLEM=False

#
# setting variable name + default values (None in general)
#
# folders stuff
SETTING_CONFIG_NAME='CONFIG_NAME'
SETTING_CONFIG_VERSION='CONFIG_VERSION'
SETTING_INBOX='INBOX'
SETTING_OUTBOX='OUTBOX'
SETTING_OUTSPACE='OUTSPACE'
SETTING_TMPSPACE='TMPSPACE'
SETTING_DONESPACE='DONESPACE'
SETTING_FAILEDSPACE='FAILEDSPACE'
# config name and version
CONFIG_NAME=None
CONFIG_VERSION=None
# file find stuff
LIST_TYPE=None
SETTING_LIST_TYPE='LIST_TYPE'
LIST_BUILD='Internal'
SETTING_LIST_BUILD='LIST_BUILD'
FILES_NAMEPATTERN=None
SETTING_FILES_NAMEPATTERN='FILES_NAMEPATTERN'
FILES_EXTPATTERN=None
SETTING_FILES_EXTPATTERN='FILES_EXTPATTERN'
DIRS_NAMEPATTERN=None
SETTING_DIRS_NAMEPATTERN='DIRS_NAMEPATTERN'
DIRS_ISLEAF=None
SETTING_DIRS_ISLEAF='DIRS_ISLEAF'
DIRS_ISEMPTY=None
SETTING_DIRS_ISEMPTY='DIRS_ISEMPTY'
LIST_LIMIT=None
SETTING_LIST_LIMIT='LIST_LIMIT'
LIST_STARTDATE=None
SETTING_LIST_STARTDATE='LIST_STARTDATE'
LIST_STOPDATE=None
SETTING_LIST_STOPDATE='LIST_STOPDATE'
#
TYPOLOGY=None
TYPOLOGY_VERSION=None
# ??
ENGINE_STATE=None
SETTING_ENGINE_STATE='ENGINE_STATE'
ENGINE=None
SETTING_ENGINE='ENGINE'
#
#
# sections name in configuration file
SETTING_Main='Main'
SETTING_Search='Search'
SETTING_Output='Output'
SETTING_workflowp='Workflow'
SETTING_eosip='eoSip'
SETTING_Data='Data'
SETTING_Ressources='Ressources'
SETTING_Services='Services'
# setting name in configuration file
SETTING_metadataReport_usedMap='metadataReport-xml-map'
SETTING_browseReport_usedMap='browseReport-xml-map'
SETTING_MISSION_SPECIFIC='Mission-specific-values'
SETTING_OUTPUT_RELATIVE_PATH_TREES='OUTPUT_RELATIVE_PATH_TREES'
SETTING_OUTPUT_SIP_PATTERN='OUTPUT_SIP_PATTERN'
SETTING_OUTPUT_EO_PATTERN='OUTPUT_EO_PATTERN'
# output stuff
OUTPUT_RELATIVE_PATH_TREES=None
OUTPUT_SIP_PATTERN=None
OUTPUT_EO_PATTERN=None
# workflow
SETTING_BUILD_IN_TMPSPACE='BUILD_IN_TMPSPACE'
SETTING_MOVE_TO_OUTBOX='MOVE_TO_OUTBOX'
SETTING_ERASE_SRC='ERASE_SRC'
SETTING_ERASE_TMP_WORK='ERASE_TMP_WORK'
SETTING_VERIFY_SRC_PRODUCT='VERIFY_SRC_PRODUCT'
SETTING_MAX_PRODUCTS_DONE='MAX_PRODUCTS_DONE'
SETTING_DISK_LOW_SPACE_LIMIT='DISK_LOW_SPACE_LIMIT'
SETTING_VALIDATE_XML='VALIDATE_XML'
SETTING_SANITIZE_XML='SANITIZE_XML'
SETTING_CREATE_INDEX='CREATE_INDEX'
SETTING_INDEX_ADDED_FIELD='INDEX_ADDED_FIELD'
SETTING_FIXED_BATCH_NAME='FIXED_BATCH_NAME'
SETTING_PRODUCT_OVERWRITE='PRODUCT_OVERWRITE'
SETTING_CAN_AUTOCORRECT_FILECOUNTER='CAN_AUTOCORRECT_FILECOUNTER'
SETTING_WANT_DUPLICATE='WANT_DUPLICATE'
SETTING_CREATE_BROWSE_REPORT='CREATE_BROWSE_REPORT'
SETTING_CREATE_SIP_REPORT='CREATE_SIP_REPORT'
SETTING_CREATE_SYS_ITEMS='CREATE_SYS_ITEMS'
SETTING_CREATE_KMZ='CREATE_KMZ'
# workflow, test stuff
SETTING_TEST_MODE='TEST_MODE'
SETTING_TEST_DONT_EXTRACT='TEST_DONT_EXTRACT'
SETTING_TEST_DONT_WRITE='TEST_DONT_WRITE'
SETTING_TEST_DONT_DO_BROWSE='TEST_DONT_DO_BROWSE'
SETTING_TEST_JUST_EXTRACT_METADATA='TEST_JUST_EXTRACT_METADATA'
# eoSip
SETTING_EOSIP_TYPOLOGY='TYPOLOGY'
SETTING_EOSIP_TYPOLOGY_VERSION='VERSION'
SETTING_EOSIP_STORE_TYPE='STORE_TYPE'
SETTING_EOSIP_STORE_EO_COMPRESSION='STORE_EO_COMPRESSION'
SETTING_EOSIP_STORE_COMPRESSION='STORE_COMPRESSION'


#
#
# config
usedConfigFile=None

# counters
num=0
num_total=0
num_done=0
num_error=0
list_done=[]
products_done=[]
eosip_done=[]
list_error=[]
description_error=[]

# the eoSip final path list
FINAL_PATH_LIST=[]

# mission stuff
mission_metadatas={}

# workflow stuff
test_mode=False
verify_product=True
max_product_done=-1
disk_low_space_limit=-1
verify_xml=True
sanitize_xml=True
create_thumbnail=False
create_browse_report=True
create_sip_report=True
create_sys_items=False
create_kmz=True
index_added=None
fixed_batch_name=None
product_overwrite=False
can_autocorrect_filecounter=False
want_duplicate=False
test_dont_extract=False
test_dont_write=False
test_dont_do_browse=False
test_just_extract_metadata=False
startJustReadConfig=False

#
test_move_source=False
test_build_in_tmpspace=False

# daemon
daemon=False
daemonClass=None
multiprocessing=False


# eoSip, defaults
# eo product stored as zip
eoSip_store_type=product_EOSIP.SRC_PRODUCT_AS_ZIP
# don't compress eoSip zip
eoSip_store_compression=False
# but compress eo product
eoSip_store_eo_compression=True

# data provider stuff
dataProviders={}

# servies provider
#servicesProvider=None


# fixed stuff
CONVERTER_LOG_FILE_NAME='converter'
CONVERTER_LOG_FILE_EXT='log'
LOG_FOLDER="./log"
#file_toBeDoneList="%s/%s" % (LOG_FOLDER, 'product_list.txt')

# conversion status var names:
CONVERSION_RESULT='CONVERSION_RESULT'
CONVERSION_ERROR='CONVERSION_ERROR'
CONVERSION_FULL_ERROR='CONVERSION_FULL_ERROR'
CONVERSION_CREATED_PRODUCT='CONVERSION_CREATED_PRODUCT'
SUCCESS='SUCCESS'
FAILURE='FAILURE'

# tupples returned by diskusage
_ntuple_diskusage = namedtuple('diskusage', 'total used free freePercent')




class Ingester(Base_Ingester):
        __metaclass__ = ABCMeta


        #
        #
        #
        def __init__(self):
        
            Base_Ingester.__init__(self)

            #
            self.sysPathsInUse = None

            #
            self.VERSION_INFO=VERSION_INFO
            self.args=None
            print "\n%s\n\n" % self.VERSION_INFO
            print ' init base ingester'
            # set default values
            self.usedConfigFile=usedConfigFile
            self.__config=None
            # file find stuff
            self.FILES_NAMEPATTERN=FILES_NAMEPATTERN
            self.FILES_EXTPATTERN=FILES_EXTPATTERN
            self.DIRS_NAMEPATTERN=DIRS_NAMEPATTERN
            self.DIRS_ISLEAF=DIRS_ISLEAF
            self.DIRS_ISEMPTY=DIRS_ISEMPTY
            self.LIST_LIMIT=LIST_LIMIT
            self.LIST_STARTDATE=LIST_STARTDATE
            self.LIST_STOPDATE=LIST_STOPDATE
            self.TYPOLOGY=TYPOLOGY
            self.TYPOLOGY_VERSION=TYPOLOGY_VERSION
            # output stuff
            self.OUTPUT_RELATIVE_PATH_TREES=OUTPUT_RELATIVE_PATH_TREES
            self.OUTPUT_SIP_PATTERN=OUTPUT_SIP_PATTERN
            self.OUTPUT_EO_PATTERN=OUTPUT_EO_PATTERN
            # eoSip
            self.eoSip_store_type=eoSip_store_type
            self.eoSip_store_eo_compression = eoSip_store_eo_compression
            self.eoSip_store_compression = eoSip_store_compression
            self.FINAL_PATH_LIST=FINAL_PATH_LIST
            # workflow stuff
            self.test_mode=test_mode
            self.create_thumbnail=create_thumbnail
            self.create_browse_report=create_browse_report
            self.create_sip_report=create_sip_report
            self.create_sys_items=create_sys_items
            self.create_kmz = create_kmz
            self.index_added=index_added
            self.fixed_batch_name=fixed_batch_name
            self.verify_product=verify_product
            self.verify_xml=verify_xml
            self.sanitize_xml=sanitize_xml
            self.product_overwrite=product_overwrite
            self.max_product_done=max_product_done
            self.disk_low_space_limit=disk_low_space_limit
            self.test_dont_extract=test_dont_extract
            self.test_dont_write=test_dont_write
            self.test_dont_do_browse=test_dont_do_browse
            self.test_just_extract_metadata=test_just_extract_metadata
            self.startJustReadConfig=startJustReadConfig
            self.can_autocorrect_filecounter=can_autocorrect_filecounter
            self.want_duplicate=want_duplicate
            #
            self.test_move_source=test_move_source
            self.test_build_in_tmpspace=test_build_in_tmpspace
            # counter
            self.num=0
            self.num_total=0
            self.num_done=0
            self.num_error=0
            self.list_done=[]
            self.products_done=[]
            self.eosip_done=[]
            self.list_error=[]
            self.description_error=[]
            # logger/DEBUG stuff
            self.LOG_FOLDER=LOG_FOLDER
            self.logger = logging.getLogger()
            #self.logger.setLevel(logging.DEBUG)
            self.logger.setLevel(logging.NOTSET)
            basicFormat='%(asctime)s - [%(levelname)s] : %(message)s'
            self.formatter = logging.Formatter(basicFormat)
            self.file_handler = RotatingFileHandler("%s.%s" % (CONVERTER_LOG_FILE_NAME, CONVERTER_LOG_FILE_EXT), '', 1000000, 1)
            self.file_handler.setLevel(logging.DEBUG)
            self.file_handler.setFormatter(self.formatter)
            self.logger.addHandler(self.file_handler)
            steam_handler = logging.StreamHandler()
            steam_handler.setLevel(logging.DEBUG)
            steam_handler.setFormatter(self.formatter)
            self.logger.addHandler(steam_handler)
            #
            self.daemon=daemon
            self.daemonClass=daemonClass
            self.multiprocessing=multiprocessing
            #
            self.joborderPath=None
            self.jobOrder=None
            #
            self.productsListFile=None
            self.productList=None
            self.productDoneList=None
            #
            self.runStartTime=None
            self.runStopTime=None
            #
            self.indexCreator=None
            self.shopcartCreator=None
            self.statsUtil=statsUtil.StatsUtil()
            # resolved output folders
            self.outputProductResolvedPaths=None
            # data/service providers
            self.dataProviders={}
            self.servicesProvider=None
            self.apercuReporter=None
            self.graphiteReporter=None
            self.loggerReporter=None
            self.ressourcesProvider=None
            # 
            self.infoKeeper = infoKeeper.InfoKeeper()
            #
            self.mission_metadatas=mission_metadatas
            #

            # error handling
            self.error=None
            self.errorSrc=None
            self.exitCode=-1
            self.exitCodeSrc=-1
            self.errorHandler = Error()

            # geoInfo
            self.footprintAgregator = FootprintAgregator()


        #
        # change the log file handler
        #
        def changeLogFileHandler(self, logFilePath):
            if self.debug!=0:
                print "change log file handler to:%s" % logFilePath
            # remove handler
            try:
                # get log path
                logPath = None
                try:
                    logPath = self.file_handler.stream.name
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    print " ERROR in changeLogFileHandler: getting log file handler stream name:%s; %s" % (exc_type, exc_obj)
                    #os._exit(1)
                self.logger.removeHandler(self.file_handler)
                # remove old log file
                if logPath is not None:
                    try:
                        self.file_handler.close()
                        os.remove(logPath)
                    except:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        print " ERROR in changeLogFileHandler: closing log file handler:%s; %s" % (exc_type, exc_obj)
                        #os._exit(1)
            except:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print " ERROR in changeLogFileHandler: %s; %s" % (exc_type, exc_obj)
                traceback.print_exc(file=sys.stdout)
            # add new handler
            self.file_handler = RotatingFileHandler(logFilePath, '', 1000000, 1)
            self.file_handler.setLevel(logging.DEBUG)
            self.file_handler.setFormatter(self.formatter)
            self.logger.addHandler(self.file_handler)


        #
        def getVersion(self):
            result=None
            aMethodName = 'getVersionImpl'
            if hasattr(self, aMethodName):
                meth = getattr(self, aMethodName, None)
                if callable(meth):
                    result = meth()
            else:
                return VERSION
            return result

        #
        #
        #
        def isInTestMode(self):
            return self.test_mode

        #
        # return the home dir of the converter software
        #
        def getConverterHomeDir(self):
            res = "%s" % parentdir
            return res

        #
        #
        #
        def keepInfo(self, info, value):
            self.infoKeeper.addInfo(info, value)

        #
        # return the service provider
        #
        def getServiceProvider(self):
            return self.servicesProvider

        #
        # return a service by name
        #
        def getService(self, name):
            if self.servicesProvider is None:
                raise Exception("no service available")
            return self.servicesProvider.getService(name)

        #
        # has a service
        #
        def hasService(self, name):
            return self.servicesProvider.hasService(name)

        #
        #
        #
        def readConfig(self, path=None):
                if not os.path.exists(path):
                    raise Exception("configuration file:'%s' doesn't exists" % path)
                
                try:
                        self.usedConfigFile=path
                        self.logger.info("\n\n\n\n\n reading configuration...")
                        self.__config = ConfigParser.RawConfigParser()
                        self.__config.optionxform=str
                        self.__config.read(path)
                        #
                        self.CONFIG_NAME = self.__config.get(SETTING_Main, SETTING_CONFIG_NAME)
                        self.CONFIG_VERSION = self.__config.get(SETTING_Main, SETTING_CONFIG_VERSION)
                        self.INBOX = self.__config.get(SETTING_Main, SETTING_INBOX)
                        self.TMPSPACE = self.__config.get(SETTING_Main, SETTING_TMPSPACE)
                        self.OUTSPACE = self.__config.get(SETTING_Main, SETTING_OUTSPACE)
                        try:
                            self.DONESPACE = self.__config.get(SETTING_Main, SETTING_DONESPACE)
                        except:
                            self.DONESPACE=None
                        try:
                            self.FAILEDSPACE = self.__config.get(SETTING_Main, SETTING_FAILEDSPACE)
                        except:
                            self.FAILEDSPACE=None
                        #
                        self.LIST_TYPE = self.__config.get(SETTING_Search, SETTING_LIST_TYPE)
                        if self.LIST_TYPE=='files':
                                try:
                                        self.FILES_NAMEPATTERN = self.__config.get(SETTING_Search, SETTING_FILES_NAMEPATTERN)
                                except:
                                        pass
                                try:
                                        self.FILES_EXTPATTERN = self.__config.get(SETTING_Search, SETTING_FILES_EXTPATTERN)
                                except:
                                        pass
                        elif self.LIST_TYPE=='dirs':
                                try:
                                        self.DIRS_NAMEPATTERN = self.__config.get(SETTING_Search, SETTING_DIRS_NAMEPATTERN)
                                except:
                                        pass
                                try:
                                        self.DIRS_ISLEAF = self.__config.get(SETTING_Search, SETTING_DIRS_ISLEAF)
                                except:
                                        pass
                                try:
                                        self.DIRS_ISEMPTY = self.__config.get(SETTING_Search, SETTING_DIRS_ISEMPTY)
                                except:
                                        pass

                                
                        try:
                                self.LIST_LIMIT = self.__config.getint(SETTING_Search, SETTING_LIST_LIMIT)
                        except:
                                pass
                        try:
                                self.LIST_STARTDATE = self.__config.get(SETTING_Search, SETTING_LIST_STARTDATE)
                        except:
                                pass
                        try:
                                self.LIST_STOPDATE = self.__config.get(SETTING_Search, SETTING_LIST_STOPDATE)
                        except:
                                pass

                        try:
                            self.OUTPUT_SIP_PATTERN = self.__config.get(SETTING_Output, SETTING_OUTPUT_SIP_PATTERN)
                        except:
                            pass

                        try:
                            self.OUTPUT_EO_PATTERN = self.__config.get(SETTING_Output, SETTING_OUTPUT_EO_PATTERN)
                        except:
                            pass

                        # if EO pattern not specified, set to SIP pattern
                        if self.OUTPUT_EO_PATTERN==None:
                            self.OUTPUT_EO_PATTERN=self.OUTPUT_SIP_PATTERN
                        # idem reverse
                        if self.OUTPUT_SIP_PATTERN==None:
                            self.OUTPUT_SIP_PATTERN=self.OUTPUT_EO_PATTERN

                        try:
                            self.OUTPUT_RELATIVE_PATH_TREES = self.__config.get(SETTING_Output, SETTING_OUTPUT_RELATIVE_PATH_TREES)
                        except:
                            pass




                        # workflow
                        try:
                            self.test_mode= self.__config.getboolean(SETTING_workflowp, SETTING_TEST_MODE)
                        except:
                            pass
                        
                        try:
                            self.verify_product= self.__config.getboolean(SETTING_workflowp, SETTING_VERIFY_SRC_PRODUCT)
                        except:
                            pass
                        
                        try:
                            self.max_product_done = self.__config.getint(SETTING_workflowp, SETTING_MAX_PRODUCTS_DONE)
                        except:
                            pass
                        
                        try:
                            self.disk_low_space_limit = int(self.__config.getint(SETTING_workflowp, SETTING_DISK_LOW_SPACE_LIMIT))
                        except:
                            pass
                        
                        try:
                            self.verify_xml = self.__config.getboolean(SETTING_workflowp, SETTING_VALIDATE_XML)
                        except:
                            pass
                        
                        try:
                            self.sanitize_xml = self.__config.getboolean(SETTING_workflowp, SETTING_SANITIZE_XML)
                        except:
                            pass


                        try:
                            self.create_kmz = self.__config.getboolean(SETTING_workflowp,
                                                                             SETTING_CREATE_KMZ)
                        except:
                            pass
                        
                        try:
                            self.index_added = self.__config.get(SETTING_workflowp, SETTING_INDEX_ADDED_FIELD)
                        except:
                            pass
                        
                        try:
                            self.fixed_batch_name = self.__config.get(SETTING_workflowp, SETTING_FIXED_BATCH_NAME)
                        except:
                            pass
                        
                        try:
                            self.product_overwrite = self.__config.getboolean(SETTING_workflowp, SETTING_PRODUCT_OVERWRITE)
                        except:
                            pass
                        
                        try:
                            self.can_autocorrect_filecounter = self.__config.getboolean(SETTING_workflowp, SETTING_CAN_AUTOCORRECT_FILECOUNTER)
                        except:
                            pass

                        try:
                            self.want_duplicate = self.__config.getboolean(SETTING_workflowp, SETTING_WANT_DUPLICATE)
                        except:
                            pass

                        
                        try:
                            self.create_browse_report = self.__config.getboolean(SETTING_workflowp, SETTING_CREATE_BROWSE_REPORT)
                        except:
                            pass
                        
                        try:
                            self.create_sip_report = self.__config.getboolean(SETTING_workflowp, SETTING_CREATE_SIP_REPORT)
                        except:
                            pass
                        
                        try:
                            self.test_dont_extract = self.__config.getboolean(SETTING_workflowp, SETTING_TEST_DONT_EXTRACT)
                        except:
                            pass
                        try:
                            self.test_dont_write = self.__config.getboolean(SETTING_workflowp, SETTING_TEST_DONT_WRITE)
                        except:
                            pass
                        try:
                            self.test_dont_do_browse = self.__config.getboolean(SETTING_workflowp, SETTING_TEST_DONT_DO_BROWSE)
                        except:
                            pass

                        try:
                            self.test_just_extract_metadata = self.__config.getboolean(SETTING_workflowp, SETTING_TEST_JUST_EXTRACT_METADATA)
                        except:
                            pass

                        try:
                            self.test_move_source = self.__config.getboolean(SETTING_workflowp, SETTING_MOVE_TO_OUTBOX)
                        except:
                            self.test_move_source=False
                        try:
                            self.test_build_in_tmpspace = self.__config.getboolean(SETTING_workflowp, SETTING_BUILD_IN_TMPSPACE)
                        except:
                            pass

                        try:
                            self.erase_tmp_work = self.__config.getboolean(SETTING_workflowp, SETTING_ERASE_TMP_WORK)
                        except:
                            self.erase_tmp_work=False

                        try:
                            self.erase_src = self.__config.getboolean(SETTING_workflowp, SETTING_ERASE_SRC)
                        except:
                            self.erase_src=False

                        try:
                            self.create_sys_items = self.__config.getboolean(SETTING_workflowp, SETTING_CREATE_SYS_ITEMS)
                        except:
                            pass
                        
                        try:
                            self.create_sip_report = self.__config.getboolean(SETTING_workflowp, SETTING_CREATE_SIP_REPORT)
                        except:
                            pass
                        
                        
                        # eoSip:
                        # mandatory block, test valid value. Assign default if not found
                        try:
                            self.TYPOLOGY = self.__config.get(SETTING_eosip, SETTING_EOSIP_TYPOLOGY)
                            # is it supported?
                            try:
                                sipBuilder.TYPOLOGY_REPRESENTATION_SUFFIX.index(self.TYPOLOGY)
                            except:
                                raise Exception("typology not supported:'%s'" % self.TYPOLOGY)

                            self.TYPOLOGY_VERSION = self.__config.get(SETTING_eosip, SETTING_EOSIP_TYPOLOGY_VERSION)
                            print " TYPOLOGY_VERSION:%s" % self.TYPOLOGY_VERSION
                            #os._exit(1)
                            
                        except Exception, e:
                            if self.TYPOLOGY==None:
                                self.TYPOLOGY = sipBuilder.TYPOLOGY_REPRESENTATION_SUFFIX[0]
                            else:
                                print " Error in reading configuration:"
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                traceback.print_exc(file=sys.stdout)
                                raise e




                        #
                        try:
                            self.eoSip_store_type = self.__config.get(SETTING_eosip, SETTING_EOSIP_STORE_TYPE)
                        except:
                            pass

                        try:
                            self.eoSip_store_compression = self.__config.getboolean(SETTING_eosip, SETTING_EOSIP_STORE_COMPRESSION)
                            print "self.eoSip_store_compression:%s; type:%s" % (self.eoSip_store_compression, type(self.eoSip_store_compression))
                        except:
                            pass

                        try:
                            self.eoSip_store_eo_compression = self.__config.getboolean(SETTING_eosip, SETTING_EOSIP_STORE_EO_COMPRESSION)
                            print "self.eoSip_store_eo_compression:%s; type:%s" % (self.eoSip_store_eo_compression, type(self.eoSip_store_eo_compression))
                        except:
                            pass
                        #os._exit(1)



                        # dataProvider: optional
                        try:
                            dataProvidersSrc=dict(self.__config.items(SETTING_Data))
                            if len(dataProvidersSrc)!=0:
                                    n=0
                                    for item in dataProvidersSrc:
                                        try:
                                                value=dataProvidersSrc[item]
                                                if self.debug!=0:
                                                    print " data provider[%d]:%s==>%s" % (n,item,value)
                                                aDataProvider = dataProvider.DataProvider(value)
                                                self.dataProviders[item]=aDataProvider
                                        except Exception, e:
                                            exc_type, exc_obj, exc_tb = sys.exc_info()
                                            if not STOP_DATAPROVIDER_PROBLEM:
                                                    print " warning dataProvider:%s %s" % (exc_type, exc_obj)
                                                    if self.debug!=0:
                                                        traceback.print_exc(file=sys.stdout)
                                            else:
                                                    print " error dataProvider:%s %s" % (exc_type, exc_obj)
                                                    traceback.print_exc(file=sys.stdout)
                                                    os._exit(-50)
                            else:
                                    print " no data provider configured"
                        except Exception, e: # no ressource section
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                print " warning data provider:%s %s" % (exc_type, exc_obj)
                                if self.debug!=0:
                                        traceback.print_exc(file=sys.stdout)

                        # Ressources: optional
                        try:
                            ressources=dict(self.__config.items(SETTING_Ressources))
                            if len(ressources)!=0:
                                    n=0
                                    self.ressourcesProvider=ressourceProvider.RessourceProvider()
                                    for item in ressources:
                                        try:
                                                value=ressources[item]
                                                if self.debug!=0:
                                                    print " ressource provider[%d]:%s==>%s" % (n,item,value)
                                                self.ressourcesProvider.addRessourcePath(item, value)
                                                n=n+1
                                        except Exception, e: # fatal
                                            exc_type, exc_obj, exc_tb = sys.exc_info()
                                            print " error ressourcesProvider:%s %s" % (exc_type, exc_obj)
                                            if self.debug!=0:
                                                traceback.print_exc(file=sys.stdout)
                                            os._exit(-51)
                            else:
                                    print " no ressource provider configured"
                        except Exception, e: # no ressource section
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                print " warning servicesProvider:%s %s" % (exc_type, exc_obj)
                                if self.debug!=0:
                                        traceback.print_exc(file=sys.stdout)

                        # servicesProvider: optional
                        try:
                            serviceProvidersSrc=dict(self.__config.items(SETTING_Services))
                            if len(serviceProvidersSrc)!=0:
                                self.servicesProvider = serviceProvider.ServiceProvider(None)
                                n=0
                                for item in serviceProvidersSrc:
                                    try:
                                        value=serviceProvidersSrc[item]
                                        if self.debug!=0:
                                            print " service[%d]:%s==>%s" % (n,item,value)
                                        self.servicesProvider.addService(item, value, self)
                                    except: # fatal
                                        exc_type, exc_obj, exc_tb = sys.exc_info()
                                        print " Error adding serviceProvider '%s': %s %s\n%s" % (exc_type, exc_obj, item, traceback.format_exc())
                                        os._exit(-52)
                                    n=n+1
                            else:
                                print " no service provider configured"
                        except Exception, e: # no service section
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                print " warning servicesProvider:%s %s" % (exc_type, exc_obj)
                                if self.debug!=0:
                                        traceback.print_exc(file=sys.stdout)
                            
                        
                        self.dump()

                        self.checkConfigurationVersion()

                except Exception, e:
                        print " Error in reading configuration:"
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        traceback.print_exc(file=sys.stdout)
                        raise e


        #
        #
        #
        def checkTypologyOk(self):
            #self.DEBUG = 1
            print " Will check generic EoSip library used VS configuration:%s" % self.TYPOLOGY_VERSION
            import eoSip_converter.sysPathTool as sysPathTool
            aSysPathTool = sysPathTool.SysPathTool()
            self.sysPathsInUse = aSysPathTool.getSysPathUsed()
            # need to have '/esaProduct/definitions_EoSip/v${self.TYPOLOGY_VERSION}' in the sys.path
            needed = '/esaProducts/definitions_EoSip/v'
            numFound=0
            otherFound=0
            mapSuffixPathFound={}
            mapPathSuffixFound={}
            mapOtherFound = {}
            for item in self.sysPathsInUse:
                    if self.debug != 0:
                        print " test sys.path:%s" % (item)
                    pos = item.find(needed)
                    if pos > 0:
                            suffix = item[pos+len(needed):]
                            if self.debug != 0:
                                print " test suffix:%s" % (suffix)
                            if suffix.startswith('%s' % self.TYPOLOGY_VERSION):
                                    numFound+=1
                                    mapSuffixPathFound[suffix]=item
                                    mapPathSuffixFound[item]=suffix
                            else:
                                    otherFound+=1
                                    mapOtherFound[suffix]=item

            print " map of found typology definition:"
            print "  typologyDefinition/path"
            n=0

            for item in mapSuffixPathFound:
                print "   type[%s] %s: path=%s" % (n, item, mapSuffixPathFound[item])

            n=0
            print "\n  path/typologyDefinition"
            for item in mapPathSuffixFound:
                print "   path[%s] %s: type=%s" % (n, item, mapPathSuffixFound[item])

            if len(mapOtherFound)>0:
                n = 0
                print "\n map of other typology definition:"
                for item in mapOtherFound:
                    print "  type[%s] %s: path=%s" % (n, item, mapOtherFound[item])
            else:
                print "\n no map of other typology definition"

            print ""
            numFoundInMap=len(mapSuffixPathFound)
            #if numFound==2 and otherFound==0:
            if numFoundInMap == 2 and otherFound == 0:
                    return
            print " wrong definition of EoSIp in path? correct found=%s; other found=%s" % (numFoundInMap, otherFound)
            print " used sys.path:%s" % self.sysPathsInUse
            raise Exception("wrong definition of EoSIp in path? correct found=%s; other found=%s" % (numFoundInMap, otherFound))
        

        #
        # start the ingester
        #  argv[1]: the configuration file
        #  argv[2]: the file holding the list of products
        #
        #
        # 
        def starts(self, args):
            global LOG_FOLDER
            #
            self.args=args
            if self.debug!=0:
                n=0
                for item in self.args:
                        print " args[%d]='%s'" % (n,item)
                        n+=1

            print "\nstarting %s" % self.getVersion()
                    
            # new: use optparse package
            from optparse import OptionParser
            parser = OptionParser()
            parser.add_option("-c", "--config", dest="configFile", help="path of the configuration file")
            parser.add_option("-l", "--list", dest="productListFile", help="path of the file containg the products list")
            parser.add_option("--doneList", dest="doneProductListFile", help="path of the file containg the products already done list")
            parser.add_option("-b", "--batch", dest="batchName", help="name of the batch job")
            parser.add_option("-i", "--batchId", dest="batchId", type="int", help="index of the batch job")
            parser.add_option("--fileCounter", dest="fileCounter", type="int", help="file counter number, one digit only!")
            parser.add_option("--inbox", dest="inbox", help="inbox folder")
            parser.add_option("-o", "--outspace", dest="outbox", help="output folder")
            parser.add_option("-t", "--tmpspace", dest="tmpbox", help="tmp folder")
            parser.add_option("--donespace", dest="donebox", help="done folder")
            parser.add_option("--failedspace", dest="failedbox", help="failed folder")
            parser.add_option("-m", "--max", dest="max", help="max product to do")
            #parser.add_option("-d", "--daemon", dest="daemon", default=False, help="run in daemon mode, remotely controled")
            parser.add_option("-d", "--daemon", dest="daemon", action="store_true", help="run in daemon mode, remotely controled")
            parser.add_option("--daemonClass", dest="daemonClass", help="daemon server classe")
            #parser.add_option("--multiprocessing", dest="multiprocessing", default=False, help="run in multiprocessing mode")
            parser.add_option("--multiprocessing", dest="multiprocessing", action="store_true", help="run in multiprocessing mode")
            parser.add_option("-s", "--single", dest="singleProduct", help="process a single product given in argument")
            parser.add_option("--joborder", dest="joborder", help="process a job order")
            #parser.add_option("--eraseTmp", dest="erase", default=False, help="erase tmp and workfolder after job done")
            parser.add_option("--eraseTmp", dest="erase", action="store_true", help="erase tmp and workfolder after job done")
            #parser.add_option("--move", dest="move", default=False, help="move source product (in done folder)")
            parser.add_option("--move", dest="move", action="store_true", help="move source product (in done folder)")
            #parser.add_option("--buildInTmp", dest="buildInTmp", default=False, help="build the final product in tmp folder, then move it to output folder")
            parser.add_option("--buildInTmp", dest="buildInTmp", action="store_true", help="build the final product in tmp folder, then move it to output folder")
            #parser.add_option("-k", "--kmz", dest="createKmz", default=True, help="create kmz file")
            parser.add_option("-k", "--kmz", dest="createKmz", action="store_true", help="create kmz file")


            self.options, args = parser.parse_args(args)

            if self.options.configFile is not None:
                print "\n options readed:\n configuration file:%s\n" % self.options.configFile
            else:
                raise Exception("need at least a configuration file path as argument")
            if self.options.productListFile is not None:
                print " product list file:%s" % self.options.productListFile
            if self.options.doneProductListFile is not None:
                print " product done list file:%s" % self.options.doneProductListFile
            if self.options.batchName is not None:
                print " batch name:%s" % self.options.batchName
            if self.options.batchId is not None:
                print " batch id:%s" % self.options.batchId

            # read the config
            self.readConfig(self.options.configFile)

            # check that we use the EoSip typology version defined in config
            self.checkTypologyOk()
            
            changeBatchName=False
            if self.options.batchName is not None:
                if self.options.batchId==None:
                    self.fixed_batch_name=self.options.batchName
                else:
                    self.fixed_batch_name="%s%d" % (self.options.batchName, self.options.batchId)
                print " ==> batchName overwritten by passed parameter:%s" % self.fixed_batch_name
                self.logger.info(" ==> batchName overwritten by passed parameter:%s" % self.fixed_batch_name)
                changeBatchName=True
            else:
                if self.options.batchId is not None:
                    self.fixed_batch_name="%s%d" % (self.fixed_batch_name, self.options.batchId)
                    print " ==> batchName overwritten by passed parameter:%s" % self.fixed_batch_name
                    self.logger.info(" ==> batchName overwritten by passed parameter:%s" % self.fixed_batch_name)
                    changeBatchName=True

            #
            # 2017/10: put basic_log_file in log folder
            #
            self.logger.info(" test log folder exists:%s" % self.LOG_FOLDER)
            if not os.path.exists(self.LOG_FOLDER):
                self.logger.info("  will make log folder:%s" % self.LOG_FOLDER)
                os.makedirs(self.LOG_FOLDER)
            if changeBatchName:
                print " changed fixed_batch_name=%s" % self.fixed_batch_name
                #self.changeLogFileHandler("%s_%s.%s" % (CONVERTER_LOG_FILE_NAME, self.fixed_batch_name, CONVERTER_LOG_FILE_EXT))
                self.changeLogFileHandler(
                    "%s/%s_%s.%s" % (LOG_FOLDER, CONVERTER_LOG_FILE_NAME, self.fixed_batch_name, CONVERTER_LOG_FILE_EXT))
                self.file_toBeDoneList="%s/product_list_%s.txt" % (LOG_FOLDER,  self.fixed_batch_name)
            else:
                print " fixed_batch_name=%s" % self.fixed_batch_name
                self.file_toBeDoneList="%s/%s" % (LOG_FOLDER, 'product_list.txt')
                self.changeLogFileHandler(
                    "%s/%s.%s" % (LOG_FOLDER, CONVERTER_LOG_FILE_NAME, CONVERTER_LOG_FILE_EXT))


            if self.options.fileCounter:
                self.fileCounter=self.options.fileCounter
                print " ==> file counter:%s" % self.fileCounter
                self.logger.info(" file counter:%s" % self.fileCounter)

            #
            #
            if self.options.inbox is not None:
                self.INBOX=self.options.inbox
                print " ==> INBOX overwritten by passed parameter:%s" % self.INBOX
                self.logger.info(" ==> INBOX overwritten by passed parameter:%s" % self.INBOX)

            if self.options.outbox is not None:
                self.OUTSPACE=self.options.outbox
                print " ==> OUTSPACE overwritten by passed parameter:%s" % self.OUTSPACE
                self.logger.info(" ==> OUTSPACE overwritten by passed parameter:%s" % self.OUTSPACE)

            if self.options.tmpbox is not None:
                self.TMPSPACE=self.options.tmpbox
                print " ==> TMPSPACE overwritten by passed parameter:%s" % self.TMPSPACE
                self.logger.info(" ==> TMPSPACE overwritten by passed parameter:%s" % self.TMPSPACE)

            if self.options.donebox is not None:
                self.DONESPACE=self.options.donebox
                print " ==> DONESPACE overwritten by passed parameter:%s" % self.DONESPACE
                self.logger.info(" ==> DONESPACE overwritten by passed parameter:%s" % self.DONESPACE)

            if self.options.failedbox is not None:
                self.FAILEDSPACE=self.options.failedbox
                print " ==> FAILEDSPACE overwritten by passed parameter:%s" % self.FAILEDSPACE
                self.logger.info(" ==> FAILEDSPACE overwritten by passed parameter:%s" % self.FAILEDSPACE)

            if self.options.max is not None:
                self.max_product_done=self.options.max
                print " ==> max_product_done overwritten by passed parameter:%s" %  self.max_product_done
                self.logger.info(" ==> max_product_done overwritten by passed parameter:%s" %  self.max_product_done)

            if self.options.daemon:
                self.daemon=self.options.daemon
            else:
                    print " ==> will NOT run in daemon mode:%s" % self.daemon
                    self.logger.info(" ==> will NOT run in daemon mode:%s" % self.daemon)


            if self.options.daemonClass:
                self.daemonClass=self.options.daemonClass
                print " ==>  daemon classe:%s" % self.daemonClass
                self.logger.info(" ==> daemon classe:%s" % self.daemonClass)

            if self.options.multiprocessing:
                if self.options.multiprocessing=='True':
                    self.multiprocessing=True
                    print " ==> multiprocessing is True"
                    self.logger.info(" ==> multiprocessing:%s" % self.multiprocessing)
                elif self.options.multiprocessing=='False':
                    print " multiprocessing is false"
                else:
                    print " strange option multiprocessing:'%s' type:%s" % (self.options.multiprocessing, type(self.options.multiprocessing))

            if self.options.move:
                if 1==2:
                    if self.options.move=='True':
                        # need to have done and failed folder defined
                        if self.DONESPACE==None or self.FAILEDSPACE==None:
                            raise Exception("--move option requiere to have DONESPACE and FAILEDSPACE defined. Actual DONESPACE=%s; FAILEDSPACE=%s" % (self.DONESPACE,self.FAILEDSPACE))

                        if self.options.move=='True':
                            self.test_move_source=True
                            print " ==> will move source product:%s into donespace:%s or failedspace:%s" % (self.test_move_source, self.DONESPACE, self.FAILEDSPACE)
                            self.logger.info(" ==> will move source product:%s into donespace:%s or failedspace:%s" % (self.test_move_source, self.DONESPACE, self.FAILEDSPACE))
                        elif self.options.move=='False':
                            print " move source is false"
                        else:
                            print " strange option move:'%s' type:%s" % (self.options.move, type(self.options.move))
                #
                if self.DONESPACE == None or self.FAILEDSPACE == None:
                    raise Exception(
                        "--move option requiere to have DONESPACE and FAILEDSPACE defined. Actual DONESPACE=%s; FAILEDSPACE=%s" % (
                        self.DONESPACE, self.FAILEDSPACE))
                    self.test_move_source = self.options.move

            if self.options.buildInTmp:
                self.test_build_in_tmpspace=self.options.buildInTmp
                print " ==> will build product in tmp folder them move it to output folder"
                    
            if self.options.erase:
                #if self.options.erase=='True':
                #    self.erase_tmp_work=self.options.erase
                #    print " ==> will remove tmp working folders"
                #    self.logger.info(" will remove tmp working folders")
                #elif self.options.erase=='False':
                #    print " will NOT remove tmp working folders"
                #else:
                #    print " strange option erase tmp folder:'%s' type:%s" % (self.options.erase, type(self.options.erase))
                self.erase_tmp_work = self.options.erase

            if self.options.singleProduct is not None:
                self.singleProduct=self.options.singleProduct
                print " ==> will use single product"
                self.logger.info(" ==> will use single product")
            else:
                self.singleProduct=None
                
            if self.options.joborder:
                self.joborderPath=self.options.joborder
                print " ==> will use a job order:%s" % self.joborderPath
                self.logger.info(" ==> will use job order:%s" % self.joborderPath)


            if self.options.createKmz is not None:
                self.create_kmz=self.options.createKmz
                print " ==> create kmz?:%s" % self.create_kmz
                self.logger.info(" ==> create kmz?:%s" % self.create_kmz)


            self.makeFolders()
            self.getMissionDefaults()

            # MOVED FROM processproducts
            if self.fixed_batch_name is not None:
                self.batchName="batch_%s_%s" % (self.CONFIG_NAME, self.fixed_batch_name)
            else:
                self.batchName="batch_%s_%s" % (self.CONFIG_NAME, formatUtils.dateNow(pattern="%m%d-%H%M%S"))


            # called after started, to make possible to set stuff in child class
            try:
                self.afterStarting()
            except:
                print " info: child ingester has no afterStarting method"
                self.logger.info(" child ingester has no afterStarting method")
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print "ERROR:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                sys.exit(0)
            
            # find and process products if not in daemon mode, of in  startJustreadConfig mode
            if self.startJustReadConfig==True:
                print " ==> run in justReadConfig mode"
                self.logger.info(" ==> run in justReadConfig mode")
                return


            #
            # get list of already done products
            #
            if self.options.doneProductListFile is not None:
                print " ==> set product done from list file:%s" % self.options.doneProductListFile
                self.logger.info(" ==> set product done from list file:%s" % self.options.doneProductListFile)
                self.setProductsDoneList(self.options.doneProductListFile)
                

            #
            # if we start in daemon mode:
            # - processing will be triggered by the daemonClass in use
            # - or by pyro if no daemon class is provided
            #
            if self.daemon:
                print " ==> run in daemon mode"
                self.logger.info(" ==> run in daemon mode")
                if self.daemonClass is not None:
                    print "   stating daemon classe:%s" % self.daemonClass
                    self.logger.info("   stating daemon classe:%s" % self.daemonClass)

                    self.daemonService = self.getService(self.daemonClass)
                    print "   daemonService:%s" % self.daemonService
                    self.daemonService.setIngester(self)

                    self.daemonService.processRequest('start')
                    #self.daemonService.setIngester(self)
                else:
                    print "   no daemon class submitted: converter will probably be used by pyro"

            #
            # or in joborder mode
            #
            # JobOrder is a Product derived class
            # - get single input product
            # - change TMPSPACE and OUTSPACE: no: done by wrapper passing arguments
            #
            elif self.joborderPath is not None:
                print " ==> run in joborder mode using joborder:%s" % self.joborderPath
                self.logger.info(" ==> run in joborder mode using joborder:%s" % self.joborderPath)
                self.jobOrder=jobOrder_product.JobOrder(self.joborderPath)
                self.logger.info(" joborder created:%s" % self.jobOrder)
                jobOrderMetadata=metadata.Metadata()
                self.jobOrder.getMetadataInfo()
                self.jobOrder.extractMetadata(jobOrderMetadata)
                print " joborder extracted metadata:\n%s" % jobOrderMetadata.toString()
                self.logger.info(" joborder extracted metadata:\n%s" % jobOrderMetadata.toString())
                print "number of inputs:%s" % self.jobOrder.getInputs()
                print "number of outputs:%s" % self.jobOrder.getOutputs()
                

                # set the info needed by the ipfLopper
                if not hasattr(self, 'ipfLopper'):
                    raise Exception("is in joborder mode, but has no ipfLopper")
                self.ipfLopper.processorname=jobOrderMetadata.getMetadataValue('processor_name')
                self.ipfLopper.processorversion=jobOrderMetadata.getMetadataValue('processor_version')

                # make specialized ingester use the jobOrder
                hasUseJobOrderMethod=False
                aMethodName = 'useJobOrder'
                if hasattr(self, aMethodName):
                    meth = getattr(self, aMethodName, None)
                    if callable(meth):
                        hasUseJobOrderMethod=True
                        meth()
                if hasUseJobOrderMethod:
                    self.logger.info(" ######### ingester has method '%s', call it" % aMethodName)
                else:
                    self.logger.info(" ######### ingester has no method '%s'" % aMethodName)
                    
                
                if len(self.jobOrder.getInputs()) != 1:
                    raise Exception("joborder dont has one input but:%s" % len(self.jobOrder.getInputs()))
                self.singleProduct=self.jobOrder.getInputs()[0]
                print " joborder input file:%s" % self.singleProduct
                self.logger.info(" joborder input file:%s" % self.singleProduct)

                if 1==2: # disabled
                    if len(self.jobOrder.getOutputs()) != 1:
                        raise Exception("joborder dont has one output but:%s" % len(self.jobOrder.getOutputs()))
                    self.OUTSPACE=self.jobOrder.getOutputs()[0]
                    print " joborder output path:%s" % self.OUTSPACE
                    self.logger.info(" joborder output path:%s" % self.OUTSPACE)

                    self.TMPSPACE=self.jobOrder.folder
                    print " joborder derived TMPSPACE:%s" % self.TMPSPACE
                    self.logger.info(" joborder derived TMPSPACE:%s" % self.TMPSPACE)

                
                self.makeProductList()
                # write file list of products
                self.writeToBeDoneProduct()
                self.exitCode = self.processProducts()

                if self.exitCode==0:
                    # create file .LIST containing created products
                    jobOrderFolder=self.jobOrder.folder
                    listPath = "%s/%s.LIST" % (self.jobOrder.folder, self.jobOrder.orderId)
                    if len(jobOrderFolder)==0:
                        listPath = "./%s.LIST" % (self.jobOrder.orderId)
                    fd = open(listPath, 'w')
                    for item in self.products_done:
                        #pos = item.find('|') 
                        #fd.write(os.path.basename(item[0:pos]))
                        fd.write(item)
                        fd.write("\n")
                    fd.flush()
                    fd.close()
                
                return self.exitCode
                    

            #
            # or in multiprocessing  mode:
            # - create a pool
            # - create in and out queue
            # - create worker that use in and out queues
            # - look for input products, feed them to worker
            #
            elif self.multiprocessing:
                print " ==> run in multiprocessing mode"
                self.logger.info(" ==> run in multiprocessing mode")
                from multiProcessor import MultiProcessor
                if self.debug!=0:
                    print "  multiprocessing import done"

                self.makeProductList()
                #if self.singleProduct is not None:
                #    print " ==> use one single product:%s" % self.singleProduct
                #    self.logger.info("  => use one single product:%s" % self.singleProduct)
                #    self.productList=[]
                #    self.productList.append(self.singleProduct)
                #elif self.options.productListFile is not None:
                #    print " ==> set product from list file:%s" % self.options.productListFile
                #    self.logger.info(" ==> set product from list file:%s" % self.options.productListFile)
                #    self.setProductsList(self.options.productListFile)
                #else:
                #    print " ==> run in findAndProcess mode"
                #    self.logger.info(" ==> run in findAndProcess mode")
                #    self.findProducts()
                    
                
                # write file list of products
                self.writeToBeDoneProduct()

                # init stats util
                self.statsUtil.start(len(self.productList))
                self.runStartTime=time.time()

                processor = MultiProcessor()
                processor.debug=1
                # change self.infoKeeper to the multiprocess proxyed one
                self.infoKeeper = processor.getInfoProxy()
                # run the jobs
                results, infoKeeper = processor.start(self.productList, self.processSingleProduct)
                self.runStopTime=time.time()

                #populate ingester list from multiprocessor result
                # result line like:Process-8 - sucess on item[1]:/home/gilles/shared/Datasets/Ikonos/2008/06/27/NNAA,20091106143532_po_2628201_0000000.zip; status_code:sucess
                n=0
                for status in results:
                    print " done queue[%s]: %s" % (n, status)
                    if status.find("- %s on item" % errors.ERROR_SUCCESS)>0:
                        # get also created product path
                        delimiter = 'created:'
                        pos = status.find(delimiter)
                        if pos<0:
                                #raise Exception("can not get created product path from status line:%s" % status)
                                pos = status.find(']:')
                                pos2 = status.find(';', pos+2)
                                if pos > 0 and pos2 > pos:
                                        eoSipPath = status[pos+2: pos2]
                        else:             
                                eoSipPath = status[pos+len(delimiter):]
                        self.products_done.append(eoSipPath)
                        #
                        self.list_done.append(status)
                        self.num_done+=1
                    elif status.find("- %s on item" % errors.ERROR_FAILURE)>0:
                        self.list_error.append(status)
                        self.num_error+=1
                    else:
                        print "ERROR: strange result:%s" % status
                    n+=1

                # write conversion info on file
                self.writeLogInfo(self.summary())
                self.writeDoneProducts()
                self.writeFailledProducts()
                self.writeKeepedInfo(infoKeeper)
                self.writeKeepedInfo()

                print "\n\n  Number of product done:%d" % self.num_done
                print "  Number of errors:%d" % self.num_error
                print "  Duration: %s sec\n" % (self.runStopTime-self.runStartTime)

                
                self.exitCode = processor.getExitCode()
                print "  exit code: %s" % self.exitCode

                return self.exitCode
                    
            #
            # or in normal mode: look for input products, process them one by one
            #
            else:
                print " ==> dont run in multiprocessing mode"
                self.logger.info(" ==> dont run in multiprocessing mode")
                self.makeProductList()
                #if self.singleProduct is not None:
                #    print " ==> use one single product:%s" % self.singleProduct
                #    self.logger.info("  => use one single product:%s" % self.singleProduct)
                #    self.productList=[]
                #    self.productList.append(self.singleProduct)
                #elif self.options.productListFile is not None:
                #    print " ==> set product from list file:%s" % self.options.productListFile
                #    self.logger.info(" ==> set product from list file:%s" % self.options.productListFile)
                #    self.setProductsList(self.options.productListFile)
                #else:
                #    print " ==> run in findAndProcess mode"
                #    self.logger.info(" ==> run in findAndProcess mode")
                #    self.findProducts()

                # write file list of products
                self.writeToBeDoneProduct()
                
                self.exitCode = self.processProducts()

                
                return self.exitCode

            

        #
        # make folder used by the ingester
        #
        def makeFolders(self):
                self.logger.info(" test TMPSPACE folder exists:%s" % self.TMPSPACE)
                if not os.path.exists(self.TMPSPACE):
                        self.logger.info("  will make TMPSPACE folder:%s" % self.TMPSPACE)
                        os.makedirs(self.TMPSPACE)
                        
                self.logger.info(" test OUTSPACE folder exists:%s" % self.OUTSPACE)
                if not os.path.exists(self.OUTSPACE):
                        self.logger.info("  will make OUTSPACE folder:%s" % self.OUTSPACE)
                        os.makedirs(self.OUTSPACE)

                if self.DONESPACE is not None and not os.path.exists(self.DONESPACE):
                        self.logger.info(" test DONESPACE folder exists:%s" % self.DONESPACE)
                        self.logger.info("  will make DONESPACE folder:%s" % self.DONESPACE)
                        os.makedirs(self.DONESPACE)

                if self.FAILEDSPACE is not None and not os.path.exists(self.FAILEDSPACE):
                        self.logger.info(" test FAILEDSPACE folder exists:%s" % self.FAILEDSPACE)
                        self.logger.info("  will make FAILEDSPACE folder:%s" % self.FAILEDSPACE)
                        os.makedirs(self.FAILEDSPACE)

                #self.logger.info(" test log folder exists:%s" % self.LOG_FOLDER)
                #if not os.path.exists(self.LOG_FOLDER):
                #        self.logger.info("  will make log folder:%s" % self.LOG_FOLDER)
                #        os.makedirs(self.LOG_FOLDER)


        #
        #
        #
        def testDiskSpace(self, path):
            try:
                #st = os.stat(path)
                #du = st.st_blocks * st.st_blksize
                #print " testDiskSpace on path %s:%s" % (path, du)
                st = os.statvfs(path)
                free = st.f_bavail * st.f_frsize
                total = st.f_blocks * st.f_frsize
                used = (st.f_blocks - st.f_bfree) * st.f_frsize
                percentFree =  float(free)/float(total)*100.0
                percentFreeS = "%.2f" % percentFree
                print " testDiskSpace on path %s: total:%s, used:%s, free:%s, percentFree=%s" % (path, total, used, free, percentFree)
                return _ntuple_diskusage(total, used, free, percentFree)
            except:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print " ERROR checking disk space:%s %s" % (exc_type, exc_obj)
                if self.debug!=0:
                    traceback.print_exc(file=sys.stdout) 



        #
        # save info in file in working folder
        #
        def saveInfo(self, filename=None, data=None):
            path="%s/%s" % (self.TMPSPACE, filename)
            fd=open(path, "a+")
            fd.write(data)
            fd.write("\n")
            fd.close()
            
            

                        
        #
        # make the destination folder
        #
        def makeOutputFolders(self, metadata, basePath=None):
                #create output directory trees according to the configuration path rules
                created=[]
                if basePath[-1]!='/':
                        basePath="%s/" % basePath
                if len(self.FINAL_PATH_LIST)==0:
                        raise Exception("FINAL_PATH_LIST is empty")
                i=0
                for rule in self.FINAL_PATH_LIST:
                        if self.debug!=0:
                            print "resolve path rule[%d/%d]:%s" % (i,len(self.FINAL_PATH_LIST), rule)
                        toks=rule.split('/')
                        new_rulez = basePath
                        n=0
                        for tok in toks:
                                new_rulez="%s%s/" % (new_rulez, metadata.getMetadataValue(tok))
                                n=n+1
                        self.logger.debug("resolved path rule[%d]:%s" % ( i, new_rulez))
                        created.append(new_rulez)
                        i=i+1
                return created

        
        #
        # make working folder
        #
        def makeWorkingFolders(self, processInfo):
                # make working folder
                tmpPath=self.TMPSPACE+"/%s_workfolder_%s" % (self.batchName, processInfo.num)
                processInfo.addLog("- create working folder if needed; working folder:%s" % (tmpPath))
                if not os.path.exists(tmpPath): # create it
                    processInfo.addLog(" => don't exist, create it")
                    self.logger.info("  will make working folder:%s" % tmpPath)
                    os.makedirs(tmpPath)
                    processInfo.addLog(" working folder created:%s\n" % (tmpPath))
                else: # already exists
                    processInfo.addLog(" => already exists")
                    pass # TODO: 
                processInfo.workFolder=tmpPath
                return tmpPath

                
        #
        # set the list of product to be processed
        # (this list is passed as a file path parameter to the ingester)
        #
        def setProductsList(self, filePath=None):
            self.logger.info(" set product list from file:%s" % filePath)
            self.productsListFile=filePath
            fd=open(filePath, "r")
            lines=fd.readlines()
            fd.close()
            list=[]
            n=0
            for line in lines:
                line=line.strip()
                if line[0]!="#":
                    path=line.replace("\\","/").replace('\n','')
                    list.append(path)
                    if self.debug!=0:
                        self.logger.info(" product[%d]:%s" % (n,path))
                    n=n+1
            self.logger.info(" there are:%s products in list" % (len(lines)))
            self.productList=list


        #
        # set the list of product already processed
        # (this list is passed as a file path parameter to the ingester)
        #
        # fiel entries can be:
        # src_product|working folder
        #   - /home/gilles/shared2/Datasets/old/Ikonos/0/NNAA,20090721222747_po_2627437_0000000.zip|/home/gilles/shared2/converter_workspace/tmpspace/batch_ikonos_ikonos_workfolder_0
        # or src_product
        #  - /home/gilles/shared2/Datasets/old/Ikonos/0/NNAA,20090721222747_po_2627437_0000000.zip
        #
        #
        def setProductsDoneList(self, filePath=None):
            self.logger.info(" set product done list from file:%s" % filePath)
            fd=open(filePath, "r")
            lines=fd.readlines()
            fd.close()
            list=[]
            n=0
            for line in lines:
                if line[0]!="#":
                    line=line.strip()   
                    pos = line.find('|')
                    if pos > 0:
                        path=line[:pos].replace("\\","/").replace('\n','')
                    else:
                        path=line.replace("\\","/").replace('\n','')
                    list.append(path)
                    if self.debug!=0:
                        print  " product done[%d]:%s" % (n, path)
                        self.logger.info(" product done[%d]:%s" % (n,path))
                    n=n+1
            self.logger.info(" there are:%s products done in list" % (len(lines)))
            self.productDoneList=list


        #
        # make the product list, single product, list of product. From list
        #
        def makeProductList(self):
            if self.singleProduct is not None:
                print " ==> use one single product:%s" % self.singleProduct
                self.logger.info("  => use one single product:%s" % self.singleProduct)
                self.productList=[]
                self.productList.append(self.singleProduct)
            elif self.options.productListFile is not None:
                print " ==> set product from list file:%s" % self.options.productListFile
                self.logger.info(" ==> set product from list file:%s" % self.options.productListFile)
                self.setProductsList(self.options.productListFile)
            else:
                print " ==> run in findAndProcess mode"
                self.logger.info(" ==> run in findAndProcess mode")
                self.findProducts()

            
        #
        # find the products to be processed, from the filesystem
        #
        def findProducts(self):
                aFileHelper=fileHelper.FileHelper()
                if self.LIST_TYPE=='files':
                        # get list of files
                        reNamePattern = None
                        reExtPattern = None
                        if self.FILES_NAMEPATTERN is not None:
                                reNamePattern = re.compile(self.FILES_NAMEPATTERN)
                        if self.FILES_EXTPATTERN is not None:
                                reExtPattern = re.compile(self.FILES_EXTPATTERN)
                        self.logger.info(" reNamePattern:%s" % reNamePattern.pattern)
                        self.logger.info(" reExtPattern:%s" % reExtPattern.pattern)
                        self.productList=aFileHelper.list_files(self.INBOX, reNamePattern, reExtPattern)
                elif self.LIST_TYPE=='dirs':
                        reNamePattern = None
                        isLeaf=0
                        isEmpty=0
                        if self.DIRS_NAMEPATTERN is not None:
                                reNamePattern = re.compile(self.DIRS_NAMEPATTERN)
                        self.logger.info(" reNamePattern:%s" % reNamePattern.pattern)
                        self.productList=aFileHelper.list_dirs(self.INBOX, reNamePattern, isLeaf, isEmpty)
                else:
                        raise "unreckognized LIST_TYPE:"+self.LIST_TYPE


        #
        # get the mission default/fixed matadata values.
        # is defined in the configuration file
        #
        def getMissionDefaults(self):
                # get mission specific metadata values, taken from configuration file
                self.mission_metadatas={}
                missionSpecificSrc=dict(self.__config.items(SETTING_MISSION_SPECIFIC))
                n=0
                for key in missionSpecificSrc.keys():
                    value=missionSpecificSrc[key]
                    if self.debug!=0:
                            print "METADATA mission specific[%d]:%s=%s" % (n, key, value)
                    self.logger.debug("metadata fixed[%d]:%s=%s" % (n, key, value))
                    self.mission_metadatas[key]=value
                    n=n+1

                # get ouput folder tree path rules, taken from configuration file
                destFolderRulesList = self.__config.get(SETTING_Output, SETTING_OUTPUT_RELATIVE_PATH_TREES)
                n=0
                for ruleName in destFolderRulesList.split(','):
                    self.FINAL_PATH_LIST.append(ruleName)


                #
                #
                # get report metadata used node map, taken from configuration file
                # : is replaced replaced by _
                try:
                    self.xmlMappingMetadata={}
                    xmlMappingMetadataSrc=dict(self.__config.items(SETTING_metadataReport_usedMap))
                    n=0
                    for key in xmlMappingMetadataSrc.keys():
                        value=xmlMappingMetadataSrc[key]
                        key=key.replace('_',':')
                        if self.debug!=0:
                                print "METADATA node used[%d]:%s=%s" % (n, key, value)
                        self.xmlMappingMetadata[key]=value
                        n=n+1
                except:
                    print " WARNING: something happened when reading report used node map:"
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    traceback.print_exc(file=sys.stdout)


                #
                #
                # get report browse used node map, taken from configuration file
                # : is replaced replaced by _
                try:
                    self.xmlMappingBrowse={}
                    xmlMappingBrowseSrc=dict(self.__config.items(SETTING_browseReport_usedMap))
                    n=0
                    for key in xmlMappingBrowseSrc.keys():
                        value=xmlMappingBrowseSrc[key]
                        key=key.replace('_',':')
                        if self.debug!=0:
                                print "BROWSE METADATA node used[%d]:%s=%s" % (n, key, value)
                        self.xmlMappingBrowse[key]=value
                        n=n+1
                except:
                    if self.debug != 0:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        print " WARNING: something happened when reading report browse used node map:%s %s" % (exc_type, exc_obj)
                        traceback.print_exc(file=sys.stdout)


        #
        # process just one products
        #
        # returns:
        # - a status dictionnary
        #
        def processSingleProduct(self, productPath, jobId):
            
                single_runStartTime=time.time()

                aProcessInfo=processInfo.processInfo()
                aProcessInfo.srcPath=productPath
                aProcessInfo.num=jobId
                self.setProcessInfo(aProcessInfo)

                
                #try:
                self.logger.info("")
                self.logger.info("")
                self.logger.info("")
                self.logger.info("")
                self.logger.info("doing single product: jobId=%s, path:%s" % (jobId, productPath))
                aProcessInfo.addLog('')
                aProcessInfo.addLog("doing single product: jobId=%s, path:%s" % (jobId, productPath))
                
                status={}
                code=self.errorHandler.ERROR_NOT_DONE
                message='no message'
                processOk=False
                try:
                        self.reportToLogger(aProcessInfo, 'info', "[PROGRESS] doing product[%s]:%s" % (jobId, productPath))
                        self.doOneProduct(aProcessInfo)
                        #
                        status[CONVERSION_RESULT]=SUCCESS
                        status[CONVERSION_CREATED_PRODUCT]=aProcessInfo.destProduct
                        code=self.errorHandler.ERROR_SUCCESS

                        # write log
                        if not self.erase_tmp_work:
                            self.writeOneConversionLog(aProcessInfo)

                        processOk=True
                        self.reportToLogger(aProcessInfo, 'info', "[PROGRESS] product[%s] done:%s" % (jobId, productPath))
                        
                except Exception, e:
                        # handle error
                        code, message = self.errorHandler.handleError(sys.exc_info())
                        status[CONVERSION_RESULT]=FAILURE
                        status[CONVERSION_CREATED_PRODUCT]=None
                        
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        status[CONVERSION_ERROR]="Error: code=%s  message=%s\n" %  (code, message)

                        self.reportToLogger(aProcessInfo, 'error', "[PROGRESS] product[%s] failure:%s" % (jobId, productPath))
                        
                        if self.debug!=0:
                            print " ERROR:%s  %s%s\n" %  (exc_type, exc_obj, traceback.format_exc())

                        # exit for FATAL ERRORS
                        #anError = errors.Error()
                        #if anError.testCodeIsError(code, errors.ERROR_LOW_DISK)==True:
                        #    print "FATAL: %s" % message
                        #    sys.exit(code)
                        self.testFatalError(code, message)
                        
                        try:
                            self.logger.error("Error:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                            aProcessInfo.addLog("Error:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                        except  Exception, ee:
                            self.logger.error(" Error 0: adding log info into processInfo=%s:%s" % (aProcessInfo, ee))
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            print " ERROR 0 adding error in log:%s  %s" %  (exc_type, exc_obj)

                        # write log
                        try:
                                prodLogPath="%s/bad_conversion_%d.log" % (aProcessInfo.workFolder, self.num_error)
                                fd=open(prodLogPath, 'w')
                                fd.write(aProcessInfo.getProdLog())
                                fd.close()
                        except Exception, eee:
                                print "Error: problem writing conversion log in fodler:%s" % aProcessInfo.workFolder
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())


                # save the pinfo in workfolder
                if processOk==False or not self.erase_tmp_work:
                    try:
                        self.saveProcessInfo(aProcessInfo)
                    except:
                        self.logger.error(" Error: saving processInfo file")
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        print " ERROR saving processInfo file:%s  %s%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                    
                # save the matadata file in workfolder
                if processOk==False or not self.erase_tmp_work:
                    try:
                        self.saveMetadata(aProcessInfo)
                    except:
                        self.logger.error(" Error: saving metadata files")
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        print " ERROR saving metadata files:%s  %s%s\n" %  (exc_type, exc_obj, traceback.format_exc())

                # remove working folder if requested
                if processOk==True and self.erase_tmp_work:
                    print "deleting working folder '%s'" %  aProcessInfo.workFolder
                    self.logger.info("deleting working folder '%s'" %  aProcessInfo.workFolder)
                    try:
                        aFileHelper=fileHelper.FileHelper()
                        aFileHelper.eraseFolder(aProcessInfo.workFolder, True)
                    except:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        self.logger.info("ERROR deleting working folder '%s':%s  %s\n%s\n" %  (aProcessInfo.workFolder, exc_type, exc_obj, traceback.format_exc()))
                        print "ERROR deleting working folder '%':%s  %s\n%s\n" %  (aProcessInfo.workFolder, exc_type, exc_obj, traceback.format_exc())
                else:
                    print "dont delete working folder '%s': processOk=%s; self.erase_tmp_work=%s" %  (aProcessInfo.workFolder, processOk, self.erase_tmp_work)
                    self.logger.info("dont delete working folder '%s': processOk=%s; self.erase_tmp_work=%s" %  (aProcessInfo.workFolder, processOk, self.erase_tmp_work))


                return status, code, message

                            
        #
        # set some usefull flags in processInfo
        #
        def setProcessInfo(self, aProcessInfo):
            # 
            aProcessInfo.create_thumbnail=self.create_thumbnail
            aProcessInfo.create_sys_items = self.create_sys_items
            aProcessInfo.create_kmz=self.create_kmz
            aProcessInfo.verify_xml=self.verify_xml
            aProcessInfo.test_dont_extract=self.test_dont_extract
            aProcessInfo.test_dont_write=self.test_dont_write
            aProcessInfo.test_dont_do_browse=self.test_dont_do_browse
            aProcessInfo.test_just_extract_metadata=self.test_just_extract_metadata
            aProcessInfo.infoKeeper=self.infoKeeper
            aProcessInfo.setLogger(self.logger)
            aProcessInfo.setIngester(self)
            aProcessInfo.errorHandler=self.errorHandler


        #
        # write to be done list in the log folder: product_list.txt
        #
        def writeToBeDoneProduct(self):
            fd=open(self.file_toBeDoneList, "w")
            if self.productList is not None:
                fd.write("# total:%s\n" % len(self.productList))
                for item in self.productList:
                    fd.write("%s\n" % item)
                fd.write("# end of file")
            else:
                fd.write("# total:0\n# end of file")
            fd.flush()
            fd.close()
            self.logger.info("\n\nlist of products to be done written in:%s\n\n" % (self.file_toBeDoneList))

            
        #
        # write the current processed file in the log folder: batchname_current.txt
        #
        def writeCurrentProduct(self, aProcessInfo):
            try:
                apath="%s/%s_current.txt" % (self.LOG_FOLDER, self.batchName)
                fd=open(apath, "w")
                fd.write(aProcessInfo.srcPath)
                fd.flush()
                fd.close()
            except Exception, eee:
                print "Error: problem writing current file log in fodler:%s" % aProcessInfo.workFolder
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())


        #
        # write the DONE list in the log folder: batchname_DONE.txt
        #
        def writeDoneProducts(self, aProcessInfo=None):
            try:
                apath="%s/%s_DONE.txt" % (self.LOG_FOLDER, self.batchName)
                fd=open(apath, "w")
                for item in self.list_done:
                    fd.write(item+"\n")
                fd.flush()
                fd.close()
                if self.debug!=0:
                    print " DONE product log for batch '%s' written in:%s" % (self.batchName, apath)
            except Exception, eee:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                if aProcessInfo is not None:
                    print "Error: problem writing DONE product log in fodler:%s" % aProcessInfo.workFolder
                    print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                else:
                    print "Error: problem writing DONE product log"
                    print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())

        #
        # write the FAILURE list in the log folder: batchname_FAILURE.txt
        #
        def writeFailledProducts(self, aProcessInfo=None):
            try:
                apath="%s/%s_ERROR.txt" % (self.LOG_FOLDER, self.batchName)
                fd=open(apath, "w")
                for item in self.list_error:
                    fd.write(item+"\n")
                fd.flush()
                fd.close()
                if self.debug!=0:
                    print " FAILLED product log for batch '%s' written in:%s" % (self.batchName, apath)
            except Exception, eee:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                if aProcessInfo is not None:
                    print "Error: problem writing FAILLED product log in fodler:%s" % aProcessInfo.workFolder
                    print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                else:
                    print "Error: problem writing FAILLED product log"
                    print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())

        #
        # write the KEEPED info in the log folder: batchname_KEEPED.txt
        #
        def writeKeepedInfo(self, keeper=None, aProcessInfo=None):
            try:
                #apath="%s/%s_KEEPED.txt" % (self.LOG_FOLDER, self.batchName)
                fd=None
                apath=None
                if keeper==None:
                    apath="%s/%s_KEEPED.txt" % (self.LOG_FOLDER, self.batchName)
                    fd=open(apath, "w")
                    fd.write(self.infoKeeper.toString())
                else:
                    apath="%s/%s_KEEPED2.txt" % (self.LOG_FOLDER, self.batchName)
                    fd=open(apath, "w")
                    fd.write(keeper.toString())
                fd.flush()
                fd.close()
                if self.debug!=0:
                    print " KEEPED info for batch '%s' written in:%s" % (self.batchName, apath)
            except Exception, eee:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                if aProcessInfo is not None:
                    print "Error: problem writing KEEPED info in fodler:%s" % aProcessInfo.workFolder
                    print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                else:
                    print "Error: problem writing KEEPED info"
                    print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())

        #
        # write the log info in the log folder: batchname_log.txt
        #
        def writeLogInfo(self, mess, aProcessInfo=None):
            try:
                apath="%s/%s_log.txt" % (self.LOG_FOLDER, self.batchName)
                fd=open(apath, "w")
                fd.write(mess)
                fd.flush()
                fd.close()
                print " log info for batch '%s' written in:%s" % (self.batchName, apath)
            except Exception, eee:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                if aProcessInfo is not None:
                    print "Error: problem writing log info in fodler:%s" % aProcessInfo.workFolder
                    print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                else:
                    print "Error: problem writing log info"
                    print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                
        #
        #
        #
        def createIndex(self, aProcessInfo):
            try:
                if len(aProcessInfo.destProduct.browse_metadata_dict)>0: # there is at least one browse
                    firstBrowsePath=aProcessInfo.destProduct.browse_metadata_dict.iterkeys().next()
                    self.indexCreator.addOneProduct(aProcessInfo.destProduct.metadata, aProcessInfo.destProduct.browse_metadata_dict[firstBrowsePath])
                else:
                    self.indexCreator.addOneProduct(aProcessInfo.destProduct.metadata, None)
            except Exception, e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print " ERROR creating index:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                aProcessInfo.addLog("ERROR creating index:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                self.logger.error("ERROR creating index: %s  %s" % (exc_type, exc_obj))
                pass

        #
        #
        #
        def createShopcart(self, aProcessInfo):
            try:
                #self.shopcartCreator.DEBUG=1
                if len(aProcessInfo.destProduct.browse_metadata_dict)>0: # there is at least one browse
                    firstBrowsePath=aProcessInfo.destProduct.browse_metadata_dict.iterkeys().next()
                    self.shopcartCreator.addOneProduct(aProcessInfo.destProduct.metadata, aProcessInfo.destProduct.browse_metadata_dict[firstBrowsePath])
                else:
                    self.shopcartCreator.addOneProduct(aProcessInfo.destProduct.metadata, None)
            except Exception, e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print " ERROR creating shopcart:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                aProcessInfo.addLog("ERROR creating shopcart:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                self.logger.error("ERROR creating shopcart: %s  %s" % (exc_type, exc_obj))
                pass

        #
        #
        #
        def writeOneConversionLog(self, aProcessInfo):
            try:
                    prodLogPath="%s/conversion_%d.log" % (aProcessInfo.workFolder, self.num_error)
                    fd=open(prodLogPath, 'w')
                    fd.write(aProcessInfo.getProdLog())
                    fd.flush()
                    fd.close()
            except Exception, eee:
                    print "Error: problem writing conversion log in fodler:%s" % aProcessInfo.workFolder
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())


        #
        #
        #
        def testFatalError(self, code, message):
            # exit for FATAL ERRORS
            #anError = errors.Error()
            if self.errorHandler.testCodeIsError(code, errors.ERROR_LOW_DISK)==True:
                print "FATAL: %s" % message
                sys.exit(code)
        
        #
        # process the list of products
        #
        def processProducts(self):
                #
                self.num=0
                self.num_total=0
                self.num_done=0
                self.num_error=0
                self.list_done=[]
                self.list_error=[]
                self.runStartTime=time.time()
                self.num_all=len(self.productList)

                #  create thumbnail:
                if self.create_thumbnail:
                    self.logger.info("will create thumbnail")

                # init stats util
                self.statsUtil.start(len(self.productList))
                
                for item in self.productList:
                        # not already done
                        try:
                            #print "look if '%s' is in already done list" % item
                            n=0
                            #print "self.productDoneList size:%d" % len(self.productDoneList)
                            #for aaa in self.productDoneList:
                            #        print " test already done[%s]:\n'%s' VS '%s" % (n, item, aaa)
                            #        n+=1
                            index = self.productDoneList.index(item)
                            self.logger.info("product already done[%d/%d][%s/%s]:%s" % ( self.num, self.num_all, self.num_done, self.num_error, item))
                            self.num=self.num+1
                            self.num_total=self.num_total+1

                            #
                            if  self.max_product_done!=-1 and self.num>= self.max_product_done:
                                    self.logger.info("max number of product to be done reached:%s; STOPPING" %  self.max_product_done)
                                    break
                                
                        except:
                            #print "TEST: stop after last already done"
                            #exc_type, exc_obj, exc_tb = sys.exc_info()
                            #print " already done problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                            #sys._exit(-1)
                            aProcessInfo=processInfo.processInfo()
                            aProcessInfo.srcPath=item
                            aProcessInfo.num=self.num
                            # set some usefull flags
                            self.setProcessInfo(aProcessInfo)
                            
                            self.num=self.num+1
                            self.num_total=self.num_total+1
                            self.logger.info("")
                            self.logger.info("")
                            self.logger.info("")
                            self.logger.info("")
                            self.logger.info("doing product[%d/%d][%s/%s]:%s" % ( self.num, self.num_all, self.num_done, self.num_error, item))
                            aProcessInfo.addLog("Doing product[%d/%d][%s/%s]:%s" % ( self.num, self.num_all, self.num_done, self.num_error, item))
                            aProcessInfo.addIngesterLog("Doing product[%d/%d][%s/%s]:%s" % ( self.num, self.num_all, self.num_done, self.num_error, item), 'PROGRESS')
                            processOk=False
                            try:
                                    self.reportToLogger(aProcessInfo, 'info', "doing product:%s" % aProcessInfo.srcPath)
                                    self.doOneProduct(aProcessInfo)

                                    self.num_done=self.num_done+1
                                    self.list_done.append(item+"|"+aProcessInfo.workFolder)

                                    # write current done product in log/batchName_current.txt file
                                    self.writeCurrentProduct(aProcessInfo)

                                    # + write a sysImage file: original name, eoSip name, size, stat, etc...
                                    if self.create_sys_items:
                                        self.createSysImFile(aProcessInfo)
                                    else:
                                        print " Warning: sysImg file is not created!"

                                    # apercu report
                                    #self.reportToApercu(aProcessInfo, "NAME=EoSip-converter&BINDING=converter:ingester&all=%s&done=%s&total=%s&error=%s&endTime=%s" % (self.num_all, self.num_done, self.num_total, self.num_error, urllib.quote(self.statsUtil.getEndDate())))
                                    self.reportToLogger(aProcessInfo, 'info',"all=%s; done=%s; total=%s; error=%s; endTime=%s" % (self.num_all, self.num_done, self.num_total, self.num_error, urllib.quote(self.statsUtil.getEndDate())))
                                    self.reportToGraphite(aProcessInfo, 'CONVERSION_OK', ['EOSIP_CONVERTER', 'SUCCESS'], "[%s]:%s" % (self.num_done - 1, item))

                                    # write log
                                    if not self.erase_tmp_work:
                                        self.writeOneConversionLog(aProcessInfo)

                                    processOk=True

                                    #
                                    self.makeJsonShape()

                                    
                            except Exception, e:
                                    # handle error
                                    self.num_error=self.num_error+1
                                    self.list_error.append("%s|%s" % (item,aProcessInfo.workFolder))
                                    code, message = self.errorHandler.handleError(sys.exc_info())
                                    if self.debug!=0:
                                        print " HANDLING RESULT; code=%s; message=%s" %  (code, message)

                                    #
                                    exc_type, exc_obj, exc_tb = sys.exc_info()
                                    self.errorSrc = "%s: %s" % (exc_type, exc_obj)
                                    #if self.DEBUG!=0:
                                    print " ERROR:%s  %s%s\n" %  (exc_type, exc_obj, traceback.format_exc())

                                    # apercu report
                                    #self.reportToApercu(aProcessInfo, "NAME=EoSip-converter&BINDING=converter:ingester&done=%s&total=%s&error=%s&endTime=%s" % (self.num_done, self.num_total, self.num_error, urllib.quote(self.statsUtil.getEndDate())))
                                    self.reportToLogger(aProcessInfo, 'error', "done=%s; total=%s; error=%s ; endTime=%s" % (self.num_done, self.num_total, self.num_error, urllib.quote(self.statsUtil.getEndDate())))
                                    self.reportToGraphite(aProcessInfo, 'CONVERSION_FAILED', ['EOSIP_CONVERTER', 'FAILURE'], "[%s]:%s. %s" % (self.num_done-1, item, message))

                                    # exit for FATAL ERRORS
                                    #anError = errors.Error()
                                    #if anError.testCodeIsError(code, errors.ERROR_LOW_DISK)==True:
                                    #    print "FATAL: %s" % message
                                    #    sys.exit(code)
                                    self.testFatalError(code, message)
                                        
                                    
                                    # 
                                    self.logger.error("Error:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                                    aProcessInfo.addLog("Error:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))

                                    # write log
                                    try:
                                            prodLogPath="%s/bad_conversion_%d.log" % (aProcessInfo.workFolder, self.num_error)
                                            fd=open(prodLogPath, 'w')
                                            fd.write(aProcessInfo.getProdLog())
                                            fd.close()
                                    except Exception, eee:
                                            print "Error: problem writing conversion log in fodler:%s" % aProcessInfo.workFolder
                                            exc_type, exc_obj, exc_tb = sys.exc_info()
                                            print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                                        
                                    # move source product if requested
                                    if self.test_move_source:
                                        self.moveSourceProductInFailed(aProcessInfo)

                            # save the matadata file in workfolder if needed
                            if processOk==False or not self.erase_tmp_work:
                                try:
                                    self.saveMetadata(aProcessInfo)
                                except:
                                    self.logger.error(" Error: saving metadata files")
                                    exc_type, exc_obj, exc_tb = sys.exc_info()
                                    print " ERROR saving metadata files:%s  %s%s\n" %  (exc_type, exc_obj, traceback.format_exc())

                            # save the pinfo in workfolder
                            if processOk==False or not self.erase_tmp_work:
                                try:
                                    self.saveProcessInfo(aProcessInfo)
                                except:
                                    self.logger.error(" Error: saving processInfo file")
                                    exc_type, exc_obj, exc_tb = sys.exc_info()
                                    print " ERROR saving processInfo file:%s  %s%s\n" %  (exc_type, exc_obj, traceback.format_exc())

                            # remove working folder if requested
                            if processOk==True and self.erase_tmp_work:
                                print " deleting working folder '%s'" %  aProcessInfo.workFolder
                                self.logger.info("deleting working folder '%s'" %  aProcessInfo.workFolder)
                                try:
                                    aFileHelper=fileHelper.FileHelper()
                                    aFileHelper.eraseFolder(aProcessInfo.workFolder, True)
                                except:
                                    exc_type, exc_obj, exc_tb = sys.exc_info()
                                    self.logger.info("ERROR deleting working folder '%s':%s  %s\n%s\n" %  (aProcessInfo.workFolder, exc_type, exc_obj, traceback.format_exc()))
                                    print "ERROR deleting working folder '%':%s  %s\n%s\n" %  (aProcessInfo.workFolder, exc_type, exc_obj, traceback.format_exc())
                            else:
                                print " dont delete working folder '%s': processOk=%s; self.erase_tmp_work=%s" %  (aProcessInfo.workFolder, processOk, self.erase_tmp_work)
                                self.logger.info("dont delete working folder '%s': processOk=%s; self.erase_tmp_work=%s" %  (aProcessInfo.workFolder, processOk, self.erase_tmp_work))
                        
                            #
                            if  self.max_product_done!=-1 and self.num>= self.max_product_done:
                                    self.logger.info("max number of product to be done reached:%s; STOPPING" %  self.max_product_done)
                                    break



                self.runStopTime=time.time()
                
                # write conversion log
                if not os.path.exists(self.LOG_FOLDER):
                    os.makedirs(self.LOG_FOLDER)
                path="%s/%s.log" % (self.LOG_FOLDER, self.batchName)
                self.writeLogInfo(self.summary());
                print " batch done log '%s' written in:%s" % (self.batchName, path)

                # write keeped info in any
                self.writeKeepedInfo()
                
                # write done list
                self.writeDoneProducts()
                
                # write error list
                self.writeFailledProducts()

                #
                self.makeJsonShape()

                #
                if self.singleProduct and self.num_error>0:
                    return -1
                else:
                    return 0


        #
        # move product into failed folder
        #
        def moveSourceProductInFailed(self, aprocessInfo):
            print "will move product into failed folder"

            # test disk space
            # usage tuples: total, used, free, freePercent
            usage = self.testDiskSpace(self.FAILEDSPACE)
            if self.debug!=0:
                print " failed partition DISK USAGE:%s" % (usage,)
            aprocessInfo.addLog(" failed partition DISK USAGE:%s" % (usage,))
            
            # bellow limit? use arbitrary 10GB
            free=usage[2]/(1024*1014*1024)
            if self.debug!=0:
                print " failed partition DISK USAGE: free disk %s ->%s" % (usage[2], free)
            if free < 10:
                raise Exception("failed partition DISK low limit reached: free:%s  limit:%s" % (free, self.disk_low_space_limit))

            print " copy src product %s at failed  path:%s" % (aprocessInfo.srcProduct.path, "%s/%s" % (self.FAILEDSPACE, aprocessInfo.srcProduct.origName)) 
            self.safeCopy(aprocessInfo.srcProduct.path, "%s/%s" % (self.FAILEDSPACE, aprocessInfo.srcProduct.origName))


        #
        # move product into done folder
        #
        def moveSourceProductInDone(self, aprocessInfo):
            print "will move product into done folder"
            
            # test disk space
            # usage tuples: total, used, free, freePercent
            usage = self.testDiskSpace(self.DONESPACE)
            if self.debug!=0:
                print " done partition DISK USAGE:%s" % (usage,)
            aprocessInfo.addLog(" done partition DISK USAGE:%s" % (usage,))

            # bellow limit? use arbitrary 10GB
            free=usage[2]/(1024*1014*1024)
            if self.debug!=0:
                print " done partition DISK USAGE: free disk %s ->%s" % (usage[2], free)
            if free < 10:
                raise Exception("done partition DISK low limit reached: free:%s  limit:%s" % (free, self.disk_low_space_limit))

            print " copy src product %s at done  path:%s" % (aprocessInfo.srcProduct.path, "%s/%s" % (self.DONESPACE, aprocessInfo.srcProduct.origName)) 
            self.safeCopy(aprocessInfo.srcProduct.path, "%s/%s" % (self.DONESPACE, aprocessInfo.srcProduct.origName))


        #
        # copy a file, verifying that the copy went well:
        # - verify sizes
        # - verify hash
        #
        def safeCopy(self, src, dest):
            # test presence of src file
            if not os.path.exists(src):
                raise ValueError('Source file does not exist: {}'.format(src))

            if os.path.exists(dest):
                raise ValueError('Destination file exist: {}'.format(dest))
            
            # create a folder for dst if not already exist
            if not os.path.exists(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))

            # get info on src
            srcSize = os.stat(src).st_size
            #aSysItem = sysItem.SysItem()
            #aSysItem.setPath(src)
            srcHash = sysItem.hashfile(src)
            #print " HASH 1:%s" % srcHash

            #aSysItem = sysItem.SysItem()
            #aSysItem.setPath(src)
            #srcHash = aSysItem.hashfile()
            #print " HASH 2:%s" % srcHash

            #aSysItem = sysItem.SysItem()
            #aSysItem.setPath(src)
            #srcHash = aSysItem.hashfile()
            #print " HASH 3:%s" % srcHash
            
            buffSize=1024
            src_fd=None
            dst_fd=None
            try:
                src_fd = os.open(src, os.O_RDONLY)
                try:
                    dst_fd = os.open(dest, os.O_WRONLY|os.O_EXCL|os.O_CREAT|os.O_EXLOCK)
                except:
                    dst_fd = os.open(dest, os.O_WRONLY|os.O_EXCL|os.O_CREAT)
                # Read buffSize bytes at a time, and copy them from src to dst
                while True:
                    data = os.read(src_fd, buffSize)
                    if not data:
                        break
                    else:
                        os.write(dst_fd, data)
            
            # An OSError errno 17 is what happens if a file pops into existence
            # at dst, so we print an error and try to copy to a new location.
            # Any other exception is unexpected and should be raised as normal.
            except OSError as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.logger.info("ERROR during safeCopy:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                print "ERROR during safeCopy:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                #if e.errno != 17 or e.strerror != 'File exists':
                #    raise
                #else:
                #    print('not file exists error')
            finally:
                try:
                    os.close(src_fd)
                except:
                    print "safeCopy: ERROR closing src_fd"
                    #pass
                try:
                    os.close(dst_fd)
                except:
                    print "safeCopy: ERROR closing dst_fd"
                    #pass

            #aSysItem = sysItem.SysItem()
            #aSysItem.setPath(src)
            #srcHash = aSysItem.hashfile()
            #print " HASH 4:%s" % srcHash
                
            # get info on dest
            destSize = os.stat(dest).st_size
            #aSysItem = sysItem.SysItem()
            #aSysItem.setPath(dest)
            destHash = sysItem.hashfile(dest)

            if destSize!=srcSize:
                raise ValueError('safe copy failed: src size=%s; dest size=%s' % (srcSize, destSize))

            if destHash!=srcHash:
                raise ValueError('safe copy failed: src hash=%s; dest hash=%s' % (srcHash, destHash))

            #sys.exit(0)
        
        #
        #
        #
        def summary(self):
            out = StringIO()
            print >> out, ("\nSummary:\n Ingester version: %s" % self.getVersion())
            print >> out, (" CONFIGURATION: %s" % self.CONFIG_NAME)
            print >> out, (" CONFIG VERSION: %s" % self.CONFIG_VERSION)
            print >> out, (" EoSip definition package path in use:%s\n" % self.sysPathsInUse)
            print >> out, (" batch name:%s\n Started at: %s" % ( self.batchName, formatUtils.dateFromSec((self.runStartTime))))
            print >> out, (" Stoped at: %s" % (formatUtils.dateFromSec(self.runStopTime)))
            print >> out, (" Duration: %s sec\n" % ((self.runStopTime-self.runStartTime)))
            print >> out, (" INBOX:%s" % (self.INBOX))
            print >> out, (" TMPSPACE:%s" % (self.TMPSPACE))
            print >> out, (" OUTSPACE:%s\n" % (self.OUTSPACE))
            print >> out, (" Total of products to be processed:%d" % (self.num_total))
            print >> out, ("  Number of products done:%d" % (self.num_done))
            print >> out, ("  Number of errors:%d\n" % (self.num_error))
            #
            #
            n=0
            for item in self.list_done:
                print >> out, (" done[%d]:%s" % ( n, item))
                n=n+1
            #
            #
            n=0
            print >> out, ("\n")
            for item in self.eosip_done:
                print >> out, (" eosip[%d]:%s" % ( n, item))
                n=n+1
            #
            #
            n=0
            print >> out, ("\n")
            for item in self.list_error:
                print >> out, (" errors[%d]:%s" % (n, item))
                n=n+1
            #
            #
            print >> out, ("  Number of product done:%d" % (self.num_done))
            print >> out, ("  Number of errors:%d" % (self.num_error))
            print >> out, (" Duration: %s sec" % ( (self.runStopTime-self.runStartTime)))
            print out.getvalue()
            return out.getvalue()

 
        #
        # do one product
        #
        def doOneProduct(self, pInfo):

                # usage tuples: total, used, free, freePercent
                usage = self.testDiskSpace(self.OUTSPACE)
                if self.debug!=0:
                    print " DISK USAGE:%s" % (usage,)
                pInfo.addLog("DISK USAGE:%s" % (usage,))
                # bellow limit?
                free=usage[2]/(1024*1014*1024)
                if self.debug!=0:
                    print " DISK USAGE: free disk %s ->%s" % (usage[2], free)
                print " DISK USAGE: free disk %s ->%s VS %s" % (usage[2], free, self.disk_low_space_limit)
                if free < self.disk_low_space_limit:
                    raise Exception("DISK low limit reached: free:%s  limit:%s" % (free, self.disk_low_space_limit))


                startProcessing=time.time()
                # create work folder
                workfolder=self.makeWorkingFolders(pInfo)
                #
                if self.verify_product==1:
                    self.verifySourceProduct(pInfo)
                # instanciate source product
                self.createSourceProduct(pInfo)
                # make processInfo available in source product
                pInfo.srcProduct.processInfo=pInfo
                # prepare it: move/decompress it in work folder
                self.prepareProducts(pInfo)
                # create empty metadata
                met=metadata.Metadata(self.mission_metadatas)
                met.setMetadataPair(metadata.METADATA_ORIGINAL_NAME, pInfo.srcProduct.origName)
                if self.debug!=0:
                        print "\n###  initial metadata dump:\n%s" % met.toString()
                        
                # extract metadata from source product
                self.extractMetadata(met, pInfo)
                if self.debug!=0:
                        print "\n###  final metadata dump:\n%s" % met.toString()

                # instanciate destination product
                self.createDestinationProduct(pInfo)
                # set generationTime
                pInfo.destProduct.setGenerationTime(self.generationTime)
                # set processInfo into destination product, to make it access things like the srcProduct or ingester
                pInfo.destProduct.setTypology(self.TYPOLOGY)
                pInfo.destProduct.setSrcProductStoreType(self.eoSip_store_type)
                pInfo.destProduct.setSrcProductStoreCompression(self.eoSip_store_compression)
                pInfo.destProduct.setSrcProductStoreEoCompression(self.eoSip_store_eo_compression)
                pInfo.destProduct.test_build_in_tmpspace = self.test_build_in_tmpspace
                pInfo.destProduct.setProcessInfo(pInfo)
                # set the EOP typology used
                met.setOtherInfo("TYPOLOGY_SUFFIX", self.TYPOLOGY)


                # set metadata if not already defined, 2015-05-20: or merge
                if pInfo.destProduct.metadata==None: #.isMetadataDefined():
                    pInfo.destProduct.setMetadata(met)
                    print " dest product metadata is NONE!"
                    self.logger.info(" dest product metadata is NONE!")
                else:
                    try:
                        print " dest product metadata is NOT NONE!:\n%s" % met.toString()
                        self.logger.info("  dest product metadata is NOT NONE!:\n%s" % met.toString())
                        pInfo.destProduct.metadata.merge(met)
                        #print "   metadata merged:\n%s" % pInfo.destProduct.metadata.toString()
                        self.logger.info("  dest product metadata is NOT NONE!:\n%s" % met.toString())
                    except:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        print "  error merging matadata%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                        self.logger.info("  error merging matadata")
                        raise Exception("error merging matadata")

                try:
                    pInfo.destProduct.setXmlMappingMetadata(self.xmlMappingMetadata, self.xmlMappingBrowse)
                except:
                    print " error merging matadata 2"
                    self.logger.info(" error merging matadata 2")
                    raise Exception("error merging matadata 2")
                
                if self.debug!=0:
                    print " dest product metadata set"
                self.logger.info(" dest product metadata set")

                # build the output relative paths list
                if 1==1:
                    try:
                        self.outputProductResolvedPaths = pInfo.destProduct.getOutputFolders(self.OUTSPACE, self.OUTPUT_RELATIVE_PATH_TREES)
                        relativePathPart=self.outputProductResolvedPaths[0][len(self.OUTSPACE):]
                        met.setMetadataPair(metadata.METADATA_PRODUCT_RELATIVE_PATH, relativePathPart)
                    except:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        pInfo.addLog("ERROR getting output relative paths:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                        self.logger.info("ERROR getting output relative paths")
                        print "ERROR getting output relative paths:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                        raise Exception("ERROR getting output relative paths:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))

                # build product name
                # set variables
                self.logger.info("  will build Eo-Sip package name" )
                pInfo.addLog('')
                pInfo.addLog("- will build Eo-Sip package name")
                if self.eoSip_store_type==product_EOSIP.SRC_PRODUCT_AS_ZIP:
                    pInfo.destProduct.setEoExtension(definitions_EoSip.getDefinition('EOSIP_PRODUCT_EXT'))
                elif self.eoSip_store_type==product_EOSIP.SRC_PRODUCT_AS_TAR:
                    pInfo.destProduct.setEoExtension(definitions_EoSip.getDefinition('TAR_EXT'))
                elif self.eoSip_store_type==product_EOSIP.SRC_PRODUCT_AS_TGZ:
                    pInfo.destProduct.setEoExtension(definitions_EoSip.getDefinition('TGZ_EXT'))
                elif self.eoSip_store_type==product_EOSIP.SRC_PRODUCT_AS_DIR:
                    pInfo.destProduct.setEoExtension(None)
                elif self.eoSip_store_type==product_EOSIP.SRC_PRODUCT_AS_FILE:
                    # don't change it if already defined
                    if pInfo.destProduct.getEoExtension() is not None:
                            print " write SRC_PRODUCT_AS_FILE don't change EO extension:%s" % pInfo.destProduct.getEoExtension()
                    else:
                            #pInfo.destProduct.setEoExtension(None)
                            pass
                    
                # build names
                self.buildEoNames(pInfo)
                namesInfo = pInfo.destProduct.getNamesInfo()
                self.logger.info(" namesInfo:\n%s" % namesInfo)
                pInfo.addLog(" namesInfo:\n%s" % namesInfo)


                # make Eo-Sip tmp folder
                data = pInfo.destProduct.makeFolder(pInfo.workFolder)
                self.logger.info("  tmpEosipFolder info:%s" % data)
                pInfo.addLog("tmpEosipFolder info:%s" % data)
                

                # build the output relative paths list
                if 1==2: # code moved before 2 to allow duplicate test?
                    try:
                        self.outputProductResolvedPaths = pInfo.destProduct.getOutputFolders(self.OUTSPACE, self.OUTPUT_RELATIVE_PATH_TREES)
                        relativePathPart=self.outputProductResolvedPaths[0][len(self.OUTSPACE):]
                        met.setMetadataPair(metadata.METADATA_PRODUCT_RELATIVE_PATH, relativePathPart)
                    except:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        pInfo.addLog("ERROR creating sysItem:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                        self.logger.info("ERROR creating sysItem")
                        print "ERROR getting output relative paths:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                        raise Exception("ERROR getting output relative paths:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))


                # make browse file
                if not self.test_just_extract_metadata:
                    self.makeBrowses(pInfo)

                # 
                self.beforeReportsDone(pInfo)

                # display info
                pInfo.destProduct.info()

                # make report files
                # SIP report
                if not self.test_just_extract_metadata and self.create_sip_report == True:
                    pInfo.addLog('')
                    pInfo.addLog("- will build SIP file")
                    self.logger.info("  will build SIP file")
                    tmp=pInfo.destProduct.buildSipReportFile()
                    pInfo.addLog(" => Sip report file built well:%s" %  (tmp))
                    self.logger.info("  Sip report file built well:%s" %  (tmp))


                # browse reports
                if not self.test_just_extract_metadata and self.create_browse_report == True:
                    pInfo.addLog('')
                    pInfo.addLog("- will build browse reports")
                    self.logger.info("  will build browse reports")
                    tmp=pInfo.destProduct.buildBrowsesReportFile()
                    n=0
                    for item in tmp:
                        pInfo.addLog(" => browse[%d] report file built:%s\n" %  (n, item))
                        self.logger.info("  browse[%d] report file built:%s" %  (n, item))
                        n=n+1

                # metadata report
                if not self.test_just_extract_metadata:
                    pInfo.addLog('')
                    pInfo.addLog("- will build product report")
                    self.logger.info("  will build product report")
                    tmp=pInfo.destProduct.buildProductReportFile()
                    pInfo.addLog(" => Product report file built well: %s" % tmp)
                    self.logger.info("  Product report file built well: %s" % tmp)

                    #
                    self.afterReportsDone(pInfo)

                # display some info
                print pInfo.destProduct.info()

                if 1==2: # code moved before 1; why?
                    # CODE MOVED FROM specialized ingested
                    # build the output relative paths list
                    try:
                        self.outputProductResolvedPaths = pInfo.destProduct.getOutputFolders(self.OUTSPACE, self.OUTPUT_RELATIVE_PATH_TREES)
                        relativePathPart=self.outputProductResolvedPaths[0][len(self.OUTSPACE):]
                        met.setMetadataPair(metadata.METADATA_PRODUCT_RELATIVE_PATH, relativePathPart)
                    except:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        pInfo.addLog("ERROR creating sysItem:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                        self.logger.info("ERROR creating sysItem")
                        print "ERROR getting output relative paths:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())
                        raise Exception("ERROR getting output relative paths:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                
                # output Eo-Sip product
                if not self.test_just_extract_metadata:
                    if self.test_dont_write==False:
                        outPath = self.output_eoSip(pInfo, self.OUTSPACE, self.OUTPUT_RELATIVE_PATH_TREES, self.product_overwrite)
                        # test for old converter not up to date
                        if outPath==None:
                            raise Exception("Ingester not up to date: self.output_eoSip() return None and not outpath")
                        self.eosip_done.append(outPath)
                    else:
                        pInfo.addLog("## EoSip write disabled !!!")
                        self.logger.info(" ## EoSip write disabled !!!")
                    
                    # move source product if requested
                    if self.test_move_source:
                        self.moveSourceProductInDone(pInfo)


                    #
                    self.afterProductDone(pInfo)


                    #
                    if not self.test_dont_write:
                        # make kmz by default
                        print " @@ pInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_KMZ_USE_BOOUNDINGBOX):%s" % (pInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_KMZ_USE_BOOUNDINGBOX))
                        #os._exit(1)
                        if self.create_kmz:
                            #
                            # new: config file may have a setting for BOOUNDINGBOX uusage
                            #      also if the browse is already well oriented (meaningful only for bbox case?)
                            #
                            useBbox = pInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_KMZ_USE_BOOUNDINGBOX)
                            pInfo.addLog("useBbox:%s; type:%s" % (useBbox, type(useBbox)))
                            if useBbox == sipBuilder.VALUE_NOT_PRESENT:
                                raise Exception("create KMZ problem: METADATA_KMZ_USE_BOOUNDINGBOX is not defined")
                            bUseBbox=False
                            if isinstance(useBbox, str):
                                #print "useBbox is string"
                                if useBbox=='True':
                                    bUseBbox = True
                            elif isinstance(useBbox, bool):
                                #print "useBbox is bool"
                                bUseBbox=useBbox

                            bDontReverseBrowse = False  # i.e. don't reverse ring when doing kmz, default case
                            dontReverseBrowse = pInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_KMZ_DONT_REVERSE_BROWSE)
                            pInfo.addLog("dontReverseBrowse:%s; type:%s" % (dontReverseBrowse, type(dontReverseBrowse)))
                            if not pInfo.srcProduct.metadata.valueExists(dontReverseBrowse):
                                #raise Exception("create KMZ problem: METADATA_KMZ_USE_BOOUNDINGBOX is not defined")
                                pass
                            else:
                                if isinstance(dontReverseBrowse, str):
                                    #print "dontReverseBrowse is string"
                                    if dontReverseBrowse=='True':
                                        bDontReverseBrowse = True
                                elif isinstance(dontReverseBrowse, bool):
                                    #print "dontReverseBrowse is bool"
                                    bDontReverseBrowse=dontReverseBrowse

                            self.makeKmz(pInfo, bUseBbox, bDontReverseBrowse)
                        else:
                            self.logger.info("KMZ creation disabled !")
                            pInfo.addLog("KMZ creation disabled !")

                        self.products_done.append(outPath)
                        if self.debug != 0:
                            print " pInfo:%s; outPath:%s;  type pInfo:%s; outPath:%s"% (pInfo, outPath, type(pInfo), type(outPath))
                        try:
                            tmp = str("product done:%s" %  outPath)
                            #print "###########3## tmp:"+tmp
                            pInfo.addLog(tmp)
                            #pInfo.addLog2(tmp)
                            self.logger.info(tmp)
                        except:
                            print "###########2## pInfo:%s; outPath:%s;  type pInfo:%s; outPath:%s"% (pInfo, outPath, type(pInfo), type(outPath))
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            print "############# pInfo.addLog problem: %s  %s\n%s" % (exc_type, exc_obj, traceback.format_exc())
                            pass


                    else:
                        self.logger.info("Product write disabled !!!")
                        pInfo.addLog("- Product write disabled !!!")


                else:
                    pInfo.addLog("## just extract metadata !!!")
                    self.logger.info(" ## just extract metadata !!!")

                self.agregateGeoInfo(pInfo)

                # compute stats
                processingDuration=time.time()-startProcessing
                pInfo.ingester.keepInfo("duration__%s" % pInfo.srcProduct.origName, "%s" % processingDuration)
                size=None
                try:
                    # TODO: move get size into product??
                    if pInfo.destProduct.path is not None: # is None for multiple product like worldview
                        size=os.stat(pInfo.destProduct.path).st_size
                    #self.logger.info("  batch run will be completed at:%s" % self.statsUtil.getEndDate())
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    pInfo.addLog("Error:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                    self.logger.info("Error doing stats")
                    print "############# stat: %s  %s\n%s" % (exc_type, exc_obj, traceback.format_exc())

                self.statsUtil.oneDone(processingDuration, size)
                print "\n\n##### LOG start ####\n%s##### LOG end ####" % pInfo.getProdLog()
                print "\n\n##### PROCESS INFO start ####\n%s#### PROCESS INFO end ####\n\n" % pInfo.toString()
                self.logger.info("\n\n##\n    item done in %s secs; batch run will be completed at:%s\n##\n" % (processingDuration, self.statsUtil.getEndDate()))
                #print "\n####\n  batch run will be completed at:%s\n####" % self.statsUtil.getEndDate()

        #
        # dump info
        #
        def dump__NOT_USED(self):
                self.logger.info("   INBOX: %s" % self.INBOX)
                self.logger.info("   TMPSPACE: %s" % self.TMPSPACE)
                self.logger.info("   OUTSPACE: %s" % self.OUTSPACE)
                self.logger.info("   DONESPACE: %s" % self.DONESPACE)
                self.logger.info("   FAILEDSPACE: %s" % self.FAILEDSPACE)
                self.logger.info("   Move source products in DONESPACE: %s" % self.test_move_source)

                self.logger.info(" ")
                self.logger.info("   daemon: %s" % self.daemon)
                self.logger.info("   daemon class: %s" % self.daemonClass)
                self.logger.info("   multiprocessing: %s" % self.multiprocessing)
                                 
                self.logger.info(" ")
                self.logger.info("   Fixed batch name: %s" % self.fixed_batch_name)
                self.logger.info("   ERASE SOURCE PRODUCT: %s" % self.erase_src)
                self.logger.info("   Erase tmp and working folder: %s" % self.erase_tmp_work)
                self.logger.info("   Max product done limit: %s" % self.max_product_done)
                self.logger.info("   Disk low space limit: %s" % self.disk_low_space_limit)
                self.logger.info("   Verify product: %s" % self.verify_product)
                self.logger.info("   Verify xml created: %s" % self.verify_xml)
                self.logger.info("   Sanitize xml created: %s" % self.sanitize_xml)
                self.logger.info("   Create thumbnail: %s" % self.create_thumbnail)
                self.logger.info("   Create browse report: %s" % self.create_browse_report)
                self.logger.info("   Create sip report: %s" % self.create_sip_report)
                self.logger.info("   Create sysItems: %s" % self.create_sys_items)
                self.logger.info("   Index added: %s" % self.index_added)
                self.logger.info("   Product overwrite: %s" % self.product_overwrite)
                self.logger.info("   Can auto  correct filecounter: %s" % self.can_autocorrect_filecounter)
                self.logger.info("   Want duplicate: %s" % self.want_duplicate)
                self.logger.info("   OUTPUT_SIP_PATTERN: %s" % self.OUTPUT_SIP_PATTERN)
                self.logger.info("   OUTPUT_EO_PATTERN: %s" % self.OUTPUT_EO_PATTERN)
                self.logger.info("   OUTPUT_RELATIVE_PATH_TREES: %s" % self.OUTPUT_RELATIVE_PATH_TREES)
                self.logger.info("   eoSip typology: %s" % self.TYPOLOGY)
                self.logger.info("   eoSip store type: %s" % self.eoSip_store_type)
                self.logger.info("   eoSip store compression: %s" % self.eoSip_store_compression)
                self.logger.info("   eoSip store Eo productt compression: %s" % self.eoSip_store_eo_compression)
                self.logger.info("   TEST MODE: %s" % self.test_mode)
                self.logger.info("   TEST; don't extract source product: %s" % self.test_dont_extract)
                self.logger.info("   TEST; don't write destination product: %s" % self.test_dont_write)
                self.logger.info("   TEST; don't do browse: %s" % self.test_dont_do_browse)
                self.logger.info("   TEST; just extract metadata: %s" % self.test_just_extract_metadata)
                #if len(dataProviders) > 0:
                self.logger.info("   additional data providers:%s" % self.dataProviders)
                #else:
                #    print "   no dataprovider"
                self.logger.info("   additional service providers:%s" % self.servicesProvider)
                #raise Exception("STOP")
                

        #
        # dump info
        #
        def dump(self):
            print self.toString()


            
        #
        # return info
        #
        def toString(self):
            out=StringIO()
            print >>out, ("   Ingester version: %s" % self.getVersion())
            print >>out, ("   CONFIGURATION: %s" % self.CONFIG_NAME)
            print >>out, ("   CONFIG VERSION: %s" % self.CONFIG_VERSION)
            print >>out, ("   INBOX: %s" % self.INBOX)
            print >>out, ("   TMPSPACE: %s" % self.TMPSPACE)
            print >>out, ("   OUTSPACE: %s" % self.OUTSPACE)
            print >>out, ("   DONESPACE: %s" % self.DONESPACE)
            print >>out, ("   FAILEDSPACE: %s" % self.FAILEDSPACE)
            print >>out, ("   Move source products in DONESPACE: %s" % self.test_move_source)
            print >>out, ("   Build products in TMPSPACE: %s" % self.test_build_in_tmpspace)

            print >>out, (" ")
            print >>out, ("   daemon: %s" % self.daemon)
            print >>out, ("   daemon class: %s" % self.daemonClass)
            print >>out, ("   multiprocessing: %s" % self.multiprocessing)

            print >>out, (" ")
            print >>out, ("   Fixed batch name: %s" % self.fixed_batch_name)
            print >>out, ("   ERASE SOURCE PRODUCT: %s" % self.erase_src)
            print >>out, ("   Erase tmp and working folder: %s" % self.erase_tmp_work)
            print >>out, ("   Max product done limit: %s" % self.max_product_done)
            print >>out, ("   Disk low space limit: %s" % self.disk_low_space_limit)
            print >>out, ("   Verify product: %s" % self.verify_product)
            print >>out, ("   Verify xml created: %s" % self.verify_xml)
            print >>out, ("   Sanitize xml created: %s T:%s" % (self.sanitize_xml, type(self.sanitize_xml)))
            print >>out, ("   Create thumbnail: %s" % self.create_thumbnail)
            print >>out, ("   Create browse repor: %s" % self.create_browse_report)
            print >>out, ("   Create sip repor: %s" % self.create_sip_report)
            print >>out, ("   Create sysItems: %s" % self.create_sys_items)
            
            print >>out, ("   Index added: %s" % self.index_added)
            print >>out, ("   Product overwrite: %s" % self.product_overwrite)
            print >>out, ("   Can auto  correct filecounter: %s" % self.can_autocorrect_filecounter)
            print >>out,("   Want duplicate: %s" % self.want_duplicate)
            print >>out, ("   OUTPUT_SIP_PATTERN: %s" % self.OUTPUT_SIP_PATTERN)
            print >>out, ("   OUTPUT_EO_PATTERN: %s" % self.OUTPUT_EO_PATTERN)
            print >>out, ("   OUTPUT_RELATIVE_PATH_TREES: %s" % self.OUTPUT_RELATIVE_PATH_TREES)

            print >>out, (" ")
            print >>out, ("   eoSip typology: %s" % self.TYPOLOGY)
            print >>out, ("   eoSip store type: %s" % self.eoSip_store_type)
            print >>out, ("   eoSip store compression: %s" % self.eoSip_store_compression)
            print >>out, ("   eoSip store Eo productt compression: %s" % self.eoSip_store_eo_compression)
            print >>out, ("   TEST MODE: %s" % self.test_mode)
            print >>out, ("   TEST; don't extract source product: %s" % self.test_dont_extract)
            print >>out, ("   TEST; don't write destination product: %s" % self.test_dont_write)
            print >>out, ("   TEST; just extract metadata: %s" % self.test_just_extract_metadata)
            print >>out, ("   eoSip store type: %s" % self.eoSip_store_type)
            #if len(dataProviders) > 0:
            print >>out, ("   additional data providers:%s" % self.dataProviders)
            #else:
            #    print "   no dataprovider"
            print >>out, ("   additional service providers:%s" % self.servicesProvider)
            #
            print >>out, ("   additional ressource providers:%s" % self.ressourcesProvider)

            # add sys.path, to check which EoSIp definition is imported
            print >>out, ("   EoSip definition package path in use:%s" % self.sysPathsInUse)

            return out.getvalue()


        #
        # 
        #
        #def getSysPathUsed(self):
        #        aSysTool = SysPathTool()
        #        return aSysTool.getSysPathUsed()

        
        #
        # save metadata as files
        #
        def saveMetadata(self, pInfo):
            if pInfo.destProduct is not None and pInfo.destProduct.metadata  is not None:
                try:
                    # save metadata in working folder
                    workfolder=pInfo.workFolder
                    fd=open("%s/metadata-product.txt" % (workfolder), 'w')
                    fd.write(pInfo.destProduct.getMetadataAsString())
                    fd.close()
                except Exception, e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        pInfo.addLog("ERROR saving product metadata files:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                        self.logger.info("ERROR saving product metadata files")
                        print "ERROR saving product metadata files:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())

            # dest product may not have browse_metadata_dict
            if hasattr(pInfo.destProduct, 'browse_metadata_dict'):
                if pInfo.destProduct is not None and pInfo.destProduct.browse_metadata_dict is not None and len(pInfo.destProduct.browse_metadata_dict)>0:
                    try: 
                        # also browse metadata
                        n=0
                        for item in pInfo.destProduct.browse_metadata_dict.values():
                            fd=open("%s/metadata-browse-%d.txt" % (workfolder, n), 'w')
                            fd.write(item.toString())
                            fd.close()
                    except Exception, e:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            pInfo.addLog("ERROR saving browse metadata files:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                            self.logger.info("ERROR saving browse metadata files")
                            print "ERROR saving browse metadata files:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())


        #
        # save processInfo as files
        #
        def saveProcessInfo(self, pInfo):
            try:
                # save pInfo in working folder
                workfolder=pInfo.workFolder
                fd=open("%s/processInfo.txt" % (workfolder), 'w')
                fd.write("####\n")
                fd.write(pInfo.toString())
                fd.write("\n####\n#### Process Info:\n####\n")
                fd.write(self.toString())
                fd.close()
            except Exception, e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    pInfo.addLog("ERROR saving pinfo files:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                    self.logger.info("ERROR saving pinfo files")
                    print"ERROR saving pinfo files:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())


        #
        #
        #
        def createSysImFile(self, aProcessInfo):
            if not self.test_just_extract_metadata and not self.test_dont_write:
                try:
                    tmp = "%s/sysImgs" % self.LOG_FOLDER
                    if not os.path.exists(tmp):
                        self.logger.info("  will make sysImgs folder:%s" % tmp)
                        os.makedirs(tmp)

                    #
                    sysitemSrc, sysitemDest = self.createSysItem(aProcessInfo)

                    #
                    if self.debug != 0:
                        print "  sysitemSrc:%s" % sysitemSrc.toString()
                    if isinstance(sysitemDest, list):
                        n=0
                        for item in sysitemDest:
                            if self.debug != 0:
                                print "  sysitemDest[%s]:%s" % (n, item.toString())
                            apath="%s/%s.img" % (tmp, item.getName())
                            fd=open(apath, "w")
                            fd.write("#items:2\n")
                            fd.write("#path:mixed\n")
                            fd.write("#date:%s\n" % formatUtils.dateFromSec(time.time()))
                            fd.write("#headers:%s\n" % sysitemSrc.getHeader())
                            fd.write("%s\n" % sysitemSrc.toString())
                            fd.write("%s\n" % item.toString())
                            fd.flush()
                            fd.close()
                            
                            n=n+1
                    else:
                        if self.debug != 0:
                            print "  sysitemDest:%s" % sysitemDest.toString()
                        apath="%s/%s.img" % (tmp, sysitemDest.getName())
                        fd=open(apath, "w")
                        fd.write("#items:2\n")
                        fd.write("#path:mixed\n")
                        fd.write("#date:%s\n" % formatUtils.dateFromSec(time.time()))
                        fd.write("#headers:%s\n" % sysitemSrc.getHeader())
                        fd.write("%s\n" % sysitemSrc.toString())
                        fd.write("%s\n" % sysitemDest.toString())
                        fd.flush()
                        fd.close()
                        
                except Exception, eee:
                    print "Error: problem writing sysItem"
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    print " problem is:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())

            else:
                if self.debug != 0:
                    print "  createSysImFile disabled because: test_just_extract_metadata=%s OR test_dont_write=%s" % (self.test_just_extract_metadata, self.test_dont_write)
                    aProcessInfo.addLog("createSysImFile disabled because: test_just_extract_metadata=%s OR test_dont_write=%s" % (self.test_just_extract_metadata, self.test_dont_write))

        #
        # send notification to graphite
        #
        def reportToGraphite(self, pInfo, what='default', tags=[], data='ingester.reportToGraphite'):
            if not self.hasService(serviceProvider.SERVICE_GRAPHITE_EVENTS):
                print" reportToGraphite not possible because has no service!"
                return
            tags.append('MISSION_%s' % self.CONFIG_NAME)
            try:
                # create graphite client first time
                if self.graphiteReporter==None:
                    self.graphiteReporter = GraphiteEventsClient.GraphiteEventsClient(pInfo)
                # send payload
                self.graphiteReporter.sendNotification(what, tags, data)
            except:
                traceback.print_exc(file=sys.stdout)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print" ERROR reportToGraphite:%s  %s" % (exc_type, exc_obj)


        #
        # send notification to logger
        #
        def reportToLogger(self, pInfo, level, message):
            if not self.hasService(serviceProvider.SERVICE_REMOTE_LOGGER):
                print" reportToLogger not possible because has no service!"
                return
            try:
                # create client first time
                if self.loggerReporter==None:
                    self.loggerReporter = remoteLoggerServiceClient.RemoteLoggerServiceClient(pInfo)
                # send 
                self.loggerReporter.processRequest(level, message)

            except:
                pass

        #
        #
        #
        def createSysItem(self, pInfo):
            try:
                #
                sysitemSrc = sysItem.SysItem()
                self.logger.info("create src sysItem for item at path:%s" % pInfo.srcProduct.path)
                sysitemSrc.setPath(pInfo.srcProduct.path)
                sysitemSrc.stat()
                sysitemDest = sysItem.SysItem()

                # dest can contains multiple products: path is string or list
                paths = pInfo.destProduct.getPath()
                self.logger.info("create dest sysItem for item at paths:%s" % paths)
                if paths is not None:
                    if isinstance(paths, list): 
                        n=0
                        sysitemDest = []
                        #aSysitemDest = sysItem.SysItem()
                        for path in paths:
                            aSysitemDest = sysItem.SysItem()
                            self.logger.info("create dest sysItem for item at path[%s]:%s" % (n, path))
                            aSysitemDest.setPath(path)
                            aSysitemDest.stat()
                            sysitemDest.append(aSysitemDest)
                            n=n+1
                    else:
                        sysitemDest = sysItem.SysItem()
                        sysitemDest.setPath(paths)
                        sysitemDest.stat()
                        
                return sysitemSrc, sysitemDest;
            except:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                pInfo.addLog("ERROR creating sysItem:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc()))
                self.logger.info("ERROR creating sysItem")
                print"ERROR creating sysItem:%s  %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())


        #
        # create a kmz
        # created in the log folder
        #
        def makeKmz(self, processInfo, useBbox, dontReverseBrowse):
                self.logger.info("WILL CREATE KMZ; useBbox=%s; dontReverseBrowse=%s" % (useBbox, dontReverseBrowse))
                if self.debug!=0:
                    print "########################################## %s" % os.path.dirname(os.path.abspath(inspect.getfile(kmz)))
                outPath = "%s/kmz" % processInfo.ingester.LOG_FOLDER
                if not os.path.exists(outPath):
                        self.logger.info("  will make kmz folder:%s" % outPath)
                        os.makedirs(outPath)
                kmzPath = kmz.eosipToKmz.makeKmlFromEoSip_new(useBbox, outPath, processInfo, dontReverseBrowse)
                print " KMZ created at path:%s; useBbox:%s; dontReverseBrowse:%s" % (kmzPath, useBbox, dontReverseBrowse)
                if kmzPath != None:
                        processInfo.addLog("KMZ created at path:%s; useBbox:%s; dontReverseBrowse:%s" % (kmzPath, useBbox, dontReverseBrowse))
                else:
                        processInfo.addLog("KMZ was NOT CREATED!")
                        raise Exception("KMZ was NOT CREATED!")


        #
        # check that configuration floatVersion is >= minimum
        # config version is like: 'name_floatVersion' or 'floatVersion'
        #
        # should be abstract
        #
        @abstractmethod
        def checkConfigurationVersion(self, processInfo):
            raise Exception("abstractmethod")

        # implement the config version test
        def _checkConfigurationVersion(self, version, minVersion):
                pos = version.find('_')
                if pos>0:
                        version=float(version[pos+1:])
                else:
                        version=float(version)
                if self.debug!=0:
                    print " check version: %s %s" %  (version, minVersion)
                if version < minVersion:
                        raise Exception("Configuration version is too old; config:%s < minimum required:%s" % (version, minVersion))
                #raise Exception("abstractmethod")


        #
        #
        #
        def getCommandLineInfo(self):
            cmd='current dir: %s\ncommand line:' % os.getcwd()
            for item in sys.argv:
                    cmd="%s %s" % (cmd, item)
            return cmd


        #
        #
        #
        def getUsedConfigInfo(self):
            info = "used configuration:%s" % (self.usedConfigFile)
            info = "%s\n used products file list:%s" % (info, self.productsListFile)
            return info


        #
        # label is written at report start: like "Image2006 IrsP6 conversion report"
        # and is the report name
        #
        def makeConversionReport(self, label, path):
            out=StringIO()
            print >> out, self.getCommandLineInfo()
            print >>out, "### Start of report\n"
            aReportMaker = reportMaker.ReportMaker()
            report = aReportMaker.makeReport(self)
            print >>out, label
            print >>out, report
            print >>out, "### End of report"
            reportPath = "%s/%s.txt" % (path, label)
            fd=open(reportPath, 'w')
            fd.write(out.getvalue())
            fd.flush()
            fd.close()
            print "conversion report written well:%s" % reportPath  
            

        #
        #
        #
        @abstractmethod
        def buildEoNames(self, processInfo, namingConvention=None):
            raise Exception("abstractmethod")

        #
        #
        #
        def buildEoNamesDefault(self, processInfo, namingConvention=None):
            if not processInfo.ingester.want_duplicate:
                #print " buildEoNames"
                processInfo.addLog(" buildEoNames")
                # processInfo.destProduct.setDebug(1)
                processInfo.destProduct.buildEoNames(namingConvention)
                if not self.product_overwrite:
                    exists, dummy, finalPath = self.checkDestinationAlreadyExists(processInfo)
                    if exists:
                        raise Exception("will create a unwanted duplicate:%s" % finalPath)

            else:
                if 1==2:
                    #
                    processInfo.destProduct.buildEoNames(namingConvention)

                # from pleiades:
                #
                ok=False
                loopNum=0
                while not ok and loopNum<10:
                        #print " buildEoNames loop:%s" % loopNum
                        processInfo.addLog(" buildEoNames loop:%s" % loopNum)
                        #processInfo.destProduct.setDebug(1)
                        if loopNum==0:
                            processInfo.destProduct.buildEoNames(namingConvention, False)
                        else:
                            processInfo.destProduct.buildEoNames(namingConvention, True)
                        processInfo.destProduct.setDebug(0)
                        if not self.product_overwrite:
                                # test for duplicate
                                exists, newFileCounter, finalPath = self.checkDestinationAlreadyExists(processInfo)
                                if exists:
                                        print " @@ buildEoNames exists:%s; newFileCounter:%s; finalPath=%s" % (exists, newFileCounter, finalPath)
                                        processInfo.addLog(" buildEoNames exists:%s; newFileCounter:%s" % (exists, newFileCounter))
                                        if newFileCounter>9:
                                                raise Exception("newFileCounter limit reached: %s" % newFileCounter)

                                        # set new file counter
                                        processInfo.destProduct.metadata.setMetadataPair(metadata.METADATA_FILECOUNTER, "%s" % newFileCounter)
                                        # set new METADATA_SIP_VERSION, because it's what is used in the hight res naming convention
                                        tmp = processInfo.destProduct.metadata.getMetadataValue(metadata.METADATA_SIP_VERSION)
                                        print " @@ buildEoNames exists: current version:%s" % (tmp)
                                        processInfo.addLog(" buildEoNames loop: current version:%s" % (tmp))
                                        tmp = "%s%s" % (tmp[0:3], newFileCounter)
                                        print " @@ buildEoNames exists: new version:%s" % (tmp)
                                        processInfo.addLog(" buildEoNames loop: new version:%s" % (tmp))
                                        processInfo.destProduct.metadata.setMetadataPair(metadata.METADATA_SIP_VERSION, tmp)
                                else:
                                        print " @@ buildEoNames does not exists:%s; newFileCounter:%s; finalPath=%s" % (exists, newFileCounter, finalPath)
                                        ok=True
                        else:
                                ok=True
                        loopNum += 1
                #
                if not ok:
                        raise Exception("error creating product filename: duplicate test reach loop limit at %s" % loopNum)


        #
        # agregate on geojson record for every EoSip done
        #
        def agregateGeoInfo(self, processInfo):
            try:
                self.footprintAgregator.addProduct(processInfo)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                errorMessage = "%s %s" % (exc_type, exc_obj)
                print("Error agregating geoInfo: %s" % errorMessage)
                traceback.print_exc(file=sys.stdout)
                #os._exit(1)

        #
        # write down aggregated geoJson as file
        #
        def makeJsonShape(self):
            data = self.footprintAgregator.makeJsonShape()
            jsonPath = "%s/%s_convertedItems.json" % (self.LOG_FOLDER, self.batchName)
            fd = open(jsonPath, 'w')
            fd.write(data)
            fd.flush()
            fd.close()
            print(" ##### convertedItems json done at path:%s" % jsonPath)

        #
        #
        #
        def setWantedMetadataInGeoInfo(self, l):
            self.footprintAgregator.setWantedMetadata(l)
            print(" ## set wanted metadata:%s" % l)


        #
        # should be abstract
        #
        @abstractmethod
        def afterProductDone(self, processInfo):
            raise Exception("abstractmethod")

        #
        # should be abstract
        #
        @abstractmethod
        def beforeReportsDone(self, processInfo):
            raise Exception("abstractmethod")


        #
        # should be abstract
        #
        @abstractmethod
        def afterReportsDone(self, processInfo):
            raise Exception("abstractmethod")
                
        #
        # should be abstract
        #
        @abstractmethod
        def createSourceProduct(self, processInfo):
            raise Exception("abstractmethod")

        #
        # should be abstract
        #
        @abstractmethod
        def createDestinationProduct(self, processInfo):
            raise Exception("abstractmethod")

        #
        # should be abstract
        #
        @abstractmethod
        def verifySourceProduct(self, processInfo):
            raise Exception("abstractmethod")

        #
        # should be abstract
        #
        @abstractmethod
        def prepareProducts(self,processInfo):
            raise Exception("abstractmethod")

        #
        # should be abstract
        #
        @abstractmethod
        def extractMetadata(self,met,processInfo):
            raise Exception("abstractmethod")
                
        #
        # should be abstract
        #
        @abstractmethod
        def makeBrowses(self,processInfo):
            raise Exception("abstractmethod")

                
        #
        # should be abstract
        #
        @abstractmethod
        def output_eoSip(self, processInfo, basePath, pathRules, overwrite):
            raise Exception("abstractmethod")

