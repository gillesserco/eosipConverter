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
from eoSip_converter.base import ingester, reportMaker
from eoSip_converter.esaProducts import product_EOSIP, product_sciamachy
from eoSip_converter.esaProducts import metadata
from eoSip_converter.esaProducts import definitions_EoSip
from eoSip_converter.esaProducts.namingConvention import NamingConvention
from eoSip_converter.esaProducts.namingConvention_envisat import NamingConvention_Envisat
import imageUtil
import fileHelper
import xmlHelper


SOURCE_REF_NAME='SCI_NL__1PYDPA20120215_193113_000060183111_00373_52111_0000.N1.gz'
SIP_REF_NAME='EN1_RPDK_SCI_NL__0P_20080309T225146_20080310T003057_031504_0388.0000.ZIP'
EO_REF_NAME='SCI_NL__0P_20080309T225146_20080310T003057_031504_0388.0000.N1.gz'


# minimum config version that can be use
MIN_CONFIG_VERSION=1.0

class Ingester_Sciamachy_l1b(ingester.Ingester):

        #
        # need to have the quality file that will be put in every EoSip
        #
        def afterStarting(self, **kargs):
                self.qualityFilePath = self.ressourcesProvider.getRessourcePath('qualityFile')
                if not os.path.exists(self.qualityFilePath):
                        raise Exception("quality file does not exists at path:%s" % self.qualityFilePath)
                print "quality file exists:%s" % self.qualityFilePath

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
                processInfo.destProduct.metadata.alterMetadataMaping('href', metadata.METADATA_FULL_PRODUCTNAME)

                
                # we want to put the input product xxx.N1.gz into the eosip, use a piece for this
                name = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_ORIGINAL_NAME)
                piece = product_EOSIP.EoPiece(name)
                piece.alias = name
                piece.localPath=processInfo.srcProduct.path
                # delete content list and add piece
                processInfo.srcProduct.contentList=[]
                processInfo.srcProduct.contentList.append(name)
                processInfo.destProduct.addPiece(piece)

                # also add the quality report file
                qlname = "%s.QR.PDF" % processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_PRODUCTNAME)
                piece = product_EOSIP.EoPiece(qlname)
                piece.alias = qlname
                piece.localPath=self.qualityFilePath
                processInfo.srcProduct.contentList.append(qlname)
                processInfo.destProduct.addPiece(piece)
                
                # add eo product in EoSip: the extracted file that is in the workfolder, as contentList
                n=0
                print " beforeReportsDone: length contentList:%s" % len(processInfo.srcProduct.contentList)
                if 1==2: # disable
                        for path in processInfo.srcProduct.contentList:
                                name=os.path.basename(path)
                                print " beforeReportsDone: add src content[%s]: path=%s; name in zip=%s" % (n, path, name)
                                processInfo.addLog(" beforeReportsDone: add src content[%s]: path=%s; name in zip=%s" % (n, path, name))
                                processInfo.destProduct.contentList.append(name)
                                processInfo.destProduct.contentListPath[name]=path
                                n+=1

                        # add input product in EoSip: the original file, as piece. Note srcProduct represent the extracted .N1 file, not the N1.gz one.
                        # want to store the input N1.gz into eoSip
                        name = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_ORIGINAL_NAME)
                        print "srcProduct name:%s" % name
                        processInfo.srcProduct.contentList.append(name)
                        piece = product_EOSIP.EoPiece(name)
                        piece.localPath=processInfo.srcProduct.path
                        print "srcProduct path:%s" % processInfo.srcProduct.path
                        #os._exit(0)
                        piece.alias=name
                        processInfo.destProduct.addPiece(piece)


        #
        # called after having done the various reports
        #
        def afterReportsDone(self, processInfo):
                self.alterReportXml(processInfo)
        

        #
        # called at the end of the doOneProduct
        #
        def afterProductDone(self, processInfo):
                pass
        
        #
        #
        def alterReportXml(self, processInfo) :
                # add codeSpace to:  <eop:processingCenter codeSpace="urn:eop:Envisat:facility">PDK</eop:processingCenter>
                #
                helper=xmlHelper.XmlHelper()
                helper.setData(processInfo.destProduct.productReport);
                helper.parseData()
                processInfo.addLog(" alterReportXml: product report parsed")
                print " alterReportXml: product report parsed"

                #/atm_EarthObservation/eop_metaDataProperty/eop_EarthObservationMetaData/eop_processing/eop_ProcessingInformation/eop_processingCenter 
                aNode = helper.getFirstNodeByPath(None, 'metaDataProperty/EarthObservationMetaData/processing/ProcessingInformation/processingCenter', None)
                #print " alterReportXml: aNode=%s" % aNode
                #os._exit(0)
                helper.setNodeAttributeText(aNode, 'codeSpace', 'urn:esa:eop:Envisat:facility')

                #/atm_EarthObservation/eop_metaDataProperty/eop_EarthObservationMetaData/eop_downlinkedTo/eop_DownlinkInformation/eop_acquisitionStation 
                aNode = helper.getFirstNodeByPath(None, 'metaDataProperty/EarthObservationMetaData/downlinkedTo/DownlinkInformation/acquisitionStation', None)
                #print " alterReportXml: aNode=%s" % aNode
                #os._exit(0)
                helper.setNodeAttributeText(aNode, 'codeSpace', 'urn:esa:eop:facility')

                #
                # add .N1.gz to xlink:href
                #
                #serviceReferenceNode = helper.getRootNode().getElementsByTagName('ows:ServiceReference')
                #print "serviceReferenceNode:%s; length:%d" % (serviceReferenceNode, len(serviceReferenceNode))
                #if len(serviceReferenceNode)!=1:
                #        raise Exception("error getting ows:ServiceReference node")
                #href = helper.getNodeAttributeText(serviceReferenceNode[0], 'xlink:href')
                #helper.setNodeAttributeText(serviceReferenceNode[0], 'xlink:href', "%s.N1" % href)

                # rebuild xml
                helper2=xmlHelper.XmlHelper()
                helper2.setData(helper.prettyPrint());
                helper2.parseData()
                formattedXml = helper2.prettyPrintAll()
                if self.debug!=0:
                        print " new XML: %s " % formattedXml
                fd=open(processInfo.destProduct.reportFullPath, 'w')
                fd.write(formattedXml)
                fd.flush()
                fd.close()
                processInfo.destProduct.productReport=formattedXml
                processInfo.addLog(" alterReportXml: product report changed at path:'%s'" % processInfo.destProduct.reportFullPath)
                

        #
        #
        #
        def buildEoNames(self, processInfo, namingConvention=None):
                #
                self.logger.info(" buildEoNames")
                processInfo.addLog(" buildEoNames")

                #
                ok=False
                loopNum=0
                while not ok and loopNum<10:
                        print " #################################### buildEoNames loop:%s; namingConvention:%s" % (loopNum, namingConvention)
                        processInfo.addLog(" buildEoNames loop:%s" % loopNum)
                        #processInfo.destProduct.setDebug(1)
                        eosipName = processInfo.destProduct.buildEoNames(namingConvention)
                        print "ref name:'%s'" % SIP_REF_NAME
                        print "mdp name:'%s'" % eosipName

                        # test name length
                        if len(eosipName) != len(SIP_REF_NAME):
                                raise Exception("EoSip package name name has incorrect length:%s VS %s" % (len(eosipName), len(SIP_REF_NAME)))
                        if eosipName.find('@') >=0 or eosipName.find('#')>0:
                                raise Exception("EoSip package name incomplet:%s" % eosipName)

                        # test eo name == input name
                        if processInfo.destProduct.eoPackageName != processInfo.srcProduct.origName:
                                raise Exception("EO product name resonstructed != orinigan one: %s VS %s" % (processInfo.destProduct.eoPackageName, processInfo.srcProduct.origName))
                        
                        #processInfo.destProduct.setDebug(0)
                        if not self.product_overwrite:
                                # test for duplicate
                                exists, newFileCounter = self.checkDestinationAlreadyExists(processInfo)
                                if exists:
                                        processInfo.destProduct.metadata.setMetadataPair(metadata.METADATA_FILECOUNTER, "%s" % newFileCounter)
                                else:
                                        ok=True
                        else:
                                ok=True
                        loopNum += 1
                if not ok:
                        raise Exception("error creating product filename: duplicate test reach loop limit of 10")
            
                
        #
        # Override
        # this is the first function called by the base ingester
        #
        # as input we have the manifest path. Need to use his parent for the product path
        #
        def createSourceProduct(self, processInfo):
            global debug,logger
            processInfo.srcPath=processInfo.srcPath.replace('\\','/')
            product = product_sciamachy.Product_Sciamachy(processInfo.srcPath)
            # test that filename is correct: test length
            if len(product.origName) != len(SOURCE_REF_NAME):
                    raise Exception("source filename has incorect format: bad length: %d vs %s" % (len(product.origName), len(SOURCE_REF_NAME)))
            #product.setDebug(1)
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
            # sip name
            namingConventionSip = NamingConvention(self.OUTPUT_SIP_PATTERN)
            #namingConventionSip.setDebug(1)
            eosipP.setNamingConventionSipInstance(namingConventionSip)

            # eo name
            namingConventionEo = NamingConvention_Envisat(self.OUTPUT_EO_PATTERN)
            #namingConventionEo.setDebug(1)
            eosipP.setNamingConventionEoInstance(namingConventionEo)
            # extension
            eosipP.setEoExtension("N1.gz")
            
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
        def extractMetadata(self,met,processInfo):
            # fill metadata object
            numAdded=processInfo.srcProduct.extractMetadata(met)

            # use method in base converter
            #met.setMetadataPair(metadata.METADATA_GENERATION_TIME, time.strftime('%Y-%m-%dT%H:%M:%SZ'))
            self.getGenerationTime(met)
            self.logger.debug("number of metadata added:%d" % numAdded)

            # keep some info
            mode = processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_SENSOR_OPERATIONAL_MODE)
            self.keepInfo("sensor mode", mode)
            sensor=processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_INSTRUMENT)
            self.keepInfo("instrument", sensor)

            # refine
            #processInfo.srcProduct.refineMetadata()
                
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
        def makeKmz(self, processInfo):
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
            ingester = Ingester_Sciamachy_l1b()
            #ingester.DEBUG=1
            exitCode = ingester.starts(sys.argv)

            out=StringIO()
            print >>out, "### Start of report\n"
            aReportMaker = reportMaker.ReportMaker()
            report = aReportMaker.makeReport(ingester)
            print >>out, "Spot5 take5 conversion report"
            print >>out, report
            print >>out, "### End of report"
            print out.getvalue()
            
            sys.exit(exitCode)
        else:
            print "syntax: python ingester_xxx.py -c configuration_file.cfg [-l list_of_product_file]"
            sys.exit(1)
            
    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
        sys.exit(99)
