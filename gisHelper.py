import os, sys, traceback
from cStringIO import StringIO


#
JSON_PATTERN='        {"type":"Feature", "properties":{"label":"LABEL"}, "geometry":{"type":"Polygon", "coordinates":[[PAIR_LONG_VIRGOLA_LAT_VIRGOLA]]}}'


#
#
#
def initJson(out):
    #out = StringIO()
    print >> out, '{ "type": "FeatureCollection",\n'
    print >> out, '    "features":\n'
    print >> out, '    [\n'

#
#
#
def closeJson(out):
    print >> out, '\n    ]\n'
    print >> out, '}'

#
#
#
def footprintToJson(coords, label):
    out = StringIO()
    initJson(out)

    #
    # 'PAIR_LONG_VIRGOLA_LAT_VIRGOLA', into: '[%s,%s],[%s,%s],[%s,%s],[%s,%s],[%s,%s]
    #
    coordPairsSring=''
    toks=coords.split(' ')
    numPairs = len(toks)
    for n in range(numPairs/2):
        if len(coordPairsSring)>0:
            coordPairsSring+=', '
        coordPairsSring += "[%s,%s]" % (toks[(n*2)+1], toks[(n*2)])
    print(" coordPairsSring=%s" % coordPairsSring)


    tmp = JSON_PATTERN.replace('PAIR_LONG_VIRGOLA_LAT_VIRGOLA', coordPairsSring).replace('LABEL', label)
    print >> out, JSON_PATTERN.replace('PAIR_LONG_VIRGOLA_LAT_VIRGOLA', coordPairsSring)
    closeJson(out)

    return out.getvalue()



#
#
#
def main():

    try:

        coords='43.797823 23.762868 43.652601 24.489380 43.130656 24.288654 43.275022 23.568147 43.797823 23.762868'
        res = footprintToJson(coords, 'the label')
        print('json:\n%s' % res)



    except Exception, e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print " Error: %s %s" % (exc_type, exc_obj)
        traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    main()