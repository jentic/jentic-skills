# jentic-skills

OpenClaw skills for the Jentic platform. These skills extend OpenClaw agents with Jentic's API workflow generation, Arazzo tooling, and integration capabilities.

## What's here

Skills in this repo are designed for anyone building with Jentic. They require a Jentic account and API key.

| Skill | Description |
|-------|-------------|
| *(skills coming soon)* | |

## Installation

```bash
# Install a skill into your OpenClaw workspace
clawhub install <skill-slug>

# Or clone and point extraDirs at this repo
git clone https://github.com/jentic/jentic-skills.git
```

Then add to your `~/.openclaw/openclaw.json`:
```json
{
  "skills": {
    "load": {
      "extraDirs": ["/path/to/jentic-skills/skills"]
    }
  }
}
```

## Contributing

Skills follow the [AgentSkills](https://agentskills.io) spec. See individual skill `SKILL.md` files for usage instructions.

## License

Apache 2.0 — see [LICENSE](LICENSE).
