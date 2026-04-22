# Archipelago Discord Bot — Design Spec

**Status:** Approved (2026-04-22). Ready for implementation planning.
**Owner:** mfkuhlmann
**Target runtime:** Python 3.13+, managed via `uv`.

## 1. Problem & Goal

Players in an Archipelago multiworld want a Discord channel that acts as a
live, per-room feed of "unlocks" — moments when one player's check finds
an item belonging to another player. The receiver should be pinged (if they
have opted in) so they know an item is on the way, and the channel doubles
as a shared history of cross-player contributions during the seed.

**In scope:**

- Listen to a running Archipelago room over its WebSocket protocol.
- Detect cross-player item sends (`PrintJSON` with `type=ItemSend`,
  `receiver != sender`).
- Post one Discord message per event, pinging the receiver when a mapping
  exists, otherwise posting with the slot name as plain text.
- Slash commands to start/stop tracking, link Discord users to slots, and
  inspect state.

**Out of scope (explicit non-goals):**

- Gap-filling events missed during bot downtime. Disconnect ≡ miss.
- Posting goal completion, release, collect, hint, chat, or join/part
  events. (Can be added later.)
- Rich embeds for unlock messages (plain one-liners for MVP; embeds are
  kept as a future option for visual polish).
- Sending checks or registering goals. The bot is strictly read-only on
  the Archipelago side — the `Tracker` tag enforces this server-side.

## 2. Protocol Facts That Drive the Design

(Verified against `X:\repos\Archipelago\docs\network protocol.md` and
`X:\repos\Archipelago\MultiServer.py` on 2026-04-22.)

- Archipelago uses a JSON-over-WebSocket protocol. Connection order:
  `RoomInfo` → `Connect` → `Connected`, with optional `GetDataPackage`
  in between.
- `PrintJSON` with `type="ItemSend"` carries the receiver slot (`receiving`)
  and a `NetworkItem(item, location, player=sender, flags)`. These are
  the unlock events we listen for.
- The `Tracker` tag (a) permits the `game` field to be empty/null in the
  `Connect` packet, (b) causes the server to reject any `LocationChecks`
  or goal `StatusUpdate` from this client (`MultiServer.py:2011, 2136`),
  making it safe as a passive listener.
- **A valid slot name is still required.** The server checks
  `args['name'] in ctx.connect_names` at `MultiServer.py:1880` and returns
  `ConnectionRefused: InvalidSlot` otherwise. There is no admin-password
  bypass at the handshake. The admin password (`server_password`) is only
  honored by the in-chat `!admin login` command, which happens after
  authentication.
- Multiple clients may authenticate to the same slot simultaneously. This
  is how existing trackers (PopTracker, BizHawk) ride along with a
  player's game client. The bot connects as an agreed-upon existing slot
  with the `Tracker` tag and does not interfere.
- `ItemSend` `PrintJSON` is broadcast to every connected client regardless
  of which slot they authed as, so the bot sees every cross-player unlock
  in the room.

## 3. Architecture

Single Python process, three internal layers, plus a SQLite store.

```
┌─────────────────────────────────────────────────────────────┐
│  Discord Layer  (discord.py cogs)                           │
│  - /track, /untrack, /link, /unlink, /links, /status,       │
│    /players, /mute, /testunlock                             │
│  - Outbound: posts messages to channels                     │
└─────────────────────────────────────────────────────────────┘
           │                                ▲
           ▼                                │
┌─────────────────────────────────────────────────────────────┐
│  Session Manager                                            │
│  - Owns N concurrent TrackerSessions (one per /track call)  │
│  - Lifecycle: start, stop, reconnect-with-backoff, resume   │
│  - Routes unlock events → Discord Layer with batching and   │
│    rate limiting                                            │
└─────────────────────────────────────────────────────────────┘
           │                                ▲
           ▼                                │
┌─────────────────────────────────────────────────────────────┐
│  ArchipelagoClient  (one instance per session)              │
│  - WebSocket client, Connect as Tracker tag                 │
│  - Parses RoomInfo → Connect → Connected → DataPackage      │
│  - Emits typed events: UnlockEvent                          │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│  Persistence  (SQLite via aiosqlite)                        │
│  - slot_links, sessions tables                              │
└─────────────────────────────────────────────────────────────┘
```

**Dependencies:** `discord.py>=2.7.1` (already installed),
`websockets` (for the Archipelago client), `aiosqlite`, `cryptography`
(for password encryption), `pytest` + `pytest-asyncio` (dev).

**Why these layers:** Each layer has one job and a narrow interface:

- `ArchipelagoClient` knows nothing about Discord. It takes raw JSON
  frames and emits `UnlockEvent` objects. Independently testable.
- `SessionManager` knows nothing about WebSocket framing. It owns
  lifecycle, retry policy, and rate-limiting. Takes `UnlockEvent`s in,
  calls Discord-facing callbacks out.
- Discord cogs know nothing about Archipelago. They translate slash
  commands into session-manager operations and turn `UnlockEvent`s into
  formatted messages.

## 4. Data Flow

**Main event path (cross-player unlock):**

1. Player `Meow` sends `LocationChecks` to the AP server.
2. AP server broadcasts `PrintJSON{type=ItemSend, receiving=<Bork's slot>,
   item=NetworkItem(item_id, location_id, player=<Meow's slot>, flags)}`
   to every connected client.
3. `ArchipelagoClient.on_message` matches `cmd="PrintJSON"`,
   `type="ItemSend"`:
   - Resolves `item_id` → item name via cached `DataPackage[Meow's game]`.
   - Resolves `location_id` → location name via `DataPackage[Meow's game]`.
   - Resolves slot ids → slot names via `slot_info` from `Connected`.
   - Drops the event if `receiver == sender` (own-world item).
   - Drops the event if `sender == 0` (server-granted item, e.g., start
     inventory).
   - Otherwise emits `UnlockEvent(receiver_slot, sender_slot, item_name,
     location_name, game, flags)`.
4. `SessionManager` pushes the event into a per-channel `asyncio.Queue`.
5. A per-channel consumer task drains the queue:
   - Looks up `discord_user_id` for `receiver_slot` in `slot_links` for
     this guild.
   - Formats the one-liner. Emoji comes from the flags bitfield:
     `0b001` → 🟣 progression, `0b010` → 🔵 useful, `0b100` → 🔴 trap,
     otherwise ⚪ filler.
   - Example: `🟣 <@123456> got **Master Sword** from Meow's A Link to
     the Past (Eastern Palace - Big Chest)`.
   - Posts to the channel. Ping resolves because `<@id>` is in message
     content, not inside an embed.
   - **Coalescing rule:** if ≥3 events arrive within a 2s window, the
     consumer holds them, concatenates them into a single multi-line
     message, and posts that. Receiver mentions are hoisted to a single
     header line at the top so all pings still land.
6. `discord.py` handles gateway-level rate limits as a second safety net.

**DataPackage caching:** On first `Connected`, the client requests
DataPackage for all games in the room via `GetDataPackage`. The result is
cached in memory per session. On cache miss during a lookup (shouldn't
happen, but possible with malformed frames), the client falls back to the
raw id (e.g., `item[1234]`) rather than dropping the event.

## 5. Persistence (SQLite schema)

Path: `./data/bot.db` (gitignored). Path overridable via
`DB_PATH` env var.

```sql
CREATE TABLE slot_links (
    guild_id        INTEGER NOT NULL,
    slot_name       TEXT    NOT NULL,
    discord_user_id INTEGER NOT NULL,
    created_at      TEXT    NOT NULL,
    PRIMARY KEY (guild_id, slot_name)
);

CREATE TABLE sessions (
    channel_id      INTEGER PRIMARY KEY,   -- one session per channel
    guild_id        INTEGER NOT NULL,
    host            TEXT    NOT NULL,
    port            INTEGER NOT NULL,
    slot_name       TEXT    NOT NULL,
    password_enc    BLOB,                   -- Fernet-encrypted, nullable
    created_at      TEXT    NOT NULL
);

CREATE TABLE muted_slots (
    channel_id  INTEGER NOT NULL,
    slot_name   TEXT    NOT NULL,
    PRIMARY KEY (channel_id, slot_name)
);
```

**Per-session volatile state** (kept in memory only, re-fetched on
connect): `slot_info`, `player_names`, `data_package`, `last_event_time`,
reconnection counter.

**Password encryption:** Passwords are encrypted with
`cryptography.fernet` using a `BOT_SECRET_KEY` env var (32 raw bytes,
url-safe base64). If `BOT_SECRET_KEY` is not set, `/track` with a
non-empty `password` argument is rejected with a clear error embed.
Passwordless rooms work either way.

**Resume-on-restart:** On `on_ready`, `SessionManager` reads all rows
from `sessions` and spawns a `TrackerSession` per row. Each attempts its
first connect. Connection failures fall into the same capped-retry
pathway as mid-session drops.

## 6. Slash Commands

| Command | Args | Who | Effect |
|---|---|---|---|
| `/track` | `host:str`, `port:int`, `slot:str`, `password:str?` | Moderator role | Create session for the current channel. Error if a session already exists. Post `Connected to <seed_name>, tracking <N> players` embed on success; rich error embed on handshake failure. |
| `/untrack` | _(none)_ | Moderator role | Tear down the session for the current channel. Post `Stopped tracking.` |
| `/status` | _(none)_ | Anyone | Show session state for this channel: connected / reconnecting / disconnected, last event time, linked slot count, mute count. |
| `/link` | `slot:str` | Anyone, self only | Map `slot` → caller's Discord user in this guild. Idempotent. |
| `/unlink` | `slot:str?` | Anyone, self only | Remove caller's link for `slot`. With no arg, remove all their links in this guild. |
| `/links` | _(none)_ | Anyone | List all slot↔user mappings in this guild. Useful to see who hasn't registered. |
| `/players` | _(none)_ | Anyone | List all slots in the current channel's active session, each tagged `[linked]` / `[unlinked]` / `[muted]`. |
| `/mute` | `slot:str` | Moderator role | Suppress messages whose receiver is `slot` in this channel. |
| `/unmute` | `slot:str` | Moderator role | Undo `/mute`. |
| `/testunlock` | _(none)_ | Moderator role | Post a fake unlock message (for format/permission testing without needing live events). |

**Permission model:** `/track`, `/untrack`, `/mute`, `/unmute`,
`/testunlock` require a role whose name is configured via env
`TRACK_ROLE_NAME` (default `AP-Mod`). If the role doesn't exist in the
guild, fall back to Discord's `Manage Channels` permission.

**Self-linking only:** `/link` records the *caller's* Discord user id;
there is no `user:User` argument. This prevents griefing (e.g., linking
an enemy to the slot that receives trap items). An admin override
command may be added later if the need is concrete.

**Slot autocomplete:** `/link`, `/unlink`, `/mute`, `/unmute` offer
autocomplete for `slot` backed by the slot list of the active session
in that channel (empty list if no session).

## 7. Error Handling & Lifecycle

**Per-session connection state machine:**

```
                    ┌───────────────┐
                    │ DISCONNECTED  │◄─────────┐
                    └──────┬────────┘          │
                           │ /track            │ websocket close
                           ▼                   │  or handshake fail
                    ┌───────────────┐          │
         ┌─────────►│  CONNECTING   ├──────────┤
         │          └──────┬────────┘          │
         │                 │ Connected pkt     │
         │ backoff         ▼                   │
         │          ┌───────────────┐          │
         │          │    RUNNING    ├──────────┘
         │          └──────┬────────┘
         │                 │ disconnect
         │                 ▼
         │          ┌───────────────┐   attempts ≥ 10
         └──────────┤ RECONNECTING  ├─────────► DISCONNECTED
                    └───────────────┘             + error embed
```

**Backoff schedule:** 1s, 2s, 4s, 8s, 16s, 32s, 60s, 60s, 60s, 60s
(10 attempts, ~5 minutes total). The attempt counter resets after 60s
of stable `RUNNING`.

**Retry exhaustion error embed** (red sidebar, posted to the channel):

```
🚫 Lost connection to Archipelago
Host: archipelago.gg:38281
Slot: Meow
Last error: ConnectionClosed 1006 (abnormal)
Attempts made: 10 over ~5m
Use /track to retry or /status to inspect.
```

**Non-retryable errors** (skip retries, emit the error embed immediately
and transition to `DISCONNECTED`):

- `ConnectionRefused` with `InvalidSlot`, `InvalidGame`, or
  `InvalidPassword` in its `errors` list — the config is wrong.
- DNS resolution failure.

**Retryable errors:**

- `websockets.ConnectionClosed` (any code except clean 1000 after
  `/untrack`).
- `asyncio.TimeoutError`.
- Transient `OSError`.
- `ConnectionRefused` with no specific known error code.

**Graceful shutdown:** On `SIGTERM` / `SIGINT`, the process cancels all
session tasks, sends close frames, flushes the persistence DB, and exits.
`discord.py`'s `bot.close()` is awaited last.

**Per-session isolation:** An uncaught exception in one `TrackerSession`
is logged, posts a short error embed to its channel, and the session
transitions to `DISCONNECTED`. It does **not** take down the bot or
other sessions. `SessionManager` uses `asyncio.gather(..., return_exceptions=True)`
at the top level to enforce this.

**Logging:** `logging` module to stderr, default `INFO`, configurable via
`LOG_LEVEL` env. Structured per-line format:
`[session=<channel_id>] [state=RUNNING] ItemSend receiver=Bork item=12 location=45`.
Passwords are never logged (neither plaintext nor ciphertext).

## 8. Testing Approach

Three layers, sized by where bugs actually hide.

### 8.1 ArchipelagoClient — pure unit tests

`pytest` + `pytest-asyncio`. The client's public surface is
`feed(raw_json_frame) → list[UnlockEvent]`. Fixtures are recorded JSON
frames taken from the protocol docs plus a small captured session.

Covered cases:

- `RoomInfo` → `Connect` → `Connected` flow emits no events.
- `DataPackage` caching works; missing-package lookup falls back to the
  raw id.
- `ItemSend` where `receiver == sender` is dropped.
- `ItemSend` with `sender == 0` (server) is dropped.
- `ItemSend` with a valid cross-player send produces exactly one
  `UnlockEvent` with the expected fields.
- Goal / Release / Collect / Join / Part `PrintJSON` types are dropped
  (out of scope for MVP).
- Malformed JSON frames are logged and dropped without crashing the
  parser.

### 8.2 SessionManager — integration with a fake AP server

An in-process `websockets.serve` fixture that replays scripted frames.

Covered cases:

- Full connect handshake, receive an `ItemSend`, assert the consumer
  callback was called with the right `UnlockEvent`.
- Retry behavior: the fake server refuses → bot retries using the
  documented backoff schedule → after 10 attempts gives up → error-embed
  callback fires with the correct fields.
- Rate-limit coalescing: inject 10 `UnlockEvent`s in 1s → exactly one
  batched message is posted with all 10 lines and the receiver mentions
  hoisted to a header.
- Resume-on-restart: pre-populate `sessions` table → start the bot
  (with a mocked Discord client) → assert a connection attempt is made
  against the recorded host/port/slot.

### 8.3 Discord layer — mocked

Mock `interaction.response.send_message` and `channel.send`; assert on
call arguments.

Covered cases:

- `/track` in a channel that already has a session → error response,
  no new row in `sessions`.
- `/link` stores the expected row in `slot_links`.
- `/link` permission check: a user cannot link a slot to a different
  Discord user id (there is no `user` argument, but verify the stored
  id matches `interaction.user.id`).
- `/mute` without the moderator role → rejected.

### 8.4 Out of scope for automated tests

- Real WebSocket against a live Archipelago server (flaky, seed-
  dependent, and slow). A manual smoke-test procedure is documented
  below.
- `discord.py` internals.

**Manual smoke test (pre-release):** Spin up a local `MultiServer.py`
with the sample seed in `X:\repos\Archipelago\data\`, run the bot, issue
`/track` against `localhost:38281` with a known slot, trigger a check in
the sample client, confirm the message appears in Discord with the
expected emoji, bold names, and ping behavior.

## 9. Known Limitations

- **Missed events during downtime.** If the bot or its Archipelago
  connection is down, events occurring in that window are lost. Gap-
  filling would require diffing `checked_locations` across reconnects
  plus seed-specific item inference from `slot_data`; out of scope for
  MVP.
- **Single-seed per channel.** One `/track` per channel is enforced.
  Running two seeds in one channel would interleave event streams
  confusingly; out of scope.
- **Slot name required for auth.** The bot can't listen anonymously —
  it must auth as one of the seed's player slots with the `Tracker`
  tag. Confirmed in the server code; no admin-password bypass exists
  at the handshake layer.
- **No rich embeds for unlock messages in MVP.** Plain one-liners only.
  Embed-per-message and embed-batched formats are documented as future
  options.

## 10. Future Enhancements (explicitly deferred)

- Rich-embed formatting mode, selectable via an env var or
  `/track format:embed`.
- Additional event types: goal completion, release, collect, hints,
  player join/part, chat.
- Admin override for `/link` (link another user).
- Gap-filling after reconnect.
- Export of unlock history to CSV or a webhook.

## 11. Configuration Summary

| Env var | Required | Default | Purpose |
|---|---|---|---|
| `DISCORD_TOKEN` | yes | — | Discord bot token |
| `BOT_SECRET_KEY` | conditional | — | Fernet key for password encryption. Required if any tracked room uses a password. |
| `DB_PATH` | no | `./data/bot.db` | SQLite file path |
| `TRACK_ROLE_NAME` | no | `AP-Mod` | Discord role name gating moderator commands |
| `LOG_LEVEL` | no | `INFO` | Python logging level |
