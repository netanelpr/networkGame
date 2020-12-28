import socket
import threading 
import time
import selectors

from offer import Offer
from network import * 
from game_data import GameData

class Server:

    def __init__(self):
        self.server_port = 0
        self.server_ip = NETWORK_ADDR
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

    """
    =========================
    ==== Server network =====
    =========================
    """


    """
    Initialize the server socket and the selector
    """
    def init_server_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(False)
        self.server_socket.bind((self.server_ip, self.server_port))
        
        self.selector.register(self.server_socket, selectors.EVENT_READ, self.accept)

        #host_name = socket.gethostname()
        #self.server_ip = socket.gethostbyname(host_name)
        self.server_port = self.server_socket.getsockname()[1]
        print("Server started,listening on IP address {}".format(self.server_ip))
               
        #init broadcast thread
        self.broadcast_thread = None

        #remove
        print("port",self.server_port)

    """
    Start the udp broadcast
    """
    def start_udp_broadcast(self):
        self.run_broadcast = True
        self.broadcast_iterations = 0
        self.broadcast_thread = threading.Thread(target=self.udp_broadcast).start()

    """
    UDP broadcast core, send the broadcast 10 times
    One broadcast every second
    """
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

    """
    Add the socket to one of the play gorups evenly
    """
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
    
    """
    Remove the client from the game.
    """
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

    """
    Method to handle new connetion to the server.
    Insert the client socket to the selector to handle the
    data he need to send (the name of the team)
    """
    def accept(self, socket, m):
        conn, addr = socket.accept()
        conn.setblocking(False)

        #self.add_socket_to_group(conn)
        self.connection_without_team_name.append(conn)
        self.selector.register(conn, selectors.EVENT_READ, self.recv_user_name)

    """
    Ignore all the data from the client. This method is for
    cleaning the socket read buffer before the game 
    """
    def ignore_user_data(self, client_socket, m):
        try:
            client_socket.fileno()
            data = client_socket.recv(256)
            if(len(data) == 0):
                self.remove_client_from_game(client_socket)
        except OSError:
            self.remove_client_from_game(client_socket)

    """
    Method to handle the data from the client before the game starts
    The data need to be the team name. After the data was recived modify
    the selecotr data of the client read event to be the ignore_user_data method.
    Use the ignore_user_data until the game will start
    """
    def recv_user_name(self, client_socket, m):
        try:
            client_socket.fileno()
            name_encoded = client_socket.recv(1024)
            if(len(name_encoded) > 0):
                name = decode(name_encoded)
                self.add_socket_to_group(client_socket, name)
                self.selector.modify(client_socket, selectors.EVENT_READ, self.ignore_user_data)
            else:
                self.remove_client_from_game(client_socket)
        except OSError:
            self.remove_client_from_game(client_socket)

    """
    The main method of the server.
    """
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

    """
    =========================
    ======= Game core =======
    =========================
    """

    """
    Init the groups data. Use it before each game
    """
    def init_groups_data(self):
        self.group_index = 0
        self.groups_dict = {}
        self.group1 = [{}, 0]
        self.group2 = [{}, 0]
        self.connection = []
        self.connection_without_team_name = []

    """
    Return all the group names from the group dict
    """
    def get_group_name(self, group_dict):
        group_names = ""
        for key in group_dict:
            group_names = group_names + group_dict[key] + "\n"
        return group_names

    """
    Return the start game message.
    The message follows the format
    """
    def create_start_game_message(self):
        message = "Welcome to Keyboard Spamming Battle Royale.\n"
        start_sentence = "\nStart pressing keys on your keyboard as fast as you can!!\n"        

        names_grop1 = "Group1:\n==\n"
        names_grop1 = names_grop1 + self.get_group_name(self.group1[0])

        names_grop2 = "Group2:\n==\n"
        names_grop2 = names_grop2 + self.get_group_name(self.group2[0])

        return message + names_grop1 + names_grop2 + start_sentence

    """
    Return the message that concludes the game
    The message follow the format. In addition there are some stat of
    the games to this point.
    """
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

    """
    Return the stat message.
    """
    def create_stat_of_the_games_message(self):
        top_message = "============\nGame stats:\n"
        close_stat_message = "============\n"
        most_used_char_tuple = self.game_data.get_most_used_char()
        most_use_char_message = "Most used char is '{0}' with {1} uses\n".format(most_used_char_tuple[0], most_used_char_tuple[1])

        return top_message + most_use_char_message + close_stat_message


    """
    The run game method. This method wraps the run_game_method in order to clean
    the data after the game and initialize and organize the server socket and selector
    """
    def run_game_wrapper(self):
        self.selector.unregister(self.server_socket)
        self.run_game()
        print("start sending out offer requests...")
        self.selector.register(self.server_socket, selectors.EVENT_READ, self.accept)
        self.on_game = False
        self.start_udp_broadcast()

    """
    Start the game
    """
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

    """
    This method is the game core which is the code that
    recive the keys from the client and handling it.
    """
    def game_core(self):
       game_running_since_second = time.time()
       game_running_for_seconds = 0

       while(game_running_for_seconds < 10):
           events = self.selector.select(0.001)
           for key, m in events:
               client = key.fileobj
               ch = decode(client.recv(1))
               
               #client close the game
               if(len(ch) == 0):
                   self.connection.remove(client)
                   self.selector.unregister(client)
                   continue

               self.game_data.add_char(ch[0])
               group_array = self.groups_dict[client]
               group_array[1] = group_array[1] + 1

           game_running_for_seconds = time.time() - game_running_since_second

    """
    Clean the game data.
    """
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
