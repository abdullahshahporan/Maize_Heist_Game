"""
entities.py — Core data classes: Player, Treasure, TemporaryWall.
"""


class Player:
    """Represents one player / agent on the board."""
    __slots__ = ('id', 'name', 'type', 'row', 'col', 'score', 'collected_count')

    def __init__(self, player_id: int, name: str, player_type: str,
                 row: int, col: int):
        self.id = player_id          # 1 or 2
        self.name = name
        self.type = player_type      # "human", "minimax", "astar"
        self.row = row
        self.col = col
        self.score = 0
        self.collected_count = 0     # total treasures collected

    @property
    def pos(self):
        return (self.row, self.col)

    def clone(self):
        p = Player(self.id, self.name, self.type, self.row, self.col)
        p.score = self.score
        p.collected_count = self.collected_count
        return p

    def __repr__(self):
        return f"Player({self.id}, pos=({self.row},{self.col}), score={self.score})"


class Treasure:
    """A collectible item on the board."""
    __slots__ = ('row', 'col', 'type', 'value')

    def __init__(self, row: int, col: int, treasure_type: str, value: int):
        self.row = row
        self.col = col
        self.type = treasure_type    # "cash", "gold", "diamond"
        self.value = value

    @property
    def pos(self):
        return (self.row, self.col)

    def clone(self):
        return Treasure(self.row, self.col, self.type, self.value)

    def __repr__(self):
        return f"Treasure({self.type}, pos=({self.row},{self.col}), val={self.value})"


class TemporaryWall:
    """A wall placed by a player that lasts for a fixed number of full rounds."""
    __slots__ = ('row', 'col', 'owner_id', 'placed_on_round', 'remaining_rounds')

    def __init__(self, row: int, col: int, owner_id: int,
                 placed_on_round: int, remaining_rounds: int = 5):
        self.row = row
        self.col = col
        self.owner_id = owner_id
        self.placed_on_round = placed_on_round
        self.remaining_rounds = remaining_rounds

    @property
    def pos(self):
        return (self.row, self.col)

    def clone(self):
        return TemporaryWall(self.row, self.col, self.owner_id,
                             self.placed_on_round, self.remaining_rounds)

    def __repr__(self):
        return (f"TempWall(pos=({self.row},{self.col}), owner={self.owner_id}, "
                f"remaining={self.remaining_rounds})")
