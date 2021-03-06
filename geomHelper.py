# -*- coding: cp1252 -*-
#
# 
#
#

import sys
from geom import vector2D
from math import radians, cos, sin, asin, sqrt, atan2, degrees

debug=0


#
#
#
def degToRad(d):
    return map(radians, d)

#
#
#
def radToDeg(r):
    return map(degrees, r)



#
#
#
def deg2rad(d):
    return radians(d)

#
#
#
def rad2deg(r):
    return degrees(r)


#
#
#
def coordinateBetween(lat1, lon1, lat2, lon2):
    if debug != 0:
       print "\n\n\n coordinateBetween deg %s %s %s %s" % (lat1, lon1, lat2, lon2)
    # convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    bx = cos(lat2) * cos(lon2 - lon1)
    by = cos(lat2) * sin(lon2 - lon1)
    lat3 = atan2(sin(lat1) + sin(lat2),  sqrt((cos(lat1) + bx) * (cos(lat1)  + bx) + by**2))
    lon3 = lon1 + atan2(by, cos(lat1) + bx)

    if debug != 0:
       print "\n\n\n coordinateBetween res deg: %s %s" % (degrees(lat3), degrees(lon3))
    return degrees(lat3), degrees(lon3)


#
# Calculate the great circle distance between two points 
# on the earth (specified in decimal degrees)
#
# returns the distance in meters
#
def metersDistanceBetween(lat1, lon1, lat2, lon2):
    # convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    if debug!=0:
        print "angle=%s" % c

    # if we want the distance in meter
    # 6378137f meters is the radius of the Earth
    meters = 6378137 * c
    return meters


# from java, == arcDistanceBetween. OK
#
# returns radians ?: yes
#
def sphericalDistance(lat1, lon1, lat2, lon2):
    phi0, lambda0, phi, alambda = map(radians, [lat1, lon1, lat2, lon2])
    pdiff = sin(((phi-phi0)/2));
    ldiff = sin((alambda-lambda0)/2);
    rval = sqrt((pdiff*pdiff) + cos(phi0)*cos(phi)*(ldiff*ldiff));
	
    return 2 * asin(rval);


# from java. OK
#
# returns lat lon in degrees
#
def getIntermediatePoint(lat1, lon1, lat2, lon2, f):
        if debug != 0:
            print " @@@@@@@@@@@@@@@@ getIntermediatePoint deg %s %s %s %s" % (lat1, lon1, lat2, lon2)
        lon = 999999
        lat = 999999
        
        # get distance a-b
        d = sphericalDistance(lat1, lon1, lat2, lon2)
        if debug != 0:
            print " @@@@@@@@@@@@@@@@ d0:%s    %s" % (d, degrees(d))
            
        # a==b case
        if d==0:
        	return lat1, lon1
        #d = arcDistanceBetween(lat1, lon1, lat2, lon2)
        #print " @@@@@@@@@@@@@@@@ d1:%s    %s" % (d, degrees(d))

        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        # apply formula
        A = sin((1.0-f)*d)/sin(d)
        B = sin(f*d)/sin(d)
        
        x = A*cos(lat1)*cos(lon1) +  B*cos(lat2)*cos(lon2)
        y = A*cos(lat1)*sin(lon1) +  B*cos(lat2)*sin(lon2)
        z = A*sin(lat1) +  B*sin(lat2)
        
        
        lat = atan2(z,sqrt(pow(x,2) + pow(y,2)))
        lon = atan2(y,x)
        
        #return lat, lon
        return degrees(lat), degrees(lon)


#
# Calculate the great circle distance between two points 
# on the earth (specified in decimal degrees)
#
# returns the arc distance in radian
#
def arcDistanceBetween(lat1, lon1, lat2, lon2):
    if debug != 0:
        print "\n\n\n arcDistanceBetween deg %s %s %s %s" % (lat1, lon1, lat2, lon2)
    # convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    #print " arcDistanceBetween rad %s %s %s %s" % (lat1, lon1, lat2, lon2)

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    if debug==0:
        print "angle=%s rad or %s deg" % (c, degrees(c))

    # if we want the distance in meter
    # 6378137f meters is the radius of the Earth
    #meters = 6378137f * c
    return c


#
# return the lat and lon of several lat and lon coordinates
#
# latInDegr and lonInDegr are list of lat and lon
#
def getLatLngCenter(latInDegr, lonInDegr):
    sumX = 0
    sumY = 0
    sumZ = 0

    for i in range(len(latInDegr)):
        lat = deg2rad(latInDegr[i])
        lng = deg2rad(lonInDegr[i])
        # sum of cartesian coordinates
        sumX = sumX + cos(lat) * cos(lng)
        sumY = sumY + cos(lat) * sin(lng)
        sumZ = sumZ + sin(lat);
    

    avgX = sumX / len(latInDegr)
    avgY = sumY / len(latInDegr)
    avgZ = sumZ / len(latInDegr)

    # convert average x, y, z coordinate to latitude and longtitude
    lng = atan2(avgY, avgX)
    hyp = sqrt(avgX * avgX + avgY * avgY)
    lat = atan2(avgZ, hyp)

    return rad2deg(lat), rad2deg(lng)


        
if __name__ == '__main__':


    print "sphericalDistance (90,0) vs (0,0):%s" % sphericalDistance(90,0,0,0)
    print "metersDistanceBetween (90,0) vs (0,0):%s" % metersDistanceBetween(90,0,0,0)
    sys.exit(0)


    p1 = array( [0.0, 0.0] )
    p2 = array( [1.0, 0.0] )

    p3 = array( [4.0, -5.0] )
    p4 = array( [4.0, 2.0] )

    print "intersect test 1:%s"  % seg_intersect( p1,p2, p3,p4)

    p1 = array( [2.0, 2.0] )
    p2 = array( [4.0, 3.0] )

    p3 = array( [6.0, 0.0] )
    p4 = array( [6.0, 3.0] )

    print seg_intersect( p1,p2, p3,p4)
    print "intersect test 2:%s"  % seg_intersect( p1,p2, p3,p4)

    

    p1 = array( [0.0, 0.0] )
    p2 = array( [4.0, 0.0] )

    p3 = array( [0.0, 5.0] )
    p4 = array( [1.0, 4.0] )

    print seg_intersect( p1,p2, p3,p4)
    print "intersect test 3:%s"  % seg_intersect( p1,p2, p3,p4)
    

   

    
    # CW:
    #poly='43.505158383 -9.7328153269 43.400659479 -8.9829417472 42.876066318 -9.1602073246 42.979779308 -9.903779609 43.505158383 -9.7328153269'
    #poly='43.5 -9.73 43.4 -8.98 42.88 -9.16 42.98 -9.9 43.5 -9.73'
    # CCW
    poly='0.43 112.969 -0.421 112.969 -0.421 113.443 0.43 113.443 0.43 112.969'
 
    
    toks=poly.split(' ')
    f=[]
    totAngle=0
    for item in toks:
        f.append(float(item))
    for i in range((len(f)/2)-1):
        n=i*2
        #print "\n\nn:%s  len(f):%d" % (n, len(f))
        y1=f[n]
        x1=f[n+1]
        nn = n+2
        if nn>=len(f):  # we come back to the first point, so use the next one to build the second angle?? normally should never be the case because it's the next test the good one
            print "0 nn=%s>%s so set to:%s" % (nn, len(f), nn-len(f))
            nn=nn-len(f)+2
        y2=f[nn]
        x2=f[nn+1]
        nn = nn+2
        if nn>=len(f): # this should be the good test: we come back to the first point, so use the next one to build the second angle
            print "1 nn=%s>%s so set to:%s" % (nn, len(f), nn-len(f)+2)
            nn=nn-len(f)+2
        y3=f[nn]
        x3=f[nn+1]
        print "do point[%s]:%s %s vs %s %s vs %s %s " % (n, x1, y1, x2, y2, x3, y3)
        v1 = vector2D.Vec2d(x2-x1, y2-y1)
        v2 = vector2D.Vec2d(x3-x2, y3-y2)
        #print "\nv1=%s" % v1
        #print "v2=%s" % v2
        angle=v2.get_angle_between(v1)
        print ">>>>>>>>>>>angle:%f" % v2.get_angle_between(v1)
        totAngle=totAngle+angle
    print "\n\n\ntotal angle=%s\n\n" % totAngle

    print "distance:%s" % metersDistanceBetween(0.43,112.969,-0.421,142.969)
    print "middle:lat=%s; lon=%s" % coordinateBetween(0.43,112.969,-40.421,142.969)
        
        
        
    #v = Vec2d(3,4)
    #v1=makeVector(0,30)
    #print "length:%s" % get_length(v1)
