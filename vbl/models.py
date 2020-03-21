class Team:
    id: str
    name: str
    ft_attempts: int

    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.ft_attempts = 0
        self.players = list()

    def add_player(self, player):
        self.players.append(player)


class Player:
    id: str
    name: str
    number: str

    def __init__(self, **kwargs):
        self.id = kwargs.get('RelGUID')
        self.name = kwargs.get('Naam')
        self.number = kwargs.get('RugNr')

    def __str__(self):
        return "[{number}] {name}".format(name=self.name, number=self.number.rjust(2, ' '))


class GameEvent:
    id: str
    type: str
    period: int
    minute: int
    number: str
    content: str

    def __init__(self, **kwargs):
        self.id = kwargs.get('RelGUID')
        self.type = kwargs.get('GebType')
        self.period = kwargs.get('Periode')
        self.minute = kwargs.get('Minuut')
        self.number = kwargs.get('RugNr')
        self.content = kwargs.get('Text')

    def is_score(self):
        return self.type == 10

    def is_foul(self):
        return self.type == 30

    def is_substitution(self):
        return self.type == 50
