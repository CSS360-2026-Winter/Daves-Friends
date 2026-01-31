# UNO Discord Bot
A Python Discord bot that lets users play UNO inside a Discord server.

## Features (Planned)
- Create and join UNO games in a channel
- Start a game when enough players join
- Draw / play cards with validation (match color/number/action)
- Enforce UNO rules:
  - Reverse, Skip, Draw Two
  - Wild, Wild Draw Four
- Turn system + automatic next player
- Game status display:
  - Top card, current turn, player list, hand sizes

### In the Server Channel (Public)
The bot maintains one message in the game channel that shows:
- The current top card
- Whose turn it is
- Player order / number of cards in each hand

This message updates every turn so everyone can follow the game without spam.

### In Player DMs (Private)
Each player receives DM updates that show:
- The top card
- Your hand
- What moves you can make (playable cards)
- Buttons/commands to:
  - Play a card
  - Draw a card
  - End turn (if needed)
  - UNO call (optional feature)

Players make all moves through DMs so nobody sees your hand.

## Tech Stack
- Python 3.10+
- discord.py

## Getting Started (Local Dev)
### 1) Clone your fork
```bash
git clone https://github.com/CSS360-2026-Winter/Daves-Friends.git
cd Daves-Friends
```

### 2) Create a virtual environment
```bash
python -m venv .venv
```

Activate it:

**Mac/Linux**
```bash
source .venv/bin/activate
```

**Windows**
```bash
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

### 4) Create your .env
```bash
DISCORD_TOKEN=your_token_here
```

### 5) Guild ID (Optional)
For faster slash command updates during development, add this to your .env:
```bash
GUILD_ID=your_server_id
```
This syncs commands instantly to that server. If not set, commands sync globally and may take longer to appear.
