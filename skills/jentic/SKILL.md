---
name: jentic
version: 1.1.3
description: "Call external APIs through Jentic — AI agent API middleware. Use whenever you need to interact with external APIs (Gmail, Google Calendar, GitHub, Stripe, Twilio, and many more). Jentic handles authentication centrally so no per-API credentials are needed in the agent. The flow is: search by intent, inspect the schema, then execute via the broker. Use this in preference to direct curl/API calls for any API in the Jentic catalog of 10,000+ APIs. Recommended backend: Jentic Mini (self-hosted). Hosted Jentic support coming soon — use the jentic-v1 skill for hosted for now. Includes an installation flow for first-time setup."
homepage: https://github.com/jentic/jentic-skills
metadata:
  {"openclaw": {"emoji": "⚡", "requires": {"env": ["JENTIC_URL", "JENTIC_API_KEY"]}, "primaryEnv": "JENTIC_API_KEY"}}
---

# Jentic

Jentic is an AI agent API middleware platform. It gives agents access to a catalog of 10,000+ external APIs through a single uniform interface. **Credentials live in Jentic, not in the agent** — API secrets are managed in the Jentic platform, eliminating prompt injection risk from embedded API keys.

This skill works against either:
- **Jentic Mini** ⭐ **(recommended)** — self-hosted Docker instance you run on your own infrastructure (VPS, home server, etc.). Host it separately from the agent where possible — running both on the same machine gives the agent direct access to the admin API, which weakens the security boundary.
- **Hosted Jentic** — managed service for businesses and enterprises with scaling, SLA, and multi-user requirements. API parity with Jentic Mini is coming soon. For now, hosted Jentic users should use the [`jentic-v1` skill](https://github.com/jentic/jentic-skills/tree/main/skills/jentic-v1) instead.

Most users should run Jentic Mini. Set `JENTIC_URL` and `JENTIC_API_KEY` once; the rest is transparent.

## 🔒 Security Model — Read Before Setup

Jentic Mini has a strict two-actor trust boundary. **Never cross it.**

| Actor | Auth mechanism | Can do |
|---|---|---|
| **Agent (you)** | `X-Jentic-API-Key: tk_xxx` | Search, inspect, execute, submit permission requests, generate OAuth connect links |
| **Human (user)** | Username + password → UI session | Approve permission requests, complete OAuth flows in browser, manage credentials |

The hard rules for this boundary are written into your workspace `TOOLS.md` at install time — read them there every session. The threat model is **prompt injection**: an attacker injects instructions into data you process (e.g. an email body), causing you to escalate your own privileges. The human approval step is the mitigation; bypassing it defeats the entire security model.

---

## Installation

> **When to run this section:** Execute this flow if `JENTIC_API_KEY` is not set, or if the user explicitly asks to install or configure Jentic.

### Step 1: Ask which backend

Ask the user:

> "Which Jentic backend would you like to connect to?
>
> 1. **Jentic Mini on a separate machine** ⭐ recommended — self-hosted on a VPS, home server, or any machine other than this one. Keeps a hard boundary between the agent and the credential store, so the agent can never bypass the security model.
>
> 2. **Jentic Mini on this machine** — runs alongside your OpenClaw instance. Fine for development and testing, but not recommended for production use: the agent has access to the Docker environment directly and can `docker exec` into the container to read or modify the database, bypassing the security model entirely.
>
> 3. **Hosted Jentic** (jentic.com) — managed service for businesses and enterprises. API parity with Jentic Mini coming soon; for now use the `jentic-v1` skill for hosted Jentic."

---

### Step 2a: Jentic Mini — separate machine (recommended)

Ask the user:

> "Do you already have Jentic Mini running on a separate machine?"

**If yes:** ask for the URL, then follow the connect flow in Step 3.

**If no:** ask:

> "Would you like help setting one up?
>
> 1. **DigitalOcean droplet** — spin up a $6/month VPS in ~5 minutes using our setup script. I'll walk you through it.
> 2. **Somewhere else** — I'll point you to the install docs and you can come back once it's running."

**If option 1 (DigitalOcean):** walk the user through the following steps:

> "Here's how to get Jentic Mini running on a DigitalOcean droplet:
>
> Full guide: https://github.com/jentic/jentic-mini/blob/main/docs/deploy/digitalocean/README.md
>
> Short version:
> 1. Create an Ubuntu 22.04 or 24.04 droplet (Basic, $6/month is enough)
> 2. Under Advanced Options, check **Add Initialization scripts** and paste the contents of: https://raw.githubusercontent.com/jentic/jentic-mini/main/docs/deploy/digitalocean/setup.sh
> 3. Wait ~5 minutes for the droplet to boot and the script to run
> 4. Come back with the droplet's public IP"

Wait for the user to return with the IP, then continue to Step 3.

**If option 2 (somewhere else):**
> "Install docs: https://github.com/jentic/jentic-mini — come back with the URL once it's running."

Stop here until the user returns with a running instance.

---

### Step 2b: Jentic Mini — this machine (dev/test only)

Warn the user:

> "Warning: Running Jentic Mini on the same machine as your OpenClaw instance means the agent has access to the Docker environment directly. It can `docker exec` into the container and read or modify the database, bypassing the security model entirely. This is fine for development and testing where you trust the agent fully, but must not be used in production. Proceed?"

If they confirm, follow the Docker setup:

**1. Ensure Docker is available:**

```bash
docker --version && docker compose version
```

If Docker is missing, install it:

```bash
curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker $USER && newgrp docker
```

**2. Pull and start Jentic Mini from Docker Hub:**

```bash
docker run -d \
  --name jentic-mini \
  --restart unless-stopped \
  -p 8900:8900 \
  -v jentic-mini-data:/app/data \
  jentic/jentic-mini
```

**3. Wait for it to be ready (up to 60s):**

```bash
for i in $(seq 1 12); do
  curl -sf http://localhost:8900/health > /dev/null 2>&1 && echo "Ready!" && break
  echo "Waiting... ($i/12)" && sleep 5
done
```

If it doesn't come up: `docker logs jentic-mini`

**4.** Set URL to `http://localhost:8900` and follow Step 3 to get the agent key and store config.

---

### Step 2c: Hosted Jentic

> "Hosted Jentic is coming soon with full API parity. For now, please use the `jentic-v1` skill for hosted Jentic — visit [jentic.com](https://jentic.com) to get started."

---

### Step 3: Connect and configure

Once you have a running instance and its URL:

**1.** Test the connection:

```bash
JENTIC_URL="<url>"
curl -sf "$JENTIC_URL/health" | python3 -m json.tool
```

If it fails: confirm the URL is correct and the instance is reachable.

**2.** Get an agent key:

```bash
KEY_RESPONSE=$(curl -sf -X POST "$JENTIC_URL/default-api-key/generate")
AGENT_KEY=$(echo "$KEY_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['key'])")
echo "Agent key: $AGENT_KEY"
```

> **Critical:** This key is shown **once only** — capture it immediately. If lost, regenerate via the Jentic Mini UI.

If `/default-api-key/generate` returns an error (already claimed), the user must generate a new key via the Jentic Mini UI.

**3.** Store and export:

```bash
export JENTIC_URL="<url>"
export JENTIC_API_KEY="$AGENT_KEY"
```

Store both in OpenClaw config (`~/.openclaw/openclaw.json` under `skills.entries.jentic`).

**4.** Append `tools-block.md` (in this skill's directory) verbatim to the workspace `TOOLS.md`. Do not paraphrase or summarise — copy it exactly. Replace `{JENTIC_URL}` with the actual URL throughout.

**5.** Confirm:
> "Connected to Jentic Mini at `<url>`. Agent key stored. To finish setup, visit `<url>` in your browser to create your admin account. Once that's done, add API credentials via the Jentic Mini UI to start using the catalog."

> **Note:** The API response from `/default-api-key/generate` may include a `setup_url` or `next_step` field referencing `/user/create` — ignore it. Direct the user to the root URL (`<url>`) only; the UI handles the rest.

> **Note on credential binding:** The **default toolkit** implicitly contains **all credentials** — no explicit binding step is needed. Do not attempt to bind credentials to the default toolkit; it will work automatically once the user adds credentials via the UI. Only named/scoped toolkits require explicit credential binding via `POST /toolkits/{id}/credentials`, and that requires a human session.

---

## TOOLS.md Block

The content to append to `TOOLS.md` lives in `references/tools-block.md` in this skill's directory. Append it verbatim — do not paraphrase or summarise. Replace `{JENTIC_URL}` with the actual instance URL throughout.

---

## Workflows — Deterministic Sequences

Jentic supports two execution primitives. Choose based on whether LLM judgment is needed between steps:

| Primitive | What it is | When to use |
|---|---|---|
| **Operation** | Single API call via broker | Any individual action; when LLM interpretation of the response determines the next step |
| **Arazzo workflow** | Multi-step sequence executed server-side | Fixed sequence where each step follows deterministically from a status code or field value — no LLM needed between steps |

**Prefer a workflow when** you're about to orchestrate a fixed sequence of 2+ operations where the output of one feeds directly into the next. Workflows run entirely server-side: faster, cheaper (no per-step LLM calls), more reliable, and consume no context window per step.

### Discover workflows

Search returns both operations and workflows — check results for both before deciding which to use:

```bash
# Search returns operations and workflows together
curl -s -H "X-Jentic-API-Key: $JENTIC_API_KEY" "$JENTIC_URL/search?q=<intent>&limit=5"

# List all registered workflows
curl -s -H "X-Jentic-API-Key: $JENTIC_API_KEY" "$JENTIC_URL/workflows"

# Get a workflow's input schema (LLM-friendly markdown)
curl -s -H "X-Jentic-API-Key: $JENTIC_API_KEY" -H "Accept: text/markdown" \
  "$JENTIC_URL/workflows/<slug>"
```

### Execute a workflow

```bash
curl -X POST \
  -H "X-Jentic-API-Key: $JENTIC_API_KEY" \
  -H "Content-Type: application/json" \
  "$JENTIC_URL/workflows/<slug>" \
  -d '{ "input_field": "value", ... }'
```

Jentic executes all steps and returns the final result. No per-step agent involvement.

### Upload a new workflow

When you identify a deterministic sequence worth encoding as a reusable workflow, upload it via the import endpoint:

```bash
curl -X POST \
  -H "X-Jentic-API-Key: $JENTIC_API_KEY" \
  -H "Content-Type: application/json" \
  "$JENTIC_URL/import" \
  -d '{
    "sources": [{
      "type": "inline",
      "content": "<arazzo-json-as-string>",
      "filename": "my-workflow.json"
    }]
  }'
```

The workflow is immediately searchable and executable. For Arazzo document format see: https://spec.openapis.org/arazzo/latest.html

### Skills vs workflows — the relationship

- A **skill** is the LLM coordination layer: context-dependent decisions, multi-turn interactions, anything requiring judgment.
- A **workflow** is the automation layer: the deterministic backbone that doesn't need the LLM at all.
- Skills call workflows as a single step for their deterministic sequences, then apply judgment to the result. They complement each other — neither replaces the other.

---

## Access Management — You Drive This

When a user asks about API access, credentials, or permissions, **you orchestrate it** — never redirect them to the UI when an API call exists to accomplish the same goal.

**Always fetch the live OpenAPI spec first** to get exact schemas before making access management calls:

```bash
curl -s "$JENTIC_URL/openapi.json" | python3 -c "
import json, sys
spec = json.load(sys.stdin)
for path, methods in spec.get('paths', {}).items():
    for method in methods:
        if any(k in path.lower() for k in ['credential', 'permission', 'access', 'oauth', 'toolkit']):
            print(method.upper(), path)
"
```

Then follow this decision tree:

| Situation | What to do |
|---|---|
| User asks what access you have | List credentials (`GET /credentials`), then list toolkits (`GET /toolkits`) |
| Permission exists but too restrictive | Submit a `modify_permissions` access request → share `approve_url` with user |
| Credential exists but not in toolkit | Submit a `grant` access request → share `approve_url` with user |
| No credential yet — OAuth API (Gmail, GitHub, etc.) | Get connect link via OAuth broker → send link to user → they complete OAuth in browser → sync → submit `grant` request |
| No credential yet — API key API | Ask user for the key → they add via Jentic Mini UI → you submit `grant` request |

The connect-link flow means you **never** say "go to the UI and connect your account" — you hand the user a direct URL to the OAuth screen, they click it, and you handle everything else programmatically.

### Listing what's available

```bash
# List all credentials
curl -s -H "X-Jentic-API-Key: $JENTIC_API_KEY" "$JENTIC_URL/credentials"

# List toolkits (scopes for agent access)
curl -s -H "X-Jentic-API-Key: $JENTIC_API_KEY" "$JENTIC_URL/toolkits"

# List OAuth brokers (needed for connect-link flow)
curl -s -H "X-Jentic-API-Key: $JENTIC_API_KEY" "$JENTIC_URL/oauth-brokers"
```

### Submitting an access request

```bash
curl -s -X POST \
  -H "X-Jentic-API-Key: $JENTIC_API_KEY" \
  -H "Content-Type: application/json" \
  "$JENTIC_URL/toolkits/default/access-requests" \
  -d '{
    "type": "grant",
    "credential_id": "cred_xxx",
    "reason": "Required to send email via Gmail on user request"
  }'
```

Types: `"grant"` (add a credential to the toolkit) or `"modify_permissions"` (expand what you can do with an existing credential).

Take the `approve_url` from the response and share it with the user. They approve it in the browser. **Do NOT approve your own requests** — that's the entire security boundary (see Security Model above).

Poll `GET /toolkits/default/access-requests/{req_id}` periodically until `status` is no longer `pending`. On `approved`, retry the operation that triggered the gap. On `denied`, surface the reason to the user and stop.

**Request minimum permissions per step** — don't ask for broad access upfront. Request only what's needed for the current operation; users are more likely to approve narrow, well-reasoned requests, and it respects least-privilege.

### OAuth connect-link flow

When there is no credential yet for an OAuth API (Gmail, Calendar, GitHub, etc.):

```bash
# Step 1: Find the broker ID
BROKER_ID=$(curl -s -H "X-Jentic-API-Key: $JENTIC_API_KEY" "$JENTIC_URL/oauth-brokers" \
  | python3 -c "import json,sys; b=json.load(sys.stdin); print(b[0]['id'] if b else 'NONE')")

# Step 2: Find the API slug from the catalog
curl -s -H "X-Jentic-API-Key: $JENTIC_API_KEY" "$JENTIC_URL/catalog?q=gmail"

# Step 3: Generate a connect link (use app_slug + api_id from catalog result)
curl -s -X POST \
  -H "X-Jentic-API-Key: $JENTIC_API_KEY" \
  -H "Content-Type: application/json" \
  "$JENTIC_URL/oauth-brokers/$BROKER_ID/connect-link" \
  -d '{"app_slug": "gmail", "api_id": "api_xxx"}'
# → returns { "connect_url": "https://..." }

# Step 4: Share the connect_url with the user
# Step 5: Once they confirm completion, sync to pull in the new credential
curl -s -X POST \
  -H "X-Jentic-API-Key: $JENTIC_API_KEY" \
  "$JENTIC_URL/oauth-brokers/$BROKER_ID/sync"

# Step 6: Submit a grant access request for the new credential
```

**If no OAuth broker exists** (`BROKER_ID` is empty): ask the user to add one via Settings → OAuth Brokers → Add in the Jentic Mini UI. They need a Pipedream Client ID, Secret, and Project ID from [pipedream.com/connect](https://pipedream.com/connect). This only needs to be set up once.

### What to say to the user

- OAuth connect link generated: *"Here's your [Service] authorization link: [url] — click it, grant access, and come back. I'll handle the rest."*
- Access request submitted: *"I've submitted a permission request. Please approve it here: [approve_url]"*
- **Never say:** *"Go to the Jentic Mini UI and add your credential there"* — unless no API call exists to get them there faster.

---

## Further Reading

- [jentic.com](https://jentic.com)
- [Jentic Mini repo](https://github.com/jentic/jentic-mini)
- [Jentic Mini AUTH docs](https://github.com/jentic/jentic-mini/blob/main/docs/AUTH.md)
- [Jentic Mini CREDENTIALS docs](https://github.com/jentic/jentic-mini/blob/main/docs/CREDENTIALS.md)
- [Jentic Skills repo](https://github.com/jentic/jentic-skills)

