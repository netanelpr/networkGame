class Offer:
    cookie = 0xfeedbeed
    offer_type = 0x02
    byte_order = "big"

    cookie_bytes = cookie.to_bytes(4, byte_order)
    offer_type_bytes = offer_type.to_bytes(1, byte_order)

    #@param port is a port number between 0 to 2^16-1 
    def __init__(self, param_port):
        self.port_bytes = param_port.to_bytes(2, Offer.byte_order)
        self.encode_data = Offer.cookie_bytes + Offer.offer_type_bytes + self.port_bytes

    """ Return the data bytes """
    def get_bytes(self):
        return self.encode_data


    """
    Return -1 if the data isnt valid else return the port
    @param bytes_offer the bytes of the offer to check
    """
    @staticmethod
    def get_port_if_valid_offer(bytes_offer):
        if(len(bytes_offer) != 7):
            return -1

        offer_cookie = bytes_offer[0:4]
        if(offer_cookie != Offer.cookie_bytes):
            return -1

        param_offer_type = bytes_offer[4:5]
        if(param_offer_type != Offer.offer_type_bytes):
            return -1

        return int.from_bytes(bytes_offer[5:7], Offer.byte_order)
