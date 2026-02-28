"""
Provides a view into the current game state.
"""

import discord
import time
from utils.utils import mention
from utils.card_image import get_card_filename
from views.base_views import BaseViews
from models.lobby_model import Lobby
from models.deck import (
    NUMBER_EMOJIS,
    COLOR_EMOJIS,
    Number,
    Skip,
    Reverse,
    DrawTwo,
    Wild,
    DrawFourWild,
    Card,
)


def _card_display(card: Card) -> str:
    card = str(card)
    if isinstance(card, Number):
        card = f"{COLOR_EMOJIS[card.color]}{NUMBER_EMOJIS[card.number]}"
    if isinstance(card, Skip):
        card = f"{COLOR_EMOJIS[card.color]}⏭️"
    if isinstance(card, Reverse):
        card = f"{COLOR_EMOJIS[card.color]}🔄"
    if isinstance(card, DrawTwo):
        card = f"{COLOR_EMOJIS[card.color]}➕2"
    if isinstance(card, Wild):
        card = f"🌈{COLOR_EMOJIS[card.color] if card.color else ''}"
    if isinstance(card, DrawFourWild):
        card = f"➕4🌈{COLOR_EMOJIS[card.color] if card.color else ''}"
    return card


class GameViews(BaseViews):
    """
    The game view displaying the current game state.
    """

    def game_embed(self, lobby: Lobby) -> tuple[discord.Embed, discord.File | None]:
        """
        Creates an embed for the game, displaying the game creator, the current players, whose turn
        it is, and the top card.
        """

        embed = self._build_embed(
            title="Game by " + lobby.user.name,
            desc="A game of UNO is in progress!",
            color=self.get_random_color(),
            gif=False,
        )

        players_turn = ""
        current_player_id = lobby.game.current_player()

        for index, player in enumerate(lobby.game.players()):
            if index > 0:
                players_turn += "\n"

            if player == current_player_id:
                players_turn += mention(player) + " ⬅️ Current Turn"
            else:
                players_turn += mention(player)

        embed.add_field(name="Current Turn", value=players_turn, inline=False)
            deadline = getattr(lobby.game, "afk_deadline", None)
            if deadline is not None:
            remaining = int(deadline - time.time())
            if remaining < 0:
                remaining = 0
            embed.add_field(
                name="⏳ AFK Timer",
                value=f"{remaining}s left",
                inline=False,
            )

        card = lobby.game.top_card()
        file = None

        if card:
            filename = get_card_filename(card)
            path = f"assets/cards/{filename}"
            file = discord.File(path, filename=filename)
            embed.set_image(url=f"attachment://{filename}")

            if isinstance(card, (Wild, DrawFourWild)) and card.color:
                embed.add_field(
                    name="Chosen Color",
                    value=f"{COLOR_EMOJIS[card.color]}  **{card.color.name.capitalize()}**",
                    inline=False,
                )

        return embed, file
