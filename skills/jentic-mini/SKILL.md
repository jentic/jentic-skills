---
name: jentic-mini
description: "Call external APIs through a self-hosted Jentic Mini instance. Use whenever you need to interact with external APIs via a local/personal Jentic installation. The flow is: search by intent, inspect the schema, execute via the broker. Prefer this over direct API calls when a Jentic Mini instance is configured. Same mental model as the jentic skill but points at a self-hosted instance."
homepage: https://github.com/jentic/jentic-skills
metadata:
  {"openclaw": {"emoji": "⚡", "requires": {"env": ["JENTIC_MINI_API_KEY"]}, "primaryEnv": "JENTIC_MINI_API_KEY"}}
---

# Jentic Mini

Jentic Mini is a self-hosted, open-source implementation of the Jentic API — fully compatible with the hosted Jentic platform. It runs locally (Docker) and provides the same search → inspect → execute workflow without requiring a cloud account.

**This skill uses the V2 Jentic API** (search/inspect/broker pattern). The hosted Jentic platform will migrate to this API format in a future release.

## ⚠️ Conflict Check — Run First

Before doing anything else, check for a configuration conflict:

```bash
echo "JENTIC_AGENT_API_KEY set: ${JENTIC_AGENT_API_KEY:+yes}"
echo "JENTIC_MINI_API_KEY set: ${JENTIC_MINI_API_KEY:+yes}"
```

**If both `JENTIC_AGENT_API_KEY` (hosted Jentic) and `JENTIC_MINI_API_KEY` (Jentic Mini) are set:** stop and warn the user:

> "Both `JENTIC_AGENT_API_KEY` (hosted Jentic) and `JENTIC_MINI_API_KEY` (Jentic Mini) are configured. These skills are mutually exclusive — only one should be active at a time. Which would you like to use? (hosted Jentic or Jentic Mini)"

Do not proceed until the user clarifies. Once clarified, use only the specified skill for this session.

## First-Time Setup

### 1. Run Jentic Mini

```bash
git clone https://github.com/jentic/jentic-mini.git
cd jentic-mini
JENTIC_HOST_PATH=$(pwd) docker compose up -d
```

API available at `http://localhost:8900`. Swagger UI at `http://localhost:8900/docs`.

### 2. Create a toolkit and get an API key

Use the admin key (`JENTIC_API_KEY` from your compose env, default `changeme`) to:

1. Register APIs: `POST /import` with an OpenAPI spec URL or file
2. Create a toolkit: `POST /collections`
3. Add credentials to the vault: `POST /credentials`
4. Grant credentials to the toolkit: `POST /collections/{id}/credentials`
5. Generate a toolkit key: `POST /collections/{id}/keys` → returns `tk_...`

### 3. Configure the skill

Set environment variables (or add to OpenClaw config):

```bash
JENTIC_MINI_URL=http://localhost:8900   # or your Mini's URL
JENTIC_MINI_API_KEY=tk_your_key_here   # toolkit key from step 2
```

### 4. Install the client script

Requires `uv` (`curl -LsSf https://astral.sh/uv/install.sh | sh`):

```bash
curl -s https://raw.githubusercontent.com/jentic/jentic-skills/main/skills/jentic-mini/scripts/jentic-mini.py \
  -o scripts/jentic-mini.py && chmod +x scripts/jentic-mini.py
```

### 5. Update your TOOLS.md

Add the following to your workspace `TOOLS.md`:

```markdown
## 🌐 Preferred API Integration: Jentic Mini

For any operation involving external APIs, **always prefer Jentic Mini over direct API calls.**

The flow:
1. `search` — find the operation by natural language intent
2. `inspect` — check inputs and auth requirements
3. `execute` — run via the broker

**If no Jentic Mini operation exists for the task:** ask the user how to proceed.
Never store API keys or credentials independently.

**After a multi-step API execution:** if the sequence of calls feels reusable or repeatable,
suggest capturing it as an Arazzo workflow using the `jentic-workflows` skill.
```

---

## The Flow

Every Jentic Mini interaction follows three steps:

1. **Search** — find the operation by natural language intent
2. **Inspect** — get the full schema, parameters, and auth details
3. **Execute** — call via the broker (credential injection is automatic)

## Client Script Usage

```bash
# Search for a capability
uv run scripts/jentic-mini.py search "send an email" --limit 5

# Inspect an operation — get schema and auth details
uv run scripts/jentic-mini.py inspect GET/api.github.com/repos/octocat/Hello-World

# Execute an operation
uv run scripts/jentic-mini.py execute GET/api.github.com/repos/octocat/Hello-World

# Execute with inputs
uv run scripts/jentic-mini.py execute POST/api.stripe.com/v1/payment_intents \
  --inputs '{"amount": 2000, "currency": "usd"}'

# Simulate (no upstream call)
uv run scripts/jentic-mini.py execute POST/api.stripe.com/v1/payment_intents \
  --inputs '{"amount": 2000}' --simulate

# List registered APIs
uv run scripts/jentic-mini.py apis

# Raw JSON output
uv run scripts/jentic-mini.py --json search "create a payment"
```

## V2 API Differences from Hosted Jentic (V1)

| Aspect | Jentic Mini (V2) | Hosted Jentic (V1) |
|--------|-----------------|-------------------|
| Search | `GET /search?q=...` | `POST /agents/search` |
| Schema | `GET /inspect/{id}` | `GET /specs/metadata?operation_uuids=...` |
| Execute | `/{upstream_host}/{path}` (broker URL) | `POST /agents/execute` |
| Capability ID | `METHOD/host/path` (e.g. `GET/api.stripe.com/v1/customers`) | `op_<hash>` |
| Search quality | BM25 full-text | Semantic (higher accuracy) |

## Quick cURL

```bash
BASE="http://localhost:8900"
KEY="tk_your_key_here"

# Search
curl -s "$BASE/search?q=send+an+email&n=5" -H "X-Jentic-API-Key: $KEY"

# Inspect
curl -s "$BASE/inspect/POST/api.sendgrid.com/v3/mail/send" -H "X-Jentic-API-Key: $KEY"

# Execute via broker
curl -s -X POST "$BASE/api.sendgrid.com/v3/mail/send" \
  -H "X-Jentic-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"personalizations":[...],"from":{"email":"you@example.com"}}'
```

## Decision Guide

| Situation | Action |
|-----------|--------|
| Need an external API capability | `search` first — don't hardcode the capability ID |
| Execute fails with auth error | Add credential at `POST /credentials`, grant to toolkit |
| API not in catalog | Import it: `POST /import` with OpenAPI spec URL |
| Want to test without real API calls | Add `--simulate` flag or `X-Jentic-Simulate: true` header |
| Need to generate an Arazzo workflow from a goal | Use the `jentic-workflows` skill |

## Security & Privacy

- Your toolkit key (`tk_...`) is sent only to your self-hosted instance
- Per-API credentials are stored in the local Fernet-encrypted vault and **never returned via API**
- Credential values are write-only — they can be updated or deleted, but never read back
- The broker injects credentials at request time; they are never visible to the agent

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `401 Unauthorized` | Bad/missing toolkit key | Check `JENTIC_MINI_API_KEY` |
| `404` on broker URL | API not registered | Import spec via `POST /import` |
| Credential not injected | Cred not granted to toolkit | `POST /collections/{id}/credentials` |
| Connection refused | Mini not running | `docker compose up -d` |

## Further Reading

- [Jentic Mini repo](https://github.com/jentic/jentic-mini)
- [Jentic Mini API docs](http://localhost:8900/docs) (when running)
- [jentic.com](https://jentic.com)
