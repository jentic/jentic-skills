# jentic-skills

OpenClaw skills for the Jentic platform. These skills extend OpenClaw agents with Jentic's API workflow generation, Arazzo tooling, and integration capabilities.

## What's here

Skills in this repo are designed for anyone building with Jentic. They require a Jentic account and API key.

| Skill | Description |
|-------|-------------|
| [jentic](skills/jentic/) | The recommended Jentic skill — designed for self-hosted [Jentic Mini](https://github.com/jentic/jentic-mini). Use this for all new installs. |
| [jentic-v1](skills/jentic-v1/) | For hosted Jentic (jentic.com). API parity with Jentic Mini coming soon — use this skill if you're on hosted Jentic for now. |
| [jentic-workflows](skills/jentic-workflows/) | Generate Arazzo 1.0.1 workflow YAML from a natural-language goal or agent tool trace. Handles API discovery via Jentic, Arazzo linting with `@jentic/arazzo-validator`, and semantic validation. |

## Installation

To install and set up the `jentic` skill, send this message to your OpenClaw agent:

> "Install the Jentic skill from https://github.com/jentic/jentic-skills/tree/main/skills/jentic into your workspace skills directory, then run the Jentic setup flow."

The agent will install the skill and walk you through connecting it to your Jentic Mini instance.

## Contributing

Skills follow the [AgentSkills](https://agentskills.io) spec. See individual skill `SKILL.md` files for usage instructions.

## License

Apache 2.0 — see [LICENSE](LICENSE).
