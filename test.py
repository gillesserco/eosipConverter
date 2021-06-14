# -*- coding: cp1252 -*-
#
#
#
#
import subprocess
import os, sys
import time
import zipfile
import traceback
import xmlHelper
import eoSip_converter.esaProducts.formatUtils as formatUtils
from datetime import datetime, timedelta
from lxml import etree


debug=0

xmlMapping = {
    'productVariant': 'keys/feature*@key==productVariant',
    'METADATA_START_DATE':'temporalCoverage/startTime',
}

toto='/home/gilles/shared/converter_workspace/tmpspace/terrasarx/batch_terrasarx_terrasarx_workfolder_0/dims_op_oc_dfd2_554486262_1/iif/TDX1_SAR__EEC_SE___HS_S_SRA_20170912T104523_20170912T104523/L1B_iif.xml'


debug = 1

#
# updated xml metadata extract
#
#
def xmlExtract(xmlData, aMetadata, xmlMapping):
    helper = xmlHelper.XmlHelper()
    helper.setDebug(1)

    fd=open(toto, 'r')
    metContent=fd.read()
    fd.close()
    helper.setData(metContent);
    helper.parseData()

    # get fields
    resultList = []
    op_element = helper.getRootNode()
    num_added = 0

    for field in xmlMapping:
        print "\n\nmetadata extract field:%s" % field
        multiple=False
        attr=None
        aPath=None
        aValue=None
        if xmlMapping[field].find("@") >= 0:
            attr = xmlMapping[field].split('@')[1]
            aPath = xmlMapping[field].split('@')[0]
            if aPath.endswith('*'):
                multiple=True
                aPath=aPath[0:-1]
                print " -> multiple used on path:%s" % aPath
        else:
            attr = None
            aPath = xmlMapping[field]

        if not multiple:
            aNode = helper.getFirstNodeByPath(None, aPath, None)
            if aNode == None:
                aValue = None
            else:
                if attr == None: # return NODE TEXT
                    aValue = helper.getNodeText(aNode)
                else: # return attribute TEXT
                    aValue = helper.getNodeAttributeText(aNode, attr)

            if debug != 0:
                print "  --> metadata[%s]: %s=%s" % (num_added, field, aValue)
            aMetadata.setMetadataPair(field, aValue)
            num_added = num_added + 1
        else: # will return NODE TEXT
            aList=[]
            helper.getNodeByPath(None, aPath, attr, aList)
            print " -> multiple; list of node found:%s" % len(aList)
            if len(aList)>0:
                for aNode in aList:
                    aValue = helper.getNodeText(aNode)
                    if debug != 0:
                        print "  --> metadata multiple[%s]: %s=%s" % (num_added, field, aValue)
                    aMetadata.setMetadataPair(field, aValue)
                    num_added = num_added + 1

        return num_added



from osgeo import gdal
from osgeo import ogr
from osgeo import osr

#
#
#
def getTifCorners(src):
    ulx, xres, xskew, uly, yskew, yres  = src.GetGeoTransform()
    lrx = ulx + (src.RasterXSize * xres)
    lry = uly + (src.RasterYSize * yres)
    print(" ######################### tif corners:%s %s %s %s" % (ulx, uly, lrx, lry))
    return ulx, uly, lrx, lry


def getCoordinates(tifPath):
    print("######################### getCoordinates of:'%s'" % tifPath)
    src = gdal.Open(tifPath)
    # Setup the source projection - you can also import from epsg, proj4...
    source = osr.SpatialReference()
    proj = src.GetProjection()
    print("######################### proj:%s" % proj)
    source.ImportFromWkt(proj)

    # The target projection
    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)

    # Create the transform - this can be used repeatedly
    transform = osr.CoordinateTransformation(source, target)

    # Transform the point. You can also create an ogr geometry and use the more generic `point.Transform()`
    ulx, uly, lrx, lry = getTifCorners(src)
    print("%s" % (transform.TransformPoint(ulx, uly),))
    #transform.TransformPoint(lrx, lry)
    #print(" ######################### tif coords:%s %s %s %s" % (a, b, c, d))



def GetExtent(gt,cols,rows):
    ''' Return list of corner coordinates from a geotransform

        @type gt:   C{tuple/list}
        @param gt: geotransform
        @type cols:   C{int}
        @param cols: number of columns in the dataset
        @type rows:   C{int}
        @param rows: number of rows in the dataset
        @rtype:    C{[float,...,float]}
        @return:   coordinates of each corner
    '''
    ext=[]
    xarr=[0,cols]
    yarr=[0,rows]

    for px in xarr:
        for py in yarr:
            x=gt[0]+(px*gt[1])+(py*gt[2])
            y=gt[3]+(px*gt[4])+(py*gt[5])
            ext.append([x,y])
            print x,y
        yarr.reverse()
    return ext

def ReprojectCoords(coords, src_srs, tgt_srs):
    ''' Reproject a list of x,y coordinates.

        @type geom:     C{tuple/list}
        @param geom:    List of [[x,y],...[x,y]] coordinates
        @type src_srs:  C{osr.SpatialReference}
        @param src_srs: OSR SpatialReference object
        @type tgt_srs:  C{osr.SpatialReference}
        @param tgt_srs: OSR SpatialReference object
        @rtype:         C{tuple/list}
        @return:        List of transformed [[x,y],...[x,y]] coordinates
    '''
    trans_coords=[]
    transform = osr.CoordinateTransformation( src_srs, tgt_srs)
    for x,y in coords:
        print(" ## will transform:%s %s" % (x, y))
        a=[x,y,0]
        x,y,z = transform.TransformPoint(a)
        trans_coords.append([x,y])
    return trans_coords




def testRadarsat():
    raster = "/home/gilles/shared/converter_workspace/tmpspace/radarsat/batch_radarsat_001_workfolder_0/RS2_OK29675_PK308710_DK264976_S3_20120705_050236_HH_SLC/imagery_HH.tif"
    ds = gdal.Open(raster)

    prj = ds.GetProjection()
    print(" ############## prj:%s" % (prj,))

    srs = osr.SpatialReference(wkt=prj)
    if srs.IsProjected:
        print " is projected:%s" % srs.GetAttrValue('projcs')
    else:
        print " is not projected"
    print " geogcs:%s" % srs.GetAttrValue('geogcs')
    print(" ############## srs:%s" % srs)
    print(" ############## srs AUTHORITY 0:%s" % srs.GetAttrValue("AUTHORITY", 0))
    print(" ############## srs AUTHORITY 1:%s" % srs.GetAttrValue("AUTHORITY", 1))

    gt = ds.GetGeoTransform()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    ext = GetExtent(gt, cols, rows)
    print(" ############## ext:%s" % ext)

    os._exit(0)


    src_srs = osr.SpatialReference()
    print(" ############## empty src_srs:%s" % src_srs)

    src_srs.ImportFromWkt(ds.GetProjection())
    print(" ############## filled src_srs:%s" % src_srs)

    print(" ############## src_srs authorityCode:%s" % src_srs.GetAttrValue("AUTHORITY", 0))
    #print(" ############## src_srs authorityCode:%s" % src_srs.GetAuthorityCode())








    print(" ############## test src_srs:%s" % src_srs.ExportToWkt())

    os._exit(0)

    tgt_srs = osr.SpatialReference()
    tgt_srs.ImportFromEPSG(4326)
    print(" ############## tgt_srs:%s" % tgt_srs)
    # tgt_srs = src_srs.CloneGeogCS()

    geo_ext = ReprojectCoords(ext, src_srs, tgt_srs)
    print(" ############## geo_ext:%s" % (geo_ext,))

#
#
#
def testXmlExtract():
    helper = xmlHelper.XmlHelper()
    helper.setDebug(1)

    fd=open(toto, 'r')
    metContent=fd.read()
    fd.close()
    helper.setData(metContent);
    helper.parseData()

    # get fields
    resultList = []
    op_element = helper.getRootNode()
    num_added = 0

    for field in xmlMapping:
        print "\n\nmetadata extract field:%s" % field
        multiple=False
        attr=None
        aPath=None
        aValue=None
        if xmlMapping[field].find("@") >= 0:
            attr = xmlMapping[field].split('@')[1]
            aPath = xmlMapping[field].split('@')[0]
            if aPath.endswith('*'):
                multiple=True
                aPath=aPath[0:-1]
                print " -> multiple used on path:%s" % aPath
        else:
            attr = None
            aPath = xmlMapping[field]

        if not multiple:
            aNode = helper.getFirstNodeByPath(None, aPath, None)
            if aNode == None:
                aValue = None
            else:
                if attr == None: # return NODE TEXT
                    aValue = helper.getNodeText(aNode)
                else: # return attribute TEXT
                    aValue = helper.getNodeAttributeText(aNode, attr)

            if debug != 0:
                print "  --> metadata[%s]: %s=%s" % (num_added, field, aValue)
            num_added = num_added + 1
        else: # will return NODE TEXT
            aList=[]
            helper.getNodeByPath(None, aPath, attr, aList)
            print " -> multiple; list of node found:%s" % len(aList)
            if len(aList)>0:
                for aNode in aList:
                    aValue = helper.getNodeText(aNode)
                    if debug != 0:
                        print "  --> metadata multiple[%s]: %s=%s" % (num_added, field, aValue)
                    num_added = num_added + 1


import xmlHelper as xmlHelper

def testRadarsatFootprint(anXmlFile):
    direction = "ASCENDING"
    direction = "DESCENDING"

    helper = xmlHelper.XmlHelper()
    fd=open(anXmlFile)
    xmlData=fd.read()
    fd.close()
    helper.setData(xmlData)
    helper.parseData()

    aNode = helper.getFirstNodeByPath(None, 'imageAttributes/geographicInformation/geolocationGrid', None)
    print(" geolocationGrid node:%s" % aNode)
    numLines = 0
    numColumns = 0
    if aNode is not None:

        nodeList = []
        helper.getNodeByPath(aNode, 'imageTiePoint', None, nodeList)
        #print(" nodeList:%s" % nodeList)

        """
                <imageTiePoint>
					<imageCoordinate>
						<line>0.00000000e+00</line>
						<pixel>0.00000000e+00</pixel>
					</imageCoordinate>
					<geodeticCoordinate>
						<latitude units="deg">3.888173047761543e+01</latitude>
						<longitude units="deg">1.560557539067346e+01</longitude>
						<height units="m">1.963720855712891e+02</height>
					</geodeticCoordinate>
				</imageTiePoint>
		"""

        currentLineIndex = 0
        currentPixelIndex = 0
        lastPixel = -1
        imCoords=None
        geoCoords=None
        #
        lastImCoords=None
        possibleLastLLNode=None
        ULNode = None
        URNode = None
        #
        lastGeoCoords=None
        possibleLastLLGeoNode=None
        ULGeoNode = None
        URGeoNode = None

        print(" doing line:%s" % currentLineIndex)
        for aNode in nodeList:
            #print(" a node:%s" % aNode)
            imCoords = helper.getFirstNodeByPath(aNode, '/imageCoordinate')
            geoCoords = helper.getFirstNodeByPath(aNode, '/geodeticCoordinate')
            #print("  imCoords:%s" % imCoords)
            lineNode = helper.getFirstNodeByPath(imCoords, 'line')
            pixelNode = helper.getFirstNodeByPath(imCoords, 'pixel')
            line = eval(helper.getNodeText(lineNode))
            pixel = eval(helper.getNodeText(pixelNode))
            print("  line:%s; pixel:%s" % (line, pixel))

            if currentPixelIndex==0:
                possibleLastLL=imCoords
                possibleLastLLGeoNode=geoCoords

            if currentLineIndex==0:
                if currentPixelIndex==0:
                    ULNode=imCoords
                    ULGeoNode = geoCoords
                    print(" ## GOT UL")

            currentPixelIndex+=1
            if pixel < lastPixel: # go to new line
                if currentLineIndex==0:
                    print(" ## GOT UR")
                    URNode = lastImCoords
                    URGeoNode = lastGeoCoords

                currentLineIndex +=1
                currentPixelIndex=0
                print( " doing line:%s" % currentLineIndex)

            lastImCoords = imCoords
            lastGeoCoords = geoCoords
            lastPixel=pixel


        footprint=""
        print(" #### UL:%s" % ULNode)
        lineNode = helper.getFirstNodeByPath(ULNode, 'line')
        pixelNode = helper.getFirstNodeByPath(ULNode, 'pixel')
        line = eval(helper.getNodeText(lineNode))
        pixel = eval(helper.getNodeText(pixelNode))
        print("   -->   line:%s; pixel:%s" % (line, pixel))
        latNode = helper.getFirstNodeByPath(ULGeoNode, 'latitude')
        lonNode = helper.getFirstNodeByPath(ULGeoNode, 'longitude')
        lat = eval(helper.getNodeText(latNode))
        lon = eval(helper.getNodeText(lonNode))
        print("   ---->>   lat:%s; lon:%s" % (lat, lon))
        footprint_ul= "%s %s" % (lat, lon)

        #
        print(" #### UR:%s" % URNode)
        lineNode = helper.getFirstNodeByPath(URNode, 'line')
        pixelNode = helper.getFirstNodeByPath(URNode, 'pixel')
        line = eval(helper.getNodeText(lineNode))
        pixel = eval(helper.getNodeText(pixelNode))
        print("   -->   line:%s; pixel:%s" % (line, pixel))
        latNode = helper.getFirstNodeByPath(URGeoNode, 'latitude')
        lonNode = helper.getFirstNodeByPath(URGeoNode, 'longitude')
        lat = eval(helper.getNodeText(latNode))
        lon = eval(helper.getNodeText(lonNode))
        print("   ---->>   lat:%s; lon:%s" % (lat, lon))
        footprint_ur = "%s %s" % (lat, lon)

        #
        print(" #### LL:%s" % possibleLastLL)
        lineNode = helper.getFirstNodeByPath(possibleLastLL, 'line')
        pixelNode = helper.getFirstNodeByPath(possibleLastLL, 'pixel')
        line = eval(helper.getNodeText(lineNode))
        pixel = eval(helper.getNodeText(pixelNode))
        print("   -->   line:%s; pixel:%s" % (line, pixel))
        latNode = helper.getFirstNodeByPath(possibleLastLLGeoNode, 'latitude')
        lonNode = helper.getFirstNodeByPath(possibleLastLLGeoNode, 'longitude')
        lat = eval(helper.getNodeText(latNode))
        lon = eval(helper.getNodeText(lonNode))
        print("   ---->>   lat:%s; lon:%s" % (lat, lon))
        footprint_ll = "%s %s" % (lat, lon)

        #
        print(" #### LR:%s" % imCoords)
        lineNode = helper.getFirstNodeByPath(imCoords, 'line')
        pixelNode = helper.getFirstNodeByPath(imCoords, 'pixel')
        line = eval(helper.getNodeText(lineNode))
        pixel = eval(helper.getNodeText(pixelNode))
        print("   -->   line:%s; pixel:%s" % (line, pixel))
        latNode = helper.getFirstNodeByPath(geoCoords, 'latitude')
        lonNode = helper.getFirstNodeByPath(geoCoords, 'longitude')
        lat = eval(helper.getNodeText(latNode))
        lon = eval(helper.getNodeText(lonNode))
        print("   ---->>   lat:%s; lon:%s" % (lat, lon))
        footprint_lr = "%s %s" % (lat, lon)

        if direction=="DESCENDING":
            footprint = "%s %s %s %s %s" % (footprint_ul, footprint_ll, footprint_lr, footprint_ur, footprint_ul)
        else:
            footprint = "%s %s %s %s %s" % (footprint_lr, footprint_ur, footprint_ul, footprint_ll, footprint_lr)

        print " ==> footprint=%s" % footprint
        return footprint

def leftPadString(s, size, pad):
    result = s
    while len(result) < size:
        result = pad + result;
    return result;



def makeGoceLut():
    REF_TYPECODE = ['EGG_NOM_1b', 'STR_VC2_1b', 'STR_VC3_1b', 'SST_NOM_1b', 'SST_RIN_1b',
                    'EGG_NOM_2_', 'EGG_TRF_2_', 'GRC_SPW_2_', 'GRD_SPW_2_', 'EGM_GOC_2_', 'EGM_GVC_2_', 'EGM_QLK_2I',
                    'GGG_225_2_', 'GGG_255_2_', 'TGG_225_2_', 'TGG_255_2_', 'GRF_GOC_2_', 'TRF_GOC_2_', 'MGG_NTC_2_',
                    'MGG_WTC_2_', 'MTR_GOC_1B', 'TDC_GOC_2_', 'SLA_GOC_2_', 'ACC_DF1_1B', 'ACC_DF2_1B', 'ACC_DF3_1B',
                    'ACC_DF4_1B', 'ACC_DF5_1B', 'ACC_DF6_1B', 'SST_PSO_2_', 'SST_AUX_2_', 'TEC_TMS_2_', 'VTGOCE_DS_',
                    'HKT_GOC_0_', 'MGM_GO1_1B', 'MGM_GO2_1B', 'MGM_GO3_1B']

    fd=open('goce_doi_lut_table.dat', 'w')
    for item in REF_TYPECODE:
        fd.write("'%s': 'DOI_%s',\n" % (item, item))

    for i in range(12000):
        fd.write("'T_%s': 'DOI_T_%s',\n" % (leftPadString("%s" % i, 8, '0'), leftPadString("%s" % i, 8, '0')))
    fd.flush()
    fd.close()


ns={'gsc': 'http://earth.esa.int/gsc',
            'gml': 'http://www.opengis.net/gml',
            'eop': 'http://earth.esa.int/eop',
            'opt': 'http://earth.esa.int/opt'}

#
#
#
def getXmlNodeValueAtPath(rootXmlNode, aXpath):


    aNodeList = rootXmlNode.xpath(aXpath, namespaces=ns)
    if len(aNodeList) == 1:
        if not aNodeList[0].text:
            print(" #### NOT FOUND:%s; not text element:%s" % (aNodeList, aNodeList[0]))
            return None
        else:
            print(" #### FOUND:%s; text=%s" % (aNodeList, aNodeList[0].text))
            return aNodeList[0].text
    else:
        print(" #### NOT FOUND:%s; list empty" % (aNodeList))
        return None

xmlMapping_XPATH = {
    #
    'toto': '//gsc:responsibleOrgName',
    'start': '//gsc:opt_metadata/gml:validTime/gml:TimePeriod/gml:beginPosition',
    'stop': '//gsc:opt_metadata/gml:validTime/gml:TimePeriod/gml:endPosition',
    'platform':'//gsc:opt_metadata/gml:using/eop:EarthObservationEquipment/eop:platform/eop:Platform/eop:shortName',
    'platformId':'//gsc:opt_metadata/gml:using/eop:EarthObservationEquipment/eop:platform/eop:Platform/eop:serialIdentifier',
    'instrument':'//gsc:opt_metadata/gml:using/eop:EarthObservationEquipment/eop:instrument/eop:Instrument/eop:shortName',
    'sensor':'//gsc:opt_metadata/gml:using/eop:EarthObservationEquipment/eop:sensor/eop:Sensor/eop:sensorType',
    'footprint':'//gsc:opt_metadata/gml:target/eop:Footprint/gml:multiExtentOf/gml:MultiSurface/gml:surfaceMembers/gml:Polygon/gml:exterior/gml:LinearRing/gml:posList',
    'cloudCover':'//gsc:opt_metadata/gml:resultOf/opt:EarthObservationResult/opt:cloudCoverPercentage',
    'cloudCoverQuotation':'//gsc:opt_metadata/gml:resultOf/opt:EarthObservationResult/opt:cloudCoverPercentageQuotationMode',
}


if __name__ == '__main__':
    try:

        a="SAR_SX_SLC - SAR_SX_SGF - SAR_SX_SGX - SAR_SX_SSG - SAR_SX_SPG - SAR_WX_SLC - SAR_WX_SGF - SAR_WX_SGX - SAR_WX_SSG - SAR_WX_SPG - SAR_FX_SLC - SAR_FX_SGF - SAR_FX_SGX - SAR_FX_SSG - SAR_FX_SPG - SAR_FW_SLC - SAR_FW_SGF - SAR_FW_SGX - SAR_FW_SSG - SAR_FW_SPG - SAR_MF_SLC - SAR_MF_SGF - SAR_MF_SGX - SAR_MF_SSG - SAR_MF_SPG - SAR_MW_SLC - SAR_MW_SGF - SAR_MW_SGX - SAR_MW_SSG - SAR_MW_SPG - SAR_EF_SLC - SAR_EF_SGF - SAR_EF_SGX - SAR_EF_SSG - SAR_EF_SPG - SAR_UF_SLC - SAR_UF_SGF - SAR_UF_SGX  - SAR_UF_SSG - SAR_UF_SPG - SAR_UW_SLC - SAR_UW_SGF - SAR_UW_SGX - SAR_UW_SSG - SAR_UW_SPG - SAR_EH_SLC - SAR_EH_SGF - SAR_EH_SGX - SAR_EH_SSG - SAR_EH_SPG - SAR_EL_SLC - SAR_EL_SGF - SAR_EL_SGX - SAR_EL_SSG - SAR_EL_SPG - SAR_SQ_SLC - SAR_SQ_SGX - SAR_SQ_SSG - SAR_SQ_SPG - SAR_QS_SLC - SAR_QS_SGX - SAR_QS_SSG - SAR_QS_SPG - SAR_FQ_SLC - SAR_FQ_SGX - SAR_FQ_SSG - SAR_FQ_SPG - SAR_QF_SLC - SAR_QF_SGX - SAR_QF_SSG - SAR_QF_SPG - SAR_SN_SCN - SAR_SN_SCF - SAR_SN_SCS - SAR_SW_SCW - SAR_SW_SCF - SAR_SW_SCS - SAR_SL_SLC - SAR_SL_SGF - SAR_SL_SGX - SAR_SL_SSG - SAR_SL_SPG"
        b=[]
        for item in a.split(" _ "):
            b.append(item)
        print b
        os._exit(0)

        aPath = '/home/gilles/shared/WEB_TOOLS/MISSIONS/Worldview2/NEW_DATASET/EW02_WV1_PM8_SO_20130403T110426_20130403T110429_DGI_18283_2402.0000/GSC#CR#ESA#VHR1-2_Urban_Atlas_2012#20151002#054228.xml'
        num_added=0
        start = time.time()
        rootXmlNode = etree.parse(aPath)
        for key in xmlMapping_XPATH:
            print " ###################### will use xml XPATH mapping:%s using path:%s" % (key, xmlMapping_XPATH[key])
            a = getXmlNodeValueAtPath(rootXmlNode, xmlMapping_XPATH[key])

        duration = time.time()-start
        os._exit(0)


        gpsEpochStr='1005000553.299677000'

        gpsMicro = gpsEpochStr.split('.')[1][0:6]
        gpsMicro = int(gpsMicro)
        gpsSec = gpsEpochStr.split('.')[0]
        gpsSec = int(gpsSec)
        print(" gpsTimeToUtc: sec=%s; msec=%s" % (gpsSec, gpsMicro))
        sec = int(gpsSec) - 15
        if sec >= 1025132400:
            sec -= 1

        initTime = formatUtils.timeFromDatePatterm('1980-01-06T00:00:00Z')
        d2 = initTime + timedelta(seconds=sec, microseconds=gpsMicro)
        timeStr = "%sZ" % d2.strftime('%Y-%m-%dT%H:%M:%S.%f')[0:-3]
        print(" gpsTimeToUtc: %s -> %s" % (gpsEpochStr, timeStr))
        os._exit(0)






        xmlFile = "/home/gilles/shared/converter_workspace/tmpspace/radarsat/batch_radarsat_001_workfolder_0/RS2_OK29675_PK308710_DK264976_S3_20120705_050236_HH_SLC/product.xml"

        #testRadarsatFootprint(xmlFile)

        #sys.exit(0)

        makeGoceLut()
        sys.exit(0)

        testRadarsat()

        #testXmlExtract()
        sys.exit(0)
            
    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)