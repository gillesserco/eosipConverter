from sipMessageBuilder import SipMessageBuilder


class sar_Acquisition(SipMessageBuilder):
    
    this = ["<sar:Acquisition>"]

    REPRESENTATION = ["<gml:orbitNumber>@orbitNumber@</gml:orbitNumber>",
        "<gml:orbitDirection>@orbitDirection@</gml:orbitDirection>",
        "<gml:wrsLongitudeGrid codeSpace=\"\">@wrsLongitudeGrid@</gml:wrsLongitudeGrid>",
        "<gml:wrsLatitudeGrid codeSpace=\"\">@wrsLatitudeGrid@</gml:wrsLatitudeGrid>",
        "<sar:polarisationMode>@polarisationMode@</sar:polarisationMode>",
        "<sar:polarisationChannels>@polarisationChannels@</sar:polarisationChannels>",
        "<sar:antennaLookDirection>@antennaLookDirection@</sar:antennaLookDirection>",
        "<sar:minimumIncidenceAngle>@minimumIncidenceAngle@</sar:minimumIncidenceAngle>",
        "<sar:maximumIncidenceAngle>@maximumIncidenceAngle@</sar:maximumIncidenceAngle>",
        "<sar:incidenceAngleVariation>@incidenceAngleVariation@</sar:incidenceAngleVariation>",
        "<sar:dopplerFrequency uom=\"$$getValidValue('UNIT_FREQUENCE')$$\">@dopplerFrequency@</sar:dopplerFrequency>"]
