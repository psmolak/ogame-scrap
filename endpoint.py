import itertools
import urllib.parse
from datetime import timedelta
from collections import OrderedDict


class Endpoint:
    """
    Stores information about particular endpoint
    such as name or update timedelta.
    """

    def __init__(self, path, delta, data=None):
        self.path = path
        self.delta = delta
        self.data = data

    @property
    def seconds(self):
        return self.delta.total_seconds()

    def encode(self):
        query = '?' + urllib.parse.urlencode(self.data) if self.data else ''
        return self.path + query


players = Endpoint('players.xml', timedelta(days=1))
alliances = Endpoint('alliances.xml', timedelta(days=1))
universe = Endpoint('universe.xml', timedelta(days=7))
universes = Endpoint('universes.xml', timedelta(days=1))
serverdata = Endpoint('serverData.xml', timedelta(days=1))
highscores = [
    Endpoint(
        'highscore.xml',
        timedelta(hours=1),
        OrderedDict([('category', c), ('type', t)])
    ) for c, t in itertools.product([1, 2], range(8))
]

