# -*- coding: cp1252 -*-
#
# this class represent a terrasar_x directory product
#
# changes:
#  - 2020-06: add worlddem type
#  - 
#
#
import os, sys, inspect
import logging
import tarfile
from subprocess import call,Popen, PIPE

#
import eoSip_converter.xmlHelper as xmlHelper
import eoSip_converter.imageUtil as imageUtil
import eoSip_converter.fileHelper as fileHelper
import eoSip_converter.geomHelper
from sectionIndentedDocument import SectionDocument

from product import Product
from product_directory import Product_Directory
from xml_nodes import sipBuilder, rep_footprint
from browseImage import BrowseImage
import product_EOSIP
import metadata
import browse_metadata
import formatUtils
import shutil




class Product_Terrasar_x(Product_Directory):


    #
    xmlMapping = {
        metadata.METADATA_START_DATE:'temporalCoverage/startTime',
        metadata.METADATA_STOP_DATE:'temporalCoverage/stopTime',
        metadata.METADATA_PROCESSING_TIME:'creation/time',
        'productVariant':'keys/feature*@key==productVariant',
        metadata.METADATA_SENSOR_OPERATIONAL_MODE: 'feature/feature*@key==imagingMode',
        metadata.METADATA_ANTENNA_LOOK_DIRECTION: 'feature/feature*@key==antennaLookDirection',
        metadata.METADATA_POLARISATION_MODE: 'feature/feature*@key==polarisationMode',
        metadata.METADATA_POLARISATION_CHANNELS: 'feature/feature*@key==polarisationChannels',
        }
    #
    xmlMapping_bis={
        metadata.METADATA_ORBIT: 'productInfo/missionInfo/absOrbit',
        metadata.METADATA_ORBIT_DIRECTION: 'productInfo/missionInfo/orbitDirection',
    }
    #
    mapping2={
        metadata.METADATA_FOOTPRINT:'*<boundingPolygon>|2,3,7,8,12,13,17,18,2,3',
        'delta_lat': '*<boundingPolygon>|2,7',
        'delta_utc': '*<boundingPolygon>|4,9',
        }

    # for WORLD_DEM:
    xmlMapping_worlddem={
        #metadata.METADATA_START_DATE:'dateStamp/Date',
        metadata.METADATA_START_DATE:'contentInfo/TSXX_addMD/acquisitionInfo/temporalCoverage/tsxx_startTime',
        metadata.METADATA_STOP_DATE:'contentInfo/TSXX_addMD/acquisitionInfo/temporalCoverage/tsxx_startTime',
        metadata.METADATA_SENSOR_OPERATIONAL_MODE: 'contentInfo/TSXX_addMD/acquisitionInfo/imagingMode',
        metadata.METADATA_ANTENNA_LOOK_DIRECTION: 'contentInfo/TSXX_addMD/acquisitionInfo/lookDirection',
        metadata.METADATA_POLARISATION_MODE: 'contentInfo/TSXX_addMD/acquisitionInfo/polarisationMode',
        metadata.METADATA_POLARISATION_CHANNELS: 'contentInfo/TSXX_addMD/acquisitionInfo/polarisation'
    }
    worlddem_mapping2={
        metadata.METADATA_FOOTPRINT:'*<gml:LinearRing>|1'
    }


    #
    # look like there are two type of products:
    # - dimap like
    # - xml + mask like
    #
    METADATA_SUFFIX= 'iif.xml'
    PREVIEW_NAME='BROWSE.tif'

    # for WORLD_DEM:
    METADATA_WORLDDEM_PREFIX='WorldDEM_DTM_'
    METADATA_WORLDDEM_SUFFIX = '.xml'
    PREVIEW_SUFFIX_WORLDDEM_NAME='_DEM_QL.tif'


    #
    REF_TYPECODES=['SAR_HS_EEC', 'SAR_HS_GEC', 'SAR_HS_MGD', 'SAR_HS_SSC', 'SAR_SC_EEC', 'SAR_SC_GEC', 'SAR_SC_MGD', 'SAR_SC_SSC', 'SAR_SL_EEC', 'SAR_SL_GEC', 'SAR_SL_MGD', 'SAR_SL_SSC', 'SAR_SM_EEC', 'SAR_SM_GEC', 'SAR_SM_MGD', 'SAR_SM_SSC', 'SAR_ST_EEC', 'SAR_ST_GEC', 'SAR_ST_MGD', 'SAR_ST_SSC', 'SAR_WS_EEC', 'SAR_WS_GEC', 'SAR_WS_MGD', 'SAR_WS_SSC']

    #
    #REF_POLARIZATIONS=['HH', 'VV', 'HH/VV']

    # possible reference polarization as per EoSip table 3.3. syntax: ImagingMode_PolarizationMode_PolarizationChannel
    REF_POLARIZATIONS_LUT=[ 'ST_S_HH',
                            'ST_S_VV',

                            'HS_S_HH',
                            'HS_S_VV',
                            'HS_D_HH, VV',

                            'SL_S_HH',
                            'SL_S_VV',
                            'SL_D_HH, VV',


                            'SM_S_HH',
                            'SM_S_VV',
                            'SM_D_HH, VV',
                            'SM_D_HH, HV',
                            'SM_D_VV, VH',
                            'SM_T_HH, VV',
                            'SM_Q_HH, HV, VH, VV',

                            'SC_S_HH',
                            'SC_S_VV',

                            'WC_S_HH',
                            'WC_S_VV',
                            'WC_S_HV',
                            'WC_S_VH']

    #
    BOUNDING_BOX_FLAG = ['SAR_HS_EEC', 'SAR_HS_GEC', 'SAR_SC_EEC', 'SAR_SC_GEC', 'SAR_SL_EEC', 'SAR_SL_GEC',
                         'SAR_SM_EEC', 'SAR_SM_GEC', 'SAR_ST_EEC', 'SAR_ST_GEC', 'SAR_WS_EEC', 'SAR_WS_GEC']

    #
    #
    #
    def __init__(self, path=None):
        Product_Directory.__init__(self, path)
        #
        self.metContentPath=None
        self.metContentName=None
        self.metContent=None
        # bis
        self.metContentName_bis=None
        self.metContent_bis=None
        #
        self.previewContentName=None
        self.previewPath=None

        # WORLDDEM
        self.metContentName_worlddem = None
        self.metContent_worlddem = None
        self.previewContentName_worlddeme = None

        #
        self.useBbox=True

        if self.debug!=0:
            print " init class Product_Terrasar_x"

        
    #
    # called at the end of the doOneProduct, before the index/shopcart creation
    #
    def afterProductDone(self):
        pass


    #
    # read matadata file
    #
    def getMetadataInfo(self):
        pass


    #
    #
    #
    def makeBrowses(self, processInfo):
        if self.debug!=0:
            print " makeBrowses"
        n=0
        anEosip = processInfo.destProduct

        # they can be no browse
        used=None
        if self.isWorldDem:
            used=self.previewContentName_worlddeme
        else:
            used=self.previewContentName

        if used is not None:
            browseName = processInfo.destProduct.getSipProductName()
            browseSrcPath = self.previewPath
            browseDestPath = "%s/%s.BI.JPG" % (processInfo.workFolder, browseName)

            if 1==2: # disabled: want non transparent PNG. NO: want JPG
                browseDestPathRaw = "%s/%s.BI.PNG_raw" % (processInfo.workFolder, browseName)
                # remove blabk filling area from PNG using stretcherAppExe
                imageUtil.makeBrowse('PNG', browseSrcPath, browseDestPathRaw)
                command = "%s -transparent %s %s 0xff000000" % (self.stretcherAppExe, browseDestPathRaw, browseDestPath)
                commandFile = "%s/command_browse.sh" % (processInfo.workFolder)
                fd = open(commandFile, 'w')
                fd.write(command)
                fd.close()

                # launch the main make_browse script:
                command = "/bin/sh -f %s" % (commandFile)
                #
                retval = call(command, shell=True)
                if self.debug:
                    print "  external make browse exit code:%s" % retval
                if retval != 0:
                    raise Exception("Error generating browse, exit coded:%s" % retval)
            else:
                imageUtil.makeBrowse('JPG', browseSrcPath, browseDestPath)
                #shutil.copyfile(browseSrcPath, browseDestPath)

            anEosip.addSourceBrowse(browseDestPath, [])
            processInfo.addLog("  browse image[%s] added: name=%s; path=%s" % (n, browseName, browseDestPath))
            # set AM timne if needed
            processInfo.destProduct.setFileAMtime(browseDestPath)

            # create browse choice for browse metadata report
            bmet = anEosip.browse_metadata_dict[browseDestPath]
            if self.debug != 0:
                print "###\n###\n### BUILD BROWSE CHOICE FROM BROWSE METADATA:%s" % (bmet.toString())

            reportBuilder = rep_footprint.rep_footprint()
            #
            if self.debug != 0:
                print "###\n###\n### BUILD BROWSE CHOICE FROM METADATA:%s" % (anEosip.metadata.toString())
            browseChoiceBlock = reportBuilder.buildMessage(anEosip.metadata,
                                                           "rep:browseReport/rep:browse/rep:footprint").strip()
            if self.debug != 0:
                print "browseChoiceBlock:%s" % (browseChoiceBlock)
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

            processInfo.addLog("  browse image[%s] choice created:browseChoiceBlock=\n%s" % (n, browseChoiceBlock))

        else:
            raise Exception("no browse")


    #
    # extract the product
    #
    def extractToPath(self, folder=None, dont_extract=False):
        if not os.path.exists(folder):
            raise Exception("destination fodler does not exists:%s" % folder)
        if self.debug!=0:
            print " will exttact directory product '%s' to path:%s" % (self.path, folder)


        if not os.path.exists(folder):
            raise Exception("destination fodler does not exists:%s" % folder)
        if self.debug!=0:
            print " will exttact product to path:%s" % folder
        tar = tarfile.open(self.path, 'r')

        # keep list of content
        self.contentList=[]
        # extract everithing
        self.EXTRACTED_PATH=folder
        tar.extractall(path=self.EXTRACTED_PATH)
        tar.close()


        # build content list
        n=0
        for root, dirs, files in os.walk(self.EXTRACTED_PATH, topdown=False):
            for name in files:
                n=n+1
                #baseName = os.path.basename(name)
                if self.debug!=0:
                    print "  test tar content[%d]:'%s'" % (n, name)

                # keep metadata and preview data
                # non WORLD_DEM
                if name.endswith(self.PREVIEW_NAME): # browse image
                    self.previewContentName = name
                    #if self.debug != 0:
                    self.previewPath = os.path.join(root, name)
                    print " #  previewContentName:%s" % (name)

                elif name.lower().find(self.METADATA_SUFFIX)>=0: # metadata
                    self.metContentName = name
                    self.metContentPath = os.path.join(root, name)
                    if self.debug!=0:
                        print "   metContentName:%s" % (name)
                    fd = open(os.path.join(root, name))
                    self.metContent=fd.read()
                    fd.close()
                    print " #  metContent length:%s" % len(self.metContent)

                elif not name.startswith(self.METADATA_WORLDDEM_PREFIX) and name.endswith('.xml') and name!='GEOREF.xml':  # metadata 2
                    self.metContentName_bis = name
                    fd = open(os.path.join(root, name))
                    self.metContent_bis=fd.read()
                    fd.close()
                    print " #  metContent_bis length:%s" % len(self.metContent_bis)


                # WORLD_DEM
                elif name.startswith(self.METADATA_WORLDDEM_PREFIX) and name.endswith(self.METADATA_WORLDDEM_SUFFIX):
                    self.metContentName_worlddem = name
                    self.metContentPath = os.path.join(root, name)
                    fd = open(os.path.join(root, name))
                    self.metContent_worlddem=fd.read()
                    fd.close()
                    print "###   metContent_worlddem length:%s" % len(self.metContent_worlddem)

                elif name.endswith(self.PREVIEW_SUFFIX_WORLDDEM_NAME):
                    self.previewContentName_worlddeme = name
                    #if self.debug != 0:
                    self.previewPath = os.path.join(root, name)
                    print "###   previewContentNam_worlddeme:%s" % (name)


                #self.contentList.append(name)
                relPath = os.path.join(root, name)[len(self.EXTRACTED_PATH) + 1:]
                print "   content[%s] workfolder relative path:%s" % (n, relPath)
                self.contentList.append(relPath)

        #os._exit(1)




    #
    # updated xml metadata extract
    #
    #
    def xmlExtract(self, xmlData, aMetadata, xmlMapping):
        helper = xmlHelper.XmlHelper()
        #helper.setDebug(1)

        helper.setData(xmlData);
        helper.parseData()

        # get fields
        resultList = []
        op_element = helper.getRootNode()
        num_added = 0

        for field in xmlMapping:
            print "\n\nmetadata extract field:%s" % field
            multiple = False
            attr = None
            aPath = None
            aValue = None
            if xmlMapping[field].find("@") >= 0:
                attr = xmlMapping[field].split('@')[1]
                aPath = xmlMapping[field].split('@')[0]
                if aPath.endswith('*'):
                    multiple = True
                    aPath = aPath[0:-1]
                    print " -> multiple used on path:%s" % aPath
            else:
                attr = None
                aPath = xmlMapping[field]

            if not multiple:
                aNode = helper.getFirstNodeByPath(None, aPath, None)
                if aNode == None:
                    aValue = None
                else:
                    if attr == None:  # return NODE TEXT
                        aValue = helper.getNodeText(aNode)
                    else:  # return attribute TEXT
                        aValue = helper.getNodeAttributeText(aNode, attr)

                if self.debug != 0:
                    print "  --> metadata[%s]: %s=%s" % (num_added, field, aValue)
                aMetadata.setMetadataPair(field, aValue)
                num_added = num_added + 1
            else:  # will return NODE TEXT
                aList = []
                helper.getNodeByPath(None, aPath, attr, aList)
                print " -> multiple; list of node found:%s" % len(aList)
                if len(aList) > 0:
                    for aNode in aList:
                        aValue = helper.getNodeText(aNode)
                        if self.debug != 0:
                            print "  --> metadata multiple[%s]: %s=%s" % (num_added, field, aValue)
                        aMetadata.setMetadataPair(field, aValue)
                        num_added = num_added + 1


        # added for bis:
        for field in xmlMapping:
            print "\n\nmetadata extract field:%s" % field
            multiple = False
            attr = None
            aPath = None
            aValue = None
            if xmlMapping[field].find("@") >= 0:
                attr = xmlMapping[field].split('@')[1]
                aPath = xmlMapping[field].split('@')[0]
                if aPath.endswith('*'):
                    multiple = True
                    aPath = aPath[0:-1]
                    print " -> multiple used on path:%s" % aPath
            else:
                attr = None
                aPath = xmlMapping[field]

            if not multiple:
                aNode = helper.getFirstNodeByPath(None, aPath, None)
                if aNode == None:
                    aValue = None
                else:
                    if attr == None:  # return NODE TEXT
                        aValue = helper.getNodeText(aNode)
                    else:  # return attribute TEXT
                        aValue = helper.getNodeAttributeText(aNode, attr)

                if self.debug != 0:
                    print "  --> metadata[%s]: %s=%s" % (num_added, field, aValue)
                aMetadata.setMetadataPair(field, aValue)
                num_added = num_added + 1
            else:  # will return NODE TEXT
                aList = []
                helper.getNodeByPath(None, aPath, attr, aList)
                print " -> multiple; list of node found:%s" % len(aList)
                if len(aList) > 0:
                    for aNode in aList:
                        aValue = helper.getNodeText(aNode)
                        if self.debug != 0:
                            print "  --> metadata multiple[%s]: %s=%s" % (num_added, field, aValue)
                        aMetadata.setMetadataPair(field, aValue)
                        num_added = num_added + 1

        return num_added

    #
    #
    #
    def extractMetadata(self, met=None):
        if met==None:
            raise Exception("metadate is None")

        self.metadata = met

        # src size
        self.size=os.stat(self.path).st_size
        met.setMetadataPair(metadata.METADATA_PRODUCT_SIZE, self.size)


        if self.metContent is not None:
            self.isWorldDem=False
            # first phase
            num_added = self.xmlExtract(self.metContent, met, self.xmlMapping)
            #addd bis to get orbit info
            num_added += self.xmlExtract(self.metContent_bis, met, self.xmlMapping_bis)
            # second phase
            num_added += self.extractMetadata02(self.metContent, self.mapping2)
            print("metadata extracted: %s" % num_added)

        elif self.metContent_worlddem is not None:
            self.isWorldDem = True
            num_added = self.xmlExtract(self.metContent_worlddem, met, self.xmlMapping_worlddem)
            # second phase
            num_added += self.extractMetadata02(self.metContent_worlddem, self.worlddem_mapping2)
            print("metadata extracted: %s" % num_added)
        else:
            raise Exception("no metadata to parse")
        #os._exit(0)



    #
    # use a SectionDocument to extract list of xml node values
    #
    def extractMetadata02(self, metContent, metMapping):

        sectionDoc = SectionDocument()
        sectionDoc.setContent(metContent)
        #sectionDoc.debug=1

        num_added=0

        for field in metMapping:
            rule=metMapping[field]
            aValue=None
            if self.debug==0:
                print " ##### Handle metadata2:%s" % field


            toks=rule.split('|')
            if len(toks)!=2:
                raise Exception("Malformed report metadata rule:%s" % field)
            # wildcard used?
            if toks[0][-1]=='*': # wildcard at end
                line=sectionDoc.getSectionLine(toks[0])
                # line offset(s) list are in second token
                offsets=toks[1].split(',')
                aValue=''
                for offset in offsets:
                    nLine=line+int(offset)
                    if len(aValue)>0:
                        aValue="%s " % aValue
                    aValue="%s%s" % (aValue,sectionDoc.getLineValue(nLine,None, separator='>'))
                if self.debug==0:
                    print "  report metadata:%s='%s'" % (field, aValue)
            elif toks[0][0]=='*': # wildcard at start
                line=sectionDoc.getSectionLine(toks[0])
                # line offset(s) list are in second token
                offsets=toks[1].split(',')
                aValue=''
                for offset in offsets:
                    nLine=line+int(offset)
                    if len(aValue)>0:
                        aValue="%s " % aValue
                    aValue="%s%s" % (aValue,sectionDoc.getLineValue(nLine,None, separator='>'))
                    pos = aValue.index('<')
                    aValue=aValue[0:pos]
                if self.debug==0:
                    print "  report metadata:%s='%s'" % (field, aValue)
            else:
                aValue=sectionDoc.getValue(toks[0], toks[1])
            # supress initial space is any
            if aValue[0]==' ':
                aValue=aValue[1:]
            if self.debug != 0:
                print "  --> metadata 1[%s]: %s=%s" % (num_added, field, aValue)
            self.metadata.setMetadataPair(field, aValue)
            num_added=num_added+1

        return num_added


    #
    # Refine the metadata.
    #
    def refineMetadata(self):

        # Defining METADATA_START_DATE, METADATA_START_TIME.
        # value is like 2017-09-12T10:45:23.117
        start = self.metadata.getMetadataValue(metadata.METADATA_START_DATE)
        start_tokens=start.split('T')
        self.metadata.setMetadataPair(metadata.METADATA_START_DATE, start_tokens[0])
        self.metadata.setMetadataPair(metadata.METADATA_START_TIME, start_tokens[1].split('.')[0])

        # Defining METADATA_STOP_DATE, METADATA_STOP_TIME.
        stop = self.metadata.getMetadataValue(metadata.METADATA_STOP_DATE)
        self.metadata.setMetadataPair(metadata.METADATA_TIME_POSITION, stop)
        stop_tokens=stop.split('T')
        self.metadata.setMetadataPair(metadata.METADATA_STOP_DATE, stop_tokens[0])
        self.metadata.setMetadataPair(metadata.METADATA_STOP_TIME, stop_tokens[1].split('.')[0])

        # build timePosition from endTime + endDate
        self.metadata.setMetadataPair(metadata.METADATA_TIME_POSITION, "%sT%sZ" % (self.metadata.getMetadataValue(metadata.METADATA_STOP_DATE), self.metadata.getMetadataValue(metadata.METADATA_STOP_TIME)))


        browseIm = BrowseImage()
        # will wrap longitude if needed
        browseIm.setFootprint(self.metadata.getMetadataValue(metadata.METADATA_FOOTPRINT))
        wrappedFootprint = browseIm.getFootprint()
        self.metadata.setMetadataPair(metadata.METADATA_FOOTPRINT, wrappedFootprint)
        if browseIm.footptintChanged():
            self.metadata.setMetadataPair("ORIGINAL_FOOTPRINT", browseIm.origFootprint)
        browseIm.calculateBoondingBox()
        clat, clon = browseIm.calculateCenter()
        self.metadata.setMetadataPair(metadata.METADATA_SCENE_CENTER_LAT, "%s" % clat)
        self.metadata.setMetadataPair(metadata.METADATA_SCENE_CENTER_LON, "%s" % clon)
        self.metadata.setMetadataPair(metadata.METADATA_SCENE_CENTER, "%s %s" % (clat, clon))
        self.boundingBox = browseIm.boondingBox
        #self.metadata.addLocalAttribute("boundingBox", browseIm.boondingBox)

        flat = float(clat)
        flon = float(clon)
        mseclon = abs(int((flon - int(flon)) * 1000))
        mseclat = abs(int((flat - int(flat)) * 1000))
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
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LATITUDE_MDEG_NORMALISED,
                                      formatUtils.leftPadString("%s" % int(mseclat), 3, '0'))
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LONGITUDE_MDEG_NORMALISED,
                                      formatUtils.leftPadString("%s" % int(mseclon), 3, '0'))
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LONGITUDE_GRID_NORMALISED, flon)
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, flat)

        # uget info from folder name, use parent of iif file
        iifParent = os.path.dirname(self.metContentPath)
        print("########### iifParent=%s" % iifParent)
        # like TDX1_SAR__SSC______ST_S_SRA_20170621T153838_20170621T153838
        produName = os.path.split(iifParent)[-1]
        self.metadata.setMetadataPair(metadata.METADATA_PRODUCT_SOURCE, produName)
        self.metadata.setMetadataPair(metadata.METADATA_IMAGING_MODE, produName[19:21])
        self.metadata.setMetadataPair(metadata.METADATA_POLARISATION_MODE, produName[22])
        self.metadata.setMetadataPair(metadata.METADATA_PRODUCT_CLASS, produName[10:13])
        self.metadata.setMetadataPair('resolutionVariant', produName[14:18])

        # define ascending or not
        tmp = self.metadata.getMetadataValue('delta_lat')
        dlat = float(tmp.split(' ')[1]) - float(tmp.split(' ')[0])
        print("########### dlat=%s" % dlat)
        tmp1 = self.metadata.getMetadataValue('delta_utc')
        utc1 = tmp1.split(' ')[0]
        msec1 = int(utc1[-3:])
        utc2 = tmp1.split(' ')[1]
        msec2 = int(utc2[-3:])
        print("########### utc1=%s; msec1=%s; utc2=%s; msec2=%s" % (utc1[0:-4]+'Z', msec1, utc2[0:-4]+'Z', msec2))
        deltaMsec = formatUtils.dateDiffmsec(utc1[0:-4]+'Z', msec1, utc2[0:-4]+'Z', msec2)
        print("########### deltaMsec=%s" % deltaMsec)
        self.metadata.setMetadataPair('deltaMsec', deltaMsec)
        self.metadata.setMetadataPair('dlat', dlat)

        #
        tmp = self.metadata.getMetadataValue(metadata.METADATA_ORBIT)
        print '############### ORBIT:%s' % tmp
        #os._exit(1)
        if tmp==None:
            self.metadata.setMetadataPair(metadata.METADATA_ORBIT, 0)
            if deltaMsec >= 0:
                if dlat >= 0:
                    self.metadata.setMetadataPair(metadata.METADATA_ORBIT_DIRECTION, 'ASCENDING')
                else:
                    self.metadata.setMetadataPair(metadata.METADATA_ORBIT_DIRECTION, 'DESCENDING')
            else:
                if dlat >= 0:
                    self.metadata.setMetadataPair(metadata.METADATA_ORBIT_DIRECTION, 'DESCENDING')
                else:
                    self.metadata.setMetadataPair(metadata.METADATA_ORBIT_DIRECTION, 'ASCENDING')

        #
        typecode = self.buildTypeCode()

        # some typecode have no boundingBox and other fields
        if typecode in self.BOUNDING_BOX_FLAG:
            # bounding box
            self.metadata.addLocalAttribute("boundingBox", self.boundingBox)
            self.metadata.setMetadataPair(metadata.METADATA_BOUNDING_BOX, self.boundingBox)
            print(" ######################## typecode %s in BOUNDING_BOX_FLAG map" % typecode)
            self.useBbox = True
        else:
            print(" ######################## typecode %s NOT in BOUNDING_BOX_FLAG map" % typecode)
            self.useBbox = False

        #
        tmp = self.metadata.getMetadataValue(metadata.METADATA_ANTENNA_LOOK_DIRECTION)
        if tmp == 'R':
            self.metadata.setMetadataPair(metadata.METADATA_ANTENNA_LOOK_DIRECTION, 'RIGHT')
        elif tmp == 'L':
            self.metadata.setMetadataPair(metadata.METADATA_ANTENNA_LOOK_DIRECTION, 'LEFT')
        else:
            self.metadata.setMetadataPair(metadata.METADATA_ANTENNA_LOOK_DIRECTION, 'UNDEFINED')

        # perform some check
        IM = self.metadata.getMetadataValue(metadata.METADATA_IMAGING_MODE)
        PC = self.metadata.getMetadataValue(metadata.METADATA_POLARISATION_CHANNELS)
        if PC.find('/')>0:
            PC=PC.replace('/', ', ')
            self.metadata.setMetadataPair(metadata.METADATA_POLARISATION_CHANNELS, PC)
        PM = self.metadata.getMetadataValue(metadata.METADATA_POLARISATION_MODE)
        # check agains possible reference polarization as per EoSip table 3.3. syntax: ImagingMode_PolarizationMode_PolarizationChannel
        if "%s_%s_%s" % (IM, PM, PC) not in self.REF_POLARIZATIONS_LUT:
            raise Exception("polarization value unknown:%s" % "%s_%s_%s" % (IM, PM, PC))
        #if  not tmp in self.REF_POLARIZATIONS:
        #    raise Exception("Unknown polarization channel:%s" % tmp)

    #
    # Refine the metadata.
    #
    def refineMetadataWorldDem(self):

        # Defining METADATA_START_DATE, METADATA_START_TIME.
        # value is like 2017-09-12
        start = self.metadata.getMetadataValue(metadata.METADATA_START_DATE)
        #self.metadata.setMetadataPair(metadata.METADATA_START_TIME, "00:00:00")
        start_tokens=start.split('T')
        self.metadata.setMetadataPair(metadata.METADATA_START_DATE, start_tokens[0])
        self.metadata.setMetadataPair(metadata.METADATA_START_TIME, start_tokens[1].split('.')[0])

        # Defining METADATA_STOP_DATE, METADATA_STOP_TIME.
        stop = self.metadata.getMetadataValue(metadata.METADATA_STOP_DATE)
        self.metadata.setMetadataPair(metadata.METADATA_TIME_POSITION, stop)
        stop_tokens=stop.split('T')
        self.metadata.setMetadataPair(metadata.METADATA_STOP_DATE, stop_tokens[0])
        self.metadata.setMetadataPair(metadata.METADATA_STOP_TIME, stop_tokens[1].split('.')[0])

        # build timePosition from endTime + endDate
        self.metadata.setMetadataPair(metadata.METADATA_TIME_POSITION, "%sT%sZ" % (self.metadata.getMetadataValue(metadata.METADATA_STOP_DATE), self.metadata.getMetadataValue(metadata.METADATA_STOP_TIME)))


        browseIm = BrowseImage()
        # will wrap longitude if needed
        browseIm.setFootprint(self.metadata.getMetadataValue(metadata.METADATA_FOOTPRINT))
        wrappedFootprint = browseIm.getFootprint()
        self.metadata.setMetadataPair(metadata.METADATA_FOOTPRINT, wrappedFootprint)
        if browseIm.footptintChanged():
            self.metadata.setMetadataPair("ORIGINAL_FOOTPRINT", browseIm.origFootprint)
        browseIm.calculateBoondingBox()
        clat, clon = browseIm.calculateCenter()
        self.metadata.setMetadataPair(metadata.METADATA_SCENE_CENTER_LAT, "%s" % clat)
        self.metadata.setMetadataPair(metadata.METADATA_SCENE_CENTER_LON, "%s" % clon)
        self.metadata.setMetadataPair(metadata.METADATA_SCENE_CENTER, "%s %s" % (clat, clon))
        self.boundingBox = browseIm.boondingBox
        #self.metadata.addLocalAttribute("boundingBox", browseIm.boondingBox)

        flat = float(clat)
        flon = float(clon)
        mseclon = abs(int((flon - int(flon)) * 1000))
        mseclat = abs(int((flat - int(flat)) * 1000))
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
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LATITUDE_MDEG_NORMALISED,
                                      formatUtils.leftPadString("%s" % int(mseclat), 3, '0'))
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LONGITUDE_MDEG_NORMALISED,
                                      formatUtils.leftPadString("%s" % int(mseclon), 3, '0'))
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LONGITUDE_GRID_NORMALISED, flon)
        self.metadata.setMetadataPair(metadata.METADATA_WRS_LATITUDE_GRID_NORMALISED, flat)

        # uget info from folder name, use parent of iif file
        iifParent = os.path.dirname(self.metContentPath)
        print("########### iifParent=%s" % iifParent)
        # like TDX1_SAR__SSC______ST_S_SRA_20170621T153838_20170621T153838
        produName = os.path.split(iifParent)[-1]
        self.metadata.setMetadataPair(metadata.METADATA_PRODUCT_SOURCE, produName)
        self.metadata.setMetadataPair(metadata.METADATA_POLARISATION_MODE, self.metadata.getMetadataValue(metadata.METADATA_POLARISATION_MODE)[0].upper())

        #self.metadata.setMetadataPair(metadata.METADATA_IMAGING_MODE, produName[19:21])
        #self.metadata.setMetadataPair(metadata.METADATA_POLARISATION_MODE, produName[22])
        #self.metadata.setMetadataPair(metadata.METADATA_PRODUCT_CLASS, produName[10:13])
        #self.metadata.setMetadataPair('resolutionVariant', produName[14:18])

        # define ascending or not
        if 1==2:
            tmp = self.metadata.getMetadataValue('delta_lat')
            dlat = float(tmp.split(' ')[1]) - float(tmp.split(' ')[0])
            print("########### dlat=%s" % dlat)
            tmp1 = self.metadata.getMetadataValue('delta_utc')
            utc1 = tmp1.split(' ')[0]
            msec1 = int(utc1[-3:])
            utc2 = tmp1.split(' ')[1]
            msec2 = int(utc2[-3:])
            print("########### utc1=%s; msec1=%s; utc2=%s; msec2=%s" % (utc1[0:-4]+'Z', msec1, utc2[0:-4]+'Z', msec2))
            deltaMsec = formatUtils.dateDiffmsec(utc1[0:-4]+'Z', msec1, utc2[0:-4]+'Z', msec2)
            print("########### deltaMsec=%s" % deltaMsec)
            self.metadata.setMetadataPair('deltaMsec', deltaMsec)
            self.metadata.setMetadataPair('dlat', dlat)

        #
        tmp = self.metadata.setMetadataPair(metadata.METADATA_ORBIT, 0)
        self.metadata.setMetadataPair(metadata.METADATA_ORBIT_DIRECTION, 'DESCENDING')
        self.metadata.setMetadataPair(metadata.METADATA_PRODUCT_CLASS, "EEC")
        if 1 == 2:
            if deltaMsec >= 0:
                if dlat >= 0:
                    self.metadata.setMetadataPair(metadata.METADATA_ORBIT_DIRECTION, 'ASCENDING')
                else:
                    self.metadata.setMetadataPair(metadata.METADATA_ORBIT_DIRECTION, 'DESCENDING')
            else:
                if dlat >= 0:
                    self.metadata.setMetadataPair(metadata.METADATA_ORBIT_DIRECTION, 'DESCENDING')
                else:
                    self.metadata.setMetadataPair(metadata.METADATA_ORBIT_DIRECTION, 'ASCENDING')


        #
        self.metadata.setMetadataPair(metadata.METADATA_IMAGING_MODE, self.metadata.getMetadataValue(metadata.METADATA_SENSOR_OPERATIONAL_MODE))
        typecode = self.buildTypeCode()

        # some typecode have no boundingBox and other fields
        if typecode in self.BOUNDING_BOX_FLAG:
            # bounding box
            self.metadata.addLocalAttribute("boundingBox", self.boundingBox)
            self.metadata.setMetadataPair(metadata.METADATA_BOUNDING_BOX, self.boundingBox)
            print(" ######################## typecode %s in BOUNDING_BOX_FLAG map" % typecode)
            self.useBbox = True
        else:
            print(" ######################## typecode %s NOT in BOUNDING_BOX_FLAG map" % typecode)
            self.useBbox = False

        #
        tmp = self.metadata.getMetadataValue(metadata.METADATA_ANTENNA_LOOK_DIRECTION)
        if tmp == 'right':
            self.metadata.setMetadataPair(metadata.METADATA_ANTENNA_LOOK_DIRECTION, 'RIGHT')
        elif tmp == 'left':
            self.metadata.setMetadataPair(metadata.METADATA_ANTENNA_LOOK_DIRECTION, 'LEFT')
        else:
            self.metadata.setMetadataPair(metadata.METADATA_ANTENNA_LOOK_DIRECTION, 'UNDEFINED')

        # perform some check
        IM = self.metadata.getMetadataValue(metadata.METADATA_IMAGING_MODE)
        PC = self.metadata.getMetadataValue(metadata.METADATA_POLARISATION_CHANNELS)
        if PC.find('/')>0:
            PC=PC.replace('/', ', ')
            self.metadata.setMetadataPair(metadata.METADATA_POLARISATION_CHANNELS, PC)
        PM = self.metadata.getMetadataValue(metadata.METADATA_POLARISATION_MODE)
        # check agains possible reference polarization as per EoSip table 3.3. syntax: ImagingMode_PolarizationMode_PolarizationChannel
        if "%s_%s_%s" % (IM, PM, PC) not in self.REF_POLARIZATIONS_LUT:
            raise Exception("polarization value unknown:%s" % "%s_%s_%s" % (IM, PM, PC))
        #if  not tmp in self.REF_POLARIZATIONS:
        #    raise Exception("Unknown polarization channel:%s" % tmp)

    #
    # 
    #
    def buildTypeCode(self):
        typeCode = "SAR_%s_%s" % (self.metadata.getMetadataValue(metadata.METADATA_IMAGING_MODE), self.metadata.getMetadataValue(metadata.METADATA_PRODUCT_CLASS))
        if not typeCode in self.REF_TYPECODES:
            raise Exception("Invalid typeCode:%s" % typeCode)
        self.metadata.setMetadataPair(metadata.METADATA_TYPECODE, typeCode)
        return typeCode

    #
    # extract quality
    #
    def extractQuality(self, helper):
        pass


    #
    # extract the footprint posList point, ccw, lat lon
    #
    def extractFootprint(self, helper):
        #
        pass

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


