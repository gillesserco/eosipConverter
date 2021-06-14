#
# For Esa/lite dissemination project
#
# Serco 03/2016 Lavaux Gilles
#
# 22/03/2016: V: 0.1
#
# ingester for cryosat products
#
# as per EoSip specESA-EOPG-MOM-SP-0003 V1.1 of 24/06/2016
#
#
import os, sys, inspect
import time
import zipfile
import shutil
import traceback
from cStringIO import StringIO

# add converter package path to sys.path 
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parrent=os.path.dirname(currentdir)
print "##### eoSip converter package dir:%s" % parrent
sys.path.insert(0, parrent)

from eoSip_converter.base import ingester, reportMaker
from eoSip_converter.esaProducts import product_EOSIP, product_cryosat, product_directory
from eoSip_converter.esaProducts import metadata, browse_metadata
from eoSip_converter.esaProducts import definitions_EoSip, formatUtils
from eoSip_converter.esaProducts.definitions_EoSip import rep_rectifiedBrowse
from eoSip_converter.esaProducts.namingConvention import NamingConvention
from eoSip_converter.esaProducts.namingConvention_AsSource import NamingConvention_AsSource
import imageUtil
import fileHelper
import xmlHelper




# minimum config version that can be use
MIN_CONFIG_VERSION=1.0

# ref EO name, used to check reconstructed filename, length
REF_EO_NAME='CS_OFFL_SIR_SIN_0M_20001122T112233_20001122T112233_0001'



#
# ref SIP name, used to check reconstructed filename, length
REF_SIP_NAME='CR2_OFFL_SIR_SIN_0M_20001122T112233_20001122T112233_0001.ZIP'


#
#
#
class Ingester_Cryosat(ingester.Ingester):

        #
        #
        #
        def afterStarting(self, **kargs):
                return
                # test the test dataset: look if we have all typecodes
                eopFiles=[]
                altFiles=[]
                fd = open('cryosat_test_product_list.txt', 'r')
                lines = fd.readlines()
                fd.close()
                
                product=None
                allTypecode=[]
                foundTypeCodes={}
                unknownTypeCodes={}
                allPresentTypecode={}
                for productPath in lines:
                        productPath = productPath.strip()
                        if productPath[0] != '#':
                                print 'testing product:%s' % productPath

                                if product==None:
                                        product = cryosat_product.Cryosat_Product(productPath)
                                        allTypecode = product.getAllTypeCodes()
                                        n=0
                                        for item in  allTypecode:
                                                print "all typecode[%s]:%s" % (n, item)
                                                n+=1
                                        
                                name = os.path.basename(productPath)
                                typecode = name[8:18]
                                print '  typecode :%s' % typecode
                                instrument, mode = product.getInstrumentFromTypeCode(typecode)
                                print '  instrument:%s mode:%s' % (instrument, mode )
                                if instrument=='SIRAL':
                                        altFiles.append(productPath)
                                else:
                                        eopFiles.append(productPath)
                                
                                allPresentTypecode[typecode] = typecode
                                try:
                                        index = allTypecode.index(typecode)
                                        foundTypeCodes[typecode] = typecode
                                except:
                                        unknownTypeCodes[typecode] = typecode

                print ""
                missingTestData={}
                n=0
                print "\nallPresentTypecode num=%s:%s\n" % (len(allPresentTypecode), allPresentTypecode)
                for item in allTypecode:
                        print "test not present test data for %s:%s" % (n, item)
                        if  allPresentTypecode.has_key(item):
                                print " present:%s" % allPresentTypecode[item]
                        else:
                                missingTestData[item] = item
                                print " missing"
                        n+=1

                print "\n\nall typecodes: num=%s; list=%s" % (len(allTypecode), allTypecode)
                a=foundTypeCodes.keys()
                a.sort()
                print "\nfound typecodes: num=%s; list=%s" % (len(a), a)
                a=unknownTypeCodes.keys()
                a.sort()
                print "\nunknownTypeCodes typecodes: num=%s; list=%s" % (len(a), a)
                a=missingTestData.keys()
                a.sort()
                print "\nmissingTestData typecodes: num=%s; list=%s" % (len(a), a)

                if 1==2:
                        fd=open('sirTestProducts.list', 'w')
                        for item in altFiles:
                                fd.write("%s\n" % item)
                        fd.close()

                        fd=open('strTestProducts.list', 'w')
                        for item in eopFiles:
                                fd.write("%s\n" % item)
                        fd.close()
                
                print '\n\n interruption'

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

                # set eop:productQualityReportURL to QR.XML filename, if QR file exists
                if processInfo.srcProduct.shouldHaveQr: # product should have QR
                        if processInfo.srcProduct.qrPresent: # product has QR
                                processInfo.srcProduct.metadata.setMetadataPair(metadata.METADATA_QUALITY_REPORT_URL, "%s.QR.XML" %  processInfo.destProduct.getEoProductName())
                        else:
                                pass

        #
        # called after having done the various reports
        #
        def afterReportsDone(self, processInfo):
                # use the .EEF as a quality report, if any
                if processInfo.srcProduct.qrPresent:
                        eefPath = "%s/%s" % (processInfo.workFolder, processInfo.srcProduct.qualityName)
                        qrPath = "%s/%s.QR.XML" % (processInfo.workFolder, processInfo.destProduct.getEoProductName())
                        shutil.copyfile(eefPath, qrPath)
                        processInfo.destProduct.addAdditionalContent(qrPath, os.path.split(qrPath)[1])
                        processInfo.addLog("  created QR:%s from EEF:%s" % (qrPath, eefPath))
        

        #
        # called at the end of the doOneProduct, before the index/shopcart creation
        #
        def afterProductDone(self, processInfo):
                pass
        
        #
        #
        def alterReportXml(self, processInfo) :
                pass

        #
        #
        #
        def buildEoNames(self, processInfo, namingConvention=None):
            #self.logger.info(" buildEoNames")
            #processInfo.addLog(" buildEoNames")
            processInfo.destProduct.buildEoNames(namingConvention)

            # test EoSip package name
            aName = processInfo.destProduct.getSipPackageName()
            if len(aName) != len(REF_SIP_NAME):
                print "ref EoSip package name:%s" % REF_SIP_NAME
                print "EoSip name:%s" % aName
                raise Exception("EoSip name has incorrect length:%s VS %s" % (len(aName), len(REF_SIP_NAME)))

            aName = processInfo.destProduct.getEoProductName()
            if len(aName) != len(REF_EO_NAME):
                print "ref EO product name:%s" % REF_EO_NAME
                print "EO product name:%s" % aName
                raise Exception("EO product name has incorrect length:%s VS %s" % (len(aName), len(REF_EO_NAME)))


            aName = processInfo.destProduct.getSipProductName()
            if aName.find('@') >=0 or aName.find('#')>0:
                    raise Exception("SipProductName incomplet:%s" % aName)

            # set platform id that was Converter_None, to have just CS_xxx package name
            processInfo.srcProduct.metadata.setMetadataPair(metadata.METADATA_PLATFORM_ID, '2')
    
        #
        # Override
        # this is the first function called by the base ingester
        #
        # as input we have the manifest path. Need to use his parent for the product path
        #
        def createSourceProduct(self, processInfo):
            global debug,logger
            processInfo.srcPath=processInfo.srcPath.replace('\\','/')
            product = product_cryosat.Product_Cryosat(processInfo.srcPath)
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
            eosipP.sourceProductPath = processInfo.srcPath
            processInfo.destProduct = eosipP

            # set naming convention instance
            # SIP naming 
            namingConventionSip = NamingConvention(self.OUTPUT_SIP_PATTERN)
            namingConventionSip.setDebug(1)
            processInfo.destProduct.setNamingConventionSipInstance(namingConventionSip)

            # EO naming is as source
            namingConventioneEo = NamingConvention_AsSource(self.OUTPUT_EO_PATTERN)
            namingConventioneEo.setDebug(1)
            processInfo.destProduct.setNamingConventionEoInstance(namingConventioneEo)
            
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

            if processInfo.srcProduct.qrProblem is not None:
                processInfo.addLog(processInfo.srcProduct.qrProblem)
                self.logger.info(processInfo.srcProduct.qrProblem) 

            # new: use method in base converter
            #met.setMetadataPair(metadata.METADATA_GENERATION_TIME, time.strftime('%Y-%m-%dT%H:%M:%SZ'))
            self.getGenerationTime(met)

            # keep some info
            processInfo.addInfo("typecode", met.getMetadataValue(metadata.METADATA_TYPECODE))

            if self.debug!=0:
                    print "metadata dump:\n%s" % met.dump()
                    
                
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
            pass


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



if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            ingester = Ingester_Cryosat()

            commandLineInfo = ingester.getCommandLineInfo()
            
            ingester.debug=1
            exitCode = ingester.starts(sys.argv)
            
            out=StringIO()
            print >> out, commandLineInfo
            print >>out, "### Start of report\n"
            aReportMaker = reportMaker.ReportMaker()
            report = aReportMaker.makeReport(ingester)
            print >>out, "Cryosat conversion report"
            print >>out, report
            print >>out, "### End of report"
            #print out.getvalue()
            reportName = "Cryosat_conversion_report.txt"
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
