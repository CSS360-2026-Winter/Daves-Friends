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

def can_play_card(top: Card, playing: Card) -> bool:

    if playing == top or (type(top) == type(playing) and type(playing) != Number):
        return True

    match playing:
        case Wild(_) | DrawFourWild(_):
            return True
        case Skip(c) | Reverse(c) | DrawTwo(c):
            return c == top.color
        case Number(c, n):
            return c == top.color or n == top.number
            
    return False
    
