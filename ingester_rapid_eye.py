#
# This is a specialized class that ingest rapideye dataset
#
# For Esa/ lite dissemination project
#
# Lavaux Gilles
#
# 2018-07: V: 0.1.1
#
#
# Changes:
# - 2018-09-06: fix type code which had incorect op mode==0
#
#
import os, sys, inspect
from datetime import datetime as dt, timedelta
import time
import zipfile
import traceback
import shutil
from cStringIO import StringIO
from PIL import Image


# add converter package path to sys.path 
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parrent=os.path.dirname(currentdir)
print "##### eoSip converter package dir:%s" % parrent
sys.path.insert(0, parrent)

#
from eoSip_converter.base import ingester, reportMaker
from eoSip_converter.esaProducts import product_rapid_eye, product_EOSIP
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip, formatUtils, valid_values

from xml_nodes import rep_footprint, sipBuilder
from eoSip_converter.esaProducts.namingConvention_hightres import NamingConvention_HightRes

import eoSip_converter.imageUtil as imageUtil
import eoSip_converter.fileHelper as fileHelper
import eoSip_converter.xmlHelper as xmlHelper




# minimum config version that can be use
MIN_CONFIG_VERSION=1.0
VERSION="Rapie-Eye converter V:1.0.0 2019-05-14"

# for verification
REF_NAME='RE__OPER_MSI_IMG_3A_20140623T162849_S08-137_W079-148_4140.SIP.ZIP'


#
#
#
class ingester_rapid_eye(ingester.Ingester):

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
        # called before doing the various reports
        # # change the mapping of href to METADATA_PACKAGENAME
        #
        def beforeReportsDone(self, processInfo):
            # change platform identifier from fixed '_' to  'RE-1'
            tmp = processInfo.destProduct.metadata.getMetadataValue('platFormSerialIdentifier')
            processInfo.destProduct.metadata.setMetadataPair(metadata.METADATA_PLATFORM_ID, tmp)

            processInfo.destProduct.metadata.alterMetadataMaping('href', metadata.METADATA_FULL_PACKAGENAME)
            # remove extension from  product name, will be set in <ows:ServiceReference xlink:href="PR1_OPER_CHR_MO1_1P_20161024T130000_N33-072_E035-084_0001">
            #processInfo.srcProduct.metadata.setMetadataPair(metadata.METADATA_PRODUCTNAME, processInfo.destProduct.eoProductName.split('.')[0])

        #
        # called after having done the various reports
        #
        def afterReportsDone(self, processInfo):
                #
                self.alterReportXml(processInfo)

                # build piece list
                n=0
                newContentList=[]
                for path in processInfo.srcProduct.contentList:
                    print " @@@@@ check contentList[%s]:%s" % (n, path)
                    piece = product_EOSIP.EoPiece(os.path.basename(path))
                    piece.alias = os.path.basename(path)
                    piece.localPath = path
                    newContentList.append(piece.alias)
                    processInfo.destProduct.addPiece(piece)
                    n+=1
                processInfo.srcProduct.contentList=newContentList


        #
        # add namespace in: <eop:operationalMode "
        #
        def alterReportXml(self, processInfo) :
            helper = xmlHelper.XmlHelper()
            helper.setData(processInfo.destProduct.productReport)
            helper.parseData()
            processInfo.addLog(" alterReportXml: product report parsed")
            if self.debug!=0:
                print " alterReportXml: product report parsed"

            # add namespace:
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
            # set AM time if needed
            processInfo.destProduct.setFileAMtime(processInfo.destProduct.reportFullPath)
            processInfo.destProduct.productReport = formattedXml
            processInfo.addLog(" alterReportXml: product report changed at path:'%s'" % processInfo.destProduct.reportFullPath)


        #
        # called at the end of the doOneProduct, before the index/shopcart creation
        #
        #
        def afterProductDone(self, processInfo):
            pass


        #
        #
        #
        def buildEoNames(self, processInfo, namingConvention=None):

            # force setEoExtension to ZIP. Because we use SRC_PRODUCT_AS_DIR to use several files as input, and we want a .SIP.ZIP package.
            processInfo.destProduct.setEoExtension(definitions_EoSip.getDefinition('PACKAGE_EXT'))
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
            dimapP = product_rapid_eye.Product_RapidEye(processInfo.srcPath)
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
            namingConventionSip = NamingConvention_HightRes(self.OUTPUT_SIP_PATTERN)
            eosipP.setNamingConventionSipInstance(namingConventionSip)
            eosipP.setNamingConventionEoInstance(namingConventionSip)
            
            self.logger.info(" Eo-Sip class created")
            processInfo.addLog("\n - Eo-Sip class created")
                    
        #
        # Override
        #
        def verifySourceProduct(self, processInfo):
                processInfo.addLog(" - verifying product: %s" % (processInfo.srcPath))
                self.logger.info(" verifying product")

            
        #
        # Override
        #
        def prepareProducts(self, processInfo):
                processInfo.addLog("\n - prepare product, will extract inside working folder:%s" % (processInfo.workFolder))
                self.logger.info(" prepare product")
                processInfo.srcProduct.extractToPath(processInfo.workFolder, processInfo.test_dont_extract)
                processInfo.addLog("  => extracted inside:%s" % (processInfo.workFolder))
                self.logger.info("  extracted inside:%s" % (processInfo.workFolder))

                self.stretcherAppExe = self.ressourcesProvider.getRessourcePath('stretchAppExe')
                processInfo.srcProduct.stretcherAppExe = self.stretcherAppExe




        #
        # Override
        #
        def extractMetadata(self,met,processInfo):
            processInfo.addLog("\n - will extract metadata from src product")
            self.logger.info(" will extract metadata from src product")
            # fill metadata object
            numAdded=processInfo.srcProduct.extractMetadata(met)

            #size=processInfo.srcProduct.getSize()
            #met.setMetadataPair(metadata.METADATA_PRODUCT_SIZE, size)

            # use method in base converter
            self.getGenerationTime(met)
            self.logger.debug("number of metadata added:%d" % numAdded)

            # refine
            processInfo.srcProduct.refineMetadata(processInfo)




        #
        # Override
        # copy the source browse image into work folder, or for better quality generate the browse from the TIF image
        # construct the browse_metadatareport footprint block(BROWSE_CHOICE): it is the rep:footprint for spot
        #
        def makeBrowses(self, processInfo):
            processInfo.addLog("\n - will make browse")
            self.logger.info(" will make browse")
            try:
                    browseSrcPath=processInfo.srcProduct.imageSrcPath
                    browseExtension=definitions_EoSip.getBrowseExtension(0, definitions_EoSip.getDefinition('BROWSE_PNG_EXT'))
                    browseDestPath="%s/%s.%s" % (processInfo.destProduct.folder, processInfo.destProduct.eoProductName, browseExtension)

                    if processInfo.srcProduct.newFormatFlag:
                        processInfo.srcProduct.browseDestPath = browseDestPath
                        processInfo.srcProduct.makeBrowses(processInfo)
                    else:
                        if 1==2:
                            if processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_ORBIT_DIRECTION) == 'ASCENDING':
                                imageUtil.makeBrowse('PNG', browseSrcPath, "%s_flipped" % browseDestPath)
                                img = Image.open("%s_flipped" % browseDestPath)
                                img2 = img.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
                                img2.save(browseDestPath)
                            else:
                                imageUtil.makeBrowse('PNG', browseSrcPath, browseDestPath)
                        else:
                            imageUtil.makeBrowse('PNG', browseSrcPath, browseDestPath)



                    processInfo.destProduct.addSourceBrowse(browseDestPath, [])
                    processInfo.addLog("  browse image added: name=%s; path=%s" % (processInfo.destProduct.eoProductName, browseDestPath))

                    # set atime and mtime to self.generationTime
                    # set AM time if needed
                    processInfo.destProduct.setFileAMtime(browseDestPath)
                    #aFileHelper = fileHelper.FileHelper()
                    #aFileHelper.setAMtime(browseDestPath, self.generationTime, self.generationTime)

                    # create browse choice for browse metadata report
                    bmet=processInfo.destProduct.browse_metadata_dict[browseDestPath]

                    
                    footprintBuilder=rep_footprint.rep_footprint()
                    #
                    print "###\n###\n### BUILD BROWSE CHOICE FROM METADATA:%s" % (processInfo.destProduct.metadata.toString())
                    browseChoiceBlock=footprintBuilder.buildMessage(processInfo.destProduct.metadata, "rep:browseReport/rep:browse/rep:footprint").strip()
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
                    processInfo.addLog("  => ERROR: %s  %s" %  (exc_type, exc_obj))
                    self.logger.info(" ERROR: %s  %s" %  (exc_type, exc_obj))
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
                processInfo.addLog("\n - will output eoSip; basePath=%s" %  (basePath))
                self.logger.info(" will output eoSip; basePath=%s" %  (basePath))
                # copy eoSip in first path
                # make links in other paths
                outputProductResolvedPaths = processInfo.destProduct.getOutputFolders(basePath, pathRules)
                if len(outputProductResolvedPaths)==0:
                        processInfo.addLog("   ERROR: no product resolved path")
                        self.logger.info(" ERROR: no product resolved path")
                        raise Exception("no product resolved path")
                else:
                        # output in first path
                        firstPath=outputProductResolvedPaths[0]
                        processInfo.addLog("  Eo-Sip product will be writen in folder:%s" %  (firstPath))
                        self.logger.info("  Eo-Sip product will be writen in folder:%s" %  (firstPath))
                        productPath = processInfo.destProduct.writeToFolder(firstPath, overwrite)
                        processInfo.addLog("  ok, writen well\n%s" % processInfo.destProduct.info())
                        self.logger.info(" ok, writen well\n%s" % processInfo.destProduct.info())
                        processInfo.addIngesterLog("  write done:%s" % processInfo.destProduct.path, 'PROGRESS')

                        # make a thumbnail FOR TEST
                        if processInfo.create_thumbnail==1:
                                self.make_thumbnail(processInfo, firstPath)
                                # move also browse image
                                self.move_browse(processInfo, firstPath)

                        # output link in other path
                        i=0
                        for item in outputProductResolvedPaths:
                                if i>0:
                                        otherPath="%s" % (item)
                                        self.logger.info("  create also (linked?) eoSip product at tree path[%d] is:%s" %(i, item))
                                        processInfo.addLog("  create also (linked?) eoSip product at tree path[%d] is:%s" %(i, item))
                                        processInfo.destProduct.writeToFolder(basePath, overwrite)
                                        processInfo.addLog("  Eo-Sip product link writen in folder[%d]:%s\n" %  (i, otherPath))
                                        self.logger.info("  Eo-Sip product link writen in folder[%d]:%s\n" %  (i, otherPath))
                                i=i+1

                self.logger.info("  done")
                return productPath


        #
        # move a browse in the destination fodler
        #
        def move_browse(self, processInfo, destPath):
                processInfo.addLog("\n - will move browse")
                self.logger.info("  will move browse")
                try:
                        if len(processInfo.destProduct.sourceBrowsesPath)>0:
                                tmp=os.path.split(processInfo.destProduct.sourceBrowsesPath[0])[1]
                                res=shutil.copyfile(processInfo.destProduct.sourceBrowsesPath[0], "%s/%s" % (destPath, tmp.split("/")[-1]))
                                print "copy browse file into:%s/%s: res=%s" % (destPath, tmp.split("/")[-1], res)

                except Exception, e:
                        print " browse move Error"
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        traceback.print_exc(file=sys.stdout)
                        self.logger.info(" ERROR: %s  %s" %  (exc_type, exc_obj))
                        processInfo.addLog("  => ERROR: %s  %s" %  (exc_type, exc_obj))
                        processInfo.addLog("%s" %  (traceback.format_exc()))
                                
        #
        # make a thumbnail in the destination fodler
        #
        def make_thumbnail(self, processInfo, destPath):
                # make a thumbnail FOR TEST
                processInfo.addLog("\n - will make thumbnail")
                self.logger.info("  will make thumbnail")
                try:
                        if len(processInfo.destProduct.sourceBrowsesPath)>0:
                                tmp=os.path.split(processInfo.destProduct.sourceBrowsesPath[0])[1]
                                tmpb=tmp.split('.')[-1:]
                                tmpa=tmp.split('.')[0:-1]
                                thumbnail = "%s.TN.%s" % (".".join(tmpa),".".join(tmpb))
                                processInfo.destProduct.metadata.setMetadataPair(metadata.METADATA_THUMBNAIL,thumbnail)
                                thumbnail="%s/%s" % (destPath, thumbnail)
                                imageUtil.makeBrowse('JPG', "%s" % (processInfo.destProduct.sourceBrowsesPath[0]), thumbnail, 25 )
                                print "builded thumbnail file:  destPath=%s" % destPath
                                print "builded thumbnail file:  tmp=%s ==> %s/%s_TN.%s" % (tmp,destPath,tmpa,tmpb)
                                self.logger.info("builded thumbnail file:%s/%s_TN.%s" % (destPath,tmpa,tmpb))
                                processInfo.addLog("builded thumbnail file:%s/%s_TN.%s" % (destPath,tmpa,tmpb))
                        
                        else:
                                print "there is no browse so no thumbnail to create in final folder"
                                self.logger.info(" no browse available, so no thumbnail...")
                                processInfo.addLog("  => no browse available, so no thumbnail...")
                                
                except Exception, e:
                        print " thubnail creation Error"
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        traceback.print_exc(file=sys.stdout)
                        self.logger.info(" ERROR: %s  %s" %  (exc_type, exc_obj))
                        processInfo.addLog("  => ERROR: %s  %s" %  (exc_type, exc_obj))
                        processInfo.addLog("%s" %  (traceback.format_exc()))
                        #raise e




if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            ingester = ingester_rapid_eye()

            commandLineInfo = ingester.getCommandLineInfo()
                        
            exitCode = ingester.starts(sys.argv)

            out=StringIO()
            print >> out, commandLineInfo
            print >>out, "### Start of report\n"
            aReportMaker = reportMaker.ReportMaker()
            report = aReportMaker.makeReport(ingester)
            print >>out, "rapid-eye conversion report"
            print >>out, report
            print >>out, "### End of report"
            #print out.getvalue()
            reportName = "Rapid-Eye_conversion_report.txt"
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
