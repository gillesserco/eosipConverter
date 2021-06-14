#
# This is a specialized class that ingest worldview dataset
#
# For Esa/ lite dissemination project
#
# Serco 02/2015
# Lavaux Gilles 
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
from eoSip_converter.esaProducts import product_worldview_block, product_EOSIP
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip,formatUtils
from eoSip_converter.esaProducts.definitions_EoSip import rep_rectifiedBrowse
from eoSip_converter.esaProducts.namingConvention import NamingConvention
import eoSip_converter.imageUtil as imageUtil
import eoSip_converter.fileHelper as fileHelper

# minimum config version that can be use
MIN_CONFIG_VERSION=1.0
VERSION="WorldView2_order converter V:1.0.0"
REF_NAME="WV2_OPER_WV-110__2A_20130519T101749_N43-568_E017-096_4061.SIP.ZIP"


"""
The ingester for the worldview dataset.
It takes as input the custom order file 'eoSipProductOrder_053963553060_01.xml' that have to be generated usiing the 'make_product_lists.py' tool.
This tool split the original order folder in block of 3x3 tiles, and calculate some metadata like center and footprint
"""
class Ingester_Worldview_Orders(ingester.Ingester):

        #
        # need to have the quality file that will be put in every EoSip
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
        # - set common files into each EoSip
        # - alter metadata mapping for href: from metadata.METADATA_PRODUCTNAME to metadata.METADATA_FULL_PACKAGENAME
        #
        def beforeReportsDone(self, processInfo):
                print "################# @@@@@@@@@@@@@@@@@@@ beforeReportsDone"
                for key in processInfo.destProduct.getEoSipKeys():
                        anEoSip = processInfo.destProduct.getEoSip(key)
                        print "################# @@@@@@@@@@@@@@@@@@@ beforeReportsDone: got eoSip for key:%s" % key

                        # alter mapping
                        anEoSip.metadata.alterMetadataMaping('href', metadata.METADATA_FULL_PACKAGENAME)

                        
                        # set the zip common content names and path,  
                        #anEoSip.contentListPath = list(processInfo.srcProduct.commonFiles)
                        # the name as it will be in the final product is what is inside the orderId folder
                        aList=[]
                        orderId=anEoSip.metadata.getMetadataValue(product_worldview_block.NODE_ID)
                        self.logger.info(" beforeReportsDone: orderId=%s" % orderId)
                        processInfo.addLog(" beforeReportsDone: orderId=%s" % orderId)

                        # orderId is now like 053963684010_01_P001, i.e not like in the path where it is like: 053963684010_01
                        pathOrderId=orderId
                        print "################# @@@@@@@@@@@@@@@@@@@ beforeReportsDone: pathOrderId initial:%s" % (pathOrderId)
                        toks = orderId.split('_')
                        if len(toks) == 3:
                                pathOrderId = '_'.join(toks[0:2])
                        print "################# @@@@@@@@@@@@@@@@@@@ beforeReportsDone: pathOrderId final:%s; len toks:%s" % (pathOrderId, len(toks))

                        n=0
                        #for path in anEoSip.contentListPath:
                        for path in processInfo.srcProduct.commonFiles:
                                print "################# @@@@@@@@@@@@@@@@@@@ beforeReportsDone: path[%s]:%s" % (n, path)
                                if not os.path.exists(path):
                                        raise Exception("EoSip commonFiles not found:%s" % path)
                                if os.path.isfile(path):
                                        pos = path.find(pathOrderId+'/')
                                        if pos<0:
                                                print "################# @@@@@@@@@@@@@@@@@@@ beforeReportsDone[%s]: not orderid:'%s'" % (n, orderId)
                                                #pass
                                                #raise Exception("can not find orderId '%s' in common path:%s" % (orderId, path))
                                        else:
                                                name = path[pos+len(pathOrderId)+1:]
                                                aList.append(name)
                                                print "################# @@@@@@@@@@@@@@@@@@@ beforeReportsDone[%s]: path=%s; name in zip=%s" % (n, path, name)
                                                processInfo.addLog(" beforeReportsDone[%s]: path=%s; name in zip=%s" % (n, path, name))
                                                anEoSip.contentListPath[name]=path
                                                n=n+1
                                else:
                                        print "################# @@@@@@@@@@@@@@@@@@@ beforeReportsDone[%s]: path=%s is a directory, don't store"

                        #os._exit(1)
                        anEoSip.contentList = aList
                        # remove the source which is the 'eoSipProductOrder_xxxxxxxxxxx_01.xml'
                        anEoSip.sourceProductPath=None
                        


        #
        # called after having done the various reports
        #
        def afterReportsDone(self, processInfo):
                pass
        

        #
        # called at the end of the doOneProduct, before the index/shopcart creation
        #
        def afterProductDone(self, processInfo):
            # do it in the dest products
            processInfo.destProduct.makeKmz(processInfo)

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
        # as input we have a 'per order like' xml file gebnerated by me, filename like: eoSipProductOrder_053963553060_01.xml
        #
        def createSourceProduct(self, processInfo):
            global debug,logger
            processInfo.srcPath=processInfo.srcPath.replace('\\','/')
            print "worldview custom prder file path:%s" % processInfo.srcPath
            self.aFileHelper=fileHelper.FileHelper()
            wp = product_worldview_block.Product_Worldview_Block(processInfo.srcPath)
            #wp.setDebug(1)
            processInfo.srcProduct = wp


        #
        # Override
        #
        def createDestinationProduct(self, processInfo):
            global debug,logger
            # do it in the source products
            processInfo.srcProduct.createDestinationProducts(processInfo, self.OUTPUT_SIP_PATTERN)
            
            self.logger.info(" Eo-Sip product created")
            processInfo.addLog(" Eo-Sip product created")

            processInfo.srcProduct.prepareBrowseCommands(processInfo)

            # refine
            #processInfo.srcProduct.refineMetadata()

                    
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

                self.tifToPngExe = self.ressourcesProvider.getRessourcePath('tifToPngExe')
                processInfo.srcProduct.tifToPngExe = self.tifToPngExe


                self.stretcherApp = self.ressourcesProvider.getRessourcePath('stretcherApp')
                processInfo.srcProduct.stretcherApp = self.stretcherApp

                
                # get common content (all except TIF files)
                #processInfo.srcProduct.getCommonContent(processInfo)
                
                processInfo.addLog("  extracted inside:%s" % (processInfo.workFolder))
                self.logger.info("  extracted inside:%s" % (processInfo.workFolder))

        #
        # Override
        #
        def extractMetadata(self,met,processInfo):
            # fill metadata object
            numAdded=processInfo.srcProduct.extractMetadata(met, processInfo)

            #met.setMetadataPair(metadata.METADATA_GENERATION_TIME, time.strftime('%Y-%m-%dT%H:%M:%SZ'))
            # use method in base converter
            self.getGenerationTime(met)

                
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
            # do it in the source products
            processInfo.srcProduct.makeBrowses(processInfo)



        #
        # Override
        #
        # output the Eo-Sip profuct in the destination folder
        # take the first rule and put the product in the resulting folder
        # create link for the other rules if any
        #
        def output_eoSip(self, processInfo, basePath, pathRules, overwrite=None):
            if self.test_mode:
                    processInfo.srcProduct.testMode=True
                    #print " will dump contentList:%s" % processInfo.destProduct.contentList
                    #n=0
                    #for item in processInfo.destProduct.contentList:
                    #        print " contentList[%s]:%s" % (n, item)
                    #        n+=1
                    #print " will dump contentList"
            # do it in the source products
            return processInfo.srcProduct.output_eoSip(processInfo, basePath, pathRules, overwrite, self.logger)




if __name__ == '__main__':
    exitCode = -1

    try:
        if len(sys.argv) > 1:
            ingester = Ingester_Worldview_Orders()
            ingester.debug=1
            exitCode = ingester.starts(sys.argv)

            out=StringIO()
            print >>out, "### Start of report\n"
            aReportMaker = reportMaker.ReportMaker()
            report = aReportMaker.makeReport(ingester)
            print >>out, "Worldview2 conversion report"
            print >>out, report
            print >>out, "### End of report"
            print out.getvalue()

            sys.exit(exitCode)
        else:
            print "syntax: python ingester_xxx.py -c configuration_file.cfg [-l list_of_product_file]"
            sys.exit(1)

    except SystemExit as e:
        sys.exit(e)
    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
        sys.exit(99)
