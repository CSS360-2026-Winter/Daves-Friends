import unittest

from deck import *

class TestValidCards(unittest.TestCase):
	def test_wilds(self):
		deck = Deck()
		deck.add_default_cards()
		
		for card in deck.cards:
			self.assertTrue(can_play_card(card, Wild()))
			self.assertTrue(can_play_card(card, DrawFourWild()))
	
	def test_identical_cards(self):
		deck = Deck()
		deck.add_default_cards()
		
		for card in deck.cards:
			self.assertTrue(can_play_card(card, card))
	
	def test_special(self):
		deck = Deck()
		deck.add_default_cards()
		
		kinds = [Skip(Color.BLUE), Reverse(Color.BLUE), DrawTwo(Color.BLUE)]
		
		for kind in kinds:
			for card in deck.cards:
				if card.color == Color.BLUE:
					self.assertTrue(can_play_card(card, kind))
				elif type(card) == type(kind):
					self.assertTrue(can_play_card(card, kind))
				else:
					self.assertFalse(can_play_card(card, kind))
	
	def test_number_cards(self):
		self.assertTrue(can_play_card(Number(Color.BLUE, 10), Number(Color.RED, 10)))
		self.assertTrue(can_play_card(Number(Color.BLUE, 10), Number(Color.BLUE, 5)))
		self.assertFalse(can_play_card(Number(Color.BLUE, 10), Number(Color.RED, 5)))
	
	def test_draw_valid_start_card(self):
    		deck = Deck()
    		deck.add_default_cards()

    		card = draw_valid_start_card(deck)

    		self.assertFalse(isinstance(card, (Wild, DrawFourWild)))

if __name__ == '__main__':
    unittest.main()

