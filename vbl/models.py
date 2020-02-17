class Team:
    name: str

    def __init__(self, name):
        self.name = name
        self.players = list()

    def add_player(self, player):
        self.players.append(player)


class Player:
    id: str
    name: str
    number: str

    def __init__(self, id, name, number):
        self.id = id
        self.name = name
        self.number = number

    def __str__(self):
        return "[{number}] {name}".format(name=self.name, number=self.number.rjust(2, ' '))
