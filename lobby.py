# lobby.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set, List

import discord
from discord import app_commands
from discord.ext import commands


def mention(user_id: int) -> str:
    return f"<@{user_id}>"


def require_channel_id(interaction: discord.Interaction) -> int:
    # Pylance: channel_id can be None (DM / edge cases). We only support server channels.
    cid = interaction.channel_id
    if cid is None:
        raise RuntimeError("This command must be used in a server channel (not DMs).")
    return cid


@dataclass
class Lobby:
    host_id: int
    players: Set[int] = field(default_factory=set)
    started: bool = False


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

        lobby = Lobby(host_id=uid, players={uid}, started=False)
        lobbies[cid] = lobby

        await interaction.response.send_message(
            f"Lobby created.\nHost: {mention(lobby.host_id)}\nPlayers: {len(lobby.players)}"
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

        if lobby.started:
            await interaction.response.send_message(
                "Game already started. You can't join right now.",
                ephemeral=True,
            )
            return

        if uid in lobby.players:
            await interaction.response.send_message(
                "You're already in this lobby.",
                ephemeral=True,
            )
            return

        lobby.players.add(uid)
        await interaction.response.send_message(
            f"{mention(uid)} joined the lobby. Players: {len(lobby.players)}"
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

        if uid not in lobby.players:
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

        lobby.players.remove(uid)
        await interaction.response.send_message(
            f"{mention(uid)} left the lobby. Players: {len(lobby.players)}"
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

        players_sorted: List[int] = sorted(lobby.players)
        players_str = ", ".join(mention(pid) for pid in players_sorted) or "(none)"

        await interaction.response.send_message(
            "Lobby status:\n"
            f"Host: {mention(lobby.host_id)}\n"
            f"Players ({len(lobby.players)}): {players_str}\n"
            f"Started: {lobby.started}"
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

        if uid != lobby.host_id:
            await interaction.response.send_message(
                "Only the host can start the lobby.",
                ephemeral=True,
            )
            return

        if lobby.started:
            await interaction.response.send_message(
                "Lobby already started.",
                ephemeral=True,
            )
            return

        if len(lobby.players) < 2:
            await interaction.response.send_message(
                "Need at least 2 players to start.",
                ephemeral=True,
            )
            return

        lobby.started = True
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
