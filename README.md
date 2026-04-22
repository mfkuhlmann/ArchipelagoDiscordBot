# ArchipelagoDiscordBot

A Discord bot that listens to an Archipelago multiworld room and posts a
one-line message to a Discord channel for each cross-player item unlock,
pinging the receiver when they have linked their Discord account to a slot.

## What It Does

- Connects to an Archipelago room as a tracker client over WebSocket
- Filters `PrintJSON` `ItemSend` events down to cross-player sends
- Posts a plain-text unlock message to a Discord channel
- Lets players link their Archipelago slot to their Discord user
- Lets moderators track rooms and mute noisy receiver slots per channel

## Requirements

- Python 3.13+
- `uv`
- A Discord bot token
- An Archipelago room and a valid slot name from that room

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Set these values:

- `DISCORD_TOKEN` is required
- `BOT_SECRET_KEY` is only required if you want to track password-protected rooms
- `DB_PATH` defaults to `./data/bot.db`
- `TRACK_ROLE_NAME` defaults to `AP-Mod`
- `LOG_LEVEL` defaults to `INFO`

Generate a Fernet key for `BOT_SECRET_KEY` with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Install

```bash
uv sync --all-groups
```

### Linux notes

On Linux, make sure you have Python 3.13+, `uv`, and the usual build tools
available. On Debian/Ubuntu-like systems, that typically means:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

If `uv` is not installed yet, install it with one of the methods from the
official docs, for example:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your shell and install project dependencies:

```bash
uv sync --all-groups
```

## Run

From the repo root:

```bash
uv run python main.py
```

On Windows PowerShell, using the checked-in virtualenv directly also works:

```powershell
.\.venv\Scripts\python.exe .\main.py
```

On Linux, you can also run the environment Python directly:

```bash
./.venv/bin/python ./main.py
```

If you want the bot to keep running after you disconnect from the shell, use a
process manager such as `systemd`, `tmux`, or `screen`. A simple `tmux`
workflow looks like:

```bash
tmux new -s archibot
uv run python main.py
```

Detach with `Ctrl+B`, then `D`, and reattach later with:

```bash
tmux attach -t archibot
```

If configuration is missing, the process exits with a clear `Config error`.

## Docker Compose

You can also run the bot with Docker Compose.

### Build and start

1. Create your `.env` file from `.env.example`
2. Fill in at least `DISCORD_TOKEN`
3. Start the container:

```bash
docker compose up -d --build
```

This setup:

- builds the image from the local `Dockerfile`
- injects environment variables from `.env`
- persists the SQLite database in `./data`
- restarts the bot automatically unless you stop it

### View logs

```bash
docker compose logs -f
```

### Stop it

```bash
docker compose down
```

### Notes

- The database path should stay at the default `./data/bot.db` when using the provided Compose setup
- Password-protected Archipelago rooms still require `BOT_SECRET_KEY` in `.env`
- If you change Python dependencies, rebuild with `docker compose up -d --build`

## First Use In Discord

1. Invite the bot to your server.
2. Make sure the bot can view and send messages in the target channel.
3. Create the moderator role named by `TRACK_ROLE_NAME`, or use a user with `Manage Channels`.
4. In the target channel, run:

```text
/track host:localhost port:38281 slot:Meow
```

5. Players can then link themselves with:

```text
/link slot:Meow
```

Once live events arrive, the bot posts messages like:

```text
🟣 <@123456789> got **Master Sword** from Meow's A Link to the Past (Eastern Palace - Big Chest)
```

## Slash Commands

| Command | Who | Effect |
|---|---|---|
| `/track host port slot [password]` | Moderator | Start tracking a room in this channel |
| `/untrack` | Moderator | Stop tracking in this channel |
| `/status` | Anyone | Show session state |
| `/link slot` | Anyone | Link your slot to your Discord account |
| `/unlink [slot]` | Anyone | Remove one slot link or all your links |
| `/links` | Anyone | List all slot-to-user mappings in this guild |
| `/players` | Anyone | Show players for the current tracked session with link/mute state |
| `/mute slot` | Moderator | Suppress unlock messages for that receiver slot in this channel |
| `/unmute slot` | Moderator | Remove a mute for that receiver slot |
| `/testunlock` | Moderator | Post a fake unlock message to verify formatting and permissions |

Moderator commands use the configured role name first and also allow users
with Discord's `Manage Channels` permission.

## Local Smoke Test

Prerequisite: a local Archipelago server. From `X:\repos\Archipelago\`:

```bash
python Generate.py
python MultiServer.py output/*.archipelago
```

Then in Discord:

```text
/track host:localhost port:38281 slot:<slot-name-from-the-seed>
```

Trigger a check in one of the connected game clients and confirm that an
unlock message appears in the Discord channel.

## Development

Run the test suite:

```bash
uv run pytest -q
```

The current implementation is covered by automated tests for:

- config loading
- persistence and encryption
- protocol parsing
- WebSocket client behavior
- session management and batching
- Discord command cogs

## Architecture

See [2026-04-22-archipelago-discord-bot-design.md](</x:/repos/ArchipelagoDiscordBot/docs/superpowers/specs/2026-04-22-archipelago-discord-bot-design.md>)
for the full design. Short version:

- `archibot.archipelago.client.ArchipelagoClient` handles WebSocket frames and emits `UnlockEvent`
- `archibot.session.tracker_session.TrackerSession` wraps connect/reconnect lifecycle
- `archibot.session.manager.SessionManager` owns live sessions and channel output
- `archibot.discord_layer.bot.ArchibotBot` wires the Discord bot, DB, and cogs together
- `archibot.persistence.*` stores links, tracked sessions, and muted slots in SQLite

## Limitations

- Events that happen while the bot is offline are lost
- One tracked Archipelago session per Discord channel
- Unlocks are plain text for the MVP, not rich embeds
- Goal, release, collect, hint, chat, join, and part events are not posted yet
