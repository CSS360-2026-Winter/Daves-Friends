from __future__ import annotations
import discord.ui
from models.game_state import GameError
from services.lobby_service import LobbyService
from utils.utils import require_channel_id, mention
from views.lobby_views import LobbyViews
from .interactions import Interactions
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from views.renderer import Renderer

class LobbyUI(Interactions):
    def __init__(self, renderer: Renderer, lobby_service: LobbyService, lobby_views: LobbyViews):
        super().__init__()
        self._renderer = renderer
        self.lobby_service = lobby_service
        self.lobby_views = lobby_views

    @discord.ui.button(label="🌟 Join", style=discord.ButtonStyle.blurple)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        cid = require_channel_id(interaction)

        try:
            self.lobby_service.join_lobby(cid, interaction.user)
        except GameError as e:
            embed = self.lobby_views.error_embed("Game Join" if e.title == "" else e.title, str(e))
            await interaction.response.send_message(
                embeds=[embed],
                ephemeral=e.private,
            )
            return

        lobby = self.lobby_service.get_lobby(cid)
        await self._renderer.update_from_interaction(interaction, lobby)

    @discord.ui.button(label="🚫 Leave", style=discord.ButtonStyle.gray)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        cid = require_channel_id(interaction)

        try:
            self.lobby_service.leave_lobby(cid, interaction.user)
        except GameError as e:
            embed = self.lobby_views.error_embed("Leave" if e.title == "" else e.title, str(e), True)
            await interaction.response.send_message(
                embeds=[embed],
                ephemeral=e.private,
            )
            return

        lobby = self.lobby_service.get_lobby(cid)
        await self._renderer.update_from_interaction(interaction, lobby)

    @discord.ui.button(label="🚀 Start Game", style=discord.ButtonStyle.success)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message("this command is a work in progress")

    @discord.ui.button(label="🚨 Disband Game", style=discord.ButtonStyle.danger)
    async def disband(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        cid = require_channel_id(interaction)

        try:
            self.lobby_service.disband_lobby(cid, interaction.user)
        except GameError as e:
            embed = self.lobby_views.error_embed("Must Be Host" if e.title == "" else e.title, str(e))
            await interaction.response.send_message(embeds=[embed], ephemeral=e.private)
            return

        embed = self.lobby_views.update_embed("Game Disbanded",
                                              "The host disbanded the game, so the lobby was deleted!")
        await interaction.response.send_message(embeds=[embed])
