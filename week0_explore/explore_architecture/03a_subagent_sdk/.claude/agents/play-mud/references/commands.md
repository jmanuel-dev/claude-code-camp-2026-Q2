# tbaMUD / CircleMUD command reference

Raw text commands to send via `mud_session.py send "<command>"`. tbaMUD accepts
abbreviations for almost everything (`n` for `north`, `l` for `look`, `i` for
`inventory`) — use whichever is clearer to you, both work.

## Movement & posture
- `north` / `south` / `east` / `west` / `up` / `down` (or `n`/`s`/`e`/`w`/`u`/`d`)
- `enter <keyword>` — enter a portal/building named in the room description
- `leave` — leave a vehicle/building back to where you entered from
- `stand` / `sit` / `rest` / `sleep` / `wake` — posture; many actions (casting,
  fighting) require standing first
- `flee` — panic-run out of combat in a random direction

## Perception
- `look` (`l`) — redescribe the current room
- `look at <target>` / `look in <container>` / `look <direction>`
- `examine <target>` — closer inspection than `look at`
- `exits` — list exits without a full room description
- `where` — list players/mobs in the zone and roughly where they are

## Combat
- `consider <target>` — gauge a target's difficulty before engaging; always do
  this before fighting something unfamiliar
- `kill <target>` / `hit <target>` — start a fight (murder implies attacking a
  non-hostile target and has PK implications — avoid unless that's the goal)
- `flee` — attempt to escape an active fight
- `diagnose [target]` — check HP of self or target
- Skill-gated attacks (need the skill first): `backstab`, `bash`, `kick`,
  `rescue`, `assist <target>`

## Self info
- `score` — full character sheet (level, HP, stats, alignment, etc.)
- `inventory` (`i`) / `equipment` (`eq`)
- `gold` — coins on hand
- `time` / `weather`
- `levels` — XP table
- `wimpy <hp>` — auto-flee threshold
- `toggle <flag>` — e.g. `brief`, `autoexit`, `compact` — see PREF_FLAGS below

## World info
- `who` — players online
- `help <topic>` / `credits` / `news` / `motd` / `policies` / `version`
- `commands` / `socials` — full command / social list

## Communication
- `say <text>` — local room speech
- `emote <text>` — third-person roleplay action
- `tell <player> <text>` / `whisper <player> <text>` / `ask <player> <text>`
- `shout <text>` / `gossip <text>` / `auction <text>` / `grats <text>` /
  `holler <text>` — global channels; some MUDs disable these for new players
- `reply` — reply to the last `tell` received

## Items
- `get <item> [container]` — pick up
- `drop <item>` / `junk <item>` / `donate <item>`
- `put <item> <container>`
- `give <item> <target>`
- `wear <item>` / `wield <item>` / `hold <item>` / `remove <item>`
- `eat <item>` / `drink <item>` (containers: `pour <from> <to>`, `fill <to> <from>`)

## Shops & economy
- `list` — see what a shopkeeper NPC sells (must be in a shop room)
- `buy <item>` / `sell <item>` / `value <item>`
- `balance` / `deposit <amount>` / `withdraw <amount>` — bank, if the zone has one

## Character lifecycle
- `save` — force-save character state without quitting
- `quit` — the only clean way to log out; saves and exits properly. Prefer
  `mud_session.py disconnect` over killing the daemon, since it sends this.
- `practice [skill]` — spend practice sessions to improve a skill

## Preference flags (`toggle <flag>`)
`autoexit`, `brief`, `compact`, `noauction`, `nogossip`, `nograts`, `norepeat`,
`noshout`, `nosummon`, `notell`, `quest`

## Notes from this world specifically
- Starting area is Midgaard (zone 30); the Temple of Midgaard (#3001) is the
  default entry room.
- A known landmark: The Bakery (#3009), reached from the Temple via
  `s, s, w, n` (Temple → Temple Square → Market Square → Main Street →
  Bakery). Sells danish pastry, bread, and waybread via `list`/`buy`.
