# -*- coding: cp1252 -*-
#
# this class represent a planetscope directory product
# 
# Supported types
"""
• PS2_BA3_1B: 3-band Analytic Basic Scene level 1B
• PS2_BA4_1B: 4-band Analytic Basic Scene level 1B
• PS2_VIS_3B: 3-band Visual Ortho Scene level 3B
• PS2_AN3_3B: 3-band Analytic Ortho Scene level 3B
• PS2_AN4_3B: 4-band Analytic Ortho Scene level 3B
• PS2_VIS_3A: 3-band Visual Ortho Tile level 3A
• PS2_AN4_3A: 4-band Analytic Ortho Tile level 3A
"""
#
import os, sys, inspect
import logging
import zipfile
import re
import shutil
from subprocess import call,Popen, PIPE

#
import eoSip_converter.xmlHelper as xmlHelper
import eoSip_converter.fileHelper as fileHelper
import eoSip_converter.geomHelper as geomHelper
import eoSip_converter.imageUtil as imageUtil

#from product import Product
from product_directory import Product_Directory
from xml_nodes import sipBuilder
from xml_nodes import rep_footprint
import product_EOSIP
from browseImage import BrowseImage
import browse_metadata
import metadata
import formatUtils
import json


# gdal commands
GDAL_3B_STEP_0='gdal_translate -b 1 -outsize 20% 20% @SRC @DEST1'
GDAL_3B_STEP_1='gdal_translate -b 2 -outsize 20% 20% @SRC @DEST2'
GDAL_3B_STEP_2='gdal_translate -b 3 -outsize 20% 20% @SRC @DEST3'
# no resize
GDAL_3B_STEP_N0='gdal_translate -b 1 @SRC @DEST1'
GDAL_3B_STEP_N1='gdal_translate -b 2 @SRC @DEST2'
GDAL_3B_STEP_N2='gdal_translate -b 3 @SRC @DEST3'

GDAL_STEP_3='gdal_merge.py -co "PHOTOMETRIC=rgb" -separate @DEST1 @DEST2 @DEST3 -o @DEST4'
GDAL_STEP_4='gdal_translate @DEST4 -scale 0 2048 -ot Byte @DEST5'

GM_STEP_1='gm convert @SRC -transparent black @DEST'


# for verification
REF_TYPECODE={'PS2_BA3_1B',
              'PS2_BA4_1B',
              'PS2_VIS_3B',
              'PS2_AN3_3B',
              'PS2_AN4_3B',
              'PS2_VIS_3A',
              'PS2_AN4_3A'}

WITH_BOUNDINGBOX=['PS2_VIS_3B',
                  'PS2_AN3_3B',
                  'PS2_AN4_3B',
                  'PS2_VIS_3A',
                  'PS2_AN4_3A']

BROWSE_SUFFIX="_visual.tif"
OTHER_BROWSE_CANDIDATE_SUFFIX="_analytic.tif"
OTHER_BROWSE_CANDIDATE2_SUFFIX="_analyticms.tif"
XML_SUFFIX=".xml"

# constants:
BEGIN_POSITION='beginPosition'
END_POSITION='endPosition'
LEVEL='level'
ORBIT_DIRECTION='orbit_direction'

#
#
#
def writeShellCommand(command, testExit=False, badExitCode=-1):
    tmp = "%s\n" % command
    if testExit:
        tmp = "%sif [ $? -ne 0 ]; then\n  exit %s\nfi\n"% (tmp, badExitCode)
    return tmp



class Product_Planetscope(Product_Directory):


    jsonMapping={
        metadata.METADATA_START_DATE_TIME: "['properties']['acquired']",
        metadata.METADATA_CLOUD_COVERAGE: "['properties']['cloud_cover']",
        metadata.METADATA_FOOTPRINT:"['geometry']['coordinates']",
        metadata.METADATA_SUN_ELEVATION:"['properties']['sun_elevation']",
        metadata.METADATA_SUN_AZIMUTH: "['properties']['sun_azimuth']",
        metadata.METADATA_INSTRUMENT_INCIDENCE_ANGLE:"['properties']['view_angle']",
        #'sun_elevation':"['properties']['sun_elevation']",
        #'sun_azimuth': "['properties']['sun_azimuth']",
        #'incidence_angle':"['properties']['view_angle']",
        metadata.METADATA_RESOLUTION:"['properties']['pixel_resolution']"
    }

    xmlMapping={BEGIN_POSITION:'validTime/TimePeriod/beginPosition',
                END_POSITION:'validTime/TimePeriod/endPosition',
                LEVEL: 'metaDataProperty/EarthObservationMetaData/productType',
                ORBIT_DIRECTION: 'using/EarthObservationEquipment/acquisitionParameters/Acquisition/orbitDirection',
                metadata.METADATA_SOFTWARE_NAME: 'metaDataProperty/EarthObservationMetaData/processing/ProcessingInformation/processorName',
                metadata.METADATA_SOFTWARE_VERSION: 'metaDataProperty/EarthObservationMetaData/processing/ProcessingInformation/processorVersion',
                metadata.METADATA_NATIVE_PRODUCT_FORMAT: 'metaDataProperty/EarthObservationMetaData/processing/ProcessingInformation/nativeProductFormat',

                #metadata.METADATA_INSTRUMENT_INCIDENCE_ANGLE: 'using/EarthObservationEquipment/acquisitionParameters/Acquisition/incidenceAngle',
                #metadata.METADATA_SUN_AZIMUTH: 'using/EarthObservationEquipment/acquisitionParameters/Acquisition/illuminationAzimuthAngle',
                #metadata.METADATA_SUN_ELEVATION: 'using/EarthObservationEquipment/acquisitionParameters/Acquisition/illuminationElevationAngle',
                }

    #
    #
    #
    def __init__(self, path=None):
        Product_Directory.__init__(self, path)
        self.metadata_path=path
        fd=open(path, 'r')
        self.metadata_content = json.load(fd)
        fd.close()

        #
        self.preview_path=None
        self.other_preview_path=None
        self.other_preview2_path=None
        self.additionnalMetadata=None

        #
        self.useBbox=False

        #
        self.productFolderName = os.path.basename(os.path.dirname(self.path))

        self.EO_FOLDER = os.path.dirname(path)

        if self.debug!=0:
            print " init class Skysat"



    #
    # read matadata file
    #
    def getMetadataInfo(self, index=0):
        pass


    #
    #
    #
    def makeBrowseFromTif(self, aTifPath, anDestpath, anAlias, processInfo):
        print(" makeBrowseFromTif; src: %s" % aTifPath)
        resize=True
        ratio = 1
        w,h = imageUtil.get_image_size(aTifPath)
        if w==1 or h==1:
            resize = False
        if resize and w <1600 and h<1600:
            resize = False
        if resize:
            maxd = w if w>h else h
            ratio = 1600.0/maxd
        print(" source .tif size: w=%s h=%s; resize:%s, ratio=%s" % (w,h,resize, ratio))

        if resize:
            command = GDAL_3B_STEP_0.replace('@SRC', aTifPath)
            command1 = command.replace('@DEST1', "%s/%s_b1.tif" % (processInfo.workFolder, anAlias))
            command = GDAL_3B_STEP_1.replace('@SRC', aTifPath)
            command2 = command.replace('@DEST2', "%s/%s_b2.tif" % (processInfo.workFolder, anAlias))
            command = GDAL_3B_STEP_2.replace('@SRC', aTifPath)
            command3 = command.replace('@DEST3', "%s/%s_b3.tif" % (processInfo.workFolder, anAlias))
        else:
            command = GDAL_3B_STEP_N0.replace('@SRC', aTifPath)
            command1 = command.replace('@DEST1', "%s/%s_b1.tif" % (processInfo.workFolder, anAlias))
            command = GDAL_3B_STEP_N1.replace('@SRC', aTifPath)
            command2 = command.replace('@DEST2', "%s/%s_b2.tif" % (processInfo.workFolder, anAlias))
            command = GDAL_3B_STEP_N2.replace('@SRC', aTifPath)
            command3 = command.replace('@DEST3', "%s/%s_b3.tif" % (processInfo.workFolder, anAlias))

        # @DEST1 @DEST2 @DEST3 -o @DEST4
        command4 = GDAL_STEP_3.replace('@DEST1', "%s/%s_b1.tif" % (processInfo.workFolder, anAlias)).replace('@DEST2', "%s/%s_b2.tif" % (processInfo.workFolder, anAlias)).replace('@DEST3', "%s/%s_b3.tif" % (processInfo.workFolder, anAlias))
        command4 = command4.replace('@DEST4', "%s/%s_bmerged.tif" % (processInfo.workFolder, anAlias))

        # no scale done
        #command5 = GDAL_STEP_4.replace('@DEST4', "%s_bmerged.tif" % (anAlias)).replace('@DEST5', "%s_merged.tif" % (anAlias))

        # PNG transparent + use stretcherApp
        command5 = "%s -transparent %s/%s_bmerged.tif %s/%s_transparent.png 0xff000000" % (
            self.stretcherApp, processInfo.workFolder, anAlias, processInfo.workFolder, anAlias)

        command6 = "%s -stretch %s/%s_transparent.png %s/%s_stretched.png 0.01" % (
            self.stretcherApp, processInfo.workFolder, anAlias, processInfo.workFolder, anAlias)

        command7 = "%s -autoBrighten %s/%s_stretched.png %s 85" % (
            self.stretcherApp, processInfo.workFolder, anAlias, anDestpath)

        #commands = "%s%s%s%s%s" % (
        commands = "%s%s%s%s%s%s%s" % (
            writeShellCommand(command1, True), writeShellCommand(command2, True), writeShellCommand(command3, True),
            #writeShellCommand(command4, True), writeShellCommand(command5, True))
            writeShellCommand(command4, True), writeShellCommand(command5, True), writeShellCommand(command6, True),  writeShellCommand(command7, True))
        commands = "%s\necho\necho\necho 'browse aliased: %s done at path: %s'" % (commands, anAlias, anDestpath)

        commandFile = "%s/command_%s.sh" % (processInfo.workFolder, anAlias)
        fd = open(commandFile, 'w')
        fd.write(commands)
        fd.close()
        #os._exit(1)

        # launch the main make_browse script:
        command="/bin/bash -i -f %s 2>&1 | tee %s/make_browses.stdout" % (commandFile,  processInfo.workFolder)
        retval = call(command, shell=True)
        print "  external make browse exit code:%s" % retval
        processInfo.addLog("  external make browse exit code:%s" % retval)
        if retval !=0:
            raise Exception("Error generating browse, exit coded:%s" % retval)

        return "%s/%s_final.png" % (processInfo.workFolder, anAlias)

    #
    #
    #
    def makeBrowses(self, processInfo):
        anEosip = processInfo.destProduct
        browseName = processInfo.destProduct.getEoProductName()
        self.browseDestPath="%s/%s.BI.PNG" % (processInfo.workFolder, browseName)

        if self.preview_path is not None:
            resize=True
            ratio = 1
            w,h = imageUtil.get_image_size(self.preview_path)
            if w==1 or h==1:
                resize = False
            if resize and w <1600 and h<1600:
                resize = False
            if resize:
                maxd = w if w>h else h
                ratio = 1600.0/maxd
            print(" source .tif size: w=%s h=%s; resize:%s, ratio=%s" % (w,h,resize, ratio))
            imageUtil.makeBrowse("PNG", self.preview_path, self.browseDestPath, resizePercent=ratio*100.0, transparent=True)
        else:
            if self.other_preview_path is None and self.other_preview2_path is None:
                raise Exception("no .tif found for browse generation")
            if self.other_preview_path is not None:
                aDest = self.makeBrowseFromTif(self.other_preview_path, self.browseDestPath, 'analytic', processInfo)
            else:
                aDest = self.makeBrowseFromTif(self.other_preview2_path, self.browseDestPath, 'analyticMs', processInfo)


        # set AM time if needed
        anEosip.setFileAMtime(self.browseDestPath)
        processInfo.destProduct.addSourceBrowse(self.browseDestPath, [])
        processInfo.addLog(" browse image added: name=%s; path=%s" % (browseName, self.browseDestPath))

        # create browse choice for browse metadata report
        bmet = anEosip.browse_metadata_dict[self.browseDestPath]
        if self.debug != 0:
            print "###\n###\n### BUILD BROWSE CHOICE FROM BROWSE METADATA:%s" % (bmet.toString())

        reportBuilder = rep_footprint.rep_footprint()
        #
        if self.debug != 0:
            print "###\n###\n### BUILD BROWSE CHOICE FROM METADATA:%s" % (anEosip.metadata.toString())
        browseChoiceBlock = reportBuilder.buildMessage(anEosip.metadata,
                                                       "rep:browseReport/rep:browse/rep:footprint").strip()
        if self.debug != 0:
            print "browseChoiceBlock :%s" % (browseChoiceBlock)
        bmet.setMetadataPair(browse_metadata.BROWSE_METADATA_BROWSE_CHOICE, browseChoiceBlock)

        # set the browse type (if not default one(i.e. product type code))for the product metadata report BROWSES block
        # if specified in configuration
        tmp = self.metadata.getMetadataValue(metadata.METADATA_BROWSES_TYPE)
        if tmp != None:
            bmet.setMetadataPair(metadata.METADATA_BROWSES_TYPE, tmp)

        # idem for METADATA_CODESPACE_REFERENCE_SYSTEM
        tmp = self.metadata.getMetadataValue(metadata.METADATA_CODESPACE_REFERENCE_SYSTEM)
        if tmp != None:
            bmet.setMetadataPair(metadata.METADATA_CODESPACE_REFERENCE_SYSTEM, tmp)

        processInfo.addLog(" browse image choice created:browseChoiceBlock=\n%s" % (browseChoiceBlock))


    #
    # extract the spot 6 7 interresting piece in working folder:
    # - metadata xml
    # - preview images
    #
    def extractToPath(self, folder=None, dont_extract=False):
        if not os.path.exists(folder):
            raise Exception("destination fodler does not exists:%s" % folder)
        if self.debug!=0:
            print " will exttact directory product '%s' to path:%s" % (self.path, folder)

        self.contentList=[]
        self.EXTRACTED_PATH=folder


        # keep list of content
        self.contentList = []
        #
        self.num_preview=0
        #
        n = 0
        for root, dirs, files in os.walk(self.EO_FOLDER, topdown=False):
            aLevel=None
            for name in files:
                n = n + 1
                eoFile = "%s/%s" % (root, name)
                print " ## product content[%d]:'%s' in:%s" % (n, name, eoFile)

                if name.lower().endswith(BROWSE_SUFFIX):
                    self.preview_path = eoFile
                    shutil.copyfile(self.preview_path, "%s/%s" % (folder, name))
                    print(" ## FOUND self.preview_path=%s" % self.preview_path)
                elif name.lower().endswith(OTHER_BROWSE_CANDIDATE_SUFFIX):
                    self.other_preview_path  = eoFile
                    shutil.copyfile(self.other_preview_path, "%s/%s" % (folder, name))
                    print(" ## FOUND self.other_preview_path=%s" % self.other_preview_path)
                elif name.lower().endswith(OTHER_BROWSE_CANDIDATE2_SUFFIX):
                    self.other_preview2_path  = eoFile
                    shutil.copyfile(self.other_preview2_path, "%s/%s" % (folder, name))
                    print(" ## FOUND self.other_preview2_path=%s" % self.other_preview2_path)
                elif name.lower().endswith(XML_SUFFIX):
                    tmpLevel = self.checkLevelOnTheFly(eoFile)
                    print(" ##################### FOUND xml file with product level=%s, ref level=%s" % (tmpLevel, aLevel))
                    if tmpLevel is None:
                        raise Exception("product level not found in xml file: %s" % eoFile)
                    if aLevel is not None and aLevel!=tmpLevel:
                        raise Exception("product level mismatch: '%s' and '%s'" % (aLevel, tmpLevel))
                    aLevel=tmpLevel
                    self.additionnalMetadata  = eoFile
                    shutil.copyfile(self.additionnalMetadata, "%s/%s" % (folder, name))
                    print(" ## FOUND self.additionnalMetadata=%s" % self.additionnalMetadata)


    #
    #
    #
    def checkLevelOnTheFly(self, aPath):
        aValue=None
        fd=open(aPath, 'r')
        metContent=fd.read()
        fd.close()
        helper=xmlHelper.XmlHelper()
        helper.setData(metContent);
        helper.parseData()
        aData = helper.getFirstNodeByPath(None, self.xmlMapping[LEVEL], None)
        if aData is not None:
            aValue = helper.getNodeText(aData)
        return aValue

    #
    #
    #
    def extractAdditionalInfo(self):
        fd=open(self.additionnalMetadata, 'r')
        metContent=fd.read()
        fd.close()
        helper=xmlHelper.XmlHelper()
        #helper.setDebug(1)
        helper.setData(metContent);
        helper.parseData()

        num_added = 0
        for field in self.xmlMapping:
            if self.xmlMapping[field].find("@") >= 0:
                attr = self.xmlMapping[field].split('@')[1]
                path = self.xmlMapping[field].split('@')[0]
            else:
                attr = None
                path = self.xmlMapping[field]

            aData = helper.getFirstNodeByPath(None, path, None)
            if aData == None:
                aValue = None
            else:
                if attr == None:
                    aValue = helper.getNodeText(aData)
                else:
                    aValue = helper.getNodeAttributeText(aData, attr)

            if self.debug != 0:
                print "  -->%s=%s" % (field, aValue)
            self.metadata.setMetadataPair(field, aValue)
            num_added = num_added + 1

    #
    #
    #
    def extractMetadata(self, met=None, processInfo=None):
        if met==None:
            raise Exception("metadate is None")

        if len(self.metadata_content)==0:
            raise Exception("no metadata to be parsed")

        

        # save metadata to workfolder for test purpose:
        destPath = "%s/%s" % (processInfo.workFolder, os.path.basename(self.path))
        shutil.copyfile(self.path, destPath)

        numAdded = 0
        jsonMetadata = self.metadata_content
        for key in self.jsonMapping:
            mapping = self.jsonMapping[key]
            try:
                print(" extracted metadata '%s' using mapping: '%s'" % (key, mapping))
                value = eval("self.metadata_content%s" % mapping)
                print("  extracted metadata '%s' value: '%s'" % (key, value))
                met.setMetadataPair(key, value)
                numAdded==1
            except:
                print(" !! metadata not found: '%s' using mapping: '%s'" % (key, mapping))

        self.metadata = met

        #
        self.extractAdditionalInfo()

        #
        self.refineMetadata(processInfo)

        #
        self.extractFootprint(processInfo)

        #
        self.buildTypeCode(processInfo)

        # set local attribute for the one with boundingbox
        tmp = self.metadata.getMetadataValue(metadata.METADATA_TYPECODE)
        if tmp in WITH_BOUNDINGBOX:
            self.useBbox=True
            processInfo.addLog("## have boundingBox:%s" % tmp)
            self.metadata.addLocalAttribute("boundingBox", self.browseIm.getBoundingBox())
        else:
            processInfo.addLog("## have NO boundingBox:%s" % tmp)




    #
    # refine the metada
    #
    def refineMetadata(self, processInfo):
        # set size to product_EOSIP.PRODUCT_SIZE_NOT_SET: we want to get the EoPackage zip size, which will be available only when
        # the EoSip package will be constructed. in EoSipProduct.writeToFolder().
        # So we mark it and will substitute with good value before product report write
        self.metadata.setMetadataPair(metadata.METADATA_PRODUCT_SIZE, product_EOSIP.PRODUCT_SIZE_NOT_SET)

        # maybe also in the xml file, which has start + stop. If present, use them
        # like: 2017-02-04T20:24:10+00:00
        start = self.metadata.getMetadataValue(BEGIN_POSITION)
        stop = self.metadata.getMetadataValue(END_POSITION)
        print("start=%s; stop=%s" % (start, stop))
        if start is not None and stop is not None:
            pos = start.find('+')
            msec=".000"
            if pos > 0:
                start = start[0:pos] + msec +"Z"
            else:
                raise Exception("unexpected start datetime format: no +: '%s'" % start)
            print("## START:%s" % start)
            self.metadata.setMetadataPair(metadata.METADATA_START_DATE_TIME, start)
            self.metadata.setMetadataPair(metadata.METADATA_START_DATE, start.split("T")[0])
            self.metadata.setMetadataPair(metadata.METADATA_START_TIME, start.split("T")[1].split('.')[0] + msec)

            #
            pos = stop.find('+')
            msec=".000"
            if pos > 0:
                stop = stop[0:pos] + msec +"Z"
            else:
                raise Exception("unexpected stop datetime format: no +: '%s'" % stop)
            print("## stop:%s" % stop)
            self.metadata.setMetadataPair(metadata.METADATA_STOP_DATE_TIME, stop)
            self.metadata.setMetadataPair(metadata.METADATA_STOP_DATE, stop.split("T")[0])
            self.metadata.setMetadataPair(metadata.METADATA_STOP_TIME, stop.split("T")[1].split('.')[0] + msec)
            #os._exit(1)
        else:
            # like: 2021-03-14T07:08:03.311795Z
            start = self.metadata.getMetadataValue(metadata.METADATA_START_DATE_TIME)
            pos = start.find('.')
            msec=".000"
            if pos > 0:
                start = start[0:pos+4] + "Z"
                msec="."+start[pos+1: pos+4]
            else:
                raise Exception("unexpected start datetime format: no .: '%s'" % start)
            print("## START:%s" % start)
            self.metadata.setMetadataPair(metadata.METADATA_START_DATE_TIME, start)
            self.metadata.setMetadataPair(metadata.METADATA_START_DATE, start.split("T")[0])
            self.metadata.setMetadataPair(metadata.METADATA_START_TIME, start.split("T")[1].split('.')[0] + msec)

            #
            self.metadata.setMetadataPair(metadata.METADATA_STOP_DATE_TIME, start)
            self.metadata.setMetadataPair(metadata.METADATA_STOP_DATE, start.split("T")[0])
            self.metadata.setMetadataPair(metadata.METADATA_STOP_TIME, start.split("T")[1].split('.')[0] + msec)

        # build timePosition from endTime + endDate
        self.metadata.setMetadataPair(metadata.METADATA_TIME_POSITION, "%sT%sZ" % (self.metadata.getMetadataValue(metadata.METADATA_STOP_DATE), self.metadata.getMetadataValue(metadata.METADATA_STOP_TIME)))

        # addLocalAttribute
        self.metadata.addLocalAttribute("originalName", self.productFolderName)

        # cloud coverage
        tmp = self.metadata.getMetadataValue(metadata.METADATA_CLOUD_COVERAGE)
        if self.metadata.valueExists(tmp):
            tmp = int(float(tmp) * 100.0)
            print("METADATA_CLOUD_COVERAGE ok: %s" % tmp)
        else:
            raise Exception("METADATA_CLOUD_COVERAGE not present")
        self.metadata.setMetadataPair(metadata.METADATA_CLOUD_COVERAGE, tmp)

        # product version
        tmp = self.metadata.getMetadataValue(metadata.METADATA_SOFTWARE_VERSION)
        if self.metadata.valueExists(tmp):
            tmp = tmp.replace('.', '')
            if len(tmp) != 3:
                raise Exception("METADATA_SOFTWARE_VERSION as str: '%s' is not 3 digit length" % tmp)
            else:
                tmp='%s0' % tmp
                print("METADATA_SOFTWARE_VERSION as str: '%s'" % tmp)
        else:
            raise Exception("METADATA_SOFTWARE_VERSION not present")
        self.metadata.setMetadataPair(metadata.METADATA_PRODUCT_VERSION, tmp)

    #
    #
    #
    def buildTypeCode(self, processInfo):
        level = self.metadata.getMetadataValue(LEVEL)
        typecode=None
        if self.productFolderName.endswith('Tile'):
            print(" #### is a tile product")
            if level != 'L3A':
                raise Exception("Incorrect level '%s' for Tile product, shall be '3A'")
            if self.preview_path is None:
                typecode='PS2_AN4_3A'
            else:
                typecode='PS2_VIS_3A'
            #self.metadata.setMetadataPair(metadata.METADATA_TYPECODE, typecode)
        elif self.productFolderName.endswith('Band'):
            print(" #### is a scene product")
            pos = self.productFolderName.find("Band")
            numBamds=int(self.productFolderName[pos-1])
            print(" #### numBamds: %s" % numBamds)
            if level == 'L1B':
                if numBamds==3:
                    typecode='PS2_BA3_1B'
                elif numBamds==1: # correct: 1 band ends up in _BA3_
                    typecode='PS2_BA4_1B'
                else:
                    raise Exception("Incorrect number of band %s for L1B product; shall be 1 or 3" % numBamds)
                #self.metadata.setMetadataPair(metadata.METADATA_TYPECODE, typecode)
            elif level == 'L3B':
                if numBamds==3:
                    if self.preview_path is None:
                        typecode='PS2_AN3_3B'
                    else:
                        typecode='PS2_VIS_3B'
                elif numBamds==4:
                    typecode='PS2_AN4_3B'
                else:
                    raise Exception("Incorrect number of band %s for L3B product; shall be 3 or 4" % numBamds)
                #self.metadata.setMetadataPair(metadata.METADATA_TYPECODE, typecode)
            else:
                raise Exception("Incorrect level '%s'" % level)
        else:
            raise Exception("Incorrect folder suffix '%s', shall ends with 'Tile' or 'Band'" % self.productFolderName)

        print("Typecode: '%s'" % typecode)
        if not typecode in  REF_TYPECODE:
            raise Exception("buildTypeCode; unknown typecode:%s" % (typecode))
        self.metadata.setMetadataPair(metadata.METADATA_TYPECODE, typecode)
        #os._exit(1)

        
    #
    # extract quality
    #
    def extractQuality(self, helper, met):
        pass


    #
    # extract the footprint posList point, ccw, lat lon
    #
    def extractFootprint(self, processInfo):

        #keep a copy
        self.metadata.setMetadataPair("json-footprint", "%s" % self.metadata.getMetadataValue(metadata.METADATA_FOOTPRINT))
        tmp = self.metadata.getMetadataValue(metadata.METADATA_FOOTPRINT) # is a list because we get what is parsed: json. So we get str/int/float...
        print("FOOTPRINT 0:%s type:%s; size=%s"  % (tmp, type(tmp), len(tmp[0])))
        if len(tmp[0])==5:
            pass
        tmp1=''
        for n in range(len(tmp[0])):
            if len(tmp1)>0:
                tmp1+=' '
            tmp1+="%s %s" % (tmp[0][n][1], tmp[0][n][0])
        print("FOOTPRINT 1:%s"  % (tmp1))
        self.metadata.setMetadataPair("footprint_json_to_lat-lon", tmp1)
        self.metadata.setMetadataPair("footprint_json_num-pairs", len(tmp[0]))
        #os._exit(1)
        if len(tmp[0])==5:
            footprint = "%s %s %s %s %s %s %s %s %s %s" % (tmp[0][0][1], tmp[0][0][0],
                                                           tmp[0][1][1], tmp[0][1][0],
                                                           tmp[0][2][1], tmp[0][2][0],
                                                           tmp[0][3][1], tmp[0][3][0],
                                                           tmp[0][0][1], tmp[0][0][0],
                                                       )
        else:
            raise Exception("strange footprint, has not 5 pairs but: %s" % len(tmp[0]))
            """footprint = "%s %s %s %s %s %s %s %s %s %s" % (tmp[0][0][1], tmp[0][0][0],
                                                           tmp[0][1][1], tmp[0][1][0],
                                                           tmp[0][2][1], tmp[0][2][0],
                                                           tmp[0][3][1], tmp[0][3][0],
                                                           tmp[0][0][1], tmp[0][0][0],
                                                           )"""

        self.metadata.setMetadataPair("first-footprint", footprint)
        #print("FOOTPRINT: %s"  % footprint)
        #os._exit(1)

        # get center
        # make sure the footprint is CCW
        browseIm = BrowseImage()
        self.browseIm = browseIm
        browseIm.setFootprint(footprint)
        browseIm.calculateBoondingBox()
        self.metadata.setMetadataPair(metadata.METADATA_FOOTPRINT, browseIm.getFootprint())
        self.metadata.setMetadataPair(metadata.METADATA_BOUNDING_BOX, browseIm.getBoundingBox())
        if self.debug!=0:
            print "browseIm:%s" % browseIm.info()
        if not browseIm.getIsCCW():
            # reverse
            if self.debug!=0:
                print "############### reverse the footprint; before:%s" % (footprint)
            browseIm.reverseFootprint()
            if self.debug!=0:
                print "###############             after;%s" % (browseIm.getFootprint())
            self.metadata.setMetadataPair(metadata.METADATA_FOOTPRINT, browseIm.getFootprint())
        else:
            self.metadata.setMetadataPair(metadata.METADATA_FOOTPRINT, footprint)

        flat, flon = browseIm.calculateCenter()
        flat=float(flat)
        flon=float(flon)

        #
        self.metadata.setMetadataPair(metadata.METADATA_SCENE_CENTER, "%s %s" % (flat, flon))

        #
        mseclon=abs(int((flon-int(flon))*1000))
        mseclat=abs(int((flat-int(flat))*1000))
        if flat < 0:
            flat = "S%s" % formatUtils.leftPadString("%s" % abs(int(flat)), 2, '0')
        else:
            flat = "N%s" % formatUtils.leftPadString("%s" % int(flat), 2, '0')
        if flon < 0:
            flon = "W%s" % formatUtils.leftPadString("%s" % abs(int(flon)), 3, '0')
        else:
            flon = "E%s" % formatUtils.leftPadString("%s" % int(flon), 3, '0')
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LATITUDE_DEG_NORMALISED, flat)
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LONGITUDE_DEG_NORMALISED, flon)
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LATITUDE_MDEG_NORMALISED,  formatUtils.leftPadString("%s" % int(mseclat), 3, '0'))
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LONGITUDE_MDEG_NORMALISED, formatUtils.leftPadString("%s" % int(mseclon), 3, '0'))

        self.metadata.setMetadataPair(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, flat)
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LONGITUDE_GRID_NORMALISED, flon)

        

    #
    #
    #
    def toString(self):
        res="path:%s" % self.path
        return res


    #
    #
    #
    def dump(self):
        res="path:%s" % self.path
        print res


