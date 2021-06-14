#
# This will read MIP_NL__2P products and build a xml file corresponding to the DCCM-ICD v 2.6
#
# 
#
# Serco 10/2015
# Lavaux Gilles 
#
#
#
#
import os, sys, inspect
import time
import zipfile
import traceback
from cStringIO import StringIO


# add converter package path to sys.path 
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parrent=os.path.dirname(currentdir)
print "##### eoSip converter package dir:%s" % parrent
sys.path.insert(0, parrent)

#
from eoSip_converter.base import ingester, reportMaker
from eoSip_converter.esaProducts import dccm_product, product_mph_sph_mipas_l2, product_mph_sph
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip,formatUtils
from eoSip_converter.esaProducts.definitions_EoSip import rep_rectifiedBrowse
from eoSip_converter.esaProducts.namingConvention_dccm import NamingConvention_Dccm
import eoSip_converter.imageUtil as imageUtil
import eoSip_converter.fileHelper as fileHelper


# minimum config version that can be use
MIN_CONFIG_VERSION=1.0


class ingester_DSI_to_DCCM(ingester.Ingester):

        #
        # 
        #
        def afterStarting(self, **kargs):
            #print(" HOHOHOHO                !!!!!")
            #os._exit(1)
            #self.setWantedMetadataInGeoInfo([metadata.METADATA_STOP_DATE, metadata.METADATA_STOP_TIME, metadata.METADATA_SUN_AZIMUTH, metadata.METADATA_SUN_ELEVATION, metadata.METADATA_PROCESSING_LEVEL, metadata.METADATA_PROCESSING_CENTER, metadata.METADATA_ORIGINAL_NAME])

        #
        # config version is like: name_floatVersion
        #
        def checkConfigurationVersion(self):
                global MIN_CONFIG_VERSION
                self._checkConfigurationVersion(self.CONFIG_VERSION, MIN_CONFIG_VERSION)
                

        #
        # prepare metadata from a browse report generation
        #
        def prepareBrowseMetadata(self, processInfo):
                pass


        #
        # called before doing the various reports
        #
        def beforeReportsDone(self, processInfo):
                # make sure we have ICD values in restricted fields
                # instrument
                processInfo.destProduct.metadata.setMetadataPair(metadata.METADATA_INSTRUMENT, processInfo.destProduct.setInstrument(processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_INSTRUMENT)))

                # METADATA_PROCESSING_CENTER
                processInfo.destProduct.metadata.setMetadataPair(metadata.METADATA_PROCESSING_CENTER, processInfo.destProduct.setProductionCentre(processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_PROCESSING_CENTER)))

                # METADATA_PROCESSING_CENTER
                processInfo.destProduct.metadata.setMetadataPair(metadata.METADATA_ACQUISITION_CENTER, processInfo.destProduct.setProductionCentre(processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_ACQUISITION_CENTER)))

                # getinfo on aux used
                for item in processInfo.srcProduct.productAux:
                        processInfo.destProduct.addProductAux(item)

                # getinfo on parent used
                #processInfo.destProduct.addProductParent(processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_PRODUCTNAME))
                processInfo.destProduct.addProductParent(processInfo.srcProduct.origName)

                # add media and datasets
                tmp = processInfo.srcProduct.metadata.getMetadataValue('__NUMBER_MEDIA')
                numMedia=0
                if tmp != None:
                        numMedia=int(tmp)
                processInfo.addLog(" numMedia:%s" % numMedia)
                for i in range(numMedia):
                        processInfo.destProduct.addMedia(processInfo.srcProduct.metadata.getMetadataValue('MEDIA_%s' % (i+1)))
                        

                tmp = processInfo.srcProduct.metadata.getMetadataValue('__NUMBER_DATASET')
                numDataset=0
                if tmp != None:
                        numDataset=int(tmp)
                processInfo.addLog(" numDataset:%s" % numDataset)
                for i in range(numDataset):
                       processInfo.destProduct. addDataset(processInfo.srcProduct.metadata.getMetadataValue('DATASET_%s' % (i+1)))

        #
        # called after having done the various reports
        #
        def afterReportsDone(self, processInfo):
                pass
        

        #
        # called at the end of the doOneProduct, before the index/shopcart creation
        #
        def afterProductDone(self, processInfo):
                pass
        
        #
        #
        #
        def buildEoNames(self, processInfo, namingConvention=None):
                processInfo.destProduct.buildEoNames(namingConvention)
    
        #
        # Override
        # this is the first function called by the base ingester
        #
        # as input we have the manifest path. Need to use his parent for the product path
        #
        def createSourceProduct(self, processInfo):
            global debug,logger
            processInfo.srcPath=processInfo.srcPath.replace('\\','/')
            product = product_mph_sph_mipas_l2.Product_Mph_Sph_Mipas_L2(processInfo.srcPath)
            #product.setDebug(1)
            processInfo.srcProduct = product


        #
        # Override
        #
        def createDestinationProduct(self, processInfo):
            global debug,logger
            destP=pProduct_dccm.Product_Dccm()
            #destP.DEBUG=1
            destP.sourceProductPath = processInfo.srcPath
            processInfo.destProduct = destP

            # set naming convention instance
            namingConventionSip = NamingConvention_Dccm(self.OUTPUT_SIP_PATTERN)
            processInfo.destProduct.setNamingConventionSipInstance(namingConventionSip)

            processInfo.destProduct.setNamingConventionEoInstance(namingConventionSip)
            
            self.logger.info(" Dccm_Product created")
            processInfo.addLog(" Dccm_Product created")

                    
        #
        # Override
        #
        def verifySourceProduct(self, processInfo):
                processInfo.addLog(" verifying product:%s" % (processInfo.srcPath))
                self.logger.info(" verifying product");
                

            
        #
        # Override
        #
        def prepareProducts(self,processInfo):
                processInfo.addLog(" prepare product in:%s" % (processInfo.workFolder))
                self.logger.info(" prepare product");
                processInfo.srcProduct.extractToPath(processInfo.workFolder, processInfo.test_dont_extract)
                
                processInfo.addLog("  extracted inside:%s" % (processInfo.workFolder))
                self.logger.info("  extracted inside:%s" % (processInfo.workFolder))

        #
        # Override
        #
        def extractMetadata(self,met,processInfo):
            # fill metadata object
            if self.debug!=0:
                    print " will extract source metadata" 
            numAdded=processInfo.srcProduct.extractMetadata(met)
            if self.debug!=0:
                    print "  metadata extracted: %s" % numAdded
                    
            # met.setMetadataPair(metadata.METADATA_GENERATION_TIME, time.strftime('%Y-%m-%dT%H:%M:%SZ'))
            # use method in base converter
            self.getGenerationTime(met)
            
            # refine
            processInfo.srcProduct.refineMetadata()
            return numAdded

                
        #
        #
        #
        def makeBrowseChoiceBlock(self, processInfo, metadata):
            pass
           

        #
        # Override
        # make the Jpeg (or Png) browse image from the TIFF image. We want Jpeg
        # construct the browse_metadatareport footprint block: it is the rectifedBrowse for tropforest
        #
        def makeBrowses(self, processInfo, ratio=50):
            pass


        #
        # Override
        #
        # output the Eo-Sip profuct in the destination folder
        # take the first rule and put the product in the resulting folder
        # create link for the other rules if any
        #
        def output_eoSip(self, processInfo, basePath, pathRules, overwrite=None):
                self.logger.info("  output_eoSip: basePath=%s" %  (basePath))
                #return
                # copy eoSip in first path; make links in other paths: 
                #
                if len(self.outputProductResolvedPaths)==0:
                        raise Exception("no product resolved path")
                else:
                        # output in first path
                        firstPath=self.outputProductResolvedPaths[0]
                        processInfo.addLog("  Eo-Sip product writen in folder:%s\n" %  (firstPath))
                        self.logger.info("  Eo-Sip product writen in folder:%s\n" %  (firstPath))
                        processInfo.destProduct.writeToFolder(firstPath, overwrite)

                        # output link in other path
                        i=0
                        for item in self.outputProductResolvedPaths:
                                if i>0:
                                        otherPath="%s" % (item)
                                        self.logger.info("  eoSip product tree path[%d] is:%s" %(i, item))
                                        processInfo.destProduct.writeToFolder(basePath, overwrite)
                                        processInfo.addLog("  Eo-Sip product link writen in folder[%d]:%s\n" %  (i, otherPath))
                                        self.logger.info("  Eo-Sip product link writen in folder[%d]:%s\n" %  (i, otherPath))
                                i=i+1




if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            ingester = ingester_DSI_to_DCCM()
            #ingester.DEBUG=1
            ingester.starts(sys.argv)
            
        else:
            print "syntax: python ingester_xxx.py -c configuration_file.cfg [-l list_of_product_file]"
            sys.exit(1)
            
    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
