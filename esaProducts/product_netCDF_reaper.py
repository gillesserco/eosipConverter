# -*- coding: cp1252 -*-
#
# this class is a base class for directory product
#
#
import os, sys
import re
import logging
import traceback
import metadata
import browse_metadata
import formatUtils
import valid_values
from product_netCDFimport  import Product_netCDF





class Product_NetCDF_Reaper(Product_netCDF):
    
    #
    # reaper product global attributes
    #
    ATTRIBUTE__PROC_STAGE='proc_stage'
    ATTRIBUTE__L2_REF_DOC='l2_ref_doc'
    ATTRIBUTE__ACQUISITION_STATION='acquisition_station'
    ATTRIBUTE__MISSION='mission'
    ATTRIBUTE__PRODUCT='product'
    ATTRIBUTE__PROC_CENTRE='proc_centre'
    ATTRIBUTE__PROC_TIME='proc_time'
    ATTRIBUTE__L2_PROC_TIME='l2_proc_time'
    ATTRIBUTE__SOFTWARE_VER='software_ver'
    ATTRIBUTE__L2_SOFTWARE_VER='l2_software_ver'
    ATTRIBUTE__SENSING_START='sensing_start'
    ATTRIBUTE__SENSING_STOP='sensing_stop'
    ATTRIBUTE__PHASE='phase'
    ATTRIBUTE__CYCLE='cycle'
    ATTRIBUTE__REL_ORBIT='rel_orbit'
    ATTRIBUTE__ABS_ORBIT='abs_orbit'
    ATTRIBUTE__STATE_VECTOR_TIME='state_vector_time'
    ATTRIBUTE__DELTA_UT1='delta_ut1'
    ATTRIBUTE__X_POSITION='x_position'
    ATTRIBUTE__Y_POSITION='y_position'
    ATTRIBUTE__Z_POSITION='z_position'
    ATTRIBUTE__X_VELOCITY='x_velocity'
    ATTRIBUTE__Y_VELOCITY='y_velocity'
    ATTRIBUTE__Z_VELOCITY='z_velocity'
    ATTRIBUTE__VECTOR_SOURCE='vector_source'
    ATTRIBUTE__UTC_SBT_TIME='utc_sbt_time'
    ATTRIBUTE__SAT_BINARY_TIME='sat_binary_time'
    ATTRIBUTE__CLOCK_STEP='clock_step'
    ATTRIBUTE__LEAP_UTC='leap_utc'
    ATTRIBUTE__LEAP_SIGN='leap_sign'
    ATTRIBUTE__LEAP_ERR='leap_err'
    ATTRIBUTE__PRODUCT_ERR='product_err'
    ATTRIBUTE__RA0_FIRST_RECORD_TIME='ra0_first_record_time'
    ATTRIBUTE__RA0_LAST_RECORD_TIME='ra0_last_record_time'
    ATTRIBUTE__RA0_FIRST_LAT='ra0_first_lat'
    ATTRIBUTE__RA0_FIRST_LONG='ra0_first_long'
    ATTRIBUTE__RA0_LAST_LAT='ra0_last_lat'
    ATTRIBUTE__RA0_LAST_LONG='ra0_last_long'
    ATTRIBUTE__RA0_PROC_FLAG='ra0_proc_flag'
    ATTRIBUTE__RA0_HEADER_FLAG='ra0_header_flag'
    ATTRIBUTE__RA0_PROCESSING_QUALITY='ra0_processing_quality'
    ATTRIBUTE__RA0_HEADER_QUALITY='ra0_header_quality'
    ATTRIBUTE__RA0_ACQUISITION_PERCENT='ra0_acquisition_percent'
    ATTRIBUTE__RA0_TRACKING_OCEAN_PERCENT='ra0_tracking_ocean_percent'
    ATTRIBUTE__RA0_TRACKING_ICE_PERCENT='ra0_tracking_ice_percent'
    ATTRIBUTE__RA0_IF_CAL_PERCENT='ra0_if_cal_percent'
    ATTRIBUTE__RA0_OLC_PTR_PERCENT='ra0_olc_ptr_percent'
    ATTRIBUTE__USO_APPLIED_1='uso_applied_1'
    ATTRIBUTE__USO_APPLIED_2='uso_applied_2'
    ATTRIBUTE__USO_APPLIED_3='uso_applied_3'
    ATTRIBUTE__OCEAN_RETRACKER_VERSION_FOR_OCEAN='ocean_retracker_version_for_ocean'
    ATTRIBUTE__OCEAN_RETRACKER_VERSION_FOR_ICE='ocean_retracker_version_for_ice'
    ATTRIBUTE__SPTR_MISSING='sptr_missing'
    ATTRIBUTE__REFERENCE_DSD_1_DS_NAME='reference_DSD_1_DS_name'
    ATTRIBUTE__REFERENCE_DSD_1_FILENAME='reference_DSD_1_filename'
    ATTRIBUTE__REFERENCE_DSD_2_DS_NAME='reference_DSD_2_DS_name'
    ATTRIBUTE__REFERENCE_DSD_2_FILENAME='reference_DSD_2_filename'
    ATTRIBUTE__REFERENCE_DSD_3_DS_NAME='reference_DSD_3_DS_name'
    ATTRIBUTE__REFERENCE_DSD_3_FILENAME='reference_DSD_3_filename'
    ATTRIBUTE__REFERENCE_DSD_4_DS_NAME='reference_DSD_4_DS_name'
    ATTRIBUTE__REFERENCE_DSD_4_FILENAME='reference_DSD_4_filename'
    ATTRIBUTE__REFERENCE_DSD_5_DS_NAME='reference_DSD_5_DS_name'
    ATTRIBUTE__REFERENCE_DSD_5_FILENAME='reference_DSD_5_filename'
    ATTRIBUTE__REFERENCE_DSD_6_DS_NAME='reference_DSD_6_DS_name'
    ATTRIBUTE__REFERENCE_DSD_6_FILENAME='reference_DSD_6_filename'
    ATTRIBUTE__REFERENCE_DSD_7_DS_NAME='reference_DSD_7_DS_name'
    ATTRIBUTE__REFERENCE_DSD_7_FILENAME='reference_DSD_7_filename'
    ATTRIBUTE__REFERENCE_DSD_8_DS_NAME='reference_DSD_8_DS_name'
    ATTRIBUTE__REFERENCE_DSD_8_FILENAME='reference_DSD_8_filename'
    ATTRIBUTE__REFERENCE_DSD_9_DS_NAME='reference_DSD_9_DS_name'
    ATTRIBUTE__REFERENCE_DSD_9_FILENAME='reference_DSD_9_filename'
    ATTRIBUTE__REFERENCE_DSD_10_DS_NAME='reference_DSD_10_DS_name'
    ATTRIBUTE__REFERENCE_DSD_10_FILENAME='reference_DSD_10_filename'
    ATTRIBUTE__REFERENCE_DSD_11_DS_NAME='reference_DSD_11_DS_name'
    ATTRIBUTE__REFERENCE_DSD_11_FILENAME='reference_DSD_11_filename'
    ATTRIBUTE__REFERENCE_DSD_12_DS_NAME='reference_DSD_12_DS_name'
    ATTRIBUTE__REFERENCE_DSD_12_FILENAME='reference_DSD_12_filename'
    ATTRIBUTE__REFERENCE_DSD_13_DS_NAME='reference_DSD_13_DS_name'
    ATTRIBUTE__REFERENCE_DSD_13_FILENAME='reference_DSD_13_filename'
    ATTRIBUTE__REFERENCE_DSD_14_DS_NAME='reference_DSD_14_DS_name'
    ATTRIBUTE__REFERENCE_DSD_14_FILENAME='reference_DSD_14_filename'
    ATTRIBUTE__REFERENCE_DSD_15_DS_NAME='reference_DSD_15_DS_name'
    ATTRIBUTE__REFERENCE_DSD_15_FILENAME='reference_DSD_15_filename'
    ATTRIBUTE__REFERENCE_DSD_16_DS_NAME='reference_DSD_16_DS_name'
    ATTRIBUTE__REFERENCE_DSD_16_FILENAME='reference_DSD_16_filename'
    ATTRIBUTE__REFERENCE_DSD_17_DS_NAME='reference_DSD_17_DS_name'
    ATTRIBUTE__REFERENCE_DSD_17_FILENAME='reference_DSD_17_filename'
    ATTRIBUTE__REFERENCE_DSD_18_DS_NAME='reference_DSD_18_DS_name'
    ATTRIBUTE__REFERENCE_DSD_18_FILENAME='reference_DSD_18_filename'
    ATTRIBUTE__REFERENCE_DSD_19_DS_NAME='reference_DSD_19_DS_name'
    ATTRIBUTE__REFERENCE_DSD_19_FILENAME='reference_DSD_19_filename'
    ATTRIBUTE__REFERENCE_DSD_20_DS_NAME='reference_DSD_20_DS_name'
    ATTRIBUTE__REFERENCE_DSD_20_FILENAME='reference_DSD_20_filename'
    ATTRIBUTE__REFERENCE_DSD_21_DS_NAME='reference_DSD_21_DS_name'
    ATTRIBUTE__REFERENCE_DSD_21_FILENAME='reference_DSD_21_filename'
    ATTRIBUTE__REFERENCE_DSD_22_DS_NAME='reference_DSD_22_DS_name'
    ATTRIBUTE__REFERENCE_DSD_22_FILENAME='reference_DSD_22_filename'
    ATTRIBUTE__REFERENCE_DSD_23_DS_NAME='reference_DSD_23_DS_name'
    ATTRIBUTE__REFERENCE_DSD_23_FILENAME='reference_DSD_23_filename'
    ATTRIBUTE__REFERENCE_DSD_24_DS_NAME='reference_DSD_24_DS_name'
    ATTRIBUTE__REFERENCE_DSD_24_FILENAME='reference_DSD_24_filename'
    ATTRIBUTE__REFERENCE_DSD_25_DS_NAME='reference_DSD_25_DS_name'
    ATTRIBUTE__REFERENCE_DSD_25_FILENAME='reference_DSD_25_filename'
    ATTRIBUTE__REFERENCE_DSD_26_DS_NAME='reference_DSD_26_DS_name'
    ATTRIBUTE__REFERENCE_DSD_26_FILENAME='reference_DSD_26_filename'
    ATTRIBUTE__REFERENCE_DSD_27_DS_NAME='reference_DSD_27_DS_name'
    ATTRIBUTE__REFERENCE_DSD_27_FILENAME='reference_DSD_27_filename'
    ATTRIBUTE__REFERENCE_DSD_28_DS_NAME='reference_DSD_28_DS_name'
    ATTRIBUTE__REFERENCE_DSD_28_FILENAME='reference_DSD_28_filename'
    ATTRIBUTE__REFERENCE_DSD_29_DS_NAME='reference_DSD_29_DS_name'
    ATTRIBUTE__REFERENCE_DSD_29_FILENAME='reference_DSD_29_filename'
    ATTRIBUTE__REFERENCE_DSD_30_DS_NAME='reference_DSD_30_DS_name'
    ATTRIBUTE__REFERENCE_DSD_30_FILENAME='reference_DSD_30_filename'
    ATTRIBUTE__REFERENCE_DSD_31_DS_NAME='reference_DSD_31_DS_name'
    ATTRIBUTE__REFERENCE_DSD_31_FILENAME='reference_DSD_31_filename'
    ATTRIBUTE__REFERENCE_DSD_32_DS_NAME='reference_DSD_32_DS_name'
    ATTRIBUTE__REFERENCE_DSD_32_FILENAME='reference_DSD_32_filename'
    ATTRIBUTE__REFERENCE_DSD_33_DS_NAME='reference_DSD_33_DS_name'
    ATTRIBUTE__REFERENCE_DSD_33_FILENAME='reference_DSD_33_filename'
    ATTRIBUTE__REFERENCE_DSD_34_DS_NAME='reference_DSD_34_DS_name'
    ATTRIBUTE__REFERENCE_DSD_34_FILENAME='reference_DSD_34_filename'
    ATTRIBUTE__REFERENCE_DSD_35_DS_NAME='reference_DSD_35_DS_name'
    ATTRIBUTE__REFERENCE_DSD_35_FILENAME='reference_DSD_35_filename'
    ATTRIBUTE__REFERENCE_DSD_36_DS_NAME='reference_DSD_36_DS_name'
    ATTRIBUTE__REFERENCE_DSD_36_FILENAME='reference_DSD_36_filename'
    ATTRIBUTE__REFERENCE_DSD_37_DS_NAME='reference_DSD_37_DS_name'
    ATTRIBUTE__REFERENCE_DSD_37_FILENAME='reference_DSD_37_filename'
    ATTRIBUTE__REFERENCE_DSD_38_DS_NAME='reference_DSD_38_DS_name'
    ATTRIBUTE__REFERENCE_DSD_38_FILENAME='reference_DSD_38_filename'
    ATTRIBUTE__REFERENCE_DSD_39_DS_NAME='reference_DSD_39_DS_name'
    ATTRIBUTE__REFERENCE_DSD_39_FILENAME='reference_DSD_39_filename'
    ATTRIBUTE__REFERENCE_DSD_40_DS_NAME='reference_DSD_40_DS_name'
    ATTRIBUTE__REFERENCE_DSD_40_FILENAME='reference_DSD_40_filename'
    ATTRIBUTE__REFERENCE_DSD_41_DS_NAME='reference_DSD_41_DS_name'
    ATTRIBUTE__REFERENCE_DSD_41_FILENAME='reference_DSD_41_filename'
    ATTRIBUTE__REFERENCE_DSD_42_DS_NAME='reference_DSD_42_DS_name'
    ATTRIBUTE__REFERENCE_DSD_42_FILENAME='reference_DSD_42_filename'
    ATTRIBUTE__REFERENCE_DSD_43_DS_NAME='reference_DSD_43_DS_name'
    ATTRIBUTE__REFERENCE_DSD_43_FILENAME='reference_DSD_43_filename'
    ATTRIBUTE__REFERENCE_DSD_44_DS_NAME='reference_DSD_44_DS_name'
    ATTRIBUTE__REFERENCE_DSD_44_FILENAME='reference_DSD_44_filename'
    ATTRIBUTE__REFERENCE_DSD_45_DS_NAME='reference_DSD_45_DS_name'
    ATTRIBUTE__REFERENCE_DSD_45_FILENAME='reference_DSD_45_filename'
    ATTRIBUTE__REFERENCE_DSD_46_DS_NAME='reference_DSD_46_DS_name'
    ATTRIBUTE__REFERENCE_DSD_46_FILENAME='reference_DSD_46_filename'
    ATTRIBUTE__REFERENCE_DSD_47_DS_NAME='reference_DSD_47_DS_name'
    ATTRIBUTE__REFERENCE_DSD_47_FILENAME='reference_DSD_47_filename'
    ATTRIBUTE__REFERENCE_DSD_48_DS_NAME='reference_DSD_48_DS_name'
    ATTRIBUTE__REFERENCE_DSD_48_FILENAME='reference_DSD_48_filename'
    ATTRIBUTE__REFERENCE_DSD_49_DS_NAME='reference_DSD_49_DS_name'
    ATTRIBUTE__REFERENCE_DSD_49_FILENAME='reference_DSD_49_filename'
    ATTRIBUTE__REFERENCE_DSD_50_DS_NAME='reference_DSD_50_DS_name'
    ATTRIBUTE__REFERENCE_DSD_50_FILENAME='reference_DSD_50_filename'
    ATTRIBUTE__REFERENCE_DSD_51_DS_NAME='reference_DSD_51_DS_name'
    ATTRIBUTE__REFERENCE_DSD_51_FILENAME='reference_DSD_51_filename'
    ATTRIBUTE__REFERENCE_DSD_52_DS_NAME='reference_DSD_52_DS_name'
    ATTRIBUTE__REFERENCE_DSD_52_FILENAME='reference_DSD_52_filename'
    ATTRIBUTE__REFERENCE_DSD_53_DS_NAME='reference_DSD_53_DS_name'
    ATTRIBUTE__REFERENCE_DSD_53_FILENAME='reference_DSD_53_filename'
    ATTRIBUTE__REFERENCE_DSD_54_DS_NAME='reference_DSD_54_DS_name'
    ATTRIBUTE__REFERENCE_DSD_54_FILENAME='reference_DSD_54_filename'
    ATTRIBUTE__REFERENCE_DSD_55_DS_NAME='reference_DSD_55_DS_name'
    ATTRIBUTE__REFERENCE_DSD_55_FILENAME='reference_DSD_55_filename'
    ATTRIBUTE__REFERENCE_DSD_56_DS_NAME='reference_DSD_56_DS_name'
    ATTRIBUTE__REFERENCE_DSD_56_FILENAME='reference_DSD_56_filename'
    ATTRIBUTE__REFERENCE_DSD_COUNT='reference_DSD_count'

    #
    xmlMapping={metadata.METADATA_START_DATE:ATTRIBUTE__SENSING_START,
                metadata.METADATA_STOP_DATE:ATTRIBUTE__SENSING_STOP,
                metadata.METADATA_PROCESSING_CENTER:ATTRIBUTE__PROC_CENTRE,
                metadata.METADATA_PROCESSING_TIME:ATTRIBUTE__PROC_TIME,
                metadata.METADATA_SOFTWARE_VERSION:ATTRIBUTE__L2_SOFTWARE_VER,
                metadata.METADATA_PARENT_PRODUCT:ATTRIBUTE__PRODUCT,
                metadata.METADATA_CYCLE:ATTRIBUTE__CYCLE,
                metadata.METADATA_PHASE:ATTRIBUTE__PHASE,
                metadata.METADATA_RELATIVE_ORBIT:ATTRIBUTE__REL_ORBIT,
                metadata.METADATA_ORBIT:ATTRIBUTE__ABS_ORBIT,
                metadata.METADATA_PROCESSING_STAGE:ATTRIBUTE__PROC_STAGE,
                }

    #
    #
    #
    def __init__(self, path):
        Product_netCDF.__init__(self, path)
        print " init class Product_NetCDF_Reaper"
        


    #
    #
    #
    def extractMetadata(self, met=None):
        #self.DEBUG=1
        if met==None:
            raise Exception("metadate is None")

        # set some evident values
        met.setMetadataPair(metadata.METADATA_PRODUCTNAME, self.origName)
        
        # use what contains the metadata file
        self.getMetadataInfo()
        #print "########## got dict:%s" % dataset.__dict__
        
        # extact metadata, from NETCDF global attributes
        #get fields
        num_added=0
        
        for field in self.xmlMapping:
            rule=self.xmlMapping[field]
            aValue=None
            #if self.DEBUG!=0:
            #    print " ##### handle metadata:%s" % field

            aValue=self.dataset.__dict__[rule]
            if self.debug!=0:
                print " ##### metadata %s=%s" % (field, aValue)
                
            met.setMetadataPair(field, aValue)
            num_added=num_added+1
            
        self.metadata=met

        # use also the filename
        # is like: GDR: E2_TEST_ERS_ALT_2__20010212T060425_20010212T080124_COM5.NC
        # is like: SGDR: E2_TEST_ERS_ALT_2S_20010212T105332_20010212T115740_COM5.NC
        toks=met.getMetadataValue(metadata.METADATA_PRODUCTNAME).split('_')
        if len(toks)>4:
            if len(toks[4])==1:
                met.setMetadataPair(metadata.METADATA_TYPECODE, "%s_%s__%s" % (toks[2],toks[3],toks[4]))
            else:
                met.setMetadataPair(metadata.METADATA_TYPECODE, "%s_%s_%s" % (toks[2],toks[3],toks[4]))
        else:
            print "WARNING: can not get 5 tokens from product name:%s" % toks
        met.setMetadataPair(metadata.METADATA_PLATFORM_ID,toks[0][1])
        
        
   
        return num_added


    #
    # refine the metada, should perform in order:
    #
    def refineMetadata(self):
        # processing time: suppress microsec
        tmp = self.metadata.getMetadataValue(metadata.METADATA_PROCESSING_TIME)
        pos = tmp.find('.')
        if pos > 0:
            tmp=tmp[0:pos]
        pos = tmp.find('Z')
        if pos < 0:
            tmp=tmp+"Z"
        self.metadata.setMetadataPair(metadata.METADATA_PROCESSING_TIME, tmp)
        
        # normalise date string: change 3 digit month into month number
        # also invert date which is dd-mm-yyyy
        tmp = self.metadata.getMetadataValue(metadata.METADATA_START_DATE)
        startDateTime=formatUtils.normaliseDateString(tmp).split('.')[0]
        toks=startDateTime.split('T')[0].split('-')
        self.metadata.setMetadataPair(metadata.METADATA_START_DATE, "%s-%s-%s" % (toks[2],toks[1],toks[0]))
        self.metadata.setMetadataPair(metadata.METADATA_START_TIME, startDateTime.split('T')[1])

        tmp = self.metadata.getMetadataValue(metadata.METADATA_STOP_DATE)
        stopDateTime=formatUtils.normaliseDateString(tmp).split('.')[0]
        toks=stopDateTime.split('T')[0].split('-')
        self.metadata.setMetadataPair(metadata.METADATA_STOP_DATE, "%s-%s-%s" % (toks[2],toks[1],toks[0]))
        self.metadata.setMetadataPair(metadata.METADATA_STOP_TIME, stopDateTime.split('T')[1])

        firstLat=self.dataset.__dict__[self.ATTRIBUTE__RA0_FIRST_LAT]
        firstLon=self.dataset.__dict__[self.ATTRIBUTE__RA0_FIRST_LONG]
        lastLat=self.dataset.__dict__[self.ATTRIBUTE__RA0_LAST_LAT]
        lastLon=self.dataset.__dict__[self.ATTRIBUTE__RA0_LAST_LONG]

        # normalize metadata.METADATA_PROCESSING_TIME: from 17-DEC-2013 20:26:48Z to 2013-12-17T11:57:41Z
        tmp = self.metadata.getMetadataValue(metadata.METADATA_PROCESSING_TIME)
        toks=tmp.split(' ')
        toksDate=toks[0].split('-')
        tmp="%s-%s-%sT%s" % (toksDate[2],toksDate[1],toksDate[0],toks[1])
        self.metadata.setMetadataPair(metadata.METADATA_PROCESSING_TIME, formatUtils.normaliseDateString(tmp))

        # get the footprint from the first/last coordinates
        #footprint="%s %s %s %s %s %s" % (firstLat, firstLon, lastLat, lastLon, firstLat, firstLon)
        footprint=self.getFootprint(0, 1)
        self.metadata.setMetadataPair(metadata.METADATA_FOOTPRINT, footprint)

        # get ascending from z_velocity vector
        tmp=self.dataset.__dict__[self.ATTRIBUTE__Z_VELOCITY]
        if float(tmp) <0:
            self.metadata.setMetadataPair(metadata.METADATA_ORBIT_DIRECTION, valid_values.DESCENDING)
        else:
            self.metadata.setMetadataPair(metadata.METADATA_ORBIT_DIRECTION, valid_values.ASCENDING)

        # convert number to string,
        tmp = self.metadata.getMetadataValue(metadata.METADATA_ORBIT)
        self.metadata.setMetadataPair(metadata.METADATA_ORBIT, "%s" % tmp)
        tmp = self.metadata.getMetadataValue(metadata.METADATA_TRACK)
        self.metadata.setMetadataPair(metadata.METADATA_TRACK, "%s" % tmp)

        # relative orbit is track
        self.metadata.setMetadataPair(metadata.METADATA_TRACK, "%s" % self.metadata.getMetadataValue(metadata.METADATA_RELATIVE_ORBIT))

        
    #
    # ERS_ALT_2_ lat variable: lat, in
    # ERS_ALT_2_ lat variable: lat, in
    #
    def getFootprint(self, number=0, reduce=50):
        return
    
        v=self.dataset.variables['latitude']
        v2=self.dataset.variables['longitude']
        n=0
        footprint=''
        # try to not have too much coords
        r=len(v)/50
        
        #print " ################ ratio=%s" % r
        for i in range(len(v)):
            if i==0:
                firstLat=float(v[i][number])
                firstLon=float(v2[i][number])
            #if i%r==r:
            fv=float(v[i][number])
            fv2=float(v2[i][number])
            if self.debug != 0:
                print " v[%d]= %f %f" % (n, (fv/1000000.0), (fv2/1000000.0))

            if len(footprint)>0:
                footprint="%s " % footprint
            footprint="%s%s %s" % (footprint, fv/1000000.0, fv2/1000000.0)
            lastLat=float(v[i][number])
            lastLon=float(v2[i][number])
            n=n+1

        if self.debug != 0:
            print "footprint[%d]:%s" % (number,footprint)
            fd=open("footprint__%d.out" % number, 'w')
            fd.write(footprint)
            fd.close()
            
        #print "Z velocity:%s" % (self.dataset.__dict__['z_velocity'])
        #print "ra0_first_lat:%s  VS %s" % (self.dataset.__dict__['ra0_first_lat'],firstLat)
        #print "ra0_first_long:%s  VS %s" % (self.dataset.__dict__['ra0_first_long'],firstLon)
        try:
            print "ra0_last_lat:%s  VS %s" % (self.dataset.__dict__['ra0_last_lat'],lastLat)
            print "ra0_last_long:%s  VS %s" % (self.dataset.__dict__['ra0_last_long'],lastLon)
        except:
            pass
        return footprint

    #
    #
    #
    def buildTypeCode(self):
        pass
        

if __name__ == '__main__':
    print "start1"
    try:
        p=Product_NetCDF_Reaper("C:/Users/glavaux/Shared/LITE/reaper/a.NC")
        p.getMetadataInfo()
        met=metadata.Metadata()
        p.extractMetadata(met)
        p.refineMetadata()
        
    except Exception, e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print "Error:%s  %s\n%s" %  (exc_type, exc_obj, traceback.format_exc())


