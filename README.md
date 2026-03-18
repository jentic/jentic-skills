# jentic-skills

OpenClaw skills for the Jentic platform. These skills extend OpenClaw agents with Jentic's API workflow generation, Arazzo tooling, and integration capabilities.

## What's here

Skills in this repo are designed for anyone building with Jentic. They require a Jentic account and API key.

| Skill | Description |
|-------|-------------|
| [jentic](skills/jentic/) | Enterprise skill for the hosted Jentic platform — semantic API search, credential brokering, and execution at scale. Requires a Jentic cloud account. |
| [jentic-mini](skills/jentic-mini/) | Open-source self-hosted skill for low-volume or personal use. Runs locally via Docker, no cloud account required. Uses the V2 Jentic API (BM25 search, broker pattern). |
| [jentic-workflows](skills/jentic-workflows/) | Generate Arazzo 1.0.1 workflow YAML from a natural-language goal or agent tool trace. Handles API discovery via Jentic, Arazzo linting with `@jentic/arazzo-validator`, and semantic validation. |

## Installation

Paste this into your OpenClaw agent to install all Jentic skills:

```
Clone https://github.com/jentic/jentic-skills.git into ~/.openclaw/skills/jentic-skills and add ~/.openclaw/skills/jentic-skills/skills to skills.load.extraDirs in ~/.openclaw/openclaw.json
```

Or manually:

```bash
git clone https://github.com/jentic/jentic-skills.git ~/.openclaw/skills/jentic-skills
```

Then add to your `~/.openclaw/openclaw.json`:
```json
{
  "skills": {
    "load": {
      "extraDirs": ["~/.openclaw/skills/jentic-skills/skills"]
    }
  }
}
```

## Contributing

Skills follow the [AgentSkills](https://agentskills.io) spec. See individual skill `SKILL.md` files for usage instructions.

## License

Apache 2.0 — see [LICENSE](LICENSE).
