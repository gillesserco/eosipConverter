#
# this is a wrapper class that will do the same usage as python ZipFile, but use os sup unzip instead
# it does not implement all the python ZipFile methods
# it needs to use temporary folder
#
# it is needed to bypass the python VS java zip header problem on file between 2GB and 4GB
#
# Lavaux Gilles 2016
#
#
import os, sys, time
import subprocess as sp
import traceback

import zipfile
import shutil
import re


#
#
ZIP_STORED=zipfile.ZIP_STORED
ZIP_DEFLATED=zipfile.ZIP_DEFLATED
#
DEFAULT_TMP_FOLDER='tmpZipWrapper'


#
debug=1
#
NOT_IMPLEMENTED='NOT_IMPLEMENTED'

# compression level
COMPRESSION_LEVEL_0='-0'
COMPRESSION_LEVEL_1='-1'
COMPRESSION_LEVEL_6='-6'
COMPRESSION_LEVEL_9='-9'
DEFAULT_COMPRESSION_LEVEL=COMPRESSION_LEVEL_1


#
#
#
class ZipFile(object):
    
    # os related:
    osZipCommand = 'zip'
    osUnzipCommand = 'unzip'


    

    #
    # create zipFile, use a file path and a rw flag
    # ZipFile method
    #
    def __init__(self, path, mode="r", compression=ZIP_STORED, allowZip64=False):
        self.path = path
        self.mode = mode
        # variable used:
        self.openWithPath=False
        self.fd=None
        self.compression=ZIP_DEFLATED
        # os commands done
        self.commands=[];
        # tmp folder
        self.tmpFolder=None
        # and files copied inside, need to delete them later
        self.tmpFolderFiles=[]
        #
        self.debug=debug
        
        #
        if type(path) == type(""):
            self.openWithPath=True
            
        if self.mode=='r':
            # file must exists
            self.fd=open(self.path, self.mode)
            if not os.path.exists(self.path):
                raise IOError("file does not exists:%s" % self.path)
        else:
            #self.fd=open(self.path, self.mode) # don't do this of a zero byte zip will be creates
            self.keepCommands("ZipFile created using path=%s and mode=%s" % (self.path, self.mode))
            if debug==0:
                print "  ZipFile created using path=%s and mode=%s" % (self.path, self.mode)


    #
    # close
    # ZipFile method
    #
    # close only in fd mode
    #
    def close(self):
        if debug==0:
            print '  closing %s; using tmpFolder:%s' % (self.path, self.tmpFolder)
        self.keepCommands('close %s' % self.path)
        #if self.openWithPath:
        #    self.keepCommands('closing, opened with path, close fd:%s' % self.fd)
        #    if self.fd is not None:
        #        self.fd.close()
        #    # clean tmpFolder if needed
        #    self.cleanTmpFolder()
        #    self.keepCommands(' closed done on %s' % self.path)
        #    print 'close %s' % self.path
        #else:
        self.keepCommands('closing, fd:%s' % self.fd)
        if self.fd is not None:
            self.fd.close()
        # clean tmpFolder if needed
        self.cleanTmpFolder()
        self.keepCommands(' closed done on %s' % self.path)
        if debug==0:
            print '  closed %s' % self.path


    #
    # flush
    # ZipFile method
    #
    # do nothing
    #
    def flush(self):
        self.keepCommands('flush')
        

    #
    # read a zipFile entry
    # ZipFile method
    #
    # param name: name of the entry
    # returns: bytes
    #
    def read(self, name):
        self.keepCommands('read(%s)' % name)
        raise Exception(NOT_IMPLEMENTED)


    #
    # test a zipFile
    # ZipFile method
    #
    def testzip(self):
        self.keepCommands('testzip')
        args = [self.osZipCommand, 't', self.path]
        res, out = self.runCommand(args)
        if res!=0:
            raise Exception(out)
        self.keepCommands(' testzip done')


    #
    # write a zipFile entry given as string
    # ZipFile method
    #
    # param data: string data
    # param alias: zip entry name
    # param compressionLevel: ZIP_DEFLATED or ZIP_STORED
    #
    def writestr(self, name, data, compressionLevel=ZIP_DEFLATED):
        self.keepCommands('writestr: data=%s; name=%s; compression=%s' % (data, name, compressionLevel))
        # test not in read mode
        if self.fd is not None and self.fd.mode == 'r': raise IOError('canot write, file %s is in read mode:%s' % (self.path, self.fd.mode))

        # name: need to use the tmp folder
        if name is None:
            raise Exception('zip entry name can not be None')
            
        # don't want to have /xxx as zipEntry name
        if name[0]=='/':
            name = name[1:]
        #
        if self.tmpFolder is None:
            raise Exception("zipfileWrapper tmpFolder not defined")
            #os._exit(1)
            #self.tmpFolder=DEFAULT_TMP_FOLDER
        if not os.path.exists(self.tmpFolder):
            # create default one
            os.makedirs(self.tmpFolder)
            self.keepCommands('default tmp folder created:%s' % self.tmpFolder)

        # then cd there, and zip file
        tmpPath = "%s/%s" % (self.tmpFolder, name)
        if self.debug != 0:
            print "  @@@@ tmpPath for name:%s is:%s" % (name, tmpPath)
        fd=open(tmpPath,'w')
        fd.write(data)
        fd.flush()
        fd.close()
        if self.debug != 0:
            print "  @@@@ tmpFile for name:%s filled" % (name)
        self.tmpFolderFiles.append(name)

        # add compression level
        cLevel=' '
        if compressionLevel==ZIP_DEFLATED:
            cLevel = ' %s ' % DEFAULT_COMPRESSION_LEVEL
        elif compressionLevel==ZIP_STORED:
            cLevel = ' -0 '
        else:
            raise Exception("unknown complession level:%s" % compressionLevel)

        # use shell command, so pass one command string
        #test: args = ['cd ' + os.path.realpath(self.tmpFolder) + '> /tmp/res0 && pwd >/tmp/res1']
        args = ['cd ' + os.path.realpath(self.tmpFolder) + '> /tmp/res0 && ' + self.osZipCommand + cLevel + self.path + ' ' + name +' >/tmp/res1']

        if self.debug != 0:
            print "  #### zip command:'%s'" % self.getCommand(args)

        #
        res, out = self.runCommand(args, True)
        if res != 0:
            raise Exception("zip error:%s" % res)
        #
        self.keepCommands(' write done')
            

    #
    # write a zipFile entry
    # ZipFile method
    #
    # param localPath: local path of file to be added
    # param alias: zip entry name
    # param compressionLevel: ZIP_DEFLATED or ZIP_STORED
    #
    def write(self, localPath, alias=None, compressionLevel=ZIP_DEFLATED):
        self.keepCommands('write: localPath=%s; alias=%s; compression=%s' % (localPath, alias, compressionLevel))
        # test file to add exists
        if not os.path.exists(localPath): raise IOError('file does not exists:%s' % localPath)
        # test not in read mode
        if self.fd is not None and self.fd.mode == 'r': raise IOError('canot write, file %s is in read mode:%s' % (self.path, self.fd.mode))

        # if alias is given: need to use the tmp folder
        if alias is not None:
            # don't want to have /xxx as zipEntry name
            if alias[0]=='/':
                alias = alias[1:]
            #
            if self.tmpFolder is None:
                raise Exception("zipfileWrapper tmpFolder not defined")
                #os._exit(1)
                #self.tmpFolder=DEFAULT_TMP_FOLDER
            if not os.path.exists(self.tmpFolder):
                # create default one
                os.makedirs(self.tmpFolder)
                self.keepCommands('default tmp folder created:%s' % self.tmpFolder)
        
            # copy localPath into tmpFolder as alias
            # then cd there, and zip file
            tmpPath = "%s/%s" % (self.tmpFolder, alias)
            if self.debug != 0:
                print "  @@@@ tmpPath for alias:%s is:%s" % (alias, tmpPath)
            if os.path.exists(tmpPath):
                raise Exception(" file already exists in tmpFolder:'%s'" % tmpPath)
            
            #
            if not os.path.exists(os.path.dirname(tmpPath)):
                os.makedirs(os.path.dirname(tmpPath))
                print "  @@@@ make folder for alias:%s is:%s" % (alias, os.path.dirname(tmpPath))

            # under investigation
            if not os.path.exists(localPath) or os.path.isdir(localPath):
                raise Exception("source file does not exists:%s" % localPath)
            # copy source file in tmp folder
            #shutil.copyfile(localPath, tmpPath)
            #if not os.path.exists(tmpPath) or os.path.isdir(tmpPath):
                raise Exception("tmp file was not created:%s" % tmpPath)
            
            # use symlink:
            os.symlink(localPath, tmpPath)
            self.tmpFolderFiles.append(alias)
            
            # add compression level
            cLevel=' '
            if compressionLevel==ZIP_DEFLATED:
                cLevel = ' %s ' % DEFAULT_COMPRESSION_LEVEL
            elif compressionLevel==ZIP_STORED:
                cLevel = ' -0 '
            else:
                raise Exception("unknown complession level:%s" % compressionLevel)

            # use shell command, so pass one command string
            #test: args = ['cd ' + os.path.realpath(self.tmpFolder) + '> /tmp/res0 && pwd >/tmp/res1']
            args = ['cd ' + os.path.realpath(self.tmpFolder) + '> /tmp/res0 && ' + self.osZipCommand + cLevel + self.path + ' ' + alias +' >/tmp/res1']

            if self.debug != 0:
                print "  #### zip command:'%s'" % self.getCommand(args)

            #
            res, out = self.runCommand(args, True)
            if res != 0:
                raise Exception("zip error:%s" % res)
            #
            self.keepCommands(' write done')
        else:
            #
            args = [self.osZipCommand, self.path, localPath]
            # add compression level
            if compressionLevel==ZIP_DEFLATED:
                args.append(DEFAULT_COMPRESSION_LEVEL)
            elif compressionLevel==ZIP_STORED:
                args.append('-0')
            else:
                raise Exception("unknown complession level:%s" % compressionLevel)

            #
            res, out = self.runCommand(args)
            if res != 0:
                raise Exception("zip error:%s" % res)
            #
            self.keepCommands(' write done')
        

    #
    # list zipFile
    # ZipFile method
    #
    def namelist(self):
        partsDelimiter='---------'
        self.keepCommands('namelist')
        args = [self.osUnzipCommand, '-l', self.path]
        res, out = self.runCommand(args)
        if res!=0:
            raise Exception(out)
        print "  out:\n%s" % out
        inside=False
        entryNames=[]
        for line in out.split('\n'):
            # is like:       103  2016-05-12 11:02   home/gilles/shared2/test/browse.txt
            if line.startswith(partsDelimiter):
                if not inside:
                    inside=True
                else:
                    inside=False
            else:
                if inside:
                    line=line.strip()
                    entryNames.append(line)

        print "  namelist: num of entries:%s" % len(entryNames)
        n=0
        res=[]
        for item in entryNames:
            #toks = item.split(' ')
            toks = re.split(" +", item)
            print "   entry[%d]:%s; %s" % (n, item, len(toks))
            j=0
            for tok in toks:
                print "   tok[%d]='%s'" % (j, tok)
                j+=1
            n+=1
            res.append(toks[3])
        self.keepCommands('namelist done')
        return res



        

    #
    #
    # MY STUFF:
    #
    #
 

    #
    #
    #
    def cleanTmpFolder(self):
        if debug==0:
            print "  cleanTmpFolder: number of files in tmpFolder: %d" % len(self.tmpFolderFiles)
        for item in self.tmpFolderFiles:
            if debug==0:
                print "   cleanTmpFolder: will erase '%s'" % item
            self.safeRemoveFile(item, self.tmpFolder)
        self.tmpFolderFiles=[]
    
    #
    # keep commands
    # GL stuff
    #
    def keepCommands(self, msg):
        self.commands.append(msg)


    #
    #
    #
    def getCommand(self, args):
        res=''
        for item in args:
            if len(res)>0:
                res="%s " % res
            res="%s %s" % (res, item)
        return res
            


    #
    # get info
    # GL stuff
    #
    def info(self):
        res = "ZipFile: fd='%s'\n" % self.fd
        res = "commands used:\n"
        for item in self.commands:
            res = "%s >%s\n" % (res, item)
        return res

    
    #
    # get info
    # GL stuff
    #
    def clearInfo(self):
        self.commands=[]


    #
    # set a tmp folder, used if zip with zipEntry alias
    # GL stuff
    #
    def setTmpFolder(self, path):
        if len(self.tmpFolderFiles)>0:
            raise Exception("can not change tmp folder when tmp files are still present:%s" % self.tmpFolderFiles)
        self.tmpFolder="%s_%s" % (path, int(time.time()*1000))


    #
    # get the tmp folder, used if zip with zipEntry alias
    # GL stuff
    #
    def getTmpFolder(self):
        return self.tmpFolder
        
        
    #
    #
    #
    def runCommand(self, args, useShell=False):
        if self.debug != 0:
            print "  will run command:%s" % args
        
        if useShell:
            sub = sp.Popen(args, stdout=sp.PIPE, stdin=sp.PIPE, shell=True)
            if self.debug != 0:
                print "   subprocess done"
        else:
            sub = sp.Popen(args, stdout=sp.PIPE, stdin=sp.PIPE)
            if self.debug != 0:
                print "   subprocess done"
        
        stdout = sub.communicate()[0]
        if self.debug != 0:
            print "   got stdout:%s" % stdout
        
        res = sub.returncode
        if self.debug != 0:
            print "   returncode:%s" % res
        
        return res, stdout


    #
    # remove a file, test that is is inside a base folder
    # TAKEN FROM FILEHELPER, TODO: remove later
    #
    def safeRemoveFile(self, path, base):
        if self.debug!=0:
            print "   safeRemoveFile: path:%s; base:%s"  % (path, base)
        if path.find("..")>=0:
            raise Exception("path can not contains ..")
        if path.startswith('/'):
            raise Exception("path can not start with /")
        realPath = os.path.realpath(base)
        if self.debug!=0:
            print "\n   safeRemoveFile: realBasePath:%s"  % realPath
            print "   safeRemoveFile:     path:%s"  % path
        finalPath="%s/%s" % (realPath, path)
        if os.path.exists(finalPath):
            if self.debug!=0: 
                print "   safeRemoveFile: can remove %s" % finalPath
            os.remove(finalPath)
        else:
            print "   safeRemoveFile: problem removing, tmp file not found:'%s':" % finalPath
            print "    FATAL until debugging done, sorry but I will stop."
            os._exit(1)
    

if __name__ == '__main__':
    try:
        print "starting"


        # test a zip file
        if 1==2:
            zipf = ZipFile('/home/gilles/shared2/test/a.zip', mode='r', allowZip64=True)
            zipf.testzip()
            zipf.close()
            print "zip test commands:%s" % zipf.info()


        # list a zip file
        if 1==1:
            zipf = ZipFile('/home/gilles/shared2/test/a.zip', mode='r', allowZip64=True)
            names = zipf.namelist()
            zipf.close()
            print "zip test commands:%s" % zipf.info()
            n=0
            for item in names:
                print "res[%s]:%s" % (n, item)
                n+=1


        # create a zip file
        if 1==2:
            zipf = ZipFile('/home/gilles/shared2/test/aaa.zip', mode='w')
            zipf.write('/home/gilles/shared2/test/browse.txt', 'browse.txt')
            zipf.write('/home/gilles/shared2/test/browse.txt', 'idem/browse.txt')
            zipf.close()
            print "zip write commands:%s" % zipf.info()
        
        print "done"
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print "xml error: %s   %s\n%s\n" %  (exc_type, exc_obj, traceback.format_exc())





    
    
