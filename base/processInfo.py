#
# classe used during the product procesing
# hold
# - the source and destination product
# - the tmpWorkig folder
# - the ingester used
#
from cStringIO import StringIO
import os,sys
import time
from datetime import datetime
import traceback


#
#
#
DEFAULT_DATE_PATTERN="%Y-%m-%d %H:%M:%S"
#
def dateNow(pattern=DEFAULT_DATE_PATTERN):
        d=datetime.fromtimestamp(time.time())
        return d.strftime(pattern)

class processInfo():

    def __init__(self):
        self.workFolder=None
        self.srcPath=None
        self.num=-1
        self.srcProduct=None
        self.destProduct=None
        self.eosipTmpFolder=None
        self.ingester=None
        #self.error=''
        #self.prodLog=''
        self.errorLogSIO=StringIO()
        self.prodLogSIO=StringIO()
        self.test_dont_extract=False
        self.test_dont_write=False
        self.test_dont_do_browse=False
        self.infoKeeper=None
        self.ingester=None
        # the ingester logger
        self.logger=None
        #print " init processInfo"


    #
    # set the ingester logger
    #
    def setLogger(self,l):
        self.logger=l

    #
    # set the ingester
    #
    def setIngester(self,i):
        self.ingester=i
        

    #
    #  add info in ingester log
    #
    def addIngesterLog(self, mess, level="INFO"):
        if self.logger is not None:
                if level=='DEBUG':
                        self.logger.debug(mess)
                elif level=='INFO':
                        self.logger.info(mess)
                elif level=='WARNING':
                        self.logger.warning(mess)
                elif level=='ERROR':
                        self.logger.error(mess)
                # added for joborder stdout reformatting:
                elif level=='PROGRESS':
                        self.logger.info("[PROGRESS] %s" % mess)
                elif level=='PINFO':
                        self.logger.info("[PINFO] %s" % mess)
                elif level=='PERROR':
                        self.logger.info("[PERROR] %s" % mess)
                else:
                        print "ERROR: unknown log level:%s" % level
        else:
                print "ERROR: NO LOGGER SET"

    #
    # add info in KEEPED info dictionnary
    #
    def addInfo(self, n, v):
            #print "#### addInfo on infoKeeper:%s" % id(self.infoKeeper)
            if self.infoKeeper is not None:
                    self.infoKeeper.addInfo(n, v)
            else:
                    raise Exception("no infoKeeper")

    #
    #  add info in production log
    #
    def addLog(self, mess):
        try:
            print >> self.prodLogSIO, "%s: %s" % (dateNow() , mess)
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print >> self.errorLogSIO, "%s %s" % (exc_type, exc_obj)
            print " processInfo.addLog error: %s  %s\n%s" % (exc_type, exc_obj, traceback.format_exc())

    #
    #
    #
    def getProdLog(self):
            return self.prodLogSIO.getvalue()

    #
    #
    #
    def getErrorLog(self):
            return self.errorLogSIO.getvalue()

    #
    #
    #
    def toString(self):
        out=StringIO()
        print >>out, '\n workFolder:%s' % self.workFolder
        print >>out, ' srcPath:%s' % self.srcPath
        print >>out, ' num:%s' % self.num
        if self.srcProduct is not None:
                print >>out, ' srcProduct:%s' % self.srcProduct.path
        else:
                print >>out, ' srcProduct: None'
        if self.destProduct is not None:
                print >>out, ' destProduct:%s' % self.destProduct.path
        else:
                print >>out, ' destProduct: None'
        print >>out, ' ingester:%s' % self.ingester
        print >>out, ' eosipTmpFolder:%s' % self.eosipTmpFolder
        
        print >>out, '  !! test_dont_extract:%s' % self.test_dont_extract
        print >>out, '  !! test_dont_write:%s' % self.test_dont_write
        print >>out, '  !! test_dont_do_browse:%s' % self.test_dont_do_browse

        print >> out, '  !! create kmz:%s' % self.create_kmz
        print >> out, '  !! create sys items:%s' % self.create_sys_items
        
        print >>out, '\nError:%s' % self.errorLogSIO.getvalue()
        print >>out, '\nLOG:\n%s' % self.prodLogSIO.getvalue()
        return out.getvalue()
        

if __name__ == '__main__':
        print "start"
        pinfo = processInfo()
        #pinfo.addInfo("aa", "bbbb")
        pinfo.addLog("aa")
        print "pinfo:%s" % pinfo.toString()


        
