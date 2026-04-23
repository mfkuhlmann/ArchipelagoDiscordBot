# ArchipelagoDiscordBot

A Discord bot that listens to an Archipelago multiworld room and posts a
one-line message to a Discord channel for each cross-player item unlock,
pinging the receiver when they have linked their Discord account to a slot.

## What It Does

- Connects to an Archipelago room as a tracker client over WebSocket
- Filters `PrintJSON` `ItemSend` events down to cross-player sends
- Posts a color-coded embed for each unlock to a Discord channel
- Lets players link their Archipelago slot to their Discord user
- Lets moderators track rooms and mute noisy receiver slots per channel

## Quick Start

For a local self-hosted run:

1. Copy `.env.example` to `.env`.
2. Fill in `DISCORD_TOKEN`.
3. Install dependencies with `uv sync --all-groups`.
4. Start the bot with `uv run python main.py`.
5. In Discord, run `/track host:<host> port:<port> slot:<slot-name>`.

If you do not want to self-host the bot, use the hosted version with this
invite link:

https://discord.com/oauth2/authorize?client_id=1496598533774639246

## Requirements

- Python 3.13+
- `uv`
- A Discord bot token
- An Archipelago room and a valid slot name from that room

Docker users do not need a host Python install; the provided image uses
Python 3.13.

## Discord Bot Setup

Create a Discord application and bot in the Discord Developer Portal, then copy
the bot token into `DISCORD_TOKEN`.

When inviting the bot, include these scopes:

- `bot`
- `applications.commands`

The bot needs these permissions in every channel where it should operate:

- View Channel
- Send Messages
- Embed Links
- Use Application Commands

The bot only enables the guild intent and does not require privileged Discord
intents.

Slash commands are synced when the bot starts. If commands do not appear
immediately, restart the Discord client or wait a few minutes for Discord to
finish updating application commands.

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Set these values:

| Variable | Required | Default | Purpose |
|---|---:|---|---|
| `DISCORD_TOKEN` | Yes | none | Discord bot token used to log in |
| `BOT_SECRET_KEY` | Only for password-protected rooms | none | Fernet key used to encrypt stored room passwords |
| `DB_PATH` | No | `./data/bot.db` | SQLite database path |
| `TRACK_ROLE_NAME` | No | `AP-Mod` | Discord role allowed to run moderator commands |
| `LOG_LEVEL` | No | `INFO` | Python logging level |
| `ARCHIBOT_IMAGE` | Docker only | `ghcr.io/mfkuh/archipelagodiscordbot:latest` | Image used by Docker Compose |

Generate a Fernet key for `BOT_SECRET_KEY` with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Use Hosted Bot

1. Invite the hosted bot with the invite link above.
2. Make sure the bot can view and send messages in the target channel.
3. Create the moderator role named by `TRACK_ROLE_NAME`, or use a user with
   Discord's `Manage Channels` permission.
4. Run `/track` in the target channel.

## Self-Host With uv

Install the project dependencies:

```bash
uv sync --all-groups
```

Start the bot from the repo root:

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

If configuration is missing, the process exits with a clear `Config error`.

### Linux Notes

On Linux, make sure Python 3.13+ and `uv` are available:

```bash
python3 --version
uv --version
```

Many distributions still install an older Python through `python3`. If your
system Python is older than 3.13, let `uv` install a compatible interpreter:

```bash
uv python install 3.13
uv sync --all-groups
```

If `uv` is not installed yet, one common option is:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your shell after installing `uv` so it is available on your `PATH`.

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

## Self-Host With Docker Compose

You can also run the bot with Docker Compose.

### Local Build and Start

1. Create your `.env` file from `.env.example`.
2. Fill in at least `DISCORD_TOKEN`.
3. Start the container:

```bash
docker compose up -d --build
```

This setup:

- tags the image as `ghcr.io/mfkuh/archipelagodiscordbot:latest` by default
- builds the image from the local `Dockerfile` when you use `--build`
- injects environment variables from `.env`
- persists the SQLite database in `./data`
- restarts the bot automatically unless you stop it

### Pull From GitHub Container Registry

The repository includes a GitHub Actions workflow that builds and pushes the
container image to GHCR whenever a GitHub Release is published.

Default image:

```text
ghcr.io/mfkuh/archipelagodiscordbot:latest
```

Published tags:

- `latest` for every published release
- the Git SHA for every published release build
- the release tag name when you publish a GitHub Release

To deploy from the registry on a server:

```bash
docker login ghcr.io
docker compose pull
docker compose up -d
```

If you want to point Compose at a different tag or fork, set `ARCHIBOT_IMAGE`
in your `.env` before running Compose.

Example:

```bash
ARCHIBOT_IMAGE=ghcr.io/mfkuh/archipelagodiscordbot:latest
```

### Docker Networking

When the bot runs in Docker, `localhost` means the bot container, not your host
machine. If the Archipelago server runs outside the container, use an address
the container can reach:

- Docker Desktop: `host.docker.internal`
- Same LAN: the host machine's LAN IP address
- Another Compose service: that service name on the shared Docker network

For example, if Archipelago is running on the host with Docker Desktop:

```text
/track host:host.docker.internal port:38281 slot:Meow
```

### View Logs

```bash
docker compose logs -f
```

### Stop It

```bash
docker compose down
```

### Docker Notes

- Keep `DB_PATH` at the default `./data/bot.db` when using the provided Compose setup
- Password-protected Archipelago rooms still require `BOT_SECRET_KEY` in `.env`
- If you change Python dependencies, rebuild with `docker compose up -d --build`

## First Use In Discord

1. Invite the bot to your server.
2. Make sure the bot can view and send messages in the target channel.
3. Create the moderator role named by `TRACK_ROLE_NAME`, or use a user with
   Discord's `Manage Channels` permission.
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
content: <@123456789>
embed title: Master Sword
embed body: Alice got an item from Bob's Dark Souls Remastered
location: BT: Wanderer Hood
```

## Slash Commands

| Command | Who | Effect |
|---|---|---|
| `/track host port slot [message_style] [password]` | Moderator | Start tracking a room in this channel |
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

### Easter Egg

`/raspberry` is a small insider command: it counts found
items named `Raspberry` per channel and per finder. It exists for an
inside joke for the game Celeste (#Raspberrygate) with the original developer group and is not part of the bot's core
tracking feature set.

### Message Style

`/track` accepts a `message_style` option:

- `embed` sends color-coded Discord embeds for unlocks
- `plain` sends the older one-line text format

If omitted, the bot defaults to `embed`.

## Local Smoke Test

Prerequisite: a local Archipelago server. Inside the local Archipelago folder:

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

## Troubleshooting

### Slash Commands Do Not Appear

Make sure the bot was invited with the `applications.commands` scope, then
restart the bot and wait a few minutes. The bot logs how many application
commands were synced during startup.

### Bot Cannot Post Unlocks

Check that the bot has View Channel, Send Messages, and Embed Links permission
in the target channel. Run `/testunlock` to verify formatting and channel
permissions without waiting for a real Archipelago event.

### `DISCORD_TOKEN must be set`

Create `.env` from `.env.example` and fill in `DISCORD_TOKEN`. With Docker
Compose, make sure `.env` is next to `docker-compose.yml`.

### Password-Protected Rooms Fail

Set `BOT_SECRET_KEY` to a Fernet key before tracking rooms with a password.
Without this key, the bot cannot safely store encrypted room passwords for
session restore.

### Docker Cannot Reach Archipelago

Do not use `localhost` unless the Archipelago server is running in the same
container. Use `host.docker.internal`, a LAN IP address, a URL, or a Compose service
name as described in Docker Networking.

### Database Errors

Make sure the directory containing `DB_PATH` exists and is writable by the bot.
With Docker Compose, the provided `./data:/app/data` volume persists the SQLite
database on the host.

## Project Layout

- `main.py` loads configuration and starts the Discord bot
- `src/archibot/archipelago/` handles WebSocket connection and protocol parsing
- `src/archibot/discord_layer/` contains the Discord bot, embeds, permissions, and slash command cogs
- `src/archibot/persistence/` stores sessions, links, muted slots, encrypted room passwords, and the Raspberry easter egg counter
- `src/archibot/session/` coordinates tracked Archipelago sessions and message formatting
- `tests/` contains automated coverage for config, persistence, protocol parsing, sessions, and Discord cogs

## Development

Run the test suite:

```bash
uv run pytest -q
```

Run a single test file:

```bash
uv run pytest tests/session/test_manager.py -q
```

The current implementation is covered by automated tests for:

- config loading
- persistence and encryption
- protocol parsing
- WebSocket client behavior
- session management and batching
- Discord command cogs

Docker images are built and pushed by the GitHub Actions workflow in
`.github/workflows/docker-publish.yml` when a GitHub Release is published.

## Limitations

- Events that happen while the bot is offline are lost
- One tracked Archipelago session per Discord channel
- Goal, release, collect, hint, chat, join, and part events are not posted yet
