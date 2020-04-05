class Team:
    id: str
    name: str
    ft_attempts: int
    players: list

    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.ft_attempts = 0
        self.players = list()

    def add_player(self, player):
        self.players.append(player)

    def __str__(self):
        return "{name}".format(name=self.name)
