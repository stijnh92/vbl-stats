class PlayerStats:
    points: int
    minutes: int
    fouls: int
    free_throws: int
    two_pointers: int
    three_pointers: int
    games_played: int

    def __init__(self):
        self.points = 0
        self.minutes = 0
        self.fouls = 0
        self.free_throws = 0
        self.two_pointers = 0
        self.three_pointers = 0
        self.games_played = 0
