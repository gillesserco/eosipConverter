#
# This is a specialized class that ingest TropForest dataset
#
# For Esa/ lite dissemination project
#
# Serco 04/2014
# Lavaux Gilles & Simone Garofalo
#
# 07/04/2014: V: 0.1
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
from eoSip_converter.esaProducts import product_dimap_tropforest, product_EOSIP
from esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts.namingConvention import NamingConvention
from eoSip_converter.esaProducts import definitions_EoSip
from eoSip_converter.esaProducts.definitions_EoSip import rep_rectifiedBrowse
import imageUtil


# minumunm config version that can be use
MIN_CONFIG_VERSION=1.0
VERSION="TropForest converter V:1.0.0"
REF_NAME='AL1_OTPF_AL1_AV2_2F_20091014T060519_20091014T060519_000000_E070_N024.SIP.ZIP'


class ingester_tropforest(ingester.Ingester):

        #
        #
        #
        def getVersionImpl(self):
            return VERSION

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
        # this is the first function called by the base ingester
        #
        def createSourceProduct(self, processInfo):
            global debug,logger
            # set ingester in processInfo for later use
            #processInfo.ingester=self
            dimapP = product_dimap_tropforest.Product_Dimap_Tropforest(processInfo.srcPath)
            processInfo.srcProduct = dimapP


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
                processInfo.srcProduct.extractToPath(processInfo.workFolder, processInfo.test_dont_extract)
                processInfo.addLog("  extracted inside:%s" % (processInfo.workFolder))
                self.logger.info("  extracted inside:%s" % (processInfo.workFolder))

        #
        # Override
        #
        def extractMetadata(self,met,processInfo):
            # fill metadata object
            numAdded=processInfo.srcProduct.extractMetadata(met)
            size=processInfo.srcProduct.getSize()
            grid_lat=processInfo.srcProduct.extractGridFromFile("lat")
            grid_lon=processInfo.srcProduct.extractGridFromFile("lon")
            grid_lat_norm=processInfo.srcProduct.extractGridFromFileNormalised("lat")
            grid_lon_norm=processInfo.srcProduct.extractGridFromFileNormalised("lon")
            met.setMetadataPair(metadata.METADATA_PRODUCT_SIZE, size)
            met.setMetadataPair('METADATA_WRS_LONGITUDE_GRID', grid_lon)
            met.setMetadataPair('METADATA_WRS_LATITUDE_GRID', grid_lat)
            met.setMetadataPair(metadata.METADATA_WRS_LONGITUDE_GRID_NORMALISED, grid_lon_norm)
            met.setMetadataPair(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, grid_lat_norm)
            met.addLocalAttribute('gridLongitude', grid_lon_norm)
            met.addLocalAttribute('gridLatitude', grid_lat_norm)
            # needed for the filename
            met.setMetadataPair(metadata.METADATA_FRAME, grid_lat_norm)
            met.setMetadataPair(metadata.METADATA_TRACK, grid_lon_norm)
            #met.setMetadataPair(metadata.METADATA_GENERATION_TIME, time.strftime('%Y-%m-%dT%H:%M:%SZ'))
            # use method in base converter
            self.getGenerationTime(met)
            self.logger.debug("number of metadata added:%d" % numAdded)

            # build typecode, set stop datetime = start datetime
            met.setMetadataPair(metadata.METADATA_STOP_DATE, met.getMetadataValue(metadata.METADATA_START_DATE))
            met.setMetadataPair(metadata.METADATA_STOP_TIME, met.getMetadataValue(metadata.METADATA_START_TIME))

            # get additionnal metadata from optionnal dataProvider:we want the orbit
            # the dataprovider key is the mission name (KOMPSAT, AVNIR, DEIMOS)
            if len(self.dataProviders)>0:
                    if self.debug!=0:
                            print " extract using dataProviders:%s" % self.dataProviders
                    # look the one for the mission
                    for item in self.dataProviders.keys():
                            if item.find(met.getMetadataValue(metadata.METADATA_PLATFORM))>=0:
                                    adataProvider=self.dataProviders[item]
                                    if self.debug!=0:
                                            print " dataProviders match PLATFORM '%s':%s" % (met.getMetadataValue(metadata.METADATA_PLATFORM), adataProvider)
                                    # need to query using the product original filename like:N00-W075_AVN_20090804_PRO_0
                                    orbit=adataProvider.getRowValue(met.getMetadataValue(metadata.METADATA_DATASET_NAME))
                                    if self.debug!=0:
                                            print " orbit:%s" % orbit
                                    if orbit != None and len(orbit.strip())==0:
                                            orbit=None
                                    met.setMetadataPair(metadata.METADATA_ORBIT, orbit)
                                    break
                                    
                    

            # refine
            processInfo.srcProduct.refineMetadata()

                
        #
        #
        #
        def makeBrowseChoiceBlock(self, processInfo, metadata):

            # create browse choice for browse metadata report
            reportBuilder=rep_rectifiedBrowse.rep_rectifiedBrowse()
            if self.debug!=0:
                    print "###\n###\n### BUILD BROWSE CHOICE FROM METADATA:%s" % (processInfo.destProduct.metadata.toString())
            browseChoiceBlock=reportBuilder.buildMessage(processInfo.destProduct.metadata, "rep:rectifiedBrowse").strip()
            if self.debug!=0:
                    print "browseChoiceBlock:%s" % (browseChoiceBlock)
            metadata.setMetadataPair(browse_metadata.BROWSE_METADATA_BROWSE_CHOICE, browseChoiceBlock)
            #print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
            #sys.exit()
           

        #
        # Override
        # make the Jpeg (or Png) browse image from the TIFF image. We want Jpeg
        # construct the browse_metadatareport footprint block: it is the rectifedBrowse for tropforest
        #
        def makeBrowses(self, processInfo, ratio=50):
            try:
                    browseSrcPath="%s/%s" % (processInfo.workFolder , processInfo.srcProduct.TIF_FILE_NAME)
                    #browseExtension=definitions_EoSip.getBrowseExtension(0, definitions_EoSip.getDefinition('BROWSE_PNG_EXT'))
                    browseExtension=definitions_EoSip.getBrowseExtension(0, definitions_EoSip.getDefinition('BROWSE_JPEG_EXT'))
                    browseDestPath="%s/%s.%s" % (processInfo.eosipTmpFolder, processInfo.destProduct.packageName, browseExtension)
                    processInfo.addLog("  makeBrowse: ext=%s; src=%s;  dest=%s" % (browseExtension, browseSrcPath, browseDestPath))
                    if processInfo.test_dont_do_browse!=True:
                            ok=imageUtil.makeBrowse('JPG', browseSrcPath, browseDestPath, ratio )

                    #if processInfo.test_dont_do_browse!=True:
                    #	    ok=imageUtil.externalMakeBrowse('JPG', browseSrcPath, browseDestPath, ratio)

                    # add browse to dest product, this create the browse metadata    
                    processInfo.destProduct.addSourceBrowse(browseDestPath, [])

                    # create browse choice for browse metadata report
                    bmet=processInfo.destProduct.browse_metadata_dict[browseDestPath]


                    self.makeBrowseChoiceBlock(processInfo, bmet)
                    #footprintBuilder=rep_footprint.rep_footprint()
                    #
                    #print "###\n###\n### BUILD BROWSE CHOICE FROM METADATA:%s" % (processInfo.destProduct.metadata.toString())
                    #browseChoiceBlock=footprintBuilder.buildMessage(processInfo.destProduct.metadata, "rep:browseReport/rep:browse/rep:footprint").strip()
                    #if self.DEBUG!=-1:
                    #        print "browseChoiceBlock:%s" % (browseChoiceBlock)
                    #bmet.setMetadataPair(browse_metadata.BROWSE_METADATA_BROWSE_CHOICE, browseChoiceBlock)


                    # set the browse type (if not default one(i.e. product type code))for the product metadata report BROWSES block
                    # if specified in configuration
                    tmp = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_BROWSES_TYPE)
                    if tmp != None:
                            bmet.setMetadataPair(metadata.METADATA_BROWSES_TYPE, tmp)

                    # idem for METADATA_CODESPACE_REFERENCE_SYSTEM
                    tmp = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_CODESPACE_REFERENCE_SYSTEM)
                    if tmp != None:
                            bmet.setMetadataPair(metadata.METADATA_CODESPACE_REFERENCE_SYSTEM, tmp)
        
                    processInfo.addLog("  browse image created:%s" %  (browseDestPath))
                    self.logger.info("  browse image created:%s" % browseDestPath)
            except Exception, e:
                    try:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            errorMsg="Error generating browse: error type:%s  exec_obj:%s" %  (exc_type, exc_obj)
                            self.logger.error(errorMsg)
                            processInfo.addLog("%s" %  (errorMsg))
                            processInfo.addLog("%s" %  (traceback.format_exc()))
                            print "ERROR: make browse error: %s\n%s" % (errorMsg, traceback.format_exc())
                    except Exception, ee:
                            self.logger.error("  problem adding browse generation error in processInfo")
                            pass
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
                        processInfo.addLog("  Eo-Sip product will be writen in folder:%s" %  (firstPath))
                        self.logger.info("  Eo-Sip product will be writen in folder:%s" %  (firstPath))
                        productPath = processInfo.destProduct.writeToFolder(firstPath, overwrite)
                        processInfo.addLog("  ok, writen well\n%s" % processInfo.destProduct.info())
                        self.logger.info(" ok, writen well\n%s" % processInfo.destProduct.info())
                        processInfo.addIngesterLog("  write done:%s" % processInfo.destProduct.path, 'PROGRESS')

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
                                
                self.logger.info("  done")
                return productPath
        

        #
        #
        #
        #def toString(self):
        #        out=StringIO()
        #        print >>out, 'tropforest ingester\n'
        #        print >>out, 'dataProviders:%s\n' % (self.dataProviders)
        #        print >>out, 'servicesProvider:%s\n' % (self.servicesProvider)
        #        return out.getvalue()

if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            ingester = ingester_tropforest()
            #ingester.DEBUG=1
            ingester.starts(sys.argv)

            out=StringIO()
            print >>out, "### Start of report\n"
            aReportMaker = reportMaker.ReportMaker()
            report = aReportMaker.makeReport(ingester)
            print >>out, "TROPFOREST conversion report"
            print >>out, report
            print >>out, "### End of report"
            print out.getvalue()
            
        else:
            print "syntax: python ingester_xxx.py -c configuration_file.cfg [-l list_of_product_file]"
            sys.exit(1)
            
    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
