from .team import Team
from .stats import PlayerStats


class Player:
    id: str
    name: str
    number: str
    team: Team
    stats: PlayerStats

    def __init__(self, team: Team, **kwargs):
        self.id = kwargs.get('RelGUID')
        self.name = kwargs.get('Naam')
        self.number = kwargs.get('RugNr')
        self.team = team
        self.stats = PlayerStats()

    def __str__(self):
        return "{name} ({number})".format(name=self.name, number=self.number)
