#
# For Esa/lite dissemination project
#
# Serco 02/2015 Lavaux Gilles
#
# 03/03/2015: V: 0.1
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
from eoSip_converter.base import ingester
from eoSip_converter.esaProducts import product_EOSIP, product_image2006irsp6
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip,formatUtils
from xml_nodes import rep_rectifiedBrowse
from eoSip_converter.esaProducts.namingConvention_hightres import NamingConvention_HightRes
import eoSip_converter.imageUtil as imageUtil
import eoSip_converter.fileHelper as fileHelper
import eoSip_converter.xmlHelper as xmlHelper


# minimum config version that can be use
MIN_CONFIG_VERSION=1.0
VERSION="Image2006_IrsP6 converter V:1.0.0"
#REF_SIP_NAME='IR6_OPER_LI3_ORT_10_20001122T112233_20001122T112233_oooooo_tttt_0001.SIP.ZIP'
REF_NAME='IR6_OPER_LI3_ORT_10_20001122T112233_N20-882_E095-939_0001.SIP.ZIP'

class ingester_Image2006IrsP6(ingester.Ingester):

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
                # set angle unit to deg
                processInfo.destProduct.metadata.setValidValue('UNIT_ANGLE', 'deg')
                # set platform id to N/A as per spec. before, for name construction was at '6'
                if not processInfo.srcProduct.isSpot:
                        processInfo.destProduct.metadata.setMetadataPair(metadata.METADATA_PLATFORM_ID, 'N/A')
                #processInfo.srcProduct.metadata.setValidValue(metadata.METADATA_PLATFORM_ID, 'N/A')
                #sys.exit(0)


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
        def alterReportXml(self, processInfo) :
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
        # as input we have the manifest path. Need to use his parent for the product path
        #
        def createSourceProduct(self, processInfo):
            global debug,logger
            processInfo.srcPath=processInfo.srcPath.replace('\\','/')
            product = product_image2006irsp6.Product_Image2006IrsP6(processInfo.srcPath)
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
            #namingConventionSip = NamingConvention(self.OUTPUT_SIP_PATTERN)
            namingConventionSip = NamingConvention_HightRes(self.OUTPUT_SIP_PATTERN)
            processInfo.destProduct.setNamingConventionSipInstance(namingConventionSip)
            eosipP.setNamingConventionSipInstance(namingConventionSip)
            eosipP.setNamingConventionEoInstance(namingConventionSip)

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
                processInfo.addLog(" prepare product in:%s" % (processInfo.workFolder))
                self.logger.info(" prepare product");
                processInfo.srcProduct.extractToPath(processInfo.workFolder, processInfo.test_dont_extract)
                
                processInfo.addLog("  extracted inside:%s" % (processInfo.workFolder))
                self.logger.info("  extracted inside:%s" % (processInfo.workFolder))

                self.imageutilsExe = self.ressourcesProvider.getRessourcePath('imageutilsExe')
                processInfo.srcProduct.imageutilsExe = self.imageutilsExe

                self.stretcherAppExe = self.ressourcesProvider.getRessourcePath('stretchAppExe')
                processInfo.srcProduct.stretcherAppExe = self.stretcherAppExe


        #
        # 
        #
        def makeImageryHdr(self,path,processInfo):
                fd=open("%s/metadata.xml" % processInfo.workFolder, 'r')
                data=fd.read()
                fd.close()
                helper=xmlHelper.XmlHelper()
                helper.setData(data);
                helper.parseData()

                aNode = helper.getFirstNodeByPath(None, 'Image/COLUMNS', None)
                rows=None
                cols=None
                if aNode is None:
                        raise Exception("can not find node Image/COLUMNS in xml data")
                cols=helper.getNodeText(aNode)
                
                aNode = helper.getFirstNodeByPath(None, 'Image/ROWS', None)
                if aNode is None:
                        raise Exception("can not find node Image/ROWS in xml data")
                rows=helper.getNodeText(aNode)

                data="""BYTEORDER     M
LAYOUT        BIL
NROWS         %s
NCOLS         %s
NBANDS        4
NBITS         8
SKIPBYTES     0
""" % (rows, cols)
                print "imagery.hdr data:\n%s" % data

                fd=open(path, 'w')
                fd.write(data)
                fd.close()
                print "imagery.hdr writen at:%s" % path
                #os._exit(0)




        #
        # 
        #
        def makeImageryblw(self,path,processInfo):
                fd=open("%s/metadata.xml" % processInfo.workFolder, 'r')
                data=fd.read()
                fd.close()
                helper=xmlHelper.XmlHelper()
                helper.setData(data);
                helper.parseData()

                aNode = helper.getFirstNodeByPath(None, 'GeoInformation/XGEOREF', None)
                XGEOREF=None
                YGEOREF=None
                if aNode is None:
                        raise Exception("can not find node GeoInformation/XGEOREF in xml data")
                XGEOREF=helper.getNodeText(aNode)
                
                aNode = helper.getFirstNodeByPath(None, 'GeoInformation/YGEOREF', None)
                if aNode is None:
                        raise Exception("can not find node GeoInformation/YGEOREF in xml data")
                YGEOREF=helper.getNodeText(aNode)

                XCELLRES=None
                YCELLRES=None
                aNode = helper.getFirstNodeByPath(None, 'GeoInformation/XCELLRES', None)
                if aNode is None:
                        raise Exception("can not find node GeoInformation/XCELLRES in xml data")
                XCELLRES=helper.getNodeText(aNode)

                YCELLRES=None
                aNode = helper.getFirstNodeByPath(None, 'GeoInformation/YCELLRES', None)
                if aNode is None:
                        raise Exception("can not find node GeoInformation/YCELLRES in xml data")
                YCELLRES=helper.getNodeText(aNode)

                data="""\t%s
\t0.000000
\t0.000000
\t-%s
\t%s
\t%s
""" % (XCELLRES, YCELLRES, XGEOREF, YGEOREF)
                print "imagery.blw data:\n%s" % data

                fd=open(path, 'w')
                fd.write(data)
                fd.close()
                print "imagery.blw writen at:%s" % path
                #os._exit(0)
                

        #
        # Override
        # + check if there is a imagery.hdr present, if not, create it
        #
        def extractMetadata(self,met,processInfo):
            # fill metadata object
            numAdded=processInfo.srcProduct.extractMetadata(met)

            # verify that a imagery.hdr is present
            tmp= "%s/imagery.hdr" % (processInfo.workFolder)
            if not os.path.exists(tmp):
                    #raise Exception('no imagery.hdr found:%s' % tmp)
                    self.makeImageryHdr(tmp, processInfo)

            # also verify that a imagery.blw is present
            tmp= "%s/imagery.blw" % (processInfo.workFolder)
            if not os.path.exists(tmp):
                    #raise Exception('no imagery.hdr found:%s' % tmp)
                    self.makeImageryblw(tmp, processInfo)

            met.setMetadataPair(metadata.METADATA_GENERATION_TIME, time.strftime('%Y-%m-%dT%H:%M:%SZ'))

            # keep some info
            mode = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_SENSOR_OPERATIONAL_MODE)
            self.keepInfo("sensor mode", mode)
            sensor = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_INSTRUMENT)
            self.keepInfo("sensor", sensor)
            typecode = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_TYPECODE)
            self.keepInfo("typecode", typecode)

            softVersion = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_SOFTWARE_VERSION)
            self.keepInfo("softVersion", softVersion)
            softName = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_SOFTWARE_NAME)
            self.keepInfo("softName", softName)

                
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
        def makeKmz(self, processInfo):
                if not self.test_dont_write:
                        processInfo.ingester.logger.info("WILL CREATE KMZ")
                        import kmz
                        outPath = "%s/kmz" % processInfo.ingester.LOG_FOLDER
                        if not os.path.exists(outPath):
                                self.logger.info("  will make kmz folder:%s" % outPath)
                                os.makedirs(outPath)
                        kmzPath = kmz.eosipToKmz.makeKmlFromEoSip_new(True, outPath, processInfo)
                        print " KMZ created at path:%s" % kmzPath
                        if kmzPath != None:
                                processInfo.addLog("KMZ created at path:%s" % kmzPath)
                        else:
                                processInfo.addLog("KMZ was NOT CREATED!")
                                raise Exception("KMZ was NOT CREATED!")

if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            ingester = ingester_Image2006IrsP6()
            ingester.debug=1
            exitCode = ingester.starts(sys.argv)
            #
            ingester.makeConversionReport("Image2006IrsP6_conversion_report", '.')

            sys.exit(exitCode)
        else:
            print "syntax: python ingester_xxx.py -c configuration_file.cfg [-l list_of_product_file]"
            sys.exit(1)

            
    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
        sys.exit(2)
