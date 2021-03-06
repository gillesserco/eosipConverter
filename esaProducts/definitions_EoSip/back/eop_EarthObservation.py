import os,sys,inspect
import logging

from eoSip_converter.esaProducts.definitions_EoSip.sipMessageBuilder import SipMessageBuilder

class eop_EarthObservation(SipMessageBuilder):
    
    this = ["<eop:EarthObservation gml:id=\"@gmlId@_$$getNextCounter()$$\" xmlns:eop=\"http://www.opengis.net/eop/2.1\" xmlns:gml=\"http://www.opengis.net/gml/3.2\" xmlns:om=\"http://www.opengis.net/om/2.0\" xmlns:ows=\"http://www.opengis.net/ows/2.0\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">", "</eop:EarthObservation>"]

    REPRESENTATION = [
        "om_phenomenonTime",
        "om_resultTime",
        "om_procedure",
        "om_observedProperty",
        "om_featureOfInterest",
        "om_result",
        "eop_metaDataProperty"
        ]


    def test(self):
        meta=Metadata()
        meta.setMetadataPair(meta.METADATA_START_DATE, '20021023')
        mess=self.buildMessage(meta, "eop.EarthObservation")
        print "message:%s" % mess
        return mess


if __name__ == '__main__':
    print "start"
    logging.basicConfig(level=logging.WARNING)
    log = logging.getLogger('example')
    try:

        #
        from eoSip_converter.esaProducts.metadata import Metadata
        from eoSip_converter.esaProducts.definitions_EoSip.sipMessageBuilder import SipMessageBuilder
        
        c=eop_earthObservation()
        mess=c.test()

        fd=open("./sipProductReport.xml", "w")
        fd.write(mess)
        fd.close()
        print "message written in file:%s" % fd
    except Exception, err:
        log.exception('Error from throws():')
