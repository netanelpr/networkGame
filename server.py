import socket
import threading 
import time
import selectors

from offer import Offer
from encoder import * 
from game_data import GameData

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
        self.broadcast_iterations = 0

        self.init_server_socket()
        self.offer = Offer(self.server_port)

        self.on_game = False;  
        self.init_groups_data()
        self.game_data = GameData()

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

    def init_groups_data(self):
        self.group_index = 0
        self.groups_dict = {}
        self.group1 = [{}, 0]
        self.group2 = [{}, 0]
        self.connection = []
        self.connection_without_team_name = []

    def start_udp_broadcast(self):
        self.run_broadcast = True
        self.broadcast_iterations = 0
        self.broadcast_thread = threading.Thread(target=self.udp_broadcast).start()

    def udp_broadcast(self):
        while (self.broadcast_iterations < 10):
            self.broadcast_iterations = self.broadcast_iterations + 1
            #remove
            print("sending broadcast")
            self.udp_broadcast_socket.sendto(self.offer.get_bytes(), (BROADCAST_IP_ADDR, BROADCAST_PORT))
            try:
                time.sleep(1)
            except SleepInterruptedException:
                continue
        self.on_game = True

    def add_socket_to_group(self, socket, team_name):
        self.connection_without_team_name.remove(socket)
        self.connection.append(socket)
        if(self.group_index == 0):
            self.group1[0][socket] = team_name
            self.groups_dict[socket] = self.group1
            self.group_index = 1
        else:
            self.group2[0][socket] = team_name
            self.groups_dict[socket] = self.group2
            self.group_index = 0
    
    def remove_client_from_game(self, client_socket):
        client_socket.close()
        self.connection.remove(client_socket)
        
        if(((self.group_index) % 2) == 0):
            self.group2[0].pop(client_socket, None)
        else:
            self.group1[0].pop(client_socket, None)

        if(client_socket in self.groups_dict):
            self.groups_dict.pop(client_socket, None)

        self.selector.unregister(client_socket)

    def accept(self, socket, m):
        conn, addr = socket.accept()
        conn.setblocking(False)

        #self.add_socket_to_group(conn)
        self.connection_without_team_name.append(conn)
        self.selector.register(conn, selectors.EVENT_READ, self.recv_user_name)

    def recv_user_name(self, client_socket, m):
        try:
            client_socket.fileno()
            name_encoded = client_socket.recv(1024)
            if(len(name_encoded) > 0):
                name = decode(name_encoded)
                self.add_socket_to_group(client_socket, name)
            else:
                self.remove_client_from_game(client_socket)
        except OSError:
            self.remove_client_from_game(client_socket)

    def run(self):
        self.start_udp_broadcast()
        self.server_socket.listen(10)
        
        while True:
             events = self.selector.select(0.001)
             for key, m in events:
                callback = key.data
                callback(key.fileobj, m)

             if(self.on_game):
                 self.run_game_wrapper()

        self.server_socket.close()

    def get_group_name(self, group_dict):
        group_names = ""
        for key in group_dict:
            group_names = group_names + group_dict[key] + "\n"
        return group_names

    def create_start_game_message(self):
        message = "Welcome to Keyboard Spamming Battle Royale.\n"
        start_sentence = "\nStart pressing keys on your keyboard as fast as you can!!\n"        

        names_grop1 = "Group1:\n==\n"
        names_grop1 = names_grop1 + self.get_group_name(self.group1[0])

        names_grop2 = "Group2:\n==\n"
        names_grop2 = names_grop2 + self.get_group_name(self.group2[0])

        return message + names_grop1 + names_grop2 + start_sentence

    def create_winners_message(self):
        group1_points = self.group1[1]
        group2_points = self.group2[1]
        
        winning_group_index = 1
        winning_group = self.group1
        if(group1_points - group2_points < 0):
            winning_group_index == 2
            winning_group = self.group2
 
        points_message = "Group 1 typed in {0} characters. Group 2 typed in {1} characters.\n".format(group1_points, group2_points)
        winning_group_message = "Group {0} wins!\n\n".format(winning_group_index)        

        group_names = "Congratulations to the winners:\n==\n"
        group_names = group_names + self.get_group_name(winning_group[0])

        return points_message + winning_group_message + group_names

    def create_stat_of_the_games_message(self):
        top_message = "============\nGame stats:\n"
        close_stat_message = "============\n"
        most_used_char_tuple = self.game_data.get_most_used_char()
        most_use_char_message = "Most used char is '{0}' with {1} uses\n".format(most_used_char_tuple[0], most_used_char_tuple[1])

        return top_message + most_use_char_message + close_stat_message

    def run_game_wrapper(self):
        self.selector.unregister(self.server_socket)
        self.run_game()
        print("start sending out offer requests...")
        self.selector.register(self.server_socket, selectors.EVENT_READ, self.accept)
        self.on_game = False
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

        winning_group_message = self.create_winners_message()
        game_stat_message = self.create_stat_of_the_games_message()
        all_game_data_message = encode_string(winning_group_message + game_stat_message)
        for client in self.connection:
            try:
                client.send(all_game_data_message)
            except OSError:
                self.remove_client_from_game(client)

        self.clean_game()

    def game_core(self):
       game_running_since_second = time.time()
       game_running_for_seconds = 0

       while(game_running_for_seconds < 10):
           events = self.selector.select(0.001)
           for key, m in events:
               client = key.fileobj
               ch = decode(client.recv(1))
               #client recv return close connection
               self.game_data.add_char(ch[0])
               group_array = self.groups_dict[client]
               group_array[1] = group_array[1] + 1

           game_running_for_seconds = time.time() - game_running_since_second
    def clean_game(self):
        print("cleaning the game")

        for client in self.connection:
            self.selector.unregister(client)
            client.close()

        self.init_groups_data()

def main():
    server = Server()
    server.run()

if __name__=="__main__":
    main()
