#!/usr/bin/env python
#
# 
# Lavaux Gilles 2014
#
# This class is used to store ressources info
#
#
#
from abc import ABCMeta, abstractmethod
import os,sys,inspect
import traceback
import csv
#from data import *

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
try:
    sys.path.index(currentdir)
except:
    sys.path.insert(0,currentdir)
import ConfigParser


debug=0

    
class RessourceProvider():

    #
    # 
    #
    def __init__(self):
        self.resseourcesPath={}
        self.debug=debug
        if self.debug!=0:
            print " init RessourceProvider"
        
    #
    def setDebug(self, d):
        if not isinstance( d, int ):
            print "ERROR setDebug: parameter is not an integer"
        self.debug=d
    #
    def getDebug(self):
        return self.debug

    #
    # add ressource entry like: icon=C:/Users/glavaux/Shared/LITE/testData/Aeolus/logo.png
    #
    def addRessourcePath(self, n, v):
        if self.debug!=0:
            print "add ressource path for '%s':'%s'" % (n, v)
        self.resseourcesPath[n]=v


    #
    # get ressource entry
    #
    def getRessourcePath(self, n):
        if self.debug!=0:
            print "get ressource path for '%s'" % n
        if not self.resseourcesPath.has_key(n):
            raise Exception("ressource not found:"+n)
        return self.resseourcesPath[n]

    #
    # return info
    #
    def toString(self):
        out=StringIO()
        print >>out, ("Resources:\n")
        n=0
        for key in   self.resseourcesPath.keys():
            print >>out, ("  %s=%s" % (key, self.resseourcesPath[n]))
        return out.getvalue()

            
if __name__ == '__main__':
    try:
        provider = RessourceProvider()
        provider.addRessourcePath('icon',':/Users/glavaux/Shared/LITE/testData/Aeolus/logo.png')


    except Exception, e:
        print " Error"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_exc(file=sys.stdout)
