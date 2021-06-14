#
# This is a specialized class that ingest Spot1-5 spotView dataset
#
# For Esa/ lite dissemination project
#
# Serco 04/2015
# Lavaux Gilles
#
# Changes:
# - 2020-09-xx: update for EoSip spec 1.8
# - 2018-09-xx: update for EoSip spec 1.5
# - 2018-03-20:
#    enable parent identifier in configuration: has fixed value
#    valid values for 'meter' is now 'm', 'degrees' is 'deg'
#
#
import os, sys, inspect
import time
import zipfile
import traceback
import shutil
from StringIO import StringIO


# add converter package path to sys.path 
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parrent=os.path.dirname(currentdir)
print "##### eoSip converter package dir:%s" % parrent
sys.path.insert(0, parrent)

#
from eoSip_converter.base import ingester, reportMaker
from eoSip_converter.esaProducts import product_EOSIP, product_spot_spotview
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip,formatUtils

from xml_nodes  import rep_footprint
from eoSip_converter.esaProducts.namingConvention import NamingConvention

import eoSip_converter.imageUtil as imageUtil
import eoSip_converter.xmlHelper as xmlHelper



# minimum config version that can be used
MIN_CONFIG_VERSION=1.0
VERSION="SpotView converter V:1.0.0"
REF_NAME='SP5_OPER_HRG__B__1A_20111025T090917_20111025T090926_000000_0092_0232.SIP.ZIP'


#
#
#
class ingester_spot_spotview(ingester.Ingester):


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
        #
        def beforeReportsDone(self, processInfo):
                processInfo.srcProduct.metadata.setMetadataPair(metadata.METADATA_PROCESSING_LEVEL, 'other: 2A')
                processInfo.destProduct.metadata.alterMetadataMaping('href', metadata.METADATA_FULL_PACKAGENAME)


        #
        # called after having done the various reports
        #
        def afterReportsDone(self, processInfo):
                self.alterReportXml(processInfo)
        
        #
        # called at the end of the doOneProduct
        # set use bounding box and browse already oriented flag
        # keep some info
        #
        def afterProductDone(self, processInfo):
                processInfo.srcProduct.metadata.setMetadataPair(metadata.METADATA_KMZ_USE_BOOUNDINGBOX, True)
                processInfo.srcProduct.metadata.setMetadataPair(metadata.METADATA_KMZ_DONT_REVERSE_BROWSE, True)
                self.keepInfo("METADATA_PROFILE", processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_PROFILE))
                self.keepInfo("GEOMETRIC_PROCESSING", processInfo.srcProduct.metadata.getMetadataValue('GEOMETRIC_PROCESSING'))
                self.keepInfo("METADATA_SENSOR_CODE", processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_SENSOR_CODE))


        #
        #
        #
        def alterReportXml(self, processInfo):
            #
            helper = xmlHelper.XmlHelper()
            helper.setData(processInfo.destProduct.productReport);
            helper.parseData()
            processInfo.addLog(" alterReportXml: product report parsed")
            if self.debug != 0:
                print " alterReportXml: product report parsed"

            # add namespace: <eop:operationalMode codeSpace=urn:esa:eop:SPOT:operationalMode
            aNode = helper.getFirstNodeByPath(None, 'procedure/EarthObservationEquipment/sensor/Sensor/operationalMode', None)
            helper.setNodeAttributeText(aNode, 'codeSpace', 'urn:esa:eop:SPOT:operationalMode')

            helper2 = xmlHelper.XmlHelper()
            helper2.setData(helper.prettyPrint());
            helper2.parseData()
            formattedXml = helper2.prettyPrintAll()
            if self.debug != 0:
                print " new XML: %s " % formattedXml
            fd = open(processInfo.destProduct.reportFullPath, 'w')
            fd.write(formattedXml)
            fd.flush()
            fd.close()
            processInfo.destProduct.productReport = formattedXml
            processInfo.addLog(" alterReportXml: product report changed at path:'%s'" % processInfo.destProduct.reportFullPath)
            # set AM timne if needed
            processInfo.destProduct.setFileAMtime(processInfo.destProduct.reportFullPath)


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
            dimapP = product_spot_spotview.Product_Spot_Spotview(processInfo.srcPath)
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
            
            self.logger.info(" Eo-Sip class created")
            processInfo.addLog("\n - Eo-Sip class created")
                    
        #
        # Override
        #
        def verifySourceProduct(self, processInfo):
                processInfo.addLog(" - verifying product: %s" % (processInfo.srcPath))
                self.logger.info(" verifying product")
                fh = open(processInfo.srcPath, 'rb')
                zf = zipfile.ZipFile(fh)
                ok = zf.testzip()
                fh.close()
                if ok is not None:
                        self.logger.error("  Zip file is corrupt:%s" % processInfo.srcPath)
                        self.logger.error("  First bad file in zip: %s" % ok)
                        processInfo.addLog("  => Zip file is corrupt:%s" % processInfo.srcPath)
                        raise Exception("Zip file is corrupt:%s" % processInfo.srcPath)
                else:
                    self.logger.info("  Zip file is ok")
                    processInfo.addLog("  => Zip file is ok")

            
        #
        # Override
        #
        def prepareProducts(self,processInfo):
                processInfo.addLog("\n - prepare product, will extract inside working folder:%s" % (processInfo.workFolder))
                self.logger.info(" prepare product")
                processInfo.srcProduct.extractToPath(processInfo.workFolder, processInfo.test_dont_extract)
                processInfo.addLog("  => extracted inside:%s" % (processInfo.workFolder))
                self.logger.info("  extracted inside:%s" % (processInfo.workFolder))


        #
        # Override
        #
        def extractMetadata(self, met, processInfo):
            processInfo.addLog("\n - will extract metadata from src product")
            self.logger.info(" will extract metadata from src product")
            # fill metadata object
            numAdded=processInfo.srcProduct.extractMetadata(met)
            size=processInfo.srcProduct.getSize()
            met.setMetadataPair(metadata.METADATA_PRODUCT_SIZE, size)
            # use method in base converter
            self.getGenerationTime(met)
            self.logger.debug("number of metadata added:%d" % numAdded)

            # set stop datetime = start datetime
            met.setMetadataPair(metadata.METADATA_STOP_DATE, met.getMetadataValue(metadata.METADATA_START_DATE))
            met.setMetadataPair(metadata.METADATA_STOP_TIME, met.getMetadataValue(metadata.METADATA_START_TIME))

            # extrack track frome from DATASET_ID. is like: SCENE 4 020-263 07/05/26 11:33:41 1 I
            # BUT there is also this info in the parent identifier: Dataset_Sources/Source_Information/SOURCE_ID like: 10223228810091145361X
            # SPOT has GRS (K, J) pair. J is lat. K is long. also track/frame
            # <S><KKK><JJJ><YY><MM><DD><HH><MM><SS><I><M>: 21 cars
            #    S is the satellite number
            #    KKK and JJJ are the GRS designator of the scene (lon, lat)
            #    YY, MM, DD, HH, MM, SS are the date and time of the center of the scene 
            #    I is the instrument number
            #    M is the spectral mode of acquisition

            # use parent identifier:
            try:
                parentId=met.getMetadataValue(metadata.METADATA_PARENT_PRODUCT)
                met.setMetadataPair(metadata.METADATA_TRACK, parentId[1:4])
                met.setMetadataPair(metadata.METADATA_FRAME, parentId[3:6])
                met.setMetadataPair(metadata.METADATA_WRS_LONGITUDE_GRID_NORMALISED, parentId[1:4])
                met.setMetadataPair(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, parentId[3:6])

                            
            except Exception, e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    print "Error %s  %s\n%s" %  (exc_type, exc_obj, traceback.format_exc())
                    processInfo.addLog("  => ERROR: %s  %s" %  (exc_type, exc_obj))
                    self.logger.info(" ERROR: %s  %s" %  (exc_type, exc_obj))
                    
            

            # TODO: to be removed
            # get additionnal metadata from optionnal dataProvider:we want the track and frame
            # dataProvider key are METADATA_TRACK or METADATA_FRAME
            productId=None
            if len(self.dataProviders)>0:
                    #print "@@@@@@@@@@@@@@@@@@@@ extract using dataProviders:%s" % self.dataProviders
                    #print "@@@@@@@@@@@@@@@@@@@@         key:%s" % met.getMetadataValue(metadata.METADATA_ORIGINAL_NAME)
                    # look the one for the mission
                    for item in self.dataProviders.keys():
                            processInfo.addLog("   also use data from data provider:%s" % item)
                            self.logger.info(" also use data from data provider:%s" % item)
                            #print "@@@@@@@@@@@@@@@@@@@@ doing dataProviders item:%s" % item
                            if item == metadata.METADATA_TRACK:  # fiel is mandatory
                                    # what value do we have?
                                    tmp = met.getMetadataValue(metadata.METADATA_TRACK)
                                    #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ current TRACK:%s" % tmp
                                    if tmp==None or tmp==sipBuilder.VALUE_NOT_PRESENT:
                                            #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ current TRACK is:%s" % tmp
                                            adataProvider=self.dataProviders[item]
                                            print "@@@@@@@@@@@@@@@@@@@@ dataProviders match TRACK:%s" % adataProvider
                                            # need to query using the product original filename like:N00-W075_AVN_20090804_PRO_0
                                            track=adataProvider.getRowValue(met.getMetadataValue(metadata.METADATA_ORIGINAL_NAME))
                                            print "@@@@@@@@@@@@@@@@@@@@ track:%s" % track
                                            if track != None and len(track.strip())==0:
                                                    track='0000'
                                            met.setMetadataPair(metadata.METADATA_TRACK, track)

                            elif item == metadata.METADATA_FRAME:  # fiel is mandatory
                                    # what value do we have?
                                    tmp = met.getMetadataValue(metadata.METADATA_FRAME)
                                    #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ current FRAME:%s" % tmp
                                    if tmp==None or tmp==sipBuilder.VALUE_NOT_PRESENT:
                                            print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ current FRAME is:%s" % tmp
                                            adataProvider=self.dataProviders[item]
                                            print "@@@@@@@@@@@@@@@@@@@@ dataProviders match FRAME:%s" % adataProvider
                                            # need to query using the product original filename like:N00-W075_AVN_20090804_PRO_0
                                            frame=adataProvider.getRowValue(met.getMetadataValue(metadata.METADATA_ORIGINAL_NAME))
                                            print "@@@@@@@@@@@@@@@@@@@@ frame:%s" % frame
                                            if frame != None and len(frame.strip())==0:
                                                    frame='0000'
                                            met.setMetadataPair(metadata.METADATA_FRAME, frame)

                            elif 1==2 and item == metadata.METADATA_PRODUCT_ID: # this is just a test, disabled now
                                    # what value do we have?
                                    tmp = met.getMetadataValue(metadata.METADATA_PRODUCT_ID)
                                    #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ current PRODUCT_ID:%s" % tmp
                                    if tmp==None or tmp==sipBuilder.VALUE_NOT_PRESENT:
                                            try:
                                                    #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ current PRODUCT_ID is:%s" % tmp
                                                    adataProvider=self.dataProviders[item]
                                                    print "@@@@@@@@@@@@@@@@@@@@ dataProviders match PRODUCT_ID:%s" % adataProvider
                                                    # need to query using the product original filename like:N00-W075_AVN_20090804_PRO_0
                                                    # productId is like: SP4-070526113337-9.HRI1_X__1P
                                                    productId=adataProvider.getRowValue(met.getMetadataValue(metadata.METADATA_ORIGINAL_NAME))
                                                    print "@@@@@@@@@@@@@@@@@@@@ productId:%s" % productId
                                                    if productId==None:
                                                            raise Exception("%s has no PRODUCT_ID in csv file" % met.getMetadataValue(metadata.METADATA_ORIGINAL_NAME))
                                                    if productId != None and len(productId.strip())==0:
                                                            productId='N/A'
                                                    met.setMetadataPair(metadata.METADATA_PRODUCT_ID, productId)
                                            except:
                                                    pass

            else:
                    print "no dataprovider"
                    #os._exit(1)
                                                    
            # refine
            processInfo.srcProduct.refineMetadata()



        #
        # Override
        # copy the source browse image into work folder, or for better quality generate the browse from the TIF image
        # construct the browse_metadatareport footprint block(BROWSE_CHOICE): it is the rep:footprint for spot
        #
        def makeBrowses(self,processInfo):
            processInfo.addLog("\n - will make browse")
            self.logger.info(" will make browse")
            try:
                    previewSrcPath=processInfo.srcProduct.preview_path
                    browseSrcPath=processInfo.srcProduct.imagery_path
                    browseExtension=definitions_EoSip.getBrowseExtension(0, definitions_EoSip.getDefinition('BROWSE_PNG_EXT'))
                    browseDestPath="%s/%s.%s" % (processInfo.destProduct.folder, processInfo.destProduct.eoProductName, browseExtension)
                    
                    # what we do depends of ptoduct processing level and platform id:
                    platformId=processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_PLATFORM_ID)
                    procLevel=processInfo.srcProduct.metadata.getMetadataValue(metadata.METADATA_PROCESSING_LEVEL)

                    # determine reduce ratio if we read from the product image (big tiff file)
                    ratio=-1
                    try:
                            w,h = imageUtil.get_image_size(browseSrcPath)
                            if self.debug!=0:
                                print "##############@@@@@@@@@@@@@@@@@@@################### product image dimension: w=%s h=%s" % (w,h)
                            if w>1000 or h>1000:
                                    if h>w:
                                            w=h
                                    ratio=int(100.0/(w/1000.0))
                                    if self.debug != 0:
                                        print "##############@@@@@@@@@@@@@@@@@@@################### reduce ratio:%s" % (ratio)
                            else:
                                    if self.debug != 0:
                                        print "##############@@@@@@@@@@@@@@@@@@@################### no reduce ratio because too small"
                    except:
                            print " ## warning: can not get product image dimension !!"
                            ratio=33

                    # transparent not needed for level 1A
                    ok=False
                    if processInfo.test_dont_do_browse!=True:
                            processInfo.addInfo("PLATFORM", platformId)
                            if platformId=='5':
                                    # copy source preview JPEG
                                    #shutil.copyfile(previewSrcPath, browseDestPath)
                                    # convert tp PNG
                                    if procLevel=='1A':
                                            if self.debug != 0:
                                                print "##############@@@@@@@@@@@@@@@@@@@################### create browse image from:%s" % previewSrcPath
                                            ok=imageUtil.makeBrowse("PNG", previewSrcPath, browseDestPath, -1, transparent=False)
                                    else:
                                            if self.debug != 0:
                                                print "##############@@@@@@@@@@@@@@@@@@@################### create browse image from:%s" % browseSrcPath
                                            ok=imageUtil.makeBrowse("PNG", browseSrcPath, browseDestPath, ratio, transparent=True)
                                    if self.debug != 0:
                                            print "##############@@@@@@@@@@@@@@@@@@@################### ok:%s" % ok
                                    if not ok:
                                            raise Exception("Error creating browse image")
                                    processInfo.addLog("  => preview image converted:%s" %  (browseDestPath))
                                    self.logger.info("  browse image copied:%s" % browseDestPath)
                                    
                            elif platformId=='4':
                                    #raise Exception("skip SPOT4")
                                    # copy source  preview JPEG
                                    #shutil.copyfile(previewSrcPath, browseDestPath)
                                    # convert tp PNG
                                    if procLevel=='1A':
                                            if self.debug != 0:
                                                print "##############@@@@@@@@@@@@@@@@@@@################### create browse image from:%s" % previewSrcPath
                                            ok=imageUtil.makeBrowse("PNG", previewSrcPath, browseDestPath, -1, transparent=False)
                                    else:
                                            if self.debug != 0:
                                                print "##############@@@@@@@@@@@@@@@@@@@################### create browse image from:%s" % browseSrcPath
                                            ok=imageUtil.makeBrowse("PNG", browseSrcPath, browseDestPath, ratio, transparent=True)
                                    if self.debug != 0:print "##############@@@@@@@@@@@@@@@@@@@################### ok:%s" % ok
                                    if not ok:
                                            raise Exception("Error creating browse image")
                                    processInfo.addLog("  => preview image converted:%s" %  (browseDestPath))
                                    self.logger.info("  browse image copied:%s" % browseDestPath)
                                    
                            else:  
                                    #raise Exception("skip SPOT1-3")
                                    # NEW: make a transparent jpeg, resize to 33% -> 1000*1000
                                    if procLevel=='1A':
                                            if self.debug != 0:
                                                print "##############@@@@@@@@@@@@@@@@@@@################### create browse image from:%s" % previewSrcPath
                                            ok=imageUtil.makeBrowse("PNG", previewSrcPath, browseDestPath, -1, transparent=False)
                                    else:
                                            if self.debug != 0:
                                                print "##############@@@@@@@@@@@@@@@@@@@################### create browse image from:%s" % browseSrcPath
                                            ok=imageUtil.makeBrowse("PNG", browseSrcPath, browseDestPath, ratio, transparent=True)
                                            if self.debug != 0:
                                            	    print "##############@@@@@@@@@@@@@@@@@@@################### ok:%s" % ok
                                    if self.debug != 0:
                                        print " ####@@@@#### MAKE BROWSE RETURNS:%s" % ok
                                    if not ok:
                                            raise Exception("Error creating browse image")
                                    processInfo.addLog("  => browse image created:%s" %  (browseDestPath))
                                    self.logger.info("  browse image created:%s" % browseDestPath)

                    processInfo.destProduct.addSourceBrowse(browseDestPath, [])
                    # set AM timne if needed
                    processInfo.destProduct.setFileAMtime(browseDestPath)

                    # create browse choice for browse metadata report
                    bmet=processInfo.destProduct.browse_metadata_dict[browseDestPath]
                    #print "######\n######\n%s" % dir(definitions_EoSip)

                    
                    footprintBuilder=rep_footprint.rep_footprint()
                    #
                    if self.debug != 0:
                        print "###\n###\n### BUILD BROWSE CHOICE FROM METADATA:%s" % (processInfo.destProduct.metadata.toString())
                    browseChoiceBlock=footprintBuilder.buildMessage(processInfo.destProduct.metadata, "rep:browseReport/rep:browse/rep:footprint").strip()
                    if self.debug!=0:
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
        # move a browse in the destination folder
        #
        def move_browse(self, processInfo, destPath):
                processInfo.addLog("\n - will move browse")
                self.logger.info("  will move browse")
                try:
                        if len(processInfo.destProduct.sourceBrowsesPath)>0:
                                tmp=os.path.split(processInfo.destProduct.sourceBrowsesPath[0])[1]
                                dest="%s/%s" % (destPath, tmp.split("/")[-1])
                                res=shutil.copyfile(processInfo.destProduct.sourceBrowsesPath[0], dest)
                                # set AM timne if needed
                                processInfo.destProduct.setFileAMtime(dest)
                                print "copy browse file into:%s/%s: res=%s" % dest

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
                        print " thumbnail creation Error"
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        traceback.print_exc(file=sys.stdout)
                        self.logger.info(" ERROR: %s  %s" %  (exc_type, exc_obj))
                        processInfo.addLog("  => ERROR: %s  %s" %  (exc_type, exc_obj))
                        processInfo.addLog("%s" %  (traceback.format_exc()))
                        #raise e



if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            ingester = ingester_spot_spotview()
            # ingester.DEBUG=1

            commandLineInfo = ingester.getCommandLineInfo()
            exitCode = ingester.starts(sys.argv)
            
            if 1==2:
            	    out=StringIO()
            	    print >> out, commandLineInfo
            	    print >>out, "### Start of report\n"
            	    aReportMaker = reportMaker.ReportMaker()
            	    report = aReportMaker.makeReport(ingester)
            	    print >>out, "Spot spotView conversion report"
            	    print >>out, report
            	    print >>out, "### End of report"
            	    #print out.getvalue()
            	    reportName = "Spot-spotview_conversion_report.txt"
            	    fd=open(reportName, 'w')
            	    fd.write(out.getvalue())
            	    fd.flush()
            	    fd.close()
            	    print "conversion report written well:%s" % reportName
            	    
            #
            ingester.makeConversionReport("Spot-spotview_conversion_report", '.')

            sys.exit(exitCode)
            
        else:
            print "syntax: python ingester_xxx.py -c configuration_file.cfg [-l list_of_product_file]"
            sys.exit(1)

    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
        sys.exit(2)
