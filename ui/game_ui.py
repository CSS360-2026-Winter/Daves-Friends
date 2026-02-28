"""
Provides the user interface for a game.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import discord

from ui.interactions import Interactions

from models.game_state import GameError, Phase
from models.lobby_model import Lobby
from services.game_service import GameService

if TYPE_CHECKING:
    from views.renderer import Renderer


class GameUI(Interactions):
    """
    The user interface for a game, connecting the game views to Discord.
    """

    def __init__(self, renderer: Renderer, lobby: Lobby, game_service: GameService):
        super().__init__()
        self._renderer = renderer
        self.lobby: Lobby = lobby
        self.game_service: GameService = game_service

    @discord.ui.button(label="1️⃣ Call Uno", style=discord.ButtonStyle.success)
    async def call_uno(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        """
        Calls Uno, protecting the caller if vulnerable or catching another player who
        failed to call it.
        """
        await interaction.response.defer(ephemeral=True)

        try:
            result = self.game_service.call_uno(interaction.channel_id, interaction.user.id)
        except GameError as e:
            embed = self._renderer.lobby_views.error_embed(
                "Game Error" if e.title == "" else e.title, str(e)
            )
            await interaction.followup.send(embeds=[embed], ephemeral=e.private)
            return

        await self._renderer.update_from_interaction(interaction, self.lobby)

        match result["result"]:
            case "safe":
                target = result["target"]
                await interaction.followup.send(f"🟩 <@{target}> called **UNO!**", ephemeral=False)
            case "too_early":
                await interaction.followup.send("Too early! Grace period is still active.",
                                                ephemeral=True)
            case "penalty":
                target = result["target"]
                caller = result["caller"]
                await interaction.followup.send(
                    f"🚨 <@{target}> got caught by <@{caller}> "
                    "and draws **+2** cards!", ephemeral=False)
            case "no_target":
                await interaction.followup.send("No one is currently at UNO.", ephemeral=True)
            case _:
                await interaction.followup.send("Unhandled UNO result.", ephemeral=True)

    @discord.ui.button(label="👀 View Cards", style=discord.ButtonStyle.blurple)
    async def view_cards(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        """
        Sends the user their cards as an embed only visible to them if the game is active.
        """
        user_id = interaction.user.id
        game = self.lobby.game

        if game.phase() != Phase.PLAYING:
            await interaction.response.send_message(
                "Game is not currently active.", ephemeral=True
            )
            return

        hand = game.hand(user_id)

        if not hand:
            await interaction.response.send_message(
                "You are not in this game.", ephemeral=True
            )
            return

        embed = self._renderer.hand_views.hand_embed(hand)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🃏 Draw Card and Pass", style=discord.ButtonStyle.gray)
    async def draw_card_and_pass(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        """
        Draws a card and passes a player's turn. Pressed if the player cannot play or does not wish
        to play.
        """

        try:
            self.game_service.draw(interaction.channel_id, interaction.user.id)

        except GameError as e:
            embed = self._renderer.lobby_views.error_embed(
                "Not your turn!" if e.title == "" else e.title, str(e)
            )
            await interaction.response.send_message(embeds=[embed], ephemeral=e.private)

            return

        await self._renderer.update_from_interaction(interaction, self.lobby)

        cog = interaction.client.get_cog("UnoCog")
        if cog is not None:
            await cog.dm_current_player_turn(self.lobby, interaction.channel_id)
