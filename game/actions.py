"""
actions.py — Defines the Action class used by all players and AI agents.
"""


# Action types
ACTION_MOVE = "move"
ACTION_PLACE_WALL = "place_wall"


class Action:
    """
    Represents a single player action per turn.
    action_type: "move" or "place_wall"
    target: (row, col) tuple — destination cell for move or wall position
    """

    def __init__(self, action_type: str, target: tuple):
        self.action_type = action_type
        self.target = target  # (row, col)

    def __repr__(self):
        return f"Action({self.action_type}, target={self.target})"

    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return self.action_type == other.action_type and self.target == other.target

    def __hash__(self):
        return hash((self.action_type, self.target))
