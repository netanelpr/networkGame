

class GameData:

    def __init__(self):
        self.team_wins = {}
        self.char_dict = {}
        self.number_of_games = 0

    """
    Add a char to the data
    @param c The char to add
    """
    def add_char(self, c):
        if c in self.char_dict:
            self.char_dict[c] = self.char_dict[c] + 1
        else:
            self.char_dict[c] = 1

    """
    Return tuple of the the most used char and 
    the number of times it has been used
    """
    def get_most_used_char(self):
        top_c = chr(0)
        number_of_used = 0
        for key in self.char_dict:
            ch_uses = self.char_dict[key]
            if(ch_uses > number_of_used):
                number_of_used = ch_uses
                top_c = key

        return (top_c, number_of_used)

    """
    Incremate the number of games
    """
    def inc_number_of_games(self):
        self.number_of_games = self.number_of_games + 1

    """
    Return the number of game so far
    """
    def get_number_of_games(self):
        return self.number_of_games
       

    """
    Add the name of the winner team to the data
    """
    def add_winner(self, team_name):
        if(team_name in self.team_wins.keys()):
            self.team_wins[team_name] = self.team_wins[team_name] + 1
        else:
            self.team_wins[team_name] = 1

    """
    Return a list the top 3 team_winner and there score
    """
    def get_top_three_winners(self):
        winners_list = sorted(self.team_wins, key=self.team_wins.get, reverse=True)[:3]
        winners_list_with_points = []
        for team_name in winners_list:
            winners_list_with_points.append((team_name, self.team_wins[team_name]))
        return winners_list_with_points


