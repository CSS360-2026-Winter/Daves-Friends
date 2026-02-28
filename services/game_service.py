"""
Provides services for interacting with various games.
"""
from typing import Any
from models.deck import Color
from services.lobby_service import LobbyService


class GameService:
    """
    The game service which provides a higher level interface for interacting with games within
    lobbies.
    """

    def __init__(self, lobby_service: LobbyService):
        self.lobby_service = lobby_service

    def play_card(
        self, channel_id: int, user_id: int, card_index: int, color: Color | None
    ):
        """
        Instructs a lobby's game to play a card.
        """

        lobby = self.lobby_service.get_lobby(channel_id)
        lobby.game.play(user_id, card_index, color)

        if lobby.game.is_bot(lobby.game.current_player()):
            lobby.game.play.play_bot()

    def draw(self, channel_id: int, user_id: int):
        """
        Instructs the game to draw and pass for a channel
        """

        lobby = self.lobby_service.get_lobby(channel_id)
        lobby.game.draw_and_pass(user_id)

    def call_uno(self, channel_id: int, caller_id: int) -> dict[str, Any]:
        """
        Instructs the game to process a Call UNO button press.
        """
        lobby = self.lobby_service.get_lobby(channel_id)
        return lobby.game.call_uno(caller_id)
