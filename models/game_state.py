"""
Provides classes and functions related to the operation of a game.
"""

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import random
import time

from dataclasses import dataclass, field
from typing import Any
from enum import Enum, auto

from models.deck import (
    Card,
    Color,
    Deck,
    Wild,
    DrawFourWild,
    can_play_card,
    Skip,
    Reverse,
    DrawTwo,
    Number,
)
from models import bot

class Phase(Enum):
    LOBBY = auto()
    PLAYING = auto()
    FINISHED = auto()


class Direction(Enum):
    COUNTER_CLOCKWISE = auto()
    CLOCKWISE = auto()


class GameError(Exception):
    def __init__(self, msg: str, private: bool = False, title: str = ""):
        super().__init__(msg)
        self.private = private
        self.title = title


@dataclass
class PlayResult:
    # pylint: disable=too-many-instance-attributes
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


def _deal_starting_hands(
    players: list[int], draw_pile: list[Card], cards_per_player: int = 7
) -> dict[int, list[Card]]:
    if len(players) < 2:
        raise GameError("Need at least 2 players to deal hands.")
    if cards_per_player <= 0:
        raise GameError("cards_per_player must be >= 1.")

    hands: dict[int, list[Card]] = {uid: [] for uid in players}

    for _ in range(cards_per_player):
        for uid in players:
            if not draw_pile:
                raise GameError("Deck ran out while dealing starting hands.")
            hands[uid].append(draw_pile.pop())

    return hands


class GameState:
    def __init__(self) -> None:
        self._rng = random.Random()
        self.state: dict[str, Any] = self._new_state()

    def _new_state(self) -> dict[str, Any]:
        return {
            "phase": Phase.LOBBY,  # stores enum
            "players": [],  # stores discord user ids
            "bots": [],  # the indices of the users which are bots
            "hands": {},  # stores user id -> list with cards
            "deck": [],  # list with cards
            "discard": [],
            "turn_index": 0,  # index representing which users turn it is
            "turn_count": 0,  # counter representing the current turn #
            "uno_vulnerable": None, # user_id who has 1 card and can be caught
            "uno_grace_until": 0.0, # tiemstamp when others may start catching
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

    def is_bot(self, user_id) -> bool:
        return user_id < 0

    def hand(self, user_id: int) -> list[Card]:
        return list(self.state["hands"].get(user_id, []))

    def top_card(self) -> Card | None:
        discard = self.state["discard"]
        return discard[-1] if discard else None

    def turn_count(self) -> int:
        return self.state["turn_count"]

    def uno_vulnerable(self) -> int | None:
        return self.state["uno_vulnerable"]

    def uno_grace_active(self) -> bool:
        return (
            self.state["uno_vulnerable"] is not None
            and self._now() < self.state["uno_grace_until"]
        )

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

    def add_bot(self) -> None:
        # Choose a new negative user ID less than any existing bot
        m = 0
        for user_id in self.state["players"]:
            m = min(m, user_id)

        self.add_player(m - 1)

    def start_game(self) -> None:
        if self.phase() != Phase.LOBBY:
            raise GameError("Game already started.", private=True)
        if len(self.state["players"]) < 2:
            raise GameError("Need at least 2 players to start.", private=True)

        deck = Deck()
        deck.add_default_cards()
        draw_pile: list[Card] = list(deck.cards)
        self._rng.shuffle(draw_pile)

        hands = _deal_starting_hands(self.state["players"], draw_pile)
        discard_pile: list[Card] = []
        _ = self._draw_first_valid_start_card(draw_pile, discard_pile)

        self.state["hands"] = hands
        self.state["deck"] = draw_pile
        self.state["discard"] = discard_pile
        self.state["turn_index"] = 0
        self.state["direction"] = Direction.CLOCKWISE
        self.state["winner"] = None
        self.state["phase"] = Phase.PLAYING

    def play(
        self, user_id: int, card_index: int, choose_color: Color | None = None
    ) -> PlayResult:
        if self.phase() != Phase.PLAYING:
            raise GameError(
                "The game has not started yet!", title="Game Not Started", private=True
            )
        if user_id != self.current_player():
            raise GameError(
                "It is currently not your turn to play.",
                title="Wrong Turn",
                private=True,
            )

        hand = self.state["hands"].get(user_id, [])
        if card_index < 0 or card_index >= len(hand):
            raise GameError(
                "That is not a valid card index",
                title="Invalid Card Index",
                private=True,
            )

        top = self.top_card()
        if top is None:
            raise GameError(
                "There is no card on top!", title="No Top Card!", private=True
            )

        card = hand[card_index]

        if isinstance(card, (Wild, DrawFourWild)):
            if choose_color is None:
                raise GameError(
                    "You must choose a color for Wild/Draw4.",
                    title="Picked Incorrectly",
                    private=True,
                )
            card.color = choose_color

        if not can_play_card(top, card):
            raise GameError(
                "You can't play that card on the current top card.",
                title="Incorrect Card",
                private=True,
            )

        played = hand.pop(card_index)
        self.state["discard"].append(played)
        self._start_uno_window_if_needed(user_id)

        res = PlayResult(
            played_by=user_id,
            played_card=played,
            chosen_color=(
                choose_color if isinstance(played, (Wild, DrawFourWild)) else None
            ),
        )

        if len(hand) == 0:
            self._clear_uno()
            self.state["phase"] = Phase.FINISHED
            self.state["winner"] = user_id
            res.winner = user_id
            return res

        self._apply_effects_and_advance(played, res)
        res.next_player = self.current_player()
        return res

    def play_bot(self):
        if not self.is_bot(self.current_player()):
            raise GameError("Current player isn't a bot")

        user_id = self.current_player()
        top = self.top_card()

        hand = self.state["hands"][user_id]
        (index, color) = bot.play_card(bot.Strategy.RANDOM, hand, top)

        if index is None:
            self.draw_and_pass(user_id)
        else:
            self.play(user_id, index, color)

    def draw_and_pass(self, user_id: int, amt: int = 1) -> DrawResult:
        if self.phase() != Phase.PLAYING:
            raise GameError(
                "Game is not currently playing.", title="Game Not Started", private=True
            )
        if user_id != self.current_player():
            raise GameError(
                "It's not your turn to play.", title="Wrong Turn", private=True
            )
        if amt <= 0:
            raise GameError("Amt must be >= 1.", title="Invalid Amount", private=True)

        draw_pile: list[Card] = self.state["deck"]
        discard_pile: list[Card] = self.state["discard"]
        hand: list[Card] = self.state["hands"][user_id]

        drawn: list[Card] = []
        for _ in range(amt):
            c = self._draw_one(draw_pile, discard_pile)
            hand.append(c)
            drawn.append(c)

        if self.state["uno_vulnerable"] == user_id:
            self._clear_uno()

        self._advance_turn(steps=1)
        return DrawResult(
            user_id=user_id, drawn=drawn, next_player=self.current_player()
        )

    def _draw_first_valid_start_card(
        self, draw_pile: list[Card], discard_pile: list[Card]
    ) -> Card:
        if not draw_pile:
            raise GameError("Deck is empty; can't pick a start card.")

        rejected: list[Card] = []

        while draw_pile:
            card = draw_pile.pop()

            if isinstance(card, Number):
                discard_pile.append(card)

                if rejected:
                    draw_pile.extend(rejected)
                    self._rng.shuffle(draw_pile)

                return card

            rejected.append(card)

        draw_pile.extend(rejected)
        self._rng.shuffle(draw_pile)
        raise GameError("Couldn't find a valid start Number card in the deck.")

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
        self.state["turn_index"] = (
            self.state["turn_index"] + steps * self._dir_sign()
        ) % n
        self.state["turn_count"] += 1

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

    def _now(self) -> float:
        return time.monotonic()

    def _clear_uno(self) -> None:
        self.state["uno_vulnerable"] = None
        self.state["uno_grace_until"] = 0.0

    # start/reset uno if player is at 1 card; otherwise clear
    def _start_uno_window_if_needed(self, user_id: int) -> None:
        hand = self.state["hands"].get(user_id, [])
        if len(hand) == 1:
            self.state["uno_vulnerable"] = user_id
            self.state["uno_grace_until"] = self._now() + 2.0
        else:
            if self.state["uno_vulnerable"] == user_id:
                self._clear_uno()

    def call_uno(self, caller_id: int) -> dict[str, Any]:
        if self.phase() != Phase.PLAYING:
            raise GameError("Game is not currently playing.", private=True)

        target = self.state["uno_vulnerable"]
        if target is None:
            return {"result": "no_target", "caller": caller_id}

        # if vulnerable player calls uno (safe, clear window)
        if caller_id == target:
            self._clear_uno()
            return {"result": "safe", "target": target, "caller": caller_id}

        # other players trying to catch vulnerable player
        if self._now() < self.state["uno_grace_until"]:
            return {"result": "too_early", "target": target, "caller": caller_id}

        self._draw_many_to(target, 2)
        self._clear_uno()
        return {"result": "penalty", "target": target, "caller": caller_id}
