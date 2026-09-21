# Faux Codex
 
A miniature analogue of OpenAI's Codex — a multi-agent engineering team, built with
[CrewAI](https://docs.crewai.com), that turns a plain-English description of some
software into working code. You type what you want built into a web UI; a small
team of AI agents designs it, writes it, builds a demo UI for it, and tests it —
with automated quality checks and an optional human-in-the-loop review step along
the way.
 
## How it works
 
**The team**
 
| Agent | Role |
|---|---|
| `project_manager` | Oversees the whole run in CrewAI's hierarchical process. Doesn't write anything itself. |
| `engineering_lead` | Designs the system: modules, classes, function signatures. No code. |
| `backend_engineer` | Writes the backend Python code, using only the standard library. |
| `frontend_engineer` | Builds a Gradio UI that demonstrates the backend. |
| `test_engineer` | Writes and runs `unittest` tests against the backend. |
| `inspector` | Reviews each deliverable against specific criteria before the crew moves on. |
 
**The pipeline**
 
1. **Design** → `engineering_lead` produces a design doc (modules, classes, function signatures only).
2. **Backend** → `backend_engineer` implements it in the sandbox.
3. **Frontend** → `frontend_engineer` builds a Gradio demo of the backend.
4. **Tests** → `test_engineer` writes and runs unit tests, fixing issues until they pass.
Each of these four steps runs inside a **CrewAI Flow**, and each one is checked by
**two guardrails** before the crew is allowed to move on:
 
- An **automated review** — the `inspector` agent checks the output against
  criteria specific to that step, and can send it back for another attempt with
  feedback if it falls short.
- An **optional human review** — when enabled, the crew pauses after each step
  and shows you exactly what was produced; you can approve it or send it back
  with your own feedback.
**Sandboxing**
 
All code the agents write and run happens inside a Docker container
(`docker run --rm ...`) that's mounted to a throwaway `sandbox/` folder and
destroyed after every execution. Agent-written code never touches your machine
directly.
 
## Prerequisites
 
- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — must be
  **running** before you start the app, since the sandbox tools shell out to
  `docker run`
- An API key for whichever LLM provider your agents are configured to use
## Setup
 
```bash
git clone <this-repo-url>
cd faux_codex
uv sync
```
 
Add your API key(s) to a `.env` file in the project root:
 
```
OPENAI_API_KEY=your-key-here
```
 
## Usage
 
Make sure Docker Desktop is open, then run:
 
```bash
uv run crewai run
```
 
This launches a Gradio app in your browser. From there:
 
1. Optionally check **"Pause for my review after each task"** if you want to
   approve or send back each step yourself.
2. Type a description of the software you want built into **Requirements**.
3. Click **Build it** and watch the **Progress** log update live as each agent
   works.
4. If human review is on, a **Pending Review** panel will appear after each
   step — click **Approve** to continue, or type feedback and click
   **Send Back** to have that step redone.
When it finishes, the generated project lives in the `sandbox/` folder as its
own standalone `uv` project (backend code, `app.py` Gradio demo, and a test
file), ready to run on its own.
 
## Project structure
 
```
src/faux_codex/
├── crew.py              # Agents, tasks, guardrails, and the hierarchical Crew
├── flow.py               # CrewAI Flow wrapping the crew as a single step
├── guardrails.py          # Inspector + human-review guardrail functions
├── human_review.py        # Shared coordination object for human-in-the-loop review
├── main.py                # Gradio launcher UI and CrewAI CLI entry points
├── config/
│   ├── agents.yaml         # Agent roles, goals, backstories
│   └── tasks.yaml           # Task descriptions and expected outputs
└── tools/
    └── sandbox_tools.py     # Docker-sandboxed file read/write/run tools
```
 
## Notes
 
- This project assumes a single user at a time — the human-review coordination
  is built around one shared reviewer, not per-session state.
- CLI commands from the original CrewAI scaffold (`train`, `test`, `replay`,
  `run_with_trigger`) are still available via `crewai train`, `crewai test`,
  etc., and call the crew directly rather than through the Gradio UI or the Flow.
