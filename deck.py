"""
Defines classes relating to an Uno deck, including proper Deck generation and validating cards can
be played on top of each other properly. Also defines various types for different kinds of cards
so they can be validated by the type system.
"""
from dataclasses import dataclass
from enum import Enum, auto
from random import shuffle


class Color(Enum):
    """
    The color of an Uno card. Can be red, yellow, blue, or green.
    """
    RED = auto()
    YELLOW = auto()
    BLUE = auto()
    GREEN = auto()


class Deck:
    """
    A set of cards and a method to generate cards for a deck.
    """
    cards = []

    def __init__(self):
        """
        Creates an empty deck.
        """
        self.cards = []

    def add_default_cards(self):
        """
        Adds the default Uno cards (as defined by the rules) to the deck. Does not otherwise
        modify the deck or remove existing cards.
        """
        colors = [Color.RED, Color.YELLOW, Color.BLUE, Color.GREEN]

        self.cards = []

        for color in colors:
            for i in range(0, 10):
                self.cards.append(Number(color, i))
                if i != 0:
                    self.cards.append(Number(color, i))

            for i in range(0, 2):
                self.cards.append(Skip(color))
                self.cards.append(DrawTwo(color))
                self.cards.append(Reverse(color))

        for i in range(0, 4):
            self.cards.append(Wild())
            self.cards.append(DrawFourWild())

        shuffle(self.cards)

    def can_play_on_top(self, playing):
        """
        Determines whether a card can be played on the top card of the deck.
        """
        return can_play_card(self.cards[0], playing)


@dataclass
class Number:
    """
    A number card, which has a particular color and number.
    """
    color: Color
    number: int


@dataclass
class Wild:
    """
    A wild card, which may or may not have a color depending on whether it has been played.
    """
    color: Color | None = None


@dataclass
class DrawFourWild:
    """
    A plus four wild card, which may or may not have a color depending on whether it has been
    played.
    """
    color: Color | None = None


@dataclass
class Skip:
    """
    A skip card, which has a color. Is considered one of the "Special" cards.
    """
    color: Color


@dataclass
class DrawTwo:
    """
    A +2 card, which has a color. Is considered one of the "Special" cards.
    """
    color: Color


@dataclass
class Reverse:
    """
    A reverse card, which has a color. It is considered one of the "Special" cards.
    """
    color: Color


Card = Number | Wild | DrawFourWild | Reverse | Skip | DrawTwo


def can_play_card(top: Card, playing: Card) -> bool:
    """
    Determines whether or not a card can be played on top of another card according to the UNO
    rules. Wilds can be played on any card, special cards can be placed on other cards with the
    same color or type, and number cards can be placed on other cards with the same color or number.
    """
    if playing == top or (type(top) is type(playing) and type(playing) is not Number):
        return True

    match playing:
        case Wild(_) | DrawFourWild(_):
            return True
        case Skip(c) | Reverse(c) | DrawTwo(c):
            return c == top.color
        case Number(c, n):
            return c == top.color or n == top.number

    return False
