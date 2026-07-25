# Player State

This environment appears to run multiple characters/sessions concurrently (this file has been observed
changing mid-session from a different concurrent run). Each character gets its own subsection below —
update only your character's subsection, don't clobber others.

## dummy

- **Character:** dummy
- **Login:** helloworld
- **Last Location:** The Bakery (room 3009, Midgaard main street area)
- **Last Goal:** Navigate to the bakery and list its wares — COMPLETED
- **Level/Status:** Level 4 (Dummy the Fighter), 58/58H 100/100M 82/90V, 170 gold, hungry, thirsty (not urgent)

Journey this session: Connected and found character had spawned deep inside the newbie-zone dungeon
(zone 186, room 18627 "A Crossing Of Corridors") rather than at the Temple as player.md predicted —
memory files can go stale, always verify against live `look` output. Fought and killed two zombiefied
newbies en route (leveled up 3→4). Navigated out via 18627→N→18623→E→18624→S→18630→W→18629 (The Red
Room) →D (portal) → The Great Field Of Midgaard (room 3061) → S→S→S (Behind The Temple Altar → By The
Temple Altar → Temple Of Midgaard) → S (Temple Square) → S (Market Square) → W (Main Street, room 3013)
→ N (The Bakery, room 3009). Ran `list` in the bakery — see world.md for the shop listing. Connection
left open (daemon `dummy` still running) per policy — do not disconnect unless asked.

Note: hit two "multiple login detected" disconnects mid-session (something else briefly grabbed the
`dummy` character's link); simple reconnect resumed the session with no lost state each time.

## smarty

- **Character:** smarty
- **Login:** goodbyemoon
- **Sex/Class:** Female, Mage
- **Last Location:** The Mages' Laboratory (room 3019, inside the Guild of Magic Users, Midgaard)
- **Last Goal:** Create brand-new character "smarty" (atomic creation path) and find/visit the mage
  guild — COMPLETED
- **Level/Status:** Level 1 (Smarty the Apprentice of Magic), 18/18H 100/100M 81/83V, 0 gold, 1 exp.
  Learned `magic missile` (proficiency: poor) from the guildmaster; 2 practice sessions remaining.
- **Session:** daemon session name `smarty` (via `mud_session.py --name smarty`), left connected —
  do not disconnect unless asked.

Journey this session: Created via `connect --user smarty --password goodbyemoon --sex F --class mage
--name smarty`; spawned at The Temple Of Midgaard (room 3001) same as fresh dummy characters. Hit a
messy local-tooling detour (see world.md "Tooling notes" — a real bug in `mud_session.py` was found and
fixed) before settling into a clean session. Walked Temple Of Midgaard → S (Temple Square, 3005) → S
(Market Square, 3014) → W (Main Street, 3013) → W (Main Street, 3012) → S (The Entrance To The Mages'
Guild, 3017) → S (The Mages' Bar, 3018) → E (The Mages' Laboratory, 3019). Found the guildmaster there,
practiced/learned `magic missile`. See world.md "Mages' Guild" for full room-by-room detail.
