# -*- coding: cp1252 -*-
#
# 
#
#
import sys,os
import subprocess
import traceback
from subprocess import call,Popen, PIPE

from esaProducts import definitions_EoSip

# try to have PIL library
PilReady=0
try:
    import PIL
    from PIL import Image
    from PIL import ImageEnhance
    PilReady=1
except:
    pass

# try to have GDAL library
GdalReady=0
try:
    import gdal
    from gdalconst import *
    GdalReady=1
except:
    pass

# 
SUPPORTED_TYPE=["JPEG", "JPG","PNG"]
a=[definitions_EoSip.getDefinition(definitions_EoSip.FIXED__JPEG_EXT)]

# DEBUG
debug=False

# command line used to build the browse, when PIL is not used
externalConverterCommand="/bin/sh -c \"/usr/bin/gm convert -verbose "


import struct
import imghdr


#
# get image dimenssion without external library
# work only for PNG, JPEG, GIF
#
def __get_image_size(fname):
    '''Determine the image type of fhandle and return its size.
    from draco'''
    fhandle = open(fname, 'rb')
    head = fhandle.read(24)
    if len(head) != 24:
        raise Exception("can not read image header")
    if imghdr.what(fname) == 'png':
        check = struct.unpack('>i', head[4:8])[0]
        if check != 0x0d0a1a0a:
            return
        width, height = struct.unpack('>ii', head[16:24])
    elif imghdr.what(fname) == 'gif':
        width, height = struct.unpack('<HH', head[6:10])
    elif imghdr.what(fname) == 'jpeg':
        try:
            fhandle.seek(0) # Read 0xff next
            size = 2
            ftype = 0
            while not 0xc0 <= ftype <= 0xcf:
                fhandle.seek(size, 1)
                byte = fhandle.read(1)
                while ord(byte) == 0xff:
                    byte = fhandle.read(1)
                ftype = ord(byte)
                size = struct.unpack('>H', fhandle.read(2))[0] - 2
            # We are at a SOFn block
            fhandle.seek(1, 1)  # Skip `precision' byte.
            height, width = struct.unpack('>HH', fhandle.read(4))
        except Exception: #IGNORE:W0703
            return
    else:
        raise Exception("unknown image type:%s" % imghdr.what(fname))
    return width, height



#
# get tif image size using PIL
#
def __get_tif_size_pil(fname):
    if debug:
        print "__get_tif_size_pil on:%s" % fname
    im = PIL.Image.open(fname)
    return im.size # is a tuple

#
# get tif image size using GDAL
#
def __get_tif_size_gdal(fname):
    if debug:
        print "__get_tif_size_gdal on:%s" % fname
    dataset = gdal.Open(fname, GA_ReadOnly)
    return (dataset.RasterXSize, dataset.RasterYSize)

#
# get image size using GDAL
#
def get_size_gdal(fname):
    #if DEBUG:
    print "get_size_gdal on:%s" % fname
    dataset = gdal.Open(fname, GA_ReadOnly)
    #os._exit(0)
    return (dataset.RasterXSize, dataset.RasterYSize)

#
#
#
def get_image_size(fname):
    pos=fname.rfind('.')
    ext=''
    if pos>0:
        ext=fname[pos+1:]
    if debug:
        print  "get_image_size '%s' extension:%s" % (fname, ext)

    ext=ext.upper()
    if ext=='PNG' or ext=='GIF' or ext=='JPEG' or ext=='JPG':
        try:
            w,h = __get_image_size(fname)
            return __get_image_size(fname)
        except:
            if PilReady==1:
                w, h =  __get_tif_size_pil(fname)
                print " get_image_size PIL found:%s %s" % (w, h)
                return (w, h)
            
    elif ext=='TIF':
        if PilReady==1:
            try:
                w, h =  __get_tif_size_pil(fname)
                print " get_image_size PIL found:%s %s" % (w, h)
                return (w, h)
            except:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print " USING PIL Error %s  %s\n%s" %  (exc_type, exc_obj, traceback.format_exc())
                if GdalReady==1:
                    w, h =  __get_tif_size_gdal(fname)
                    print " get_image_size GDAL found:%s %s" % (w, h)
                    return (w, h)
                else:
                    raise Exception('can not get image size: PIL failed and no GDAL')
        else:
            if GdalReady==1:
                w, h =  __get_tif_size_gdal(fname)
                print " get_image_size GDAL found:%s %s" % (w, h)
                return (w, h)
            else:
                raise Exception('can not get image size: no PIL and GDAL failed')
    else:
        raise Exception('unknown extension:%s' % ext)
        
    

#
# make a browse image
#
def makeBrowse(type="JPEG", src=None, dest=None, resizePercent=-1, w=-1, h=-1, enhance=None, transparent=False, transparentThreshold = 0):
    try:
        SUPPORTED_TYPE.index(type)
    except:
        raise Exception("unsupported browse type:%s" % type)
    #
    # convert to supported type
    #
    if type.lower()=="jpg":
        type="JPEG"

    ok=False
    if PilReady==1:
        try:
            ok=makeBrowsePil(type, src, dest, resizePercent, w, h, enhance, transparent, False, transparentThreshold)
        except Exception, e:
            print " ######################################## 0 can not make browse using PIL:%s" % e
            if debug:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                traceback.print_exc(file=sys.stdout)
            try:
                ok=externalMakeBrowse(type, src, dest, resizePercent, transparent, False)
            except Exception, e:
                print " ######################################## 1 Error making browse using external call:%s" % e
                exc_type, exc_obj, exc_tb = sys.exc_info()
                traceback.print_exc(file=sys.stdout)
                raise e
                #pass
    else:
        try:
            ok=externalMakeBrowse(type, src, dest, resizePercent, transparent, False, transparentThreshold)
        except Exception, e:
            print " ######################################## 2 Error making browse using external call:%s" % e
            exc_type, exc_obj, exc_tb = sys.exc_info()
            traceback.print_exc(file=sys.stdout)
            raise e
            #pass

    return ok
    
        

#
# run external command to generate the browse
#
def externalMakeBrowse(type="JPEG", src=None, dest=None, resizePercent=100, transparent=False, showTraceback=False, transparentThreshold = 0):
    try:
        src=src.replace("//","/")
        dest=dest.replace("//","/")
        if debug:
            print " external resize image:%s into:%s" % (src, dest)
        if resizePercent==-1 or resizePercent==100:
            command="%s %s %s\"" % (externalConverterCommand, src, dest)
        else:
            command="%s -scale %s%s %s %s\"" % (externalConverterCommand, resizePercent , '%', src, dest)
        #if DEBUG:
        print "command:'%s'" % command
        retval = subprocess.call(command, shell=True)
        print " ######################################## external make browse exit code:%s" % retval
        if debug:
            print "  retval:%s" % retval
        if retval!=0:
            raise Exception("Error externalMakeJpeg: subprocess exit code is not 0 but:%s" % retval)
        if debug:
            print "  browse saved as:%s" % dest
        return True
    except Exception, e:
        print " ######################################## 3 externalMakeBrowse error:%s" % e
        if showTraceback:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            traceback.print_exc(file=sys.stdout)
        raise e
    


#
# test
#
def splitBands(img=None):
    newIm=None
    try:
        r, g, b, a = img.split()
        if debug:
            print "  im splitted"
        newIm = Image.merge("RGB", (r, g, b))
    except:
        r, g, b = img.split()
        if debug:
            print "  im splitted"
        newIm = Image.merge("RGB", (r, g, b))
    return newIm
    
#
# make a browse image using PIL
# w and h parameter not used at this time
#
def makeBrowsePil(type="JPEG", src=None, dest=None, resizePercent=-1, w=-1, h=-1, enhance=None, transparent=False, showTraceback=False, transparentThreshold = 0):
    try:
        if debug:
            print " internal resize image:%s into:%s; percent:%s" % (src, dest, resizePercent)
        im = Image.open(src)
        im = im.convert('RGBA')
        if debug:
            print "  src image readed:%s" % im.info

        img=None
        if enhance != None:
            converter = ImageEnhance.Contrast(im)
            newIm = converter.enhance(1.5)
            #r, g, b, a = img.split()
            #if DEBUG:
            #    print "  im splitted"
            #newIm = Image.merge("RGB", (r, g, b))
            #newIm = splitBands(img)
        else:
            #try:       
            #    r, g, b, a = im.split()
            #    if DEBUG:
            #        print "  im splitted rgba"
            #    newIm = Image.merge("RGB", (r, g, b))
            #except:
            #    r, g, b = im.split()
            #    if DEBUG:
            #        print "  im splitted rgb"
            #    newIm = Image.merge("RGB", (r, g, b))
            newIm = im.copy()
            
        if debug:
            print "  newIm:%s" % newIm

        width, height = newIm.size
        newSize=None
        if resizePercent!=-1:
            nw=width*resizePercent/100
            nh=height*resizePercent/100
            newSize=[nw,nh]
        elif w>0 and h>0:
            newSize=[w,h]

        if newSize is not None:
            newIm=newIm.resize(newSize, Image.BILINEAR )
            if debug:
                print "  newIm resized"
            if type=="PNG" and transparent==True:
                source = newIm.split() 
                R, G, B, A = 0, 1, 2, 3
                mask = newIm.point(lambda i: i > transparentThreshold and 255) # use black as transparent
                source[A].paste(mask)
                newIm = Image.merge(im.mode, source)  # build a new multiband image 
            newIm.save(dest, type)
        else:
            if type=="PNG" and transparent==True:
                source = newIm.split() 
                R, G, B, A = 0, 1, 2, 3
                mask = newIm.point(lambda i: i > transparentThreshold and 255) # use black as transparent
                source[A].paste(mask)
                newIm = Image.merge(im.mode, source)  # build a new multiband image 
            newIm.save(dest, type)
            
        if debug:
            print "  browse saved as:%s" % dest
        return True
    
    except Exception, e:
        print " ######################################## 4 Error making browse:%s" %e
        if showTraceback:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            traceback.print_exc(file=sys.stdout)
        raise e

#
# all coords relate to top-left corner of the image
#
def cropImage(aSrcPath, aDestPath, left, top, width, height, type='PNG'):
    im = PIL.Image.open(aSrcPath)
    bbox=(left, top, left+width, top+height)
    cropped = im.crop(bbox)
    cropped.save(aDestPath, type)

    
if __name__ == '__main__':
    print "PilReady:%s" % PilReady
    if len(sys.argv) > 1:
        print "res:%s %s" % get_image_size(sys.argv[1])
    else:
        #src="/home/gilles/shared2/Lite/Worldview/diskA12695/053963563010_01/053963563010_01_P001_MUL/12MAR23110731-M2AS_R01C1-053963563010_01_P001.TIF"
        src="/home/gilles/shared2/Datasets/Spot6-7/stranges-spot-5/imagery_known.tif"
        #src="C:/Users/glavaux/Shared/LITE/tmp/unzipped/imagery.tif"
        #src="C:/Users/glavaux/Shared/LITE/tmp/imagery_pb.tif"
        #dest="C:/Users/glavaux/Shared/LITE/tmp/test.png"
        #ok=makeBrowse("PNG", src, dest, 50, transparent=True)
        print "res:%s %s" % get_image_size(src)

    #print a


