# Skill Benchmark: play-mud

**Model**: claude-sonnet-5  
**Date**: 2026-07-22T15:31:08Z  
**Evals**: 1, 2, 3 (1 run(s) each per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 100% ± 0% | 100% ± 0% | +0.00 |
| Time (s) | 83.0 ± 18.9 | 225.5 ± 19.7 | -142.5s |
| Tokens | 30875.3 ± 2070.4 | 42170.0 ± 4501.5 | -11295 |

## Per-Eval Breakdown

### Eval 1: orient-and-report

| Config | Run | Pass Rate | Time (s) |
|--------|-----|-----------|----------|
| With Skill | 1 | 100% (4/4) | 63.6 |
| With Skill | **Avg** | **100%** | **63.6** |
| Without Skill | 1 | 100% (4/4) | 245.4 |
| Without Skill | **Avg** | **100%** | **245.4** |

| Assertion | With Skill | Without Skill |
|---|---|---|
| Used a persistent/reusable connection mechanism rather than one ad hoc telnet/nc call per command | ✓ | ✓ |
| Successfully logged in as dummy without a wrong-password or connection error | ✓ | ✓ |
| Reported a room name/description that matches what the live server actually returned (not fabricated) | ✓ | ✓ |
| Response to the user names the specific room and describes visible exits/features | ✓ | ✓ |

<details><summary>Evidence for each assertion</summary>

**With Skill (run 1)**

- ✓ Used a persistent/reusable connection mechanism rather than one ad hoc telnet/nc call per command
  - *Evidence:* Used mud_session.py's connect/send/status/disconnect subcommands, each a separate Bash invocation, all sharing one backgrounded daemon connection.
- ✓ Successfully logged in as dummy without a wrong-password or connection error
  - *Evidence:* connect output shows full fresh login flow (banner, menu, 'Welcome to tbaMUD! May your visit here be... Enlightening') with no error.
- ✓ Reported a room name/description that matches what the live server actually returned (not fabricated)
  - *Evidence:* Transcript shows raw 'Main Street' description; final_answer.md matches it exactly (room, exits n/e/s/w, HP/mana/move).
- ✓ Response to the user names the specific room and describes visible exits/features
  - *Evidence:* final_answer.md names Main Street and lists all four exits with their destinations (Armory south, Bakery north, Market Square east).

**Without Skill (run 1)**

- ✓ Used a persistent/reusable connection mechanism rather than one ad hoc telnet/nc call per command
  - *Evidence:* Wrote a one-off Python socket script that held a single connection open for the whole login+look+quit sequence within one Bash invocation -- avoided the naive per-command reconnect failure, but required bespoke engineering (IAC stripping, login-dance regex) built from scratch rather than a reusable tool.
- ✓ Successfully logged in as dummy without a wrong-password or connection error
  - *Evidence:* Transcript shows clean 'dummy'/'helloworld' login reaching the menu and entering the game with no errors.
- ✓ Reported a room name/description that matches what the live server actually returned (not fabricated)
  - *Evidence:* Raw RECV block shows 'Main Street' description verbatim; final_answer.md matches.
- ✓ Response to the user names the specific room and describes visible exits/features
  - *Evidence:* final_answer.md names Main Street with bakery/Armory/market square exits, matching transcript.

</details>

### Eval 2: explore-and-return

| Config | Run | Pass Rate | Time (s) |
|--------|-----|-----------|----------|
| With Skill | 1 | 100% (4/4) | 101.4 |
| With Skill | **Avg** | **100%** | **101.4** |
| Without Skill | 1 | 100% (4/4) | 206.0 |
| Without Skill | **Avg** | **100%** | **206.0** |

| Assertion | With Skill | Without Skill |
|---|---|---|
| Maintained a single session across all moves (no evidence of re-login or a fresh connection per move) | ✓ | ✓ |
| Moved through at least two different rooms and accurately reported what was in each | ✓ | ✓ |
| Confirmed return to the original starting room (e.g. via a final look), not just claimed it | ✓ | ✓ |
| Reacted to actual room output when choosing directions rather than sending a blind pre-planned sequence | ✓ | ✓ |

<details><summary>Evidence for each assertion</summary>

**With Skill (run 1)**

- ✓ Maintained a single session across all moves (no evidence of re-login or a fresh connection per move)
  - *Evidence:* Every move (look, north, look at sign, south, east, look at statue, west) was a separate `send` call against the same already-connected daemon session; only one login occurred, at the initial `connect`.
- ✓ Moved through at least two different rooms and accurately reported what was in each
  - *Evidence:* Visited The Bakery (north) and Market Square (east), both reported accurately in final_answer.md matching the raw room text (bakery smell/shelves/sign; market square statue of the Midgaard Worm, 4 exits).
- ✓ Confirmed return to the original starting room (e.g. via a final look), not just claimed it
  - *Evidence:* Final `send "west"` response shows the Main Street room description again, textually identical to the starting room, before disconnecting.
- ✓ Reacted to actual room output when choosing directions rather than sending a blind pre-planned sequence
  - *Evidence:* Used `look at sign` and `look at statue` after reading each room's description, referencing details unique to that room's actual text -- suggests reading before acting rather than a canned script.

**Without Skill (run 1)**

- ✓ Maintained a single session across all moves (no evidence of re-login or a fresh connection per move)
  - *Evidence:* One continuous raw-socket script handled login through final quit/exit in a single held connection; no re-login observed mid-sequence.
- ✓ Moved through at least two different rooms and accurately reported what was in each
  - *Evidence:* Visited The Bakery and Market Square, matching raw transcript text; also noted an NPC event (cityguard arriving/leaving) not present in the with-skill run, showing it captured async chatter too.
- ✓ Confirmed return to the original starting room (e.g. via a final look), not just claimed it
  - *Evidence:* Sent an explicit extra `look` after each move (including the final `west`), confirming Main Street's description before quitting -- more explicit re-confirmation than the with-skill run.
- ✓ Reacted to actual room output when choosing directions rather than sending a blind pre-planned sequence
  - *Evidence:* Sent a `look` after every move before proceeding, consistent with reading output before deciding, though the actual direction choices (north/south/east/west back) look like they could have been pre-planned rather than adaptively chosen given no unexpected obstacles arose.

</details>

### Eval 3: status-and-shop

| Config | Run | Pass Rate | Time (s) |
|--------|-----|-----------|----------|
| With Skill | 1 | 100% (4/4) | 84.1 |
| With Skill | **Avg** | **100%** | **84.1** |
| Without Skill | 1 | 100% (4/4) | 225.2 |
| Without Skill | **Avg** | **100%** | **225.2** |

| Assertion | With Skill | Without Skill |
|---|---|---|
| Used an in-game info command (score/inventory/gold or equivalent) rather than guessing character stats | ✓ | ✓ |
| Maintained one persistent connection while both checking status and exploring for a shop | ✓ | ✓ |
| If a shop was found, the reported items/prices match the server's actual `list` output | ✓ | ✓ |
| Clearly reports what was checked/found even if no shop was located within a reasonable search | ✓ | ✓ |

<details><summary>Evidence for each assertion</summary>

**With Skill (run 1)**

- ✓ Used an in-game info command (score/inventory/gold or equivalent) rather than guessing character stats
  - *Evidence:* Ran `score` and captured its exact raw output (22/22 HP, 100/100 mana, 20 gold, level 1 Swordpupil, etc.).
- ✓ Maintained one persistent connection while both checking status and exploring for a shop
  - *Evidence:* connect -> score -> look -> north -> list -> disconnect all issued as separate Bash calls against the same daemon session, no re-login between them.
- ✓ If a shop was found, the reported items/prices match the server's actual `list` output
  - *Evidence:* Raw `list` output (danish pastry 7g, bread 14g, waybread 74g) matches final_answer.md exactly.
- ✓ Clearly reports what was checked/found even if no shop was located within a reasonable search
  - *Evidence:* final_answer.md reports both the score results and the bakery's shop listing clearly and completely.

**Without Skill (run 1)**

- ✓ Used an in-game info command (score/inventory/gold or equivalent) rather than guessing character stats
  - *Evidence:* Ran `score` via its raw socket script and captured the exact raw output, identical in substance to the with-skill run.
- ✓ Maintained one persistent connection while both checking status and exploring for a shop
  - *Evidence:* One held socket connection handled login through score/list/quit/exit.
- ✓ If a shop was found, the reported items/prices match the server's actual `list` output
  - *Evidence:* Raw `list` output matches final_answer.md exactly (danish pastry 7g, bread 14g, waybread 74g).
- ✓ Clearly reports what was checked/found even if no shop was located within a reasonable search
  - *Evidence:* final_answer.md reports score and bakery listing clearly.

</details>

## Analysis Notes

- Every assertion passed for both configurations across all 3 evals -- these were live, competent agents on either side, so pass-rate doesn't discriminate here. The real signal is cost: with-skill was ~2.7x faster (83s vs 226s mean) and used ~27% fewer tokens (30.9k vs 42.2k mean) on every single eval, because the baseline had to rediscover the tbaMUD login dance and telnet IAC-stripping from scratch each time instead of reusing a pre-built connection tool.
- These runs used only one live MUD character ('dummy'), so with-skill and baseline runs were executed sequentially (never in parallel) to avoid two connections fighting over the same character -- tbaMUD drops the older link when a second login as the same character arrives ('Reconnecting.' branch was observed live during testing). This also means character state (position, hunger) carried over between runs; eval prompts were written to be self-orienting (always `look`/`score` before acting) to stay valid regardless of starting position, but it means eval 3's 'track down a shop nearby' was trivially satisfied in both configs because the character happened to already be standing in the bakery from eval 3's with-skill run.
- The 'connection persistence' assertions were only weakly discriminating: a competent baseline agent can write one throwaway script that holds a single socket open for an entire one-shot task, which technically satisfies 'not one telnet call per command.' The gap the skill actually closes shows up in engineering cost avoided (not needing to re-derive the login/menu/IAC handling every time) and in supporting a natural multi-turn, react-to-output play style across genuinely separate tool calls -- which is what the time/token deltas capture indirectly.
- If this eval set is reused for a future iteration, pre-creating a couple of throwaway characters (each spawns fresh at the Temple of Midgaard) would give real start-position reproducibility and would also unlock true parallel with-skill/baseline runs instead of sequential ones.
