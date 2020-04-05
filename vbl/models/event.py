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
