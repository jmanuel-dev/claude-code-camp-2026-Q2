# Preweek Technical Documentation

## Technical Goal

As a Cloud Engineer with limited AI experience, I have the following goals:
- Understand what are the different AI architecture that may be considered for the bootcamp's design.
- Discover the strengths and weaknesses of each AI architecture, and what value each architecture adds to the former.

## Technical Uncertainty

- I struggle to understand how I can possibly translate the analogy of an agent "playing a MUD" into actual use cases in my profession.
- I'm uncertain if a base subscription such as what I'm using (Claude Pro Plan) has enough usage limits for the harness/loop to play the MUD.
- I can't imagine how Claude Code would manage a long-running telnet connection and pass commands to the MUD.
- 
 
## Technical Hypotheses

- Given the different architectures, I'd assume that one is more efficient than others and in specific scenarios/prompts, usage limits will be hit for a subscription-based model.

## Technical Observations
- Due to automode being set to my Claude Code by default, it's been observed multiple times that Claude will cheat and look for context from other parts of the project directory, such as the ruby code meant for future week.
- A plain AGENT.md file is not a viable solution as Claude will be unable to hold a long-running telnet/nc connection through that. It immediately opted to create a python script to manage the session and send commands through.
- The world.md file is also not enough for keeping memory of the map. It's been observed multiple times that the agent gets lost even when they've already passed the same room on a prior goal.
- The reasoning will sometimes fail to reason into a solution that makes sense. Cases like below:
    1. The agent got lost finding its way back to a place it already came from, it decided to delete the character ***to start fresh***.
    2. Haiku successfully killed the massive minotaur but one that was not in the Red Room as per instructions.
- It does look like creating a skill saves on tokens and time spent reasoning as opposed to plain AGENT.md files.
- Subagents, while convenient, does not necessarily help in reasoning/efficiency. It's only adding the capability to background a task/goal and/or enable multiplayer (through agents).
- Due to the text-heavy nature of the MUD, a long-running task where an agent will first try to find its way to another area will consume alot of tokens and context window. As it will try to  reason every response it gets from each room.
- During the first phases of the python script, random NPC chatter would sometimes break the connection. Claude fixed this in future iterations of the script but this definitely need to be considered for the final architecture design.
- The N8N-based architecture seems to add unnecessary complexity.

## Technical Conclusions

- Skill-based agent is viable but not efficient.
- N8N is not viable for the bootcamp's project.
- A wrapper script/program is mandatory for the LLM to be able to keep the session alive and send commands through. This should also consider the random chatter that NPCs send when idle.
- Even on the best reasoning models such as Opus, the primary limitation of all architectures tested is the world map. It is very complicated and connected through "spaghetti wires". It's best to create a Graph database that the agent can easily access to check for navigation.

## Key Takeaway
- While I'm unsure how this bootcamp will help me on my own professional projects (personal or work), it looks like there are lots of things I'm discovering about how these AI harnesses work. These will definitely impact the way I use AI harnesses in the future so I can be more efficient in both usage and time.
- I'm very excited to see what we can reach with week1 and week2 architecture.