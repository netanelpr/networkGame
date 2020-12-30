import socket
import select
import termios, fcntl, sys, os

from offer import Offer
from network import * 

TEAM_NAME = "NekoodaPsik"

class Client:

    def __init__(self):
        self.udp_init()

    def udp_init(self):
        self.udp_socket_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket_listener.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket_listener.bind((BROADCAST_IP_ADDR, BROADCAST_PORT))

    """
    The main funtion of the client.
    """
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

            try:
                self.udp_socket_listener.close()
            except: pass
            self.udp_init()


    """
    Connect to the server and run the game
    @param server_addr The server ip address
    @param server_port The server port
    """
    def connect_and_run_the_game(self, server_addr, server_port):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            #client_socket.connect(("127.0.0.1", server_port))
            client_socket.connect((server_addr, server_port))
        except OSError:
            print("​Error when tring to connect to the server")
            return
        client_socket.send(encode_string(TEAM_NAME+"\n"))
    
        run_game = True
        start_game_message = ""
        try:
            start_game_message = decode(client_socket.recv(1024)) + "\n"
        except OSError:
            client_socket.close()
            return

        e_game_message = ""

        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
        fd = sys.stdin.fileno()
        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

        print(start_game_message)
        try:
            while run_game:
                readable, _, _ = select.select([sys.stdin, client_socket], [], [], 0.1)
                for reader in readable:
                    if(reader == sys.stdin):
                        c = sys.stdin.read(1)
                        client_socket.send(encode_string(str(c)))
                    else:
                        e_game_message = decode(reader.recv(1024))
                        if(len(e_game_message) == 0):
                            run_game = False
                            break
                        else:
                            print(e_game_message)
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

        try:
            client_socket.close()
        except Exeption:
            pass

def main():
    client = Client()
    client.run()

if __name__=="__main__":
    main()
