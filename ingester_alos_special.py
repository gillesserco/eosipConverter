#
# This is a TEMPLATE ingester class. 
#
# For Esa/lite dissemination project
#
# Serco 08/2015
# Lavaux Gilles & Fabrizio Borgia
#
# 06/08/2015: V: 0.1
#
#
#
import os, sys, inspect
import time
import zipfile
import traceback
from cStringIO import StringIO
from subprocess import call,Popen, PIPE


# add converter package path to sys.path 
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parrent=os.path.dirname(currentdir)
print "##### eoSip converter package dir:%s" % parrent
sys.path.insert(0, parrent)
                
from eoSip_converter.base import ingester
from eoSip_converter.esaProducts import product_EOSIP, product_alos_special
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip
from eoSip_converter.esaProducts.definitions_EoSip import rep_footprint
from eoSip_converter.esaProducts.namingConvention import NamingConvention


# minimum config version that can be use
MIN_CONFIG_VERSION=1.0
VERSION="Alos Special Collection converter V:1.0.0"
REF_NAME='TBC'

class ingester_alos_special(ingester.Ingester):

        #
        #
        #
        def getVersionImpl(self):
            return VERSION

        #
        # 
        #
        def afterStarting(self, **kargs):
                pass

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
                print "\n####\n  batch run will be completed at:%s\n####" % self.statsUtil.getEndDate()


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
        # as input we have the manifest path. Need to use his parent for the product path
        #
        def createSourceProduct(self, processInfo):
            global debug,logger
            processInfo.srcPath=processInfo.srcPath.replace('\\','/')
            product = product_alos_special.Product_Alos_Special(processInfo.srcPath)
            product.setDebug(1)
            processInfo.srcProduct = product


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
                processInfo.addLog("[ingester_alos_special.prepareProducts] Prepare product in: %s" % (processInfo.workFolder))
                self.logger.info(" Prepare product");

                self.makeBrowseCommand = parentdir + "/" + self.ressourcesProvider.getRessourcePath('makeBrowseCommand')
                processInfo.srcProduct.makeBrowseCommand = self.makeBrowseCommand

                processInfo.srcProduct.extractToPath(processInfo.workFolder, processInfo.test_dont_extract)
                
                processInfo.addLog("  extracted inside:%s" % (processInfo.workFolder))
                self.logger.info("  extracted inside:%s" % (processInfo.workFolder))

        #
        # Override
        #
        def extractMetadata(self,met,processInfo):
            # fill metadata object
            numAdded=processInfo.srcProduct.extractMetadata(met)

            #met.setMetadataPair(metadata.METADATA_GENERATION_TIME, time.strftime('%Y-%m-%dT%H:%M:%SZ'))
            # use method in base converter
            self.getGenerationTime(met)

            # refine
            processInfo.srcProduct.refineMetadata()

                
        #
        #
        #
        def makeBrowseChoiceBlock(self, processInfo, metadata):
            pass

           

        #
        # Override
        # Extracts the PNG browse image from the native ALOS product.
        #
        def makeBrowses(self, processInfo, ratio=50):

            # Building input/output paths.
            browseSrcPath = "%s/%s" % (processInfo.workFolder, processInfo.srcProduct.tempProductDirectory)
            browseExtension=definitions_EoSip.getBrowseExtension(0, definitions_EoSip.getDefinition('BROWSE_PNG_EXT'))
            browseDestPath="%s/%s.%s" % (processInfo.destProduct.folder, processInfo.destProduct.eoProductName, browseExtension)

            # Invoking external resource for browse generation.
            print "[alos_special_product.makeBrowses] /bin/sh %s %s %s" % (self.makeBrowseCommand, browseSrcPath, browseDestPath)
            command="/bin/sh %s %s %s" % (self.makeBrowseCommand, browseSrcPath, browseDestPath)
            retval = call(command, shell=True)

            if self.debug:
                print "[alos_special_product.makeBrowses] External make browse exit code: %s" % retval
            
            if retval !=0:
                raise Exception("[alos_special_product.makeBrowses] Error generating browse, exit code: %s" % retval)
            print "[alos_special_product.makeBrowses] External make browse exit code :%s" % retval

            # Adding browse to destination product.
            processInfo.destProduct.addSourceBrowse(browseDestPath, [])

            # Create browse choice for browse metadata report
            bmet=processInfo.destProduct.browse_metadata_dict[browseDestPath]
            print "######\n######\n%s" % dir(definitions_EoSip)

            reportBuilder=rep_footprint.rep_footprint()

            print "###\n###\n### BUILD BROWSE CHOICE FROM METADATA:%s" % (processInfo.destProduct.metadata.toString())
            browseChoiceBlock=reportBuilder.buildMessage(processInfo.destProduct.metadata, "rep:browseReport/rep:browse/rep:footprint").strip()
            if self.debug!=-1:
                print "browseChoiceBlock:%s" % (browseChoiceBlock)
            bmet.setMetadataPair(browse_metadata.BROWSE_METADATA_BROWSE_CHOICE, browseChoiceBlock)

            # Set the browse type (if not default one(i.e. product type code))for the product metadata report BROWSES block
            # If specified in configuration
            tmp = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_BROWSES_TYPE)
            if tmp != None:
                bmet.setMetadataPair(metadata.METADATA_BROWSES_TYPE, tmp)

            # idem for METADATA_CODESPACE_REFERENCE_SYSTEM
            tmp = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_CODESPACE_REFERENCE_SYSTEM)
            if tmp != None:
                bmet.setMetadataPair(metadata.METADATA_CODESPACE_REFERENCE_SYSTEM, tmp)


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
                self.outputProductResolvedPaths = processInfo.destProduct.getOutputFolders(basePath, pathRules)

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
            ingester = ingester_alos_special()
            ingester.debug=1
            ingester.starts(sys.argv)
            
        else:
            print "syntax: python ingester_xxx.py -c configuration_file.cfg [-l list_of_product_file]"
            sys.exit(1)
            
    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
