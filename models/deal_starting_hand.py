from game_state import Gamestate

from deck import *

def deal_starting_hand(self, cards_per_player = 7):
    # creates a new deck for every player
    for player in self.players():
        if player not in self.state["hands"]:
            self.state["hands"]["players"] = []

            # grabs 7 cards from the deck and adds it to each players' hand
            for _ in range(cards_per_player):
                if not self.state["deck"]:
                    break
                
                card = self.state["deck"].pop()
                self.state["hands"].append(card)
                