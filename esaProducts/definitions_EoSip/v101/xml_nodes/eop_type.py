from sipMessageBuilder import SipMessageBuilder


class eop_type(SipMessageBuilder):
    
    this = []

    REPRESENTATION = ["<eop:type>@browsesType@</eop:type>"]
