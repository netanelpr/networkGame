import socket
import threading 
import time
import selectors
from datetime import datetime

from offer import Offer
from encoder import * 

BROADCAST_PORT = 13117
BROADCAST_IP_ADDR = "10.0.2.255"
BROADCAST_MESSAGE = b"hello"

class Server:

    def __init__(self):
        self.server_port = 0
        self.server_ip = "127.0.0.1"
        self.server_socket = None
        self.selector = selectors.DefaultSelector()

        self.udp_broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_thread = None
        self.run_broadcast = True     

        self.init_server_socket()
        self.offer = Offer(self.server_port)

        #connections and groups
        self.group_index = 0
        self.groups_dict = {}
        self.group1 = [[], [], 0]
        self.group2 = [[], [], 0]
        self.connection = []

    def init_server_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(False)
        self.server_socket.bind((self.server_ip, self.server_port))
        
        self.selector.register(self.server_socket, selectors.EVENT_READ, self.accept)

        host_name = socket.gethostname()
        self.server_ip = socket.gethostbyname(host_name)
        self.server_port = self.server_socket.getsockname()[1]
        print("Server started,listening on IP address {}".format(self.server_ip))
               
        #init broadcast thread
        self.broadcast_thread = None

        #remove
        print("port",self.server_port)

    def start_udp_broadcast(self):
        self.run_broadcast = True  
        self.broadcast_thread = threading.Thread(target=self.udp_broadcast).start()

    def stop_udp_broadcast(self):
        self.run_broadcast = False  

    def add_socket_to_group(self, socket):
        self.connection.append(socket)
        if(self.group_index == 0):
            self.group1[0].append(socket)
            self.groups_dict[socket] = self.group1
            self.group_index = 1
        else:
            self.group2[0].append(socket)
            self.groups_dict[socket] = self.group2
            self.group_index = 0
    
    def remove_client_from_game(self, client_socket):
        client_socket.close()
        self.connection.remove(client_socket)
        
        if(((self.group_index) % 2) == 0):
            self.group2[0].remove(client_socket)
        else:
            self.group1[0].remove(client_socket)

        if(client_socket in self.groups_dict):
            self.groups_dict.pop(client_socket, None)

        self.selector.unregister(client_socket)

    def accept(self, socket, m):
        conn, addr = socket.accept()
        conn.setblocking(False)

        self.add_socket_to_group(conn)
        self.selector.register(conn, selectors.EVENT_READ, self.recv_user_name)

    def recv_user_name(self, client_socket, m):
        try:
            client_socket.fileno()
            name_encoded = client_socket.recv(1024)
            if(len(name_encoded) > 0):
                name = decode(name_encoded)
                (self.groups_dict[client_socket])[1].append(name)
            else:
                self.remove_client_from_game(client_socket)
        except OSError:
            self.remove_client_from_game(client_socket)

    def run(self):
        self.start_udp_broadcast()
        self.server_socket.listen(10)
        
        start_game = False
        accpecpt_connection_start_time = 0
        while True:
             events = self.selector.select(0.1)
             for key, m in events:
                callback = key.data
                callback(key.fileobj, m)
                if(not start_game):
                   start_game = True
                   accpecpt_connection_start_time = datetime.now()

             if(start_game):
                 time_since_started_game = (datetime.now() - accpecpt_connection_start_time).seconds
                 if(time_since_started_game > 10):
                     print(time_since_started_game)
                     self.run_game_wrapper()
                     start_game = False

        self.server_socket.close()

    def create_start_game_message(self):
        message = "Welcome to Keyboard Spamming Battle Royale.\n"
        start_sentence = "\nStart pressing keys on your keyboard as fast as you can!!\n"        

        names_grop1 = "Group1:\n=="
        for team_name in self.group1[1]:
            names_grop1 = names_grop1 + "\n" + team_name

        names_grop2 = "\nGroup2:\n=="
        for team_name in self.group2[1]:
            names_grop2 =  names_grop2 + "\n" + team_name

        return message + names_grop1 + names_grop2 + start_sentence

    def create_winners_message(self):
        group1_points = self.group1[2]
        group2_points = self.group2[2]
        
        winning_group_index = 1
        winning_group = self.group1
        if(group1_points - group2_points < 0):
            winning_group_index == 2
            winning_group = self.group2
 
        points_message = "Group 1 typed in {0} characters. Group 2 typed in {1} characters.\n".format(group1_points, group2_points)
        winning_group_message = "Group {0} wins!\n\n".format(winning_group_index)        

        names_grop = "Congratulations to the winners:\n=="
        for team_name in winning_group[1]:
            names_grop =  names_grop + "\n" + team_name

        return points_message + winning_group_message + names_grop

    def run_game_wrapper(self):
        self.stop_udp_broadcast()
        self.selector.unregister(self.server_socket)
        self.run_game()
        print("start sending out offer requests...")
        self.selector.register(self.server_socket, selectors.EVENT_READ, self.accept) 
        self.start_udp_broadcast()

    def run_game(self):
        print("starting the game")

        start_game_message_encoded = encode_string(self.create_start_game_message())
        for client in self.connection:
            try:
                client.send(start_game_message_encoded)
            except OSError:
                self.remove_client_from_game(client)
            
        self.game_core()

        winning_graoup_message = encode_string(self.create_winners_message())
        for client in self.connection:
            try:
                client.send(winning_graoup_message)
            except OSError:
                self.remove_client_from_game(client)

        self.clean_game()

    def game_core(self):
       start_game_time = datetime.now()
       game_running_for_seconds = 0
       
       while(game_running_for_seconds < 10):
           events = self.selector.select(0.1)
           for key, m in events:
               client = key.fileobj
               client.recv(1)
               group_array = self.groups_dict[client]
               group_array[2] = group_array[2] + 1

           game_running_for_seconds = (datetime.now() - start_game_time).seconds

    def clean_game(self):
        print("cleaning the game")

        for client in self.connection:
            self.selector.unregister(client)
            client.close()

        self.group_index = 0
        self.groups_dict = {}
        self.group1 = [[], [], 0]
        self.group2 = [[], [], 0]
        self.connection = []
        

    def udp_broadcast(self):
        while self.run_broadcast:
            #remove
            print("sending broadcast")
            self.udp_broadcast_socket.sendto(self.offer.get_bytes(), (BROADCAST_IP_ADDR, BROADCAST_PORT))
            try:
                time.sleep(1)
            except SleepInterruptedException:
                continue 

def main():
    server = Server()
    server.run()

if __name__=="__main__":
    main()
