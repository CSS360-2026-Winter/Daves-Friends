# uno.py
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
# message_content not needed for slash commands, but harmless:
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.tree.command(name="ping", description="Replies with pong.")
async def ping(interaction: discord.Interaction, text: str | None = None):
    msg = "pong" if not text else f"pong {text}"
    await interaction.response.send_message(msg)


@bot.event
async def on_ready():
    # Load lobby commands from lobby.py (extension style: async def setup(bot))
    try:
        await bot.load_extension("lobby")
    except commands.ExtensionAlreadyLoaded:
        pass

    # Fast sync: set GUILD_ID in .env to sync instantly in that server
    guild_id = os.getenv("GUILD_ID")
    if guild_id:
        guild = discord.Object(id=int(guild_id))
        await bot.tree.sync(guild=guild)
        print(f"Synced commands to guild {guild_id} as {bot.user}")
    else:
        # Global sync can take a while to propagate
        await bot.tree.sync()
        print(f"Synced commands globally as {bot.user}")


token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN is not set. Check your .env file.")

bot.run(token)
