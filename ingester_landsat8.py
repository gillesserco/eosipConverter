#
# For Esa/lite dissemination project
#
# Serco 02/2020 Lavaux Gilles
#
# 20/07/2020: V: 0.1
#
#
#
#
import os, sys, inspect
import zipfile
import traceback
from cStringIO import StringIO


# add converter package path to sys.path 
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parrent=os.path.dirname(currentdir)
print("##### eoSip converter package dir:%s" % parrent)
sys.path.insert(0, parrent)

#
from eoSip_converter.base import ingester, reportMaker
from eoSip_converter.esaProducts import product_EOSIP, product_landsat8
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip,formatUtils
from eoSip_converter.esaProducts.namingConvention_DDOT import NamingConvention_DDOT
from eoSip_converter.esaProducts.namingConvention_AsSource import NamingConvention_AsSource
#

import eoSip_converter.xmlHelper as xmlHelper

# minimum config version that can be use
MIN_CONFIG_VERSION=1.0
VERSION="Landsat8 converter V:1.0.0"
#SIP_REF_NAME='LA1_OPER_WV6_PAN_OR_20100527T231608_N13-756_W100-028_0100.SIP.ZIP'
SIP_REF_NAME='L08_OPER_OAT_GTC_1P_20200902T105622_20200902T105702_224596_0205_0020_01_v0100.SIP.ZIP'
EO_REF_NAME='LA1_OPER_WV6_PAN_OR_20100527T231608_N13-756_W100-028_0100'



#
#
#
class Ingester_Landsat8(ingester.Ingester):

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

            asq = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_ACQUISITION_CENTER)
            if not processInfo.destProduct.metadata.valueExists(asq):
                print("disable downlinkedTo")
                processInfo.destProduct.metadata.xmlNodeUsedMapping['/opt:EarthObservation/eop:metaDataProperty/eop:EarthObservationMetaData/eop:downlinkedTo'] = 'UNUSED'
                #os.exit(1)


        #
        # called after having done the various reports
        #
        def afterReportsDone(self, processInfo):
            # alter MD.XML
            self.alterReportXml(processInfo)

            #
            # build piece list
            # just the src .tar.gz product, converted as zip
            #
            n = 0
            newContentList = []
            piece = product_EOSIP.EoPiece(processInfo.srcProduct.origName)
            piece.alias = processInfo.srcProduct.origName
            piece.localPath = processInfo.srcProduct.path
            newContentList.append(piece.alias)
            processInfo.destProduct.addPiece(piece)
            processInfo.srcProduct.contentList = newContentList

            #os._exit(1)


        #
        # called at the end of the doOneProduct, before the index/shopcart creation
        #
        def afterProductDone(self, processInfo):
            pass


        #
        # add namespace in: <eop:operationalMode
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

            # add namespace in eop:acquisitionStation:
            codeSpaceAcqStation=processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_CODESPACE_ACQUISITION_STATION)
            if self.debug != 0:
                print "alterReportXml: codeSpaceAcqStation='%s'"  % codeSpaceAcqStation
            if not processInfo.destProduct.testValueIsDefined(codeSpaceAcqStation):
                raise Exception("codeSpaceAcqStation is not defined")
            aNode = helper.getFirstNodeByPath(None, 'metaDataProperty/EarthObservationMetaData/downlinkedTo/DownlinkInformation/acquisitionStation',None)
            helper.setNodeAttributeText(aNode, 'codeSpace', codeSpaceAcqStation)

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
            # test default in ingester
            self.buildEoNamesDefault(processInfo, namingConvention)

            # test EoSip package name
            aName = processInfo.destProduct.getSipPackageName()
            if len(aName) != len(SIP_REF_NAME):
                print("Ref name  :%s" % SIP_REF_NAME)
                print("EoSip name:%s" % aName)
                raise Exception("EoSip name has incorrect length:%s VS %s" % (len(aName), len(SIP_REF_NAME)))

            if aName.find('@') >= 0 or aName.find('#') > 0:
                raise Exception("SipProductName incomplet:%s" % aName)

            anEoName = processInfo.destProduct.getEoProductName()
            #if len(anEoName) != len(EO_REF_NAME):
            #    print("Ref EO name:%s" % EO_REF_NAME)
            #    print("EO name    :%s" % anEoName)
            #    raise Exception("EO name has incorrect length:%s VS %s" % (len(anEoName), len(EO_REF_NAME)))


            if anEoName.find('@') >= 0 or aName.find('#') > 0:
                raise Exception("EoProductName incomplet:%s" % aName)

            #som = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_SENSOR_OPERATIONAL_MODE)
            #opm = product_radarsat.operationalMode[som]
            #print(" -> sensor operational mode string:%s" % opm)
            #processInfo.srcProduct.metadata.setMetadataPair(metadata.METADATA_SENSOR_OPERATIONAL_MODE, opm)
            
                
        #
        # Override
        # this is the first function called by the base ingester
        #
        # as input we have the manifest path. Need to use his parent for the product path
        #
        def createSourceProduct(self, processInfo):
            global debug,logger
            #
            processInfo.srcPath=processInfo.srcPath.replace('\\','/')
            product = product_landsat8.Product_Landsat8(processInfo.srcPath)

            #product.setDebug(1)
            processInfo.srcProduct = product
            self.stretcherApp = self.ressourcesProvider.getRessourcePath('stretchAppExe')
            processInfo.srcProduct.stretcherApp = self.stretcherApp


        #
        # Override
        #
        def createDestinationProduct(self, processInfo):
            global debug,logger
            eosipP=product_EOSIP.Product_EOSIP()
            #eosipP.setDebug(1)
            eosipP.sourceProductPath = processInfo.srcPath
            eosipP.setSipInfoType(product_EOSIP.EXTENDED_SIP_INFO_TYPE)
            processInfo.destProduct = eosipP

            # set naming convention instance
            namingConventionSip = NamingConvention_DDOT(self.OUTPUT_SIP_PATTERN)
            #namingConventionSip.setDebug(1)
            eosipP.setNamingConventionSipInstance(namingConventionSip)

            namingConventionEo = NamingConvention_AsSource(self.OUTPUT_EO_PATTERN)
            #namingConventionSip.setDebug(1)
            eosipP.setNamingConventionEoInstance(namingConventionEo)
            
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
        def prepareProducts(self, processInfo):
                processInfo.addLog(" prepare product in:%s" % (processInfo.workFolder))
                self.logger.info(" prepare product");
                processInfo.srcProduct.extractToPath(processInfo.workFolder, processInfo.test_dont_extract)
                
                processInfo.addLog("  extracted inside:%s" % (processInfo.workFolder))
                self.logger.info("  extracted inside:%s" % (processInfo.workFolder))

                self.stretcherAppExe = self.ressourcesProvider.getRessourcePath('stretchAppExe')
                processInfo.srcProduct.stretcherAppExe = self.stretcherAppExe

        #
        # Override
        #
        def extractMetadata(self, met, processInfo):
            #print(" #### extractMetadata; processInfo:%s" % processInfo)
            #os._exit(1)
            # fill metadata object
            numAdded=processInfo.srcProduct.extractMetadata(met, processInfo)

            # use method in base converter
            self.getGenerationTime(met)

            # the one using bbox or not
            if processInfo.srcProduct.useBbox:
                self.keepInfo('useBbox', processInfo.srcProduct.path)
            else:
                self.keepInfo('dontUseBbox', processInfo.srcProduct.path)

            # orbit direction
            tmp=processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_PROCESSING_LEVEL)
            self.keepInfo(metadata.METADATA_PROCESSING_LEVEL, tmp)

            #self.keepInfo('imageDescriptor', processInfo.srcProduct.metadata.getMetadataValue('imageDescriptor'))

            #self.keepInfo('numberOfBands', processInfo.srcProduct.metadata.getMetadataValue('numberOfBands'))

            #self.keepInfo(metadata.METADATA_TYPECODE, processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_TYPECODE))

            self.keepInfo(metadata.METADATA_INSTRUMENT, processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_INSTRUMENT))

                
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
            ingester = Ingester_Landsat8()

            commandLineInfo = ingester.getCommandLineInfo()
            
            #ingester.DEBUG=1
            exitCode = ingester.starts(sys.argv)

            out=StringIO()
            print >> out, commandLineInfo
            print >>out, "### Start of report\n"
            aReportMaker = reportMaker.ReportMaker()
            report = aReportMaker.makeReport(ingester)
            print >>out, "Landsat8 conversion report"
            print >>out, report
            print >>out, "### End of report"
            reportName = "Landsat8_conversion_report.txt"
            fd=open(reportName, 'w')
            fd.write(out.getvalue())
            fd.flush()
            fd.close()
            print("conversion report written well:%s" % reportName)

            sys.exit(exitCode)
        else:
            print("syntax: python ingester_xxx.py -c configuration_file.cfg [-l list_of_product_file]")
            sys.exit(1)
            
    except Exception, e:
        print(" Error")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
        sys.exit(2)
