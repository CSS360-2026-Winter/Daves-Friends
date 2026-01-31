
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import discord
from discord import app_commands
from discord.ext import commands

from models.game_state import GameState, GameError, Phase


def mention(user_id: int) -> str:
    return f"<@{user_id}>"


def require_channel_id(interaction: discord.Interaction) -> int:
    cid = interaction.channel_id
    if cid is None:
        raise RuntimeError("This command must be used in a server channel (not DMs).")
    return cid


@dataclass
class Lobby:
    host_id: int
    game: GameState


# One lobby per channel
lobbies: Dict[int, Lobby] = {}


class LobbyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="create", description="Create a lobby in this channel.")
    async def create(self, interaction: discord.Interaction) -> None:
        cid = require_channel_id(interaction)
        uid = interaction.user.id

        if cid in lobbies:
            await interaction.response.send_message(
                "A lobby already exists in this channel. Use /status.",
                ephemeral=True,
            )
            return

        g = GameState()
        g.add_player(uid)
        lobbies[cid] = Lobby(host_id=uid, game=g)

        lobby = lobbies[cid]
        await interaction.response.send_message(
            f"Lobby created.\nHost: {mention(lobby.host_id)}\nPlayers: {len(lobby.game.players())}"
        )

    @app_commands.command(name="join", description="Join the lobby in this channel.")
    async def join(self, interaction: discord.Interaction) -> None:
        cid = require_channel_id(interaction)
        uid = interaction.user.id

        lobby = lobbies.get(cid)
        if lobby is None:
            await interaction.response.send_message(
                "No lobby in this channel. Use /create first.",
                ephemeral=True,
            )
            return

        if lobby.game.phase() != Phase.LOBBY:
            await interaction.response.send_message(
                "Game already started. You can't join right now.",
                ephemeral=True,
            )
            return

        if uid in lobby.game.players():
            await interaction.response.send_message(
                "You're already in this lobby.",
                ephemeral=True,
            )
            return

        try:
            lobby.game.add_player(uid)
        except GameError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        await interaction.response.send_message(
            f"{mention(uid)} joined the lobby. Players: {len(lobby.game.players())}"
        )

    @app_commands.command(name="leave", description="Leave the lobby in this channel.")
    async def leave(self, interaction: discord.Interaction) -> None:
        cid = require_channel_id(interaction)
        uid = interaction.user.id

        lobby = lobbies.get(cid)
        if lobby is None:
            await interaction.response.send_message(
                "No lobby in this channel.",
                ephemeral=True,
            )
            return

        if uid not in lobby.game.players():
            await interaction.response.send_message(
                "You're not in this lobby.",
                ephemeral=True,
            )
            return

        # If host leaves: end lobby (simple + avoids host-transfer edge cases)
        if uid == lobby.host_id:
            del lobbies[cid]
            await interaction.response.send_message("Host left, so the lobby was ended.")
            return

        try:
            lobby.game.remove_player(uid)
        except GameError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        await interaction.response.send_message(
            f"{mention(uid)} left the lobby. Players: {len(lobby.game.players())}"
        )

    @app_commands.command(name="status", description="Show lobby status for this channel.")
    async def status(self, interaction: discord.Interaction) -> None:
        cid = require_channel_id(interaction)
        lobby = lobbies.get(cid)

        if lobby is None:
            await interaction.response.send_message(
                "No lobby in this channel. Use /create.",
                ephemeral=True,
            )
            return

        players_sorted: List[int] = sorted(lobby.game.players())
        players_str = ", ".join(mention(pid) for pid in players_sorted) or "(none)"

        started = lobby.game.phase() != Phase.LOBBY

        await interaction.response.send_message(
            "Lobby status:\n"
            f"Host: {mention(lobby.host_id)}\n"
            f"Players ({len(players_sorted)}): {players_str}\n"
            f"Started: {started}"
        )

    @app_commands.command(name="start", description="Start the lobby game (host only).")
    async def start(self, interaction: discord.Interaction) -> None:
        cid = require_channel_id(interaction)
        uid = interaction.user.id

        lobby = lobbies.get(cid)
        if lobby is None:
            await interaction.response.send_message(
                "No lobby in this channel. Use /create.",
                ephemeral=True,
            )
            return
        elif uid != lobby.host_id:
            await interaction.response.send_message(
                "Only the host can start the lobby.",
                ephemeral=True,
            )
            return
        elif lobby.game.phase() != Phase.LOBBY:
            await interaction.response.send_message(
                "Lobby already started.",
                ephemeral=True,
            )
            return
        elif len(lobby.game.players()) < 2:
            await interaction.response.send_message(
                "Need at least 2 players to start.",
                ephemeral=True,
            )
            return
        else:
            try:
                lobby.game.start_game()
            except NotImplementedError:
                await interaction.response.send_message(
                    "Start logic isn't finished yet (dealing + first start card are teammate-owned).",
                    ephemeral=True,
                )
                return
            except GameError as e:
                await interaction.response.send_message(str(e), ephemeral=True)
                return

            await interaction.response.send_message("Lobby started.")

    @app_commands.command(name="end", description="End the lobby (host only).")
    async def end(self, interaction: discord.Interaction) -> None:
        cid = require_channel_id(interaction)
        uid = interaction.user.id

        lobby = lobbies.get(cid)
        if lobby is None:
            await interaction.response.send_message(
                "No lobby in this channel.",
                ephemeral=True,
            )
            return

        if uid != lobby.host_id:
            await interaction.response.send_message(
                "Only the host can end the lobby.",
                ephemeral=True,
            )
            return

        del lobbies[cid]
        await interaction.response.send_message("Lobby ended.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LobbyCog(bot))
