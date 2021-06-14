#
# This is a specialized class that ingest ASAR-GM dataset
#
# For Esa/ lite dissemination project
#
# Serco 02/2015 Lavaux Gilles
#
# 07/04/2014: V: 0.1
#
#
#
import os, sys
import time
import zipfile
import traceback
from cStringIO import StringIO


from eoSip_converter.base import ingester
from eoSip_converter.esaProducts import product_mph_sph, product_EOSIP, product
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip
from eoSip_converter.esaProducts.definitions_EoSip import rep_footprint
from eoSip_converter.esaProducts.namingConvention import NamingConvention
from eoSip_converter.esaProducts.definitions_EoSip import sipBuilder
import imageUtil
import fileHelper
import shutil



# minimum config version that can be use
MIN_CONFIG_VERSION=1.0

class ingester_asar_gm(ingester.Ingester):

        #
        # config version is like: name_floatVersion
        #
        def checkConfigurationVersion(self):
                global MIN_CONFIG_VERSION
                self._checkConfigurationVersion(self.CONFIG_VERSION, MIN_CONFIG_VERSION)
                
        #
        # 
        #
        def afterStarting(self, **kargs):
                pass
        
        #
        # prepare metadata from a browse report generation
        #
        def prepareBrowseMetadata(self, processInfo):
                pass


        #
        # called before doing the various reports
        #
        def beforeReportsDone(self, processInfo):
                pass


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
        # Override
        # this is the first function called by the base ingester
        #
        #
        def createSourceProduct(self, processInfo):
            global debug,logger
            mp = product_mph_sph.Product_Mph_Sph(processInfo.srcPath)
            mp.setDebug(1)
            processInfo.srcProduct = mp


        #
        # Override
        #
        def createDestinationProduct(self, processInfo):
            global debug,logger
            eosipP=product_EOSIP.Product_EOSIP()
            eosipP.sourceProductPath = processInfo.srcPath
            processInfo.destProduct = eosipP

            # set naming convention instance
            namingConventionSip = NamingConvention(self.OUTPUT_SIP_PATTERN)
            processInfo.destProduct.setNamingConventionSipInstance(namingConventionSip)

            processInfo.destProduct.setNamingConventionEoInstance(namingConventionSip)
            
            self.logger.info(" Eo-Sip product created")
            processInfo.addLog(" Eo-Sip product created")

                    
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
                pass
                processInfo.addLog(" prepare product in:%s" % (processInfo.workFolder))
                self.logger.info(" prepare product");
                
                processInfo.addLog("  extracted inside:%s" % (processInfo.workFolder))
                self.logger.info("  extracted inside:%s" % (processInfo.workFolder))

        #
        # Override
        #
        def extractMetadata(self,met,processInfo):
            # fill metadata object
            # do also refine + getTypecode

            #met.setMetadataPair(metadata.METADATA_GENERATION_TIME, time.strftime('%Y-%m-%dT%H:%M:%SZ'))
            # use method in base converter
            self.getGenerationTime(met)
            
            numAdded=processInfo.srcProduct.extractMetadata(met)


                
        #
        #
        #
        def makeBrowseChoiceBlock(self, processInfo, metadata):
            pass
           

        #
        # Override
        # 
        #
        def makeBrowses(self, processInfo, ratio=50):
            try:
                    # we take the browse from a folder structure that has the same structure as the products one
                    # top of folders is given by 'browse' ressource setting
                    browseTopPath = self.ressourcesProvider.getRessourcePath('browse')
                    processInfo.addLog("  ### browseTopPath:%s" %  (browseTopPath))

                    inbox=self.INBOX.replace('\\','/')
                    processInfo.addLog("  ### inbox:%s" %  (inbox))

                    srcPath=processInfo.srcProduct.path.replace('\\','/')
                    processInfo.addLog("  ### srcPath:%s" %  (srcPath))

                    relpath=srcPath[len(inbox):]
                    processInfo.addLog("  ### relpath:%s" %  (relpath))
                                                                
                    browseFullPath="%s/%s.JPG" % (browseTopPath, relpath)
                    if os.path.exists(browseFullPath):
                            browseSrcPath = browseFullPath
                            processInfo.addLog("  ### browseSrcPath: EXIST")
                    else:
                            browseSrcPath = self.ressourcesProvider.getRessourcePath('logo')
                            processInfo.addLog("  ### browseSrcPath: DOES NOT EXIST")

                    processInfo.addLog("  ### browseSrcPath: %s" % browseSrcPath)
                    #browseSrcPath = self.ressourcesProvider.getRessourcePath('logo')
                    browseExtension=definitions_EoSip.getBrowseExtension(0, definitions_EoSip.getDefinition('BROWSE_JPEG_EXT'))
                    browseDestPath="%s/%s.%s" % (processInfo.eosipTmpFolder, processInfo.destProduct.eoProductName, browseExtension)
                    shutil.copyfile(browseSrcPath, browseDestPath)
                    processInfo.destProduct.addSourceBrowse(browseDestPath, [])
                    processInfo.addLog("  browse image created:%s" %  (browseDestPath))
                    self.logger.info("  browse image created:%s" % browseDestPath)


                    # create browse choice for browse metadata report
                    bmet=processInfo.destProduct.browse_metadata_dict[browseDestPath]
                    reportBuilder=rep_footprint.rep_footprint()
                    #
                    print "###\n###\n### BUILD BROWSE CHOICE FROM METADATA:%s" % (processInfo.destProduct.metadata.toString())
                    browseChoiceBlock=reportBuilder.buildMessage(processInfo.destProduct.metadata, "rep:browseReport/rep:browse/rep:footprint").strip()
                    if self.debug!=-1:
                            print "browseChoiceBlock:%s" % (browseChoiceBlock)
                    bmet.setMetadataPair(browse_metadata.BROWSE_METADATA_BROWSE_CHOICE, browseChoiceBlock)

                    # set the browse type (if not default one(i.e. product type code))for the product metadata report BROWSES block
                    # if specified in configuration
                    tmp = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_BROWSES_TYPE)
                    if tmp != None:
                            bmet.setMetadataPair(metadata.METADATA_BROWSES_TYPE, tmp)

                    # idem for METADATA_CODESPACE_REFERENCE_SYSTEM
                    tmp = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_CODESPACE_REFERENCE_SYSTEM)
                    if tmp != None:
                            bmet.setMetadataPair(metadata.METADATA_CODESPACE_REFERENCE_SYSTEM, tmp)
                    
            except Exception, e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    errorMsg="Error generating browse:%s  %s\n%s" %  (exc_type, exc_obj, traceback.format_exc())
                    self.logger.error(errorMsg)
                    processInfo.addLog("%s" %  (errorMsg))
                    processInfo.addLog("%s" %  (traceback.format_exc()))
                    raise e

        #
        # Override
        #
        # output the Eo-Sip profuct in the destination folder
        # take the first rule and put the product in the resulting folder
        # create link for the other rules if any
        #
        def output_eoSip(self, processInfo, basePath, pathRules, overwrite=None):
                self.logger.info("  output_eoSip: basePath=%s" %  (basePath))
                # copy eoSip in first path; make links in other paths: 
                
                # now done before in base_ingester.doOneProduct
                #self.outputProductResolvedPaths = processInfo.destProduct.getOutputFolders(basePath, pathRules)

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
            ingester = ingester_asar_gm()
            ingester.debug=1
            ingester.starts(sys.argv)
            
        else:
            print "syntax: python ingester_xxx.py -c configuration_file.cfg [-l list_of_product_file]"
            sys.exit(1)
            
    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
