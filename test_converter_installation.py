#
# This is an installation testing utility
# For the ASAR to MDP tool
#
# it will check that the following is ok:
# - check python version: has to be delivered !!CUSTOMIZED!! anaconda version 2.7.6 minimum
# - check tool import
# - check xml import (need LXML)
# - check image utils (need PIL)
# - check that we use our !!CUSTOMIZED!! anaconda: has Gdal, NumPy,Netcdf4, Pyro4
#
# Serco 12/2015
# Lavaux Gilles 
#
#
#
#
import os, sys
import time
import traceback

#
REQUIERED_PYTHON_VERSION=(2,7,9)
REQUIERED_PYTHON='2.7.9 |Anaconda 1.9.2 '
#
tool='stripline_to_mdp'
xml='xmlHelper'
image='imageUtil'
ourAnaconda_1='Pyro4'
ourAnaconda_2='gdal'
ourAnaconda_3='numpy'

#
#
#
if __name__ == '__main__':
        exitCode=-1

        try:
            print "\nWill test current python agains requirement for ASAR to MDP converter tool...\n need to be run INSIDE the tool folder!\n you should see NO WARNING OR ERROR!!\n\n"
            
            # python version
            if sys.version_info < REQUIERED_PYTHON_VERSION:
                raise Exception("Minimum python version not ok: %s < %s" % (sys.version_info, REQUIERED_PYTHON_VERSION))
            print " - test python minimum version %s: ok" % (REQUIERED_PYTHON_VERSION,)

            # anaconda version
            if sys.version.find(REQUIERED_PYTHON):
                raise Exception("Anaconda version not ok: '%s' VS '%s'" % (sys.version[0:len(REQUIERED_PYTHON)], REQUIERED_PYTHON))
            print " - test Anaconda version %s: ok" % (REQUIERED_PYTHON)
            
            # can import converte tool
            __import__(tool)
            print " - test importing tool %s: ok" % tool

            # can import xml helper
            __import__(xml)
            print " - test importing xml helper ok"

            # can import image utils
            __import__(image)
            print " - test importing image utils ok"

            # use our customized anaconda package
            try:
                # 
                __import__(ourAnaconda_1)
                print " - test python is our customized anaconda part1: ok"
                __import__(ourAnaconda_2)
                print " - test python is our customized anaconda part2: ok"
                __import__(ourAnaconda_3)
                print " - test python is our customized anaconda part3: ok"
            except:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print " Error: %s; %s" % (exc_type, exc_obj)
                traceback.print_exc(file=sys.stdout)
                raise Exception("Error: the anaconda installed is NOT the delivered customized one!")

            print "\n test finished, all ok"
            exitCode=0
        except Exception, e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print " Error: %s; %s" % (exc_type, exc_obj)
            traceback.print_exc(file=sys.stdout)


        sys.exit(exitCode)
