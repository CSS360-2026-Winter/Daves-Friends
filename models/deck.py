from dataclasses import dataclass
from enum import Enum, auto
from random import shuffle

class Color(Enum):
    RED = auto()
    YELLOW = auto()
    BLUE = auto()
    GREEN = auto()


class Deck:
    cards = []

    def __init__(self):
        self.cards = []

    def add_default_cards(self):
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


@dataclass
class Number:
    color: Color
    number: int


@dataclass
class Wild:
    color: Color | None = None


@dataclass
class DrawFourWild:
    color: Color | None = None


@dataclass
class Skip:
    color: Color


@dataclass
class DrawTwo:
    color: Color


@dataclass
class Reverse:
    color: Color


Card = Number | Wild | DrawFourWild | Reverse | Skip | DrawTwo

COLOR_EMOJIS = {
    Color.RED: "🟥",
    Color.YELLOW: "🟨",
    Color.BLUE: "🟦",
    Color.GREEN: "🟩",
}

NUMBER_EMOJIS = {
    0: "0️⃣",
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
}

def can_play_card(top: Card, playing: Card) -> bool:
    if playing == top or (type(top) is type(playing) and type(playing) is not Number):
        return True

    match playing:
        case Wild(_) | DrawFourWild(_):
            return True
        case Skip(c) | Reverse(c) | DrawTwo(c):
            return c == top.color
        case Number(c, n):
            if isinstance(top, Number):
                return c == top.color or n == top.number
            return c == top.color

    return False

def format_card(card: Card | None) -> str:
    if card is None:
        return "(none)"

    match card:
        case Number(color, number):
            return f"{COLOR_EMOJIS[color]} {NUMBER_EMOJIS[number]}"
        case Skip(color):
            return f"{COLOR_EMOJIS[color]} ⏭️ SKIP"
        case Reverse(color):
            return f"{COLOR_EMOJIS[color]} 🔄 REVERSE"
        case DrawTwo(color):
            return f"{COLOR_EMOJIS[color]} ➕2 DRAW 2"
        case DrawFourWild(color):
            return f"🌈 ➕4 DRAW 4"
        case Wild(color):
            return f"🌈 WILD"
        case _:
            return str(card)