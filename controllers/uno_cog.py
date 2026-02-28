"""
Provides the Discord commands and high-level validation of them.
"""

from __future__ import annotations

import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from models.deck import Color
from models.game_state import GameError
from repos.lobby_repo import LobbyRepository
from services.game_service import GameService
from services.lobby_service import LobbyService
from utils.utils import require_channel_id
from views.renderer import Renderer


class UnoCog(commands.Cog):
    """
    The UnoCog which provides Uno commands to the Discord bot and initializes the rest of the game
    state, views, and services.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lobby_repo = LobbyRepository()
        self.lobby_service = LobbyService(self.lobby_repo)
        self.game_service = GameService(self.lobby_service)
        self._renderer = Renderer(self.lobby_service, self.game_service)

    @app_commands.command(name="create", description="Create a lobby in this channel.")
    async def create(self, interaction: discord.Interaction) -> None:
        cid = require_channel_id(interaction)

        try:
            lobby = self.lobby_service.create_lobby(cid, interaction.user)
        except GameError as e:
            embed = self._renderer.lobby_views.error_embed(
                "Lobby Exists" if e.title == "" else e.title, str(e)
            )
            await interaction.response.send_message(embeds=[embed], ephemeral=e.private)
            return

        embeds, view, files = await self._renderer.render(lobby)
        await interaction.response.send_message(embeds=embeds, view=view, files=files)
        msg = await interaction.original_response()
        lobby.main_message = msg.id

    @app_commands.command(
        name="play",
        description="Play a card from your hand on your turn (index starts at 0).",
    )
    @app_commands.describe(
        card_index="Index of the card in your hand (0-based).",
        color="Required for Wild / Draw4 (red/yellow/blue/green).",
    )
    @app_commands.choices(
        color=[
            app_commands.Choice(name="Red", value="red"),
            app_commands.Choice(name="Yellow", value="yellow"),
            app_commands.Choice(name="Blue", value="blue"),
            app_commands.Choice(name="Green", value="green"),
        ]
    )
    async def play(
        self,
        interaction: discord.Interaction,
        card_index: int | None = None,
        color: app_commands.Choice[str] | None = None,
    ) -> None:
        cid = require_channel_id(interaction)
        lobby = self.lobby_service.get_lobby(cid)
        main_msg_id = lobby.main_message

        try:
            if card_index is None and color is None:
                raise GameError(
                    "You must specify either a card index or a color.",
                    title="Game Error",
                    private=True,
                )

            self.game_service.play_card(
                cid,
                interaction.user.id,
                card_index,
                Color[color.value.upper()] if color else None,
            )
        except GameError as e:
            embed = self._renderer.lobby_views.error_embed(
                "Lobby Exists" if e.title == "" else e.title, str(e)
            )
            await interaction.response.send_message(embeds=[embed], ephemeral=e.private)
            return

        await self._renderer.update_by_message_id(self.bot, cid, main_msg_id, lobby)
        await self.dm_current_player_turn(lobby, cid)
        await interaction.response.send_message("Successfully played card!", ephemeral=True)

        bot = interaction.client
        guild_id = interaction.guild.id if interaction.guild else None
        user = await bot.fetch_user(interaction.user.id)
        hand = lobby.game.hand(interaction.user.id)

        link = ""
        if guild_id is not None:
            link = f"\nLink to Game: https://discord.com/channels/{guild_id}/{cid}/{lobby.main_message}"

        embed = self._renderer.hand_views.hand_embed(
            hand,
            optional_message=f"This is your new hand after your latest action.{link}",
        )
        await user.send(embed=embed)

    async def dm_current_player_turn(self, lobby, channel_id: int) -> None:
        game = lobby.game
        if game.phase().name != "PLAYING":
            return

        current = game.current_player()
        if game.is_bot(current):
            return

        if not getattr(lobby, "main_message", None):
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None or channel.guild is None:
            return

        link = f"https://discord.com/channels/{channel.guild.id}/{channel_id}/{lobby.main_message}"

        try:
            user = await self.bot.fetch_user(current)
            await user.send(f"🎮 It's your turn!\nLink to Game: {link}")
        except discord.Forbidden:
            pass

    async def run_afk_timer(self, channel_id: int, player_id: int, start_turn_count: int) -> None:
        import time

        try:
            lobby = self.lobby_service.get_lobby(channel_id)
        except GameError:
            return

        if lobby.game.phase().name != "PLAYING":
            return

        lobby.game.state["afk_deadline"] = time.time() + 60

        for _ in range(60):
            await asyncio.sleep(1)

            lobby = self.lobby_service.get_lobby(channel_id)

            if (
                lobby.game.current_player() != player_id
                or lobby.game.state["turn_count"] != start_turn_count
            ):
                lobby.game.state.pop("afk_deadline", None)
                return

            await self._renderer.update_from_channel(channel_id, lobby)

        try:
            lobby = self.lobby_service.get_lobby(channel_id)
            game = lobby.game

            if (
                game.current_player() == player_id
                and game.state["turn_count"] == start_turn_count
            ):
                game.draw_and_pass(player_id)

                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(
                        f"<@{player_id}> was AFK. They drew a card and were skipped."
                    )

                    await self._renderer.update_by_message_id(
                        self.bot,
                        channel_id,
                        lobby.main_message,
                        lobby,
                    )

                asyncio.create_task(
                    self.run_afk_timer(
                        channel_id,
                        game.current_player(),
                        game.state["turn_count"],
                    )
                )
        except GameError as e:
            print(f"AFK Timer Error: {e}")
        finally:
            lobby.game.state.pop("afk_deadline", None)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UnoCog(bot))