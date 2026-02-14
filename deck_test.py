import unittest

from deck import (
    Color,
    Deck,
    DrawFourWild,
    DrawTwo,
    Number,
    Reverse,
    Skip,
    Wild,
    can_play_card,
)

class TestValidCards(unittest.TestCase):
    """
    Makes sure the deck generation and comparison code behave correctly.
    Uses a new deck for each method.
    """
    def test_generation(self):
        """
        Ensures the generated deck is the correct size.
        """
        deck = Deck()
        deck.add_default_cards()
        self.assertTrue(len(deck.cards) == 108)

    def test_wilds(self):
        """
        Ensures wild cards (normal and plus four) can be played on all cards in the deck.
        """
        deck = Deck()
        deck.add_default_cards()

        for card in deck.cards:
            self.assertTrue(can_play_card(card, Wild()))
            self.assertTrue(can_play_card(card, DrawFourWild()))

    def test_identical_cards(self):
        """
        Ensures idential cards can always be played on top of each other.
        """
        deck = Deck()
        deck.add_default_cards()

        for card in deck.cards:
            self.assertTrue(can_play_card(card, card))

    def test_special(self):
        """
        Ensures all special cards (Skip, Reverse, and DrawTwo) can be played on other cards
        of the same color or kind.
        """
        deck = Deck()
        deck.add_default_cards()

        kinds = [Skip(Color.BLUE), Reverse(Color.BLUE), DrawTwo(Color.BLUE)]

        for kind in kinds:
            for card in deck.cards:
                if card.color == Color.BLUE:
                    self.assertTrue(can_play_card(card, kind))
                elif type(card) is type(kind):
                    self.assertTrue(can_play_card(card, kind))
                else:
                    self.assertFalse(can_play_card(card, kind))

    def test_number_cards(self):
        """
        Ensures some number cards can be played on top of number cards with the same number or
        color. Tests important variants: different numbers and different colors, and ensures they
        can be properly played or not played on top of each other.
        """
        self.assertTrue(can_play_card(Number(Color.BLUE, 10), Number(Color.RED, 10)))
        self.assertTrue(can_play_card(Number(Color.BLUE, 10), Number(Color.BLUE, 5)))
        self.assertFalse(can_play_card(Number(Color.BLUE, 10), Number(Color.RED, 5)))


if __name__ == "__main__":
    unittest.main()
