---
name: play-mud
description: Play the tbaMUD/CircleMUD text adventure server running on localhost:4000 as the player "dummy" — connect, log in, walk around, fight, talk, shop, and complete whatever goal the user gives inside the game world. Use this any time the user asks you to play, explore, log into, connect to, or do something inside "the mud", "the game", "tbaMUD", "CircleMUD", localhost:4000, or mentions the dummy/helloworld character, even if they just describe an in-game goal (e.g. "find the bakery", "go kill a rat", "see what's south of the temple") without naming the skill directly. Always use the bundled scripts/mud_session.py helper to talk to the MUD rather than opening your own telnet/nc connection — a fresh connection per command loses login state, so a persistent session is required.
---

# Playing tbaMUD

A MUD is a stateful, persistent socket — not a request/response API. The
character's login, position, HP, and combat state all live inside one long-running
TCP connection to the server. Every Bash tool call you make, though, is a brand-new
process. If you `telnet localhost 4000` fresh for each command, each connection
starts back at the login prompt with no memory of the last one, and either fails to
log back in mid-combat or the server (some MUDs) treats it as a whole new guest.

`scripts/mud_session.py` solves this by running a small background daemon that
holds the *one* real connection to the MUD open, logged in, for as long as you need
it. You then talk to that daemon through short-lived CLI calls — each one is a
separate process, but they all share the same underlying game session. Think of it
like a `tmux` session for the MUD: you attach, issue a command, and detach, and the
character stays exactly where you left it.

## Connection details

- Host: `localhost`, Port: `4000` (already running via Docker; nothing to start)
- Credentials: `dummy` / `helloworld`
- These are the script's defaults — you don't need to pass them unless testing
  against a different server or character.

## Workflow

0. **Before connecting, check for `data/player.md` and `data/world.md`** (project
   root, not inside this skill folder) — see "Memory" below. If they exist, they
   tell you where the character was and what's already been mapped.

1. **Connect once per work session:**
   ```
   python3 scripts/mud_session.py connect
   ```
   This starts the daemon (or reuses one already running), logs in, and prints
   whatever the MUD shows right after login — usually a room description if this
   is a fresh login, or the room the character was last in if the server
   reconnected an existing session. Read this output before doing anything else;
   it's your starting orientation.

2. **Send commands, one at a time, reading each response before deciding the
   next one** — exactly like a human player would:
   ```
   python3 scripts/mud_session.py send "look"
   python3 scripts/mud_session.py send "south"
   python3 scripts/mud_session.py send "say hello"
   ```
   Don't queue up a long sequence of moves blind — a room might not have the exit
   you expected, or a monster might attack en route. React to the actual output.

3. **`read` (no command sent) drains anything that arrived on its own** — other
   players talking, combat rounds resolving, a mob wandering in. Use it if you
   sent a command but suspect there's more still coming, or after waiting a
   moment during a fight.

4. **`status`** tells you if the daemon is still alive and connected, without
   touching the game state — a cheap sanity check if something seems stuck.

5. **`disconnect` when you're done or switching tasks.** This sends `quit`
   properly (so the character and its state are saved) before stopping the
   daemon. Don't just leave the daemon running forever, and don't kill it with
   `kill`/`pkill` — an ungraceful exit skips the save and can leave the character
   link-dead in the world.

If you're managing more than one character at once, pass `--name <label>` to any
subcommand to namespace the session (each name gets its own daemon and Unix
socket) — e.g. `--name scout` and `--name fighter` can run independently.

## Memory: data/player.md and data/world.md

The MUD session itself is only as persistent as the daemon — once you
disconnect, everything you learned (where rooms lead, what a shop sells, what
the character was last doing) is gone unless you write it down somewhere that
outlives the process. Two files at `data/player.md` and `data/world.md`, in
the project's working directory (a sibling of `.claude/`, not inside this
skill folder), are that durable memory across separate work sessions.

- **Before connecting**, read both files if they exist. `player.md` tells you
  where the character was last seen and what goal was in progress or just
  completed — use it to orient instead of assuming a fresh start. `world.md`
  tells you what rooms, paths, and shops are already mapped, so you don't
  re-explore ground you've already covered; treat it as a cheat sheet, but
  still verify against what the server actually shows you rather than
  trusting stale notes blindly (rooms can change, prices can change).
- **After finishing a goal, or before disconnecting**, update both files with
  what changed this session:
  - `player.md` — keep it short: name, login, last known location (room name
    and number if known), and the last goal with its outcome. Overwrite the
    old location/goal rather than appending a growing log.
  - `world.md` — append or merge in anything newly discovered: new rooms and
    the exits/paths that reach them, notable NPCs, shop inventories and
    prices (pulled from actual `list`/`score`-equivalent output, never
    guessed). Organize by zone or landmark so it stays a useful map rather
    than a raw transcript.
  - If neither file exists yet, create them — `data/player.md` starting with
    a `# Player State` heading and `data/world.md` with a `# World Notes`
    heading, following the bullet/section shape above.

This is cheap to skip for a single throwaway command, but for anything
involving real exploration or a stated goal, do it — the next session (yours
or a future one) shouldn't have to rediscover the map from scratch.

## Reading output

Output is the MUD's raw text, ANSI color codes included — treat it like a
transcript, not structured data. Room descriptions typically start with a colored
title line, then a paragraph, then an `[ Exits: ... ]` line. The trailing line like
`22H 100M 81V >` is the status prompt (current HP/mana/move); its presence just
means the server is done responding and waiting for your next input.

## Command vocabulary

`send` accepts whatever raw text the MUD itself understands — this is the same
command language a human player would type. See `references/commands.md` for a
categorized cheat sheet (movement, combat, communication, shops, etc.) covering
the commands most likely to come up. When in doubt about something not listed
there, `help <topic>` inside the game is authoritative.

## Timing tips

- `send` waits for the `> ` prompt by default, which is the most reliable signal
  that the server finished responding to that specific command.
- During combat, extra rounds can arrive between your commands. If output looks
  cut off or you're unsure what happened, call `read` to pick up anything that
  landed after the prompt.
- If a `send` call times out (rare — e.g. an unusually slow area), it falls back
  to returning whatever's buffered so far rather than hanging indefinitely; you
  can always follow up with `read` or `send "look"` to re-orient.
