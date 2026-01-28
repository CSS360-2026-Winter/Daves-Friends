from typing import Any
from enum import Enum, auto

from deck import Card, Color

class Phase(Enum):
    LOBBY = auto()
    PLAYING = auto()
    FINISHED = auto()

class Direction(Enum):
    COUNTER_CLOCKWISE = auto()
    CLOCKWISE = auto()


class GameState:
    def __init__(self) -> None:
        self.state: dict[str, Any] = self._new_state()

    def _new_state(self) -> dict[str, Any]:
        return {
            "phase": Phase.LOBBY, # stores enum
            "players": [], # stores discord user ids
            "hands": [], # stores user id -> list with cards
            "deck": [], # list with cards
            "turn_index": 0, # index representing which users turn it is 
            "direction": Direction,
            "winner": None,
        }

    def reset(self) -> None:
        self.state = self._new_state()

    # Getters
    def phase(self) -> Phase:
        return self.state["phase"]
    
    def players(self) -> list[int]:
        return list(self.state["players"])

    def current_player(self) -> int:
        return self.state["players"][self.state["turn_index"]]
    
    def hand(self, user_id: int) -> list[Card]:
        return list(self.state["hands"].get(user_id, []))

    def top_card(self) -> Card:
        pass

    # Actions
    def add_player(self, user_id: int) -> None:
        pass

    def remove_player(self, user_id: int) -> None:
        pass

    def start_game(self) -> None:
        pass 

    def play(self, user_id: int, card_index: int, choose_color: Color | None = None) -> None:
        pass

    def draw_and_pass(self, user_id: int, amt: int = 1) -> list[card]:
        pass