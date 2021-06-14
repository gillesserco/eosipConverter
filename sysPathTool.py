#!/usr/bin/env python
#
# this helper class will check the sys.path to see if the EoSip definitions folder is present
# if not it will be appened to the sys.path
#
# this to handle the fact that the EoSip definitions have several versions, and that the corresponding
# package have to be imported from different paths 
#
#

import os,sys,inspect
import traceback

#
# path definitions
#
# EoSip packages relative path, definitions path from converter path
RELATIVE_EOSIP_DEFINITION_PATH='eoSip_converter/esaProducts/definitions_EoSip'
# xml_node
XML_NODE_PATH='xml_node'
# needed
NEEDED_PATHS_SUFFIX=[RELATIVE_EOSIP_DEFINITION_PATH]

DEBUG=False


class SysPathTool():
    #
    #
    #
    def __init__(self):
        if DEBUG:
            print " SysPathTool init"
        self.eoSipVersion=None
        self.sysPath=None


    #
    #
    #
    def isNeededPath(self, aPath):
        for item in NEEDED_PATHS_SUFFIX:
            if aPath.endswith(item):
                return item
        else:
            return None

        
    #
    #
    #
    def checkSysPath(self, version):
        print " checkSysPath; EoSip generic version:%s" % version

        n=0
        self.sysPath=[]
        neededPresent=[]
        for item in sys.path:
           self.sysPath.append(item)

           # test we have the neede one
           needed = self.isNeededPath(item)
           if needed is not None:
               neededPresent.append(needed)

           if DEBUG:
               print " sys.path[%s]=%s; needed?:%s" % (n, item, needed)
           n+=1

        n=0
        for item in neededPresent:
            if DEBUG:
                print " needed[%s]:%s" % (n, item)
            n+=1
            
        print " found %s needed path(s) out of:%s" % (n, len(NEEDED_PATHS_SUFFIX))

        # if needed not found, append to sys.path using sys.path item at index 0
        # note: only insert first needed at this time
        if n!=len(NEEDED_PATHS_SUFFIX):
            newPath =  "%s/%s/v%s" % (sys.path[0], RELATIVE_EOSIP_DEFINITION_PATH, version)
            aCheckedPath = "%s/xml_nodes" % (newPath)
            if not os.path.exists(aCheckedPath):
                raise Exception('needed reference path not found:%s' % aCheckedPath)
            
            if DEBUG:
                print " insert new EoSip definition path:%s" % newPath
            self.sysPath.insert(0, newPath)

        return self.sysPath

    #
    #
    #
    def getEoSipVersion(self, version):
        return self.getEoSipVersion

    #
    #
    #
    def getSysPath(self):
        return self.sysPath

    #
    #
    #
    def getSysPathUsed(self):
        res=[]
        n=0
        for item in sys.path:
            if DEBUG: 
                print " @@@###@@@@ SysPathTool.getSysPathUsed: test path item[%s]='%s'" % (n, item)
            # test we have the neede one
            needed = self.isNeededPath(item)
            for item2 in NEEDED_PATHS_SUFFIX:
                if DEBUG:
                    print " !!!!!!!!!!!!!!!!!!!!! test '%s' VS '%s'" % (item, item2)
                if item.find(item2) >=0 :
                    if DEBUG:
                        print "   @@@###@@@@ SysPathTool.getSysPathUsed: path item[%s]='%s' >>>>>>>> MATCH <<<<<<<<<<" % (n, item)
                    res.append(item)
                else:
                    if DEBUG:
                        print "   @@@###@@@@ SysPathTool.getSysPathUsed: path item[%s]='%s' DONT MATCH" % (n, item)
        print "getSysPathUsed:%s" % res
        #os._exit(1)
        return res
