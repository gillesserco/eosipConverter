#
# This is a Planetscope ingester class. 
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
from eoSip_converter.esaProducts import product_EOSIP, product_Planetscope
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip,formatUtils
from xml_nodes import rep_rectifiedBrowse
from eoSip_converter.esaProducts.namingConvention_hightres import NamingConvention_HightRes
import eoSip_converter.imageUtil as imageUtil
import eoSip_converter.fileHelper as fileHelper
import eoSip_converter.xmlHelper as xmlHelper

# minimum config version that can be use
MIN_CONFIG_VERSION=1.0
VERSION="PlanetScope converter V:1.0.0"

SIP_REF_NAME='PSC_OPER_PS2_AN3_3B_20200415T105622_N49-507_E008-502_4140_v0100.SIP.ZIP'
EO_REF_NAME='PSC_OPER_PS2_AN3_3B_20200415T105622_N49-507_E008-502_4140'

class ingester_planetscope(ingester.Ingester):

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

                processInfo.destProduct.metadata.setMetadataPair(metadata.METADATA_PLATFORM_ID, '1')

        #
        # called after having done the various reports
        #
        def afterReportsDone(self, processInfo):
            # alter MD.XML
            self.alterReportXml(processInfo)

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
        

        #
        # called at the end of the doOneProduct
        #
        def afterProductDone(self, processInfo):

            self.keepInfo('orbit_direction', processInfo.srcProduct.metadata.getMetadataValue('orbit_direction'))
            self.keepInfo('level', processInfo.srcProduct.metadata.getMetadataValue('level'))
            self.keepInfo(processInfo.srcProduct.productFolderName, "footprint_json_num-pairs= %s" % processInfo.srcProduct.metadata.getMetadataValue('footprint_json_num-pairs'))

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
            if 1==1 or self.debug != 0:
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
            processInfo.addLog("alterReportXml: product  aaaaaaaaaaaaaaa report changed at path:'%s'" % processInfo.destProduct.reportFullPath)
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
            product = product_Planetscope.Product_Planetscope(processInfo.srcPath)
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

                self.stretcherApp = self.ressourcesProvider.getRessourcePath('stretchAppExe')
                processInfo.srcProduct.stretcherApp = self.stretcherApp
                
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

        #
        # create a kmz, use the bounding box
        # created in the log folder
        #
        def makeKmz__NOT_USED(self, processInfo):
                if not self.test_dont_write:
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



if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            ingester = ingester_planetscope()

            commandLineInfo = ingester.getCommandLineInfo()
            
            #ingester.DEBUG=1
            exitCode = ingester.starts(sys.argv)
            
            out=StringIO()
            print >> out, commandLineInfo
            print >>out, "### Start of report\n"
            aReportMaker = reportMaker.ReportMaker()
            report = aReportMaker.makeReport(ingester)
            print >>out, "Planetscope conversion report"
            print >>out, report
            print >>out, "### End of report"
            #print out.getvalue()
            reportName = "Planetscope_conversion_report.txt"
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
