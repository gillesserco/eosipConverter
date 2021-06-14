#
# This is a SkySat ingester class.
#
# For Esa/lite dissemination project
#
# Serco 06/2021 Lavaux Gilles
#

import os, sys, inspect
import time
import zipfile
import traceback
from cStringIO import StringIO


# add converter package path to sys.path 
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parrent=os.path.dirname(currentdir)
sys.path.insert(0, parrent)

#
from eoSip_converter.base import ingester, reportMaker
from eoSip_converter.esaProducts import product_EOSIP, product_skysat
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip,formatUtils
from xml_nodes import rep_rectifiedBrowse
from eoSip_converter.esaProducts.namingConvention_hightres import NamingConvention_HightRes
import eoSip_converter.imageUtil as imageUtil
import eoSip_converter.fileHelper as fileHelper
import eoSip_converter.xmlHelper as xmlHelper

# minimum config version that can be use
MIN_CONFIG_VERSION=1.0
VERSION="SkySat converter V:1.0.0"

SIP_REF_NAME='SSC_OPER_CSG_AN4_3B_20200415T105622_N49-507_E008-502_01_v0100.SIP.ZIP'
EO_REF_NAME='SSC_OPER_CSG_AN4_3B_20200415T105622_N49-507_E008-502_01'

class ingester_skysat(ingester.Ingester):

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
                # alter href mapping
                processInfo.destProduct.metadata.alterMetadataMaping('href', metadata.METADATA_FULL_PACKAGENAME)
                
                
                if processInfo.srcProduct.useBbox==False:
                    processInfo.addLog("############ browse node unused !!")
                    print("############ browse node unused !!")
                    processInfo.destProduct.browseBlockDisabled = True

        #
        # called after having done the various reports
        #
        def afterReportsDone(self, processInfo):

            n = 0
            newContentList = []
            for path in processInfo.srcProduct.contentList:
                print " @@@@@ check contentList[%s]:%s" % (n, path)
                piece = product_EOSIP.EoPiece(path)
                piece.alias = path
                piece.localPath = "%s/%s" % (processInfo.srcProduct.EO_FOLDER, path)
                newContentList.append(piece.alias)
                processInfo.destProduct.addPiece(piece)
                n += 1

            n = 0
            for root, dirs, files in os.walk(processInfo.srcProduct.EO_FOLDER, topdown=False):
                for name in files:
                    aPath = relPath = os.path.join(root, name)
                    relPath = os.path.join(root, name)[len(processInfo.srcProduct.EO_FOLDER) + 1:]
                    print "   content[%s] EO_FOLDER relative path:%s" % (n, relPath)

                    piece = product_EOSIP.EoPiece(relPath)
                    piece.alias = relPath
                    piece.localPath = aPath
                    newContentList.append(piece.alias)
                    processInfo.destProduct.addPiece(piece)

            processInfo.srcProduct.contentList = newContentList

            if processInfo.srcProduct.supResolution:
                self.keepInfo(processInfo.srcProduct.origName , 'sup resolution')
            else:
                self.keepInfo(processInfo.srcProduct.origName , 'NO sup resolution')

        #
        # called at the end of the doOneProduct, before the index/shopcart creation
        #
        def afterProductDone(self, processInfo):
            # alter MD.XML
            self.alterReportXml(processInfo)

        #
        #
        #
        def alterReportXml(self, processInfo) :
            helper = xmlHelper.XmlHelper()
            helper.setData(processInfo.destProduct.productReport)
            helper.parseData()
            processInfo.addLog("- alterReportXml: product report parsed")
            if self.debug!=0:
                print " alterReportXml: product report parsed"

            # add namespace in sensor operational mode:
            codeSpaceOpMode=processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_CODESPACE_SENSOR_OPERATIONAL_MODE)
            if self.debug != 0:
                print "alterReportXml: codeSpaceOpMode='%s'"  % codeSpaceOpMode
            if not processInfo.destProduct.testValueIsDefined(codeSpaceOpMode):
                raise Exception("codeSpaceOpMode is not defined")
            aNode = helper.getFirstNodeByPath(None, 'procedure/EarthObservationEquipment/sensor/Sensor/operationalMode',None)
            helper.setNodeAttributeText(aNode, 'codeSpace', codeSpaceOpMode)

            helper2 = xmlHelper.XmlHelper()
            helper2.setData(helper.prettyPrint())
            helper2.parseData()
            formattedXml = helper2.prettyPrintAll()
            if self.debug != 0:
                print " new XML: %s " % formattedXml
            fd = open(processInfo.destProduct.reportFullPath, 'w')
            fd.write(formattedXml)
            fd.flush()
            fd.close()
            processInfo.destProduct.productReport = formattedXml
            processInfo.addLog("alterReportXml: product report changed at path:'%s'" % processInfo.destProduct.reportFullPath)
            # set AM time if needed
            processInfo.destProduct.setFileAMtime(processInfo.destProduct.reportFullPath)


        #
        #
        #
        def buildEoNames(self, processInfo, namingConvention=None):
            # force setEoExtension to ZIP. Because we use SRC_PRODUCT_AS_DIR to use several files as input, and we want a .SIP.ZIP package.
            processInfo.destProduct.setEoExtension(definitions_EoSip.getDefinition('PACKAGE_EXT'))
            #
            self.buildEoNamesDefault(processInfo, namingConvention)

    
        #
        # Override
        # this is the first function called by the base ingester
        #
        # as input we have the manifest path. Need to use his parent for the product path
        #
        def createSourceProduct(self, processInfo):
            global debug,logger
            processInfo.srcPath=processInfo.srcPath.replace('\\','/')
            product = product_skysat.Product_Skysat(processInfo.srcPath)
            if self.test_mode:
                    product.setDebug(1)
            processInfo.srcProduct = product
            product.processInfo = processInfo


        #
        # Override
        #
        def createDestinationProduct(self, processInfo):
            global debug,logger
            eosipP=product_EOSIP.Product_EOSIP()
            """# use wrapped zip if size ~ 2gb
            aSize = processInfo.srcProduct.getSize()
            # d'ont want an Eosip > 2gb done using python zip lib
            if aSize > 1900*1024*1024:
                processInfo.addLog(" ## zip: will use wrapped library because size >=1.9 gb: %s" % (aSize))
                eosipP.setUsePythonZipLib(False)
            else:
                processInfo.addLog(" ## zip: will use python library because size <1.9 gb: %s" % (aSize))
            #"""
            eosipP.sourceProductPath = processInfo.srcPath
            processInfo.destProduct = eosipP

            # set naming convention instance
            namingConventionSip = NamingConvention_HightRes(self.OUTPUT_SIP_PATTERN)
            eosipP.setNamingConventionSipInstance(namingConventionSip)
            eosipP.setNamingConventionEoInstance(namingConventionSip)

            processInfo.destProduct.setNamingConventionEoInstance(namingConventionSip)

            # long sip file
            eosipP.setSipInfoType(product_EOSIP.EXTENDED_SIP_INFO_TYPE)
            
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
                processInfo.addLog(" prepare product in:%s" % (processInfo.workFolder))
                self.logger.info(" prepare product");
                processInfo.srcProduct.extractToPath(processInfo.workFolder, processInfo.test_dont_extract)
                
                processInfo.addLog("  extracted inside:%s" % (processInfo.workFolder))
                self.logger.info("  extracted inside:%s" % (processInfo.workFolder))

        #
        # Override
        #
        def extractMetadata(self, met, processInfo):
            # fill metadata object
            numAdded=processInfo.srcProduct.extractMetadata(met, processInfo)
            

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
            processInfo.srcProduct.makeBrowses(processInfo)


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
                
                # now done before in base_ingester.doOneProduct
                #self.outputProductResolvedPaths = processInfo.destProduct.getOutputFolders(basePath, pathRules)

                #
                productPath=None
                if len(self.outputProductResolvedPaths)==0:
                        raise Exception("no product resolved path")
                else:
                        # output in first path
                        firstPath=self.outputProductResolvedPaths[0]
                        processInfo.addLog("  Eo-Sip product writen in folder:%s\n" %  (firstPath))
                        self.logger.info("  Eo-Sip product writen in folder:%s\n" %  (firstPath))
                        productPath = processInfo.destProduct.writeToFolder(firstPath, overwrite)
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


if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            ingester = ingester_skysat()

            commandLineInfo = ingester.getCommandLineInfo()
            
            #ingester.DEBUG=1
            exitCode = ingester.starts(sys.argv)
            
            out=StringIO()
            print >> out, commandLineInfo
            print >>out, "### Start of report\n"
            aReportMaker = reportMaker.ReportMaker()
            report = aReportMaker.makeReport(ingester)
            print >>out, "SkySat conversion report"
            print >>out, report
            print >>out, "### End of report"
            #print out.getvalue()
            reportName = "Skysat_conversion_report.txt"
            fd=open(reportName, 'w')
            fd.write(out.getvalue())
            fd.flush()
            fd.close()
            print "conversion report written well:%s" % reportName

            sys.exit(exitCode)

        else:
            print "syntax: python ingester_xxx.py -c configuration_file.cfg [-l list_of_product_file]"
            sys.exit(1)
            
    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
        sys.exit(2)
