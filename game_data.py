

class GameData:

    def __init__(self):
        self.char_dict = {}

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
        
