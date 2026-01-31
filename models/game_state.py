from dataclasses import dataclass, field
from typing import Any
from enum import Enum, auto

import random
from deck import Card, Color, Deck, Wild, DrawFourWild, can_play_card, Skip, Reverse, DrawTwo, Number


class Phase(Enum):
    LOBBY = auto()
    PLAYING = auto()
    FINISHED = auto()

class Direction(Enum):
    COUNTER_CLOCKWISE = auto()
    CLOCKWISE = auto()

class GameError(Exception):
    pass

@dataclass
class PlayResult:
    played_by: int
    played_card: Card
    chosen_color: Color | None = None

    reversed: bool = False
    skipped: bool = False
    drew_cards: dict[int, int] = field(default_factory=dict)

    next_player: int | None = None
    winner: int | None = None


@dataclass
class DrawResult:
    user_id: int
    drawn: list[Card]
    next_player: int

class GameState:
    def __init__(self) -> None:
        self._rng = random.Random()
        self.state: dict[str, Any] = self._new_state()

    def _new_state(self) -> dict[str, Any]:
        return {
            "phase": Phase.LOBBY, # stores enum
            "players": [], # stores discord user ids
            "hands": {}, # stores user id -> list with cards
            "deck": [], # list with cards
            "discard": [],
            "turn_index": 0, # index representing which users turn it is 
            "direction": Direction.CLOCKWISE,
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
        if not self.state["players"]:
            raise GameError("No players.")
        return self.state["players"][self.state["turn_index"]]


    def hand(self, user_id: int) -> list[Card]:
        return list(self.state["hands"].get(user_id, []))

    def top_card(self) -> Card | None:
        discard = self.state["discard"]
        return discard[-1] if discard else None

    # Actions
    def add_player(self, user_id: int) -> None:
        if self.state["phase"] != Phase.LOBBY:
            raise GameError("Game state has already been started.")
        if user_id in self.state["players"]:
            raise GameError("Player already in lobby.")
        self.state["players"].append(user_id)
        self.state["hands"][user_id] = []

    def remove_player(self, user_id: int) -> None:

        if self.phase() != Phase.LOBBY:
            raise GameError("You can't leave after the game starts.")
        if user_id not in self.state["players"]:
            raise GameError("Player not in lobby.")
        self.state["players"].remove(user_id)
        self.state["hands"].pop(user_id, None)


    def start_game(self) -> None:
        if self.phase() != Phase.LOBBY:
            raise GameError("Game already started.")
        if len(self.state["players"]) < 2:
            raise GameError("Need at least 2 players to start.")

        deck = Deck()
        deck.add_default_cards()
        draw_pile: list[Card] = list(deck.cards)
        self._rng.shuffle(draw_pile)

        hands = self._deal_starting_hands(self.state["players"], draw_pile)
        discard_pile: list[Card] = []
        _ = self._draw_first_valid_start_card(draw_pile, discard_pile)

        self.state["hands"] = hands
        self.state["deck"] = draw_pile
        self.state["discard"] = discard_pile
        self.state["turn_index"] = 0
        self.state["direction"] = Direction.CLOCKWISE
        self.state["winner"] = None
        self.state["phase"] = Phase.PLAYING


    def play(self, user_id: int, card_index: int, choose_color: Color | None = None) -> PlayResult:
        if self.phase() != Phase.PLAYING:
            raise GameError("Game not started.")
        if user_id != self.current_player():
            raise GameError("Not your turn.")


        hand = self.state["hands"].get(user_id, [])
        if card_index < 0 or card_index >= len(hand):
            raise GameError("Invalid card index.")

        top = self.top_card()
        if top is None:
            raise GameError("No top card.")

        card = hand[card_index]

        if isinstance(card, (Wild, DrawFourWild)):
            if choose_color is None:
                raise GameError("You must choose a color for Wild/Draw4.")
            card.color = choose_color


        if not can_play_card(top, card):
            raise GameError("You can't play that card on the current top card.")

        played = hand.pop(card_index)
        self.state["discard"].append(played)

        res = PlayResult(
            played_by=user_id,
            played_card=played,
            chosen_color=(choose_color if isinstance(played, (Wild, DrawFourWild)) else None),
        )

        if len(hand) == 0:
            self.state["phase"] = Phase.FINISHED
            self.state["winner"] = user_id
            res.winner = user_id
            return res

        self._apply_effects_and_advance(played, res)
        res.next_player = self.current_player()
        return res


    def draw_and_pass(self, user_id: int, amt: int = 1) -> DrawResult:
        if self.phase() != Phase.PLAYING:
            raise GameError("Game is not currently playing.")
        if user_id != self.current_player():
            raise GameError("Not your turn.")
        if amt <= 0:
            raise GameError("amt must be >= 1.")

        draw_pile: list[Card] = self.state["deck"]
        discard_pile: list[Card] = self.state["discard"]
        hand: list[Card] = self.state["hands"][user_id]

        drawn: list[Card] = []
        for _ in range(amt):
            c = self._draw_one(draw_pile, discard_pile)
            hand.append(c)
            drawn.append(c)

        self._advance_turn(steps=1)
        return DrawResult(user_id=user_id, drawn=drawn, next_player=self.current_player())

    def _deal_starting_hands(self, players: list[int], draw_pile: list[Card]) -> dict[int, list[Card]]:
        for player in self.players():
            if player not in self.state["hands"]:
                self.state["hands"]["players"] = []

                for _ in range(cards_per_player = 7):
                    if not self.state["deck"]:
                        break
                    
                    card = self.state["deck"].pop()
                    self.state["hands"].append(card)

    def _draw_first_valid_start_card(self, draw_pile: list[Card], discard_pile: list[Card]) -> Card:
        raise NotImplementedError

    def _apply_effects_and_advance(self, played: Card, res: PlayResult) -> None:
        players = self.state["players"]
        n = len(players)

        match played:
            case Skip(_):
                res.skipped = True
                self._advance_turn(steps=2)

            case Reverse(_):
                self.state["direction"] = (
                    Direction.COUNTER_CLOCKWISE
                    if self.state["direction"] == Direction.CLOCKWISE
                    else Direction.CLOCKWISE
                )
                res.reversed = True

                if n == 2:
                    res.skipped = True
                    self._advance_turn(steps=2)
                else:
                    self._advance_turn(steps=1)

            case DrawTwo(_):
                target = self._peek_next_player_id()
                self._draw_many_to(target, 2)
                res.drew_cards[target] = 2
                res.skipped = True
                self._advance_turn(steps=2)

            case DrawFourWild(_):
                target = self._peek_next_player_id()
                self._draw_many_to(target, 4)
                res.drew_cards[target] = 4
                res.skipped = True
                self._advance_turn(steps=2)

            case Wild(_):
                self._advance_turn(steps=1)

            case Number(_, _):
                self._advance_turn(steps=1)

            case _:
                self._advance_turn(steps=1)

    def _advance_turn(self, steps: int = 1) -> None:
        players: list[int] = self.state["players"]
        if not players:
            return
        n = len(players)
        self.state["turn_index"] = (self.state["turn_index"] + steps * self._dir_sign()) % n


    def _peek_next_player_id(self) -> int:
        players: list[int] = self.state["players"]
        if not players:
            raise GameError("No players.")
        n = len(players)
        idx = self.state["turn_index"]
        next_idx = (idx + self._dir_sign()) % n
        return players[next_idx]

    def _draw_many_to(self, user_id: int, count: int) -> None:
        if count <= 0:
            return
        if user_id not in self.state["hands"]:
            raise GameError("Target player not found.")

        draw_pile: list[Card] = self.state["deck"]
        discard_pile: list[Card] = self.state["discard"]
        hand: list[Card] = self.state["hands"][user_id]

        for _ in range(count):
            hand.append(self._draw_one(draw_pile, discard_pile))

    def _draw_one(self, draw_pile: list[Card], discard_pile: list[Card]) -> Card:
        if draw_pile:
            return draw_pile.pop()

        if len(discard_pile) <= 1:
            raise GameError("No cards left to draw.")

        top = discard_pile[-1]
        refill = discard_pile[:-1]
        discard_pile[:] = [top]

        self._rng.shuffle(refill)
        draw_pile.extend(refill)

        # now must have cards
        return draw_pile.pop()

    def _dir_sign(self) -> int:
        return 1 if self.state["direction"] == Direction.CLOCKWISE else -1