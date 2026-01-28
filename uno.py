import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

# keeps track of the one public game message
status_message: discord.Message | None = None
# simple counter to show the game is updating
turn: int = 0

def render_status() -> str:
    # text shown in the public game message
    return f"UNO Game Status\nTurn: {turn}"

@bot.command()
async def ping(ctx: commands.Context[commands.Bot], arg: str = ""):
    await ctx.send(f"pong {arg}")

@bot.command()
async def start(ctx: commands.Context[commands.Bot]):
    # creates the first public message
    global status_message, turn
    turn = 1
    status_message = await ctx.send(render_status())

@bot.command()
async def next(ctx: commands.Context[commands.Bot]):
    # edits the same message instead of sending a new one
    global status_message, turn

    if status_message is None:
        await ctx.send("No game started yet. Run /start first.")
        return

    turn += 1
    await status_message.edit(content=render_status())

token = os.getenv("DISCORD_TOKEN")
if token is None:
    raise RuntimeError("DISCORD_TOKEN is not set in .env")

bot.run(token)