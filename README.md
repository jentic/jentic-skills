# jentic-skills

OpenClaw skills for the Jentic platform. These skills extend OpenClaw agents with Jentic's API workflow generation, Arazzo tooling, and integration capabilities.

## What's here

Skills in this repo are designed for anyone building with Jentic. They require a Jentic account and API key.

| Skill | Description |
|-------|-------------|
| [jentic](skills/jentic/) | The current Jentic skill (V2 API) — works against hosted Jentic V2 or self-hosted jentic-mini. Single `JENTIC_API_KEY` + optional `JENTIC_URL` for backend selection. Use this for all new installs. |
| [jentic-v1](skills/jentic-v1/) | Legacy V1 skill for installs still on the original hosted Jentic API (`JENTIC_AGENT_API_KEY`). Use only if you haven't migrated to V2 yet. |
| [jentic-apis](skills/jentic-apis/) | Score and improve OpenAPI specifications for AI-readiness using the JAIRF framework. Includes CLI tooling (`jentic-apitools score`) and the full JAIRF scoring reference for improvement passes. |
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
