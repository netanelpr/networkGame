import socket
import select
import termios, fcntl, sys, os

from offer import Offer
from encoder import * 

BROADCAST_PORT = 13117
BROADCAST_IP_ADDR = "10.0.2.255"
BROADCAST_MESSAGE = b"hello"

TEAM_NAME = "Earthlings"

class Client:

    def __init__(self):
        self.udp_socket_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket_listener.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket_listener.bind((BROADCAST_IP_ADDR, BROADCAST_PORT))

    def run(self):
        print("Client started, listening for offer requests...")
        
        while True:
            data, addr = self.udp_socket_listener.recvfrom(1024)
            tcp_server_port = Offer.get_port_if_valid_offer(data)

            if(tcp_server_port < 0):
                print("​Received invalid offer from {0}\n\twith data {1}".format(addr, data))
                continue

            print("​Received offer from {0},attempting to connect...".format(addr))
            self.connect_and_run_the_game(addr[0], tcp_server_port)
            print("​Server disconnected, listening for offer requests...")


    def connect_and_run_the_game(self, server_addr, server_port):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', server_port))
        #client_socket.connect((server_addr, server_port))

        client_socket.send(encode_string(TEAM_NAME+"\n"))
    
        run_game = True
        start_game_message = decode(client_socket.recv(1024)) + "\n"
        e_game_message = ""

        fd = sys.stdin.fileno()
        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

        print(start_game_message)
        presses = 0
        try:
            while run_game:
                try:
                    c = sys.stdin.read(1)
                    if(len(c) == 1):
                        presses = presses + 1
                        client_socket.send(encode_string(str(c)))
                except IOError: pass

                readable_socket, _, _ = select.select([client_socket], [], [], 0)
                for con in readable_socket:
                    e_game_message = con.recv(1024)
                    run_game = False
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

        print(decode(e_game_message))
    
        #remove
        print(presses)
    
        try:
            client_socket.close()
        except Exeption:
            pass

def main():
    client = Client()
    client.run()

if __name__=="__main__":
    main()
