# -*- coding: cp1252 -*-
#
# this class represent a PFM job order
# will be used with the --joborder command line argument
#
#


import os, sys, time, inspect
import logging
import zipfile
import logging
#
import eoSip_converter.xmlHelper
from  eoSip_converter.esaProducts.product import Product
from eoSip_converter.esaProducts import metadata


debug=1

class JobOrder(Product):

    
    xmlMapping={'processor_name': 'Ipf_Conf/Processor_Name',
            'processor_version': 'Ipf_Conf/Version',
            'order_type': 'Ipf_Conf/order_type',
            'Logging_Level': 'Ipf_Conf/Logging_Level'
            }

    OUTPUT_MAPPING='List_of_Ipf_Procs/Ipf_Proc/List_of_Outputs/Output'

    INPUT_MAPPING='List_of_Ipf_Procs/Ipf_Proc/List_of_Inputs/Input'

    PARAMETER_MAPPING='Processing_Parameters'

    #
    #
    #
    def __init__(self, path=None):
        Product.__init__(self, path)
        # JobOrder.<order_id>.xml
        self.orderId=self.origName.lower().replace('joborder.','').replace('.xml', '')
        self.helper=None
        self.debug=debug
        self.processingParameters={}
        self.inputs=[]
        self.outputs=[]
        print " init class jobOrder done, orderId=%s" % self.orderId


    #
    #
    #
    def getInputs(self):
        return self.inputs


    #
    #
    #
    def getOutputs(self):
        return self.outputs


    #
    # return processing parameters dictionnary
    #
    def getProcessingParameters(self):
        return self.processingParameters

    #
    # return one processing parameters value
    #
    def getProcessingParameter(self, name):
        return self.processingParameters[name]

    #
    # read metadata file
    #
    def getMetadataInfo(self):
        if self.debug!=0:
            print " matadata source is itself:%s" % self.path
        fd=open(self.path, 'r')
        self.metContent=fd.read()
        fd.close()
        if self.debug!=0:
            print " extract metadata from:%s" % self.metContent
            
        return self.metContent


    #
    #
    #
    def getMetadataValue(self, key):
        return met.getMetadataValue(key)
        


    #
    # get metadata: common to all blocks
    #
    def extractMetadata(self, met=None, pinfo=None):
        # extact metadata
        self.helper=xmlHelper.XmlHelper()
        #self.helper.setDebug(1)
        self.helper.setData(self.metContent);
        self.helper.parseData()

        #get fields
        resultList=[]
        op_element = self.helper.getRootNode()
        num_added=0
        
        for field in self.xmlMapping:
            attr=None
            path=self.xmlMapping[field]

            aData = self.helper.getFirstNodeByPath(None, path, None)
            print " %s:%s" % (path, aData)
            if aData==None:
                aValue=None
            else:
                if attr==None:
                    aValue=self.helper.getNodeText(aData)
                else:
                    aValue=self.helper.getNodeAttributeText(aData,attr)        

            if self.debug!=0:
                print "  -->%s=%s" % (field, aValue)
            met.setMetadataPair(field, aValue)
            num_added=num_added+1

        met.label="job order:%s" % self.path

        # get input
        anInputNode = self.helper.getFirstNodeByPath(None, self.INPUT_MAPPING, None)
        aInFileNode = self.helper.getFirstNodeByPath(anInputNode, 'List_of_File_Names/File_Name', None)
        print "input node:%s" % aInFileNode
        inFile = self.helper.getNodeText(aInFileNode)
        print "\n #### input file:%s" % inFile
        self.inputs.append(inFile)
        

        # get output
        anOutputNode = self.helper.getFirstNodeByPath(None, self.OUTPUT_MAPPING, None)
        aOutFileNode = self.helper.getFirstNodeByPath(anOutputNode, 'File_Name', None)
        print "output node:%s" % aOutFileNode
        outFile = self.helper.getNodeText(aOutFileNode)
        print "\n #### output file:%s" % outFile
        self.outputs.append(outFile)

        # get parameters
        aParamNode = self.helper.getFirstNodeByPath(None, self.PARAMETER_MAPPING, None)
        print "\n #### aParamNode:%s" % aParamNode
        aList=[]
        self.helper.getNodeByPath(aParamNode, 'Processing_Parameter', None, aList)
        for item in aList:
            print "param node:%s" % aOutFileNode
            nodeN = self.helper.getFirstNodeByPath(item, 'Name', None)
            name=self.helper.getNodeText(nodeN)
            nodeV = self.helper.getFirstNodeByPath(item, 'Value', None)
            value=self.helper.getNodeText(nodeV)
            print " #### param name:%s value:%s" % (name, value)
            self.processingParameters[name]=value

        self.metadata=met
            
        
    #
    # refine the metada, should perform in order:
    #
    def refineMetadata(self):
        print " refineMetadata"

        

if __name__ == '__main__':
    print "start"
    logging.basicConfig(level=logging.WARNING)
    log = logging.getLogger('example')
    try:
        p=JobOrder("/home/gilles/shared2/joborder/JobOrder_stripline_to_mdp.xml")
        p.getMetadataInfo()
        met=metadata.Metadata()
        p.extractMetadata(met)
        print "\n\nExtracted metadata:\n%s" % met.toString()
    except Exception, err:
        log.exception('Error from throws():')






        
