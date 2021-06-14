# -*- coding: cp1252 -*-
#
# this class encapsulate the metadata info for products 
#
#
from abc import ABCMeta, abstractmethod
import sys
import traceback
from cStringIO import StringIO



# type of metadata:
METADATATYPE_PRODUCT='METADATATYPE_PRODUCT'
METADATATYPE_BROWSE='METADATATYPE_BROWSE'
METADATATYPE_BASE='METADATATYPE_BASE'

# moved from sipBuilder
VALUE_OPTIONAL="OPTIONAL"
VALUE_CONDITIONS="CONDITIONS"
VALUE_UNKNOWN="CONVERTER_UNKNOWN"
VALUE_NONE="CONVERTER_None"
VALUE_NOT_PRESENT="CONVERTER_NOT-PRESENT"

class Base_Metadata:

    #
    NOT_DEFINED_VALUES = [VALUE_UNKNOWN, VALUE_NONE, VALUE_NOT_PRESENT]

    #
    counter=0
    
    #
    debug=0
    
    # the mapping of nodes used in xml report. keys is node path
    xmlNodeUsedMapping={}

    # the mapping of nodes used in xml report. keys is node path
    xmlVarnameMapping={}
    
    
    #
    #
    #
    def __init__(self):
        global METADATATYPE_BASE
        # metadata dictionnary
        self.dict={}
        self.dict['__METADATATYPE__']=METADATATYPE_BASE
        # a counter, can be used to increment the gml_id in the xml reports
        self.counter=0
        # other info
        self.otherInfo={}
        # the localAttibutes
        self.localAttributes=[]
        self.label='no label'
        self.defined=False
        
        if self.debug!=0:
            print ' init Base_Metadata done'

    #
    #
    #
    def valueExists(self, v):
        if v is None or v == VALUE_NOT_PRESENT or v == VALUE_NONE or v == VALUE_UNKNOWN:
            return False
        else:
            return True

    #
    def setDebug(self, d):
        if not isinstance( d, int ):
            print "ERROR Base_Metadata.setDebug: parameter is not an integer"
        self.debug=d
    #
    def getDebug(self):
        return self.debug

    
    #
    # tells if the metadata are defined. used to prevent to set everything to None
    #
    def isMetadataDefined(self):
        return self.defined
        
    #
    # set if the metadata are defined.
    #
    def setMetadataDefined(self, b):
        self.defined = b

    
    #
    #
    #
    def alterMetadataMaping(self, key, value):
        #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ will alterMetadataMaping for: key=%s  mapping=%s" % (key, value)
        self.xmlVarnameMapping[key]=value
    #
    #
    #
    def isMetadataMapingAltered(self):
        return len(self.xmlVarnameMapping.keys())>0
    #
    #
    #
    def getMetadataMaping(self, key, origMappingMap):
        #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ origMappingMap:%s" % (origMappingMap)
        if self.xmlVarnameMapping.has_key(key):
            return self.xmlVarnameMapping[key]
        else:
            if origMappingMap.has_key(key):
                return origMappingMap[key]
            else:
                return None
    #
    #
    #
    def setOtherInfo(self, key, value):
        self.otherInfo[key]=value


    #
    #
    #
    def getOtherInfo(self, key):
        return self.otherInfo[key]
    

    #
    # add a local attributes
    #
    def addLocalAttribute(self, name, value):
        adict={}
        adict[name]=value
        self.localAttributes.append(adict)


    #
    # get all local attributes
    #
    def getLocalAttributes(self):
        return self.localAttributes

    #
    # get one local attribute
    #
    def getLocalAttributeValue(self, name):
        res=None
        for i in range(len(self.localAttributes)):
            adict=self.localAttributes[i]
            if adict.has_key(name):
                res=adict[name]
        return res


    #
    # remove a local attributes
    #
    def removeLocalAttribute(self, name):
        tdict=None
        for i in range(len(self.localAttributes)):
            adict=self.localAttributes[i]
            if adict.has_key(name):
                tdict=adict
                break
        if tdict is not None:
            self.localAttributes.remove(tdict)


    #
    # test if localattribute exists
    #
    def localAttributeExists(self, name):
        exists=False
        for i in range(len(self.localAttributes)):
            adict=self.localAttributes[i]
            if adict.has_key(name):
                exists=True
                break
        return exists
    
    
    #
    # set the dictionnary of node used in the xml reports
    #
    def setUsedInXmlMap(self, adict):
        self.xmlNodeUsedMapping=adict

    #
    # get the dictionnary of node used in the xml reports
    #
    def getUsedInXmlMap(self):
        return self.xmlNodeUsedMapping



    #
    # test if a field is used in the xml report
    #
    def isFieldUsed(self, path=None, aDebug=False):
        if self.debug>=2 or aDebug:
            print "###########################\n###########################\n isFieldUsed: path:'%s'  len(exclusion):%d" % (path, len(self.xmlNodeUsedMapping))
        n=0
        for item in self.xmlNodeUsedMapping.keys():
            if self.debug>=2 or aDebug:
                print "########################### exclusion[%d]:%s=%s." % (n, item, self.xmlNodeUsedMapping[item])
            n=n+1
            
        if self.xmlNodeUsedMapping.has_key(path):
            if self.debug>=2 or aDebug:
                print "   field at path:'%s' used flag:%s" % (path, self.xmlNodeUsedMapping[path])
            if self.xmlNodeUsedMapping[path]=='UNUSED':
                if self.debug>=2 or aDebug:
                    print "########################### UNUSED"
                return 0
            else:
                if self.debug>=2 or aDebug:
                    print "########################### USED"
                return 1
        else:
            if self.debug>=2 or aDebug:
                print "########################### NO MAPPING; USED"
                print "  field with path:'%s' has no used map entry" % path
            return 1
            
    #
    # get metadata keys
    #
    def getMetadataNames(self):
        return sorted(self.dict.keys())
    
    #
    # set a metadata name + value
    #
    def setMetadataPair(self, name=None, value=None):
        #print " setMetadataPair name=%s; value=%s; type=%s" % (name, value, type(value))
        self.dict[name] = value

    #
    # get a metadata value
    #
    def getMetadataValue(self, name=None):
        if self.dict.has_key(name):
            #print " getMetadataValue name=%s; value=%s; type=%s" % (name, self.dict[name], type(self.dict[name]))
            return self.dict[name]
        else:
            #return sipBuilder.VALUE_NOT_PRESENT
            return VALUE_NOT_PRESENT

    #
    # test if metadata name exists
    #
    def hasMetadataName(self, key):
        return self.dict.has_key(key)

    #
    # delete a metadata
    #
    def deleteMetadata(self, key):
        if not self.dict.has_key(key):
            raise Exception("metadata has no key:'%s'" % key)
        else:
            del self.dict[key]

    #
    # merge another metadata into this one
    #
    def merge(self, other, allowOverwrite=False):
        print " MERGE METADATA; self:%s\n\nVS\n\n%s" % (self.toString(), other.toString())
        # merge dict, allow overwrite or not if value egual
        n=0
        for key in other.dict.keys():

            print " MERGE METADATA key[%s]:%s; other.value=%s" % (n, key, other.dict[key])
            if allowOverwrite:
                self.dict[key]=other.dict[key]
                print " MERGE METADATA (overwrite) key[%s]:%s; self.value=%s; other.value=%s" % (n, key, self.dict[key], other.dict[key])
            else:
                if key in self.dict.keys():
                    ok=False
                    same=False
                    if self.dict[key] is None:
                        ok=True
                        print " MERGE METADATA already present (not overwrite) ok because value is None"
                    elif self.dict[key] in self.NOT_DEFINED_VALUES:
                        ok = True
                        print " MERGE METADATA already present (not overwrite) ok because value is in NOT_DEFINED_VALUES"
                    elif self.dict[key] == other.dict[key]:
                        ok = True
                        same = True
                        print " MERGE METADATA already present (not overwrite) ok because value are equals"

                    if ok:
                        if not same:
                            self.dict[key] = other.dict[key]
                    else:
                        raise Exception("can not merge: collide on otherInfo key:%s; self.value=%s; other.value=%s" % (key, self.dict[key], other.dict[key]))
                else:
                    self.dict[key] = other.dict[key]
                    print " MERGED"
            n+=1

        # merge other info, allow overwrite or not if value egual
        n=0
        for key in other.otherInfo.keys():
            print " MERGED METADATA otherKey[%s]=%s" % (n, key)
            if allowOverwrite:
                self.otherInfo[key]=other.otherInfo[key]
            else:
                #self.otherInfo.keys().index(key)
                valueOther = other.otherInfo[key]
                if key in self.otherInfo:
                    value = self.otherInfo[key]
                    if valueOther!=valueOther:
                        self.otherInfo[key] = valueOther
                        print " MERGED METADATA otherInfo pair: %s=%s" % (key, other.otherInfo[key])
                    else:
                        raise Exception("can not merge: collide on otherInfo key:%s; value=%s" % (key, value))
                else:
                    print " MERGED METADATA otherInfo pair: %s=%s" % (key, other.otherInfo[key])
                    self.otherInfo[key] = valueOther
            n += 1

        # merge xmlNodeUsedMapping
        for key in other.xmlNodeUsedMapping.keys():
            self.xmlNodeUsedMapping[key]=other.xmlNodeUsedMapping[key]
            print " MERGED METADATA xmlNodeUsedMapping pair: %s=%s" % (key, other.xmlNodeUsedMapping[key])

        # merge xmlNodeUsedMapping
        for key in other.xmlVarnameMapping.keys():
            self.xmlVarnameMapping[key]=other.xmlVarnameMapping[key]
            print " MERGED METADATA xmlVarnameMapping pair: %s=%s" % (key, other.xmlVarnameMapping[key])


        # merge label
        self.label = "%s merged with:%s" % (self.label, other.label)
        print " MERGED METADATA label: %s" % (self.label)
        #if self.label==None:
        #    self.label = other.label

        #counter
        #if allowOverwrite:
        #    this.counter = other.counter
        #else:
        #    if self.counter!=other.counter:
        #        self.counter==other.counter:
        #    else:
        #        raise Exception("can not merge: collide on counter:%s" % counter)
            
        # merge localAttributes
        for item in other.localAttributes:
            if allowOverwrite:
                self.localAttributes.append(item)
                print " MERGED localAttributes (overwrite) item: %s" % (item)
            else:
                if self.localAttributes.contains(item):
                    raise Exception("can not merge: collide on localAttribute:%s" % item)
                else:
                    self.localAttributes.append(item)
                    print " MERGED localAttributes item: %s" % (item)

        


    #
    # clone this metadata into a new one, return it
    #
    def clone__(self):
        clone = Base_Metadata()
        clone.dict = self.dict.copy()
        clone.counter = self.counter
        clone.debug = self.debug
        clone.xmlNodeUsedMapping = self.xmlNodeUsedMapping.copy()
        clone.xmlVarnameMapping = self.xmlVarnameMapping.copy()
        clone.otherInfo=self.otherInfo.copy()
        clone.localAttributes=list(self.localAttributes)
        clone.label="%s" % self.label
        clone.defined=self.defined
        return clone


    #
    #
    #
    def toString(self):
        out=StringIO()
        print >>out, '\n##################################\n#### START Metadata Info #########\n### Label:%s\n### Dict:' % self.label
        for item in sorted(self.dict.keys()):
            print >>out, "%s=%s" % (item, self.dict[item])
            
        if self.xmlNodeUsedMapping is not None:
            if  len(self.xmlNodeUsedMapping.keys())>0:
                print >>out, "\n### Xml used mapping:"
                for item in sorted(self.xmlNodeUsedMapping.keys()):
                    print >>out, "%s=%s" % (item, self.xmlNodeUsedMapping[item])
            else:
                print >> out, "\n### Xml mapping empty"
        else:
            print >>out, "\n### NO xml mapping"
                
        if self.otherInfo is not None:
            if len(self.otherInfo.keys())>0:
                print >>out, "\n### Other info:"
                for item in sorted(self.otherInfo.keys()):
                    print >>out, "%s=%s" % (item, self.otherInfo[item])
            else:
                print >> out, "\n### Other info empty"
        else:
            print >>out, "\n### NO other info"

        if self.localAttributes is not None:
            if len(self.localAttributes)>0:
                print >>out, "\n### local attribute:"
                for item in sorted(self.localAttributes):
                    print >>out, "%s" % (item)
            else:
                print >> out, "\n### local attribute empty"
        else:
            print >>out, "\n### NO local attribute"

            
        print >>out, "#### END Metadata Info ###########\n##################################"
        return out.getvalue()


    #
    #
    #
    def dump(self):
        tmp = self.toString()
        print(tmp)
        return tmp
        
