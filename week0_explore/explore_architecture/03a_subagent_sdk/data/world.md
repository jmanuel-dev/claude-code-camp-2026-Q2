# World Notes

## Midgaard City Areas

### Temple Square
- **Description:** Temple square with huge marble steps leading up to the temple gate
- **Features:** Large fountain carved from blue-streaked marble (bubbling merrily) — water source for drinking
- **Exits:** North (temple gate), South (market square), East (Grunting Boar Inn), West (Clerics' Guild)
- **NPCs:** Peacekeeper

### Market Square
- **Description:** Famous Square of Midgaard with a peculiar looking statue in the middle
- **Exits:** North (temple square), South (common square), East (main street), West (main street)
- **NPCs:** Peacekeeper, oozing green gelatinous blob, cityguard (seen this session)

### Main Street (room 3013, west of Market Square)
- **Description:** Main street passing through the City of Midgaard
- **Exits:** North (The Bakery, room 3009), East (Market Square), South (the Armory), West (another Main Street room, 3012)

### Main Street (room 3012, west of room 3013)
- **Description:** "You are at the end of the main street of Midgaard." Magic shop to the north, city
  gate to the west, Guild of Magic Users entrance to the south.
- **Exits:** North (magic shop, room 3033), East (Main Street 3013), South (Entrance To The Mages'
  Guild, room 3017), West (city gate, room 3040)
- **NPCs seen:** cityguard, beastly fidos (garbage-scavenging)

### Mages' Guild (Guild of Magic Users) — Magic-User/Mage starter guild
- **Route from Temple Square:** S (Market Square) → W (Main Street 3013) → W (Main Street 3012) →
  S (guild entrance) → S (bar) → E (laboratory, guildmaster).
- **The Entrance To The Mages' Guild (room 3017):** "The entrance hall to this guild is a small, poor
  lighted room." Has an ATM. Exits: North (Main Street 3012), South (Mages' Bar, 3018).
  NPC: a "sorcerer" guarding the entrance (zone data calls this mob "Mage Guard").
- **The Mages' Bar (room 3018):** "The bar is one of the weirdest in the land. Mystical images float
  around the air. Illusions of fine furniture appear all around the room." Has a social bulletin board.
  Exits: North (entrance, 3017), East (laboratory, 3019). NPC: a waiter ("Magic Users' Waiter" in zone
  data) — likely sells drinks via buy/list per the standard guild-bar sign pattern seen elsewhere.
- **The Mages' Laboratory (room 3019) — guildmaster room:** "This is the Magical Experiments Laboratory.
  Dark smoke-stained stones arch over numerous huge oaken tables, most of these cluttered with
  strange-looking pipes and flasks. The floor is covered with half-erased pentagrams and even weirder
  symbols, and a blackboard in a dark corner has only been partially cleaned, some painful-looking
  letters faintly visible." A well in the middle leads down into darkness (too dark/dangerous to
  descend — warned as impossible to climb back up; per world files this well drops into a much higher-
  level zone, room 7017 — avoid at low level). Exits: West (bar, 3018) only (well/down not a normal exit).
  - **Guildmaster NPC:** "the mages' guildmaster" (keywords: guildmaster, master, mage) — female,
    described as "old and tired" but with "vast amount of knowledge," wearing fine magic clothing,
    "surrounded by a blue shimmering aura." Room-idle text: "Your guildmaster is studying a spellbook
    while preparing to cast a spell."
  - **Trainable here (`practice` command):** confirmed live — offers the `magic missile` spell (new
    level-1 mage character started with 3 practice sessions, "magic missile (not learned)" listed;
    after `practice magic missile` it became "magic missile (poor)" and practice sessions dropped to 2).
    Likely more spells unlock as the character levels; only `magic missile` was offered at level 1.

### The Bakery (room 3009, north of Main Street)
- **Description:** Small bakery — "A sweet scent of danish and fine bread fills the room." Bread and
  Danish arranged on shelves. A small sign on the counter (readable) with buy/list instructions.
- **Exits:** South (back to Main Street)
- **NPC:** The baker (shopkeeper), calmly wiping flour from his face
- **Shop listing (live `list` output, confirmed this session):**
  ```
   ##   Available   Item                                               Cost
  ----------------------------------------------------------------------------
    1)  Unlimited   A danish pastry                                       7
    2)  Unlimited   A bread                                              14
    3)  Unlimited   A waybread                                           74
  ```
  (Prices are in gold coins; use `buy <item>` to purchase.)
- **Route from Temple Square:** South (Market Square) → West (Main Street) → North (The Bakery).

### Common Square
- **Description:** Common square where people gather
- **Exits:** North (market square), South (the dump), East (dark alley), West (poor alley)
- **NPCs:** Janitor, multiple fidos

### The Dump
- **Description:** Where the city drops garbage; entrance to the sewer system
- **Exits:** North (common square), Down (sewer system)

## Sewer System (Brief Map)
- Multiple interconnected passages
- Watery Sewer Junction (starting area with gold coins)
- The Quadruple Junction Under The Dump (has metal ladder leading up)
- Various dark passages and dead ends
- NPCs: small hairy spider, huge hungry sewer rat

## Tooling notes (mud_session.py)

- **Fixed a real bug this session:** `MudLink.open()` called
  `socket.create_connection((host, port), timeout=10)`, which leaves the resulting socket's timeout
  permanently set to 10s (it's not just a connect-attempt timeout, despite the name). The background
  reader thread's blocking `recv()` then raised `socket.timeout` (a subclass of `OSError`) after any 10s
  stretch of MUD-side silence — indistinguishable to the `except OSError: pass` handler from a real
  close, so the link silently flipped to `closed=True` (visible as `status` reporting `connected=False`
  and subsequent `send`/`disconnect` failing with "mud connection is closed") even though the MUD server
  still considered the character fully connected. Fixed by adding `self.sock.settimeout(None)`
  immediately after `create_connection` succeeds, restoring blocking mode for the reader thread. This
  file lives at `.claude/agents/play-mud/scripts/mud_session.py` in each explore_architecture subdir —
  the fix was only applied to the `03_subagent_sdk` copy. **Verified** (via grep, not assumed): the
  `02_agent_skills/.claude/skills/play-mud/scripts/mud_session.py` copy has the identical unfixed line
  (`socket.create_connection((self.host, self.port), timeout=10)` with no `settimeout(None)` after it) —
  apply the same one-line fix there if this bug bites during a session that uses that copy.
- **Concurrency hazard:** all sessions share `$TMPDIR/mud-skill/<name>.{sock,pid,log}` regardless of which
  copy of the script runs them. Multiple parallel agent invocations (this environment appears to run
  several concurrently — observed stray `dummy`/`smarty-probe`/`explorer`/`warrior` session files and
  daemons from what look like other concurrent runs) can collide on session `--name`. Always pass
  `--name` on **every** subcommand (connect/send/read/status/disconnect), and never run `connect --name X`
  without also passing `--user`/`--password` for an existing character — omitting them defaults to
  `dummy`/`helloworld`, and `daemon_main` unconditionally deletes `X`'s old socket file before attempting
  that (wrong) login, which can orphan a perfectly good running daemon (unreachable but still alive,
  harmless garbage) and burn time debugging a self-inflicted problem instead of a real one.

## Useful Resource: Offline World Files
The repo ships a parsed CircleMUD world dataset at
`/home/john/claude-code-camp-2026-Q2/week0_explore/circlemud-world-parser/assets/` (`.wld`/`.mob`/`.obj`/`.shp`/`.zon`
per zone, raw diku format, zone 30 = Midgaard city, zone 186 = newbie-zone dungeon). Grepping room
description text there (unique per room) is much faster than blind-walking to find a room's vnum, its
exits, or a shop's item/price list — confirmed accurate against live server output this session (room
text matched exactly). Worth checking before wandering next time a room isn't in this file.

## Newbie Zone (Training Area)
- **Entrance:** East from The Great Field of Midgaard (off the path north from temple)
- **The Beginning Of The Passage:** First room with newbie monster
- **The Dirty Hallway:** Contains red-marked (locked) exits to south
- **A Nexus:** Intersection with red-marked exits north and east (locked doors)
- **The Alchemist's Room:** Off main hallway; has a sign warning: "If you are below level 7 and alone, or below level 4 then bugger off!"
  - Contains dark stairway leading down to dungeon
  - NPCs: Newbie Alchemist
- **Dungeon (below alchemist room, zone 186):**
  - The Entrance (room 18632): Quasits
  - A Crossing Of Corridors (room 18627): Zombie newbies (aggressive — attack on room entry)
  - A Corner In The Hallway (room 18623): **Great Minotaur (DEFEATED prior session)** — gray brick walls
    with green fungus, reward 2668 exp when killed; may or may not respawn.
  - The Red Room (room 18629): round glowing portal in the floor — `down` from here teleports to The
    Great Field Of Midgaard (room 3061, zone 30/Midgaard) — **fastest known way out of this dungeon
    back to the city.**
  - **Route from Crossing (18627) to the Red Room portal:** north (→18623, Corner In The Hallway) →
    east (→18624, Another Turn) → south (→18630, A Branching Passage) → west (→18629, Red Room) →
    down (→3061, Great Field Of Midgaard). Confirmed working this session; zombiefied newbies are
    aggressive and will interrupt movement along this route (had to fight through two of them).
  - **Route from Great Field (3061) into Midgaard city center:** south → south (Behind The Temple Altar)
    → south (By The Temple Altar) → south (Temple Of Midgaard, matches "Temple Of Midgaard" room from
    prior notes) → south (Temple Square).
