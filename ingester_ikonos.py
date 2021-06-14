#
# This is a specialized class that ingest Ikonos dataset
#
# For Esa/ lite dissemination project
#
# Serco 04/2014 Lavaux Gilles
#
# 07/04/2014: V: 0.1
#
#
#
import os, sys, inspect
import time
import zipfile
import traceback
import shutil

# add converter package path to sys.path 
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parrent=os.path.dirname(currentdir)
print "##### eoSip converter package dir:%s" % parrent
sys.path.insert(0, parrent)

#
from eoSip_converter.base import ingester, reportMaker
from eoSip_converter.esaProducts import product_ikonos, product_EOSIP
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip, formatUtils
from xml_nodes import rep_footprint
from eoSip_converter.esaProducts.namingConvention_hightres import NamingConvention_HightRes
import eoSip_converter.imageUtil as imageUtil


# minimum config version that can be use
MIN_CONFIG_VERSION=1.0
VERSION="Ikonos converter V:1.0.0"
REF_NAME='IK2_OPER_OSA_GEO_1P_20001225T085500_N39-944_E027-035_0002.SIP.ZIP'

class ingester_ikonos(ingester.Ingester):

        #
        #
        #
        def getVersionImpl(self):
            return VERSION

        #
        #
        #
        def afterStarting(self, **kargs):
                #super(ingester_ikonos, self).starts(args)
                #self.wfsCountryResolver = WfsServiceClient.WfsServiceClient(self.processInfo)
                print "## afterStarting ##"
                
        #
        # config version is like: name_floatVersion
        #
        def checkConfigurationVersion(self):
                global MIN_CONFIG_VERSION
                self._checkConfigurationVersion(self.CONFIG_VERSION, MIN_CONFIG_VERSION)
                
        #
        # called before doing the various reports
        #
        def beforeReportsDone(self, processInfo):
                # alter mapping
                processInfo.destProduct.metadata.alterMetadataMaping('href', metadata.METADATA_FULL_PACKAGENAME)
                processInfo.destProduct.metadata.setValidValue('UNIT_ANGLE', 'deg')

        #
        # called after having done the various reports
        #
        def afterReportsDone(self, processInfo):
                pass

        #
        # called at the end of the doOneProduct, before the index/shopcart creation
        #
        def afterProductDone(self, processInfo):
                self.makeKmz(processInfo)

        #
        #
        #
        def buildEoNames(self, processInfo, namingConvention=None):
            # test default in ingester
            self.buildEoNamesDefault(processInfo, namingConvention)

            # test EoSip package name
            aName = processInfo.destProduct.getSipPackageName()
            if len(aName) != len(REF_NAME):
                print "ref name:%s" % REF_NAME
                print "EoSip name:%s" % aName
                raise Exception("EoSip name has incorrect length:%s VS %s" % (len(aName), len(REF_NAME)))
            if aName.find('@') >= 0 or aName.find('#') > 0:
                raise Exception("SipProductName incomplet:%s" % aName)

        
        #
        # Override
        #
        def createSourceProduct(self, processInfo):
            global debug,logger
            #processInfo.ingester=self
            processInfo.srcProduct = product_ikonos.Product_Ikonos(processInfo.srcPath)

        #
        # Override
        #
        def createDestinationProduct(self, processInfo):
            global debug,logger
            eosipP=product_EOSIP.Product_EOSIP()
            #eosipP.setUsePythonZipLib(False)
            eosipP.sourceProductPath = processInfo.srcPath
            processInfo.destProduct = eosipP

            # set naming convention instance
            namingConventionSip = NamingConvention_HightRes(self.OUTPUT_SIP_PATTERN)
            processInfo.destProduct.setNamingConventionSipInstance(namingConventionSip)
            processInfo.destProduct.setNamingConventionEoInstance(namingConventionSip)
            
            self.logger.info(" Eo-Sip product created")
            processInfo.addLog(" Eo-Sip product created")
                    
        #
        # Override
        #
        def verifySourceProduct(self, processInfo):
                return
                processInfo.addLog(" verifying product:%s" % (processInfo.srcPath))
                self.logger.info(" verifying product");
                fh = open(processInfo.srcPath, 'rb')
                zf = zipfile.ZipFile(fh)
                ok = zf.testzip()
                fh.close()
                if ok is not None:
                        self.logger.error("  Zip file is corrupt:%s" % processInfo.srcPath)
                        self.logger.error("  First bad file in zip: %s" % ok)
                        processInfo.addLog("  Zip file is corrupt:%s" % processInfo.srcPath)
                        raise Exception("Zip file is corrupt:%s" % processInfo.srcPath)
                else:
                    self.logger.info("  Zip file is ok")
                    processInfo.addLog("  Zip file is ok")

            
        #
        # Override
        #
        def prepareProducts(self,processInfo):
                processInfo.addLog(" prepare product in:%s" % (processInfo.workFolder))
                self.logger.info(" prepare product");
                processInfo.srcProduct.extractToPath(processInfo.workFolder)
                processInfo.addLog("  extracted inside:%s" % (processInfo.workFolder))
                self.logger.info("  extracted inside:%s" % (processInfo.workFolder))


        #
        # Override
        #
        def extractMetadata(self,met,processInfo):
            # fill metadata object
            numAdded=processInfo.srcProduct.extractMetadata(met)
            size=processInfo.srcProduct.getSize()
            met.setMetadataPair(metadata.METADATA_PRODUCT_SIZE, size)
            #met.setMetadataPair(metadata.METADATA_GENERATION_TIME, time.strftime('%Y-%m-%dT%H:%M:%SZ'))
            self.getGenerationTime(met)
            self.logger.debug("number of metadata added:%d" % numAdded)

            # build typecode, set stop datetime = start datetime
            met.setMetadataPair(metadata.METADATA_STOP_DATE, met.getMetadataValue(metadata.METADATA_START_DATE))
            met.setMetadataPair(metadata.METADATA_STOP_TIME, met.getMetadataValue(metadata.METADATA_START_TIME))
            # refine
            processInfo.srcProduct.refineMetadata()

                

        #
        # Override
        #
        def makeBrowses(self,processInfo):
            try:
                    #browseSrcPath="%s/%s" % (processInfo.workFolder , processInfo.srcProduct.PREVIEW_NAME)
                    browseSrcPath=processInfo.srcProduct.preview_path
                    browseExtension=definitions_EoSip.getBrowseExtension(0, definitions_EoSip.getDefinition('BROWSE_PNG_EXT'))
                    browseDestPath="%s/%s.%s" % (processInfo.destProduct.folder, processInfo.destProduct.eoProductName, browseExtension)

                    if self.debug:
                            print "@@@@@@@@@@@@@@@@@@@@@@@@@  browseSrcPath=%s;browseDestPath=%s" % (browseSrcPath, browseDestPath)
                    
                    #shutil.copyfile(browseSrcPath, browseDestPath)
                    #processInfo.destProduct.addSourceBrowse(browseDestPath, [])
                    #processInfo.addLog("  browse image created:%s" %  (browseDestPath))
                    #self.logger.info("  browse image created:%s" % browseDestPath)

                    # NEW: make a transparent jpeg, resize to 33% -> 1000*1000
                    if processInfo.test_dont_do_browse!=True:
                            ok=imageUtil.makeBrowse("PNG", browseSrcPath, browseDestPath, -1, transparent=False)
                    processInfo.destProduct.addSourceBrowse(browseDestPath, [])
                    processInfo.addLog("  => browse image created:%s" %  (browseDestPath))
                    self.logger.info("  browse image created:%s" % browseDestPath)

                    # create browse choice for browse metadata report
                    bmet=processInfo.destProduct.browse_metadata_dict[browseDestPath]
                    print "######\n######\n%s" % dir(definitions_EoSip)

                    
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
                # copy eoSip in first path
                # make links in other paths
                outputProductResolvedPaths = processInfo.destProduct.getOutputFolders(basePath, pathRules)
                if len(outputProductResolvedPaths)==0:
                        raise Exception("no product resolved path")
                else:
                        # output in first path
                        firstPath=outputProductResolvedPaths[0]
                        processInfo.addLog("  Eo-Sip product writen in folder:%s\n" %  (firstPath))
                        self.logger.info("  Eo-Sip product writen in folder:%s\n" %  (firstPath))
                        productPath = processInfo.destProduct.writeToFolder(firstPath, overwrite)
                        processInfo.addIngesterLog("  write done:%s" % processInfo.destProduct.path)
                        
                        # output link in other path
                        i=0
                        for item in outputProductResolvedPaths:
                                if i>0:
                                        otherPath="%s" % (item)
                                        self.logger.info("  eoSip product tree path[%d] is:%s" %(i, item))
                                        processInfo.destProduct.writeToFolder(basePath, overwrite)
                                        processInfo.addLog("  Eo-Sip product link writen in folder[%d]:%s\n" %  (i, otherPath))
                                        self.logger.info("  Eo-Sip product link writen in folder[%d]:%s\n" %  (i, otherPath))
                                i=i+1
                self.logger.info("  done")
                return productPath


        #
        # create a kmz, use the bounding box
        # created in the log folder
        #
        def makeKmz(self, processInfo):
                #try:
                processInfo.ingester.logger.info("WILL CREATE KMZ")
                import kmz
                outPath = "%s/kmz" % processInfo.ingester.LOG_FOLDER
                if not os.path.exists(outPath):
                        self.logger.info("  will make kmz folder:%s" % outPath)
                        os.makedirs(outPath)
                kmzPath = kmz.eosipToKmz.makeKmlFromEoSip_new(False, outPath, processInfo)
                print " KMZ created at path:%s" % kmzPath
                if kmzPath != None:
                        processInfo.addLog("KMZ created at path:%s" % kmzPath)
                else:
                        processInfo.addLog("KMZ was NOT CREATED!")
                        raise Exception("KMZ was NOT CREATED!")
                #except:
                #    exc_type, exc_obj, exc_tb = sys.exc_info()
                #    errorMsg="Error generating KMZ:%s  %s\n%s" %  (exc_type, exc_obj, traceback.format_exc())
                #    self.logger.error(errorMsg)
                #    processInfo.addLog("%s" %  (errorMsg))
                #    processInfo.addLog("%s" %  (traceback.format_exc()))



if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            ingester = ingester_ikonos()
            ingester.debug=0
            ingester.starts(sys.argv)
            
        else:
            print "syntax: python ingester_xxx.py configuration_file.cfg"
            sys.exit(1)
            
    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
