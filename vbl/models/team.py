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

    @property
    def ft_scored(self):
        return sum(player.stats.get('ft', 0) for player in self.players)

    def ft_percentage(self):
        if self.ft_attempts == 0:
            return 0

        return round((self.ft_scored / self.ft_attempts) * 100)

    def __str__(self):
        return "{name}".format(name=self.name)
