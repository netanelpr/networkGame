NETWORK_ADDR = "127.0.0.1"
BROADCAST_IP_ADDR = "10.0.2.255"

NETWORK_ADAPTER_1 = "eth1"
NETWORK_BROADCAST_1 = "172.1.255.255"
NETWORK_ADAPTER_2 = "eth2"
NETWORK_BROADCAST_2 = "172.99.255.255"

try:
    import scapy.all
    NETWORK_ADDR = scapy.all.get_if_addr(NETWORK_ADAPTER_2)
    BROADCAST_IP_ADDR = NETWORK_BROADCAST_2
except:
    pass

BROADCAST_PORT = 13117

def encode_string(string):
    return string.encode()

def decode(bytes):
    return bytes.decode()     
