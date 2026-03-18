---
name: jentic-apis
description: "Score, analyze, and improve OpenAPI specifications for AI-readiness using the JAIRF framework. Use when: (1) scoring an OpenAPI spec, (2) identifying why a spec scores poorly, (3) making improvement recommendations to raise the JAIRF score. The skill provides CLI tooling (jentic-apitools) and a scoring reference (JAIRF) so the agent can both score and meaningfully suggest improvements."
homepage: https://github.com/jentic/jentic-skills
metadata:
  {"openclaw": {"emoji": "📊"}}
---

# Jentic APIs

Score and improve OpenAPI specifications for AI-readiness using the **JAIRF (Jentic API AI-Readiness Framework)**. The framework produces a 0–100 score, a readiness level (0–4), and per-dimension breakdowns that tell you exactly what to fix.

## Setup

> **Note:** `jentic-apitools` is not yet published to PyPI. Install from source until it is.

All tooling installs into a dedicated venv at `~/.jentic/venv` to avoid conflicts with system Python.

```bash
# Create the venv
uv venv ~/.jentic/venv

# Install jentic-openapi-tools (published on PyPI)
uv pip install --python ~/.jentic/venv jentic-openapi-tools

# Clone and install jentic-apitools from source
git clone https://github.com/jentic/jentic-apitools.git ~/.jentic/jentic-apitools
uv pip install --python ~/.jentic/venv \
  -e ~/.jentic/jentic-apitools/packages/common \
  -e ~/.jentic/jentic-apitools/packages/analyze \
  -e ~/.jentic/jentic-apitools/packages/score \
  -e ~/.jentic/jentic-apitools/packages/cli
```

Verify:
```bash
~/.jentic/venv/bin/jentic-apitools --version
~/.jentic/venv/bin/python -c "from jentic.apitools.openapi.parser.core import OpenAPIParser; print('ok')"
```

If already installed, pull latest `jentic-apitools`:
```bash
cd ~/.jentic/jentic-apitools && git pull
```

### TOOLS.md

Add to your workspace `TOOLS.md`:

```markdown
## 🔧 jentic-apis Skill

Installed in a dedicated venv at `~/.jentic/venv`.

- **jentic-apitools CLI:** `~/.jentic/venv/bin/jentic-apitools`
- **jentic-openapi-tools Python:** `~/.jentic/venv/bin/python`
- **jentic-apitools source:** `~/.jentic/jentic-apitools/` (cloned from GitHub)

Always use the full venv path when invoking these tools.
```

## Score a Spec

> **Note:** The `jentic-apitools score` CLI is not yet wired up. Use the bundled `scripts/score_spec.py` instead.

```bash
# Score a spec (JSON output)
~/.jentic/venv/bin/python {skill_dir}/scripts/score_spec.py openapi.yaml

# Score without the per-signal details (summary only)
~/.jentic/venv/bin/python {skill_dir}/scripts/score_spec.py openapi.yaml --no-details

# Save results
~/.jentic/venv/bin/python {skill_dir}/scripts/score_spec.py openapi.yaml > score-report.json
```

Replace `{skill_dir}` with the path to this skill's directory (e.g. `~/.openclaw/workspace/repositories/jentic-skills/skills/jentic-apis`).

## Interpreting Output

| Score | Level | Name | What it means |
|-------|-------|------|---------------|
| < 40 | 0 | Not Ready | Fundamentally unsuitable for AI agents |
| 40–60 | 1 | Foundational | Developer-usable, partially AI-usable |
| 60–75 | 2 | AI-Aware | Semantically interpretable, safe for guided use |
| 75–90 | 3 | AI-Ready | Structurally rich, semantically clear, agent-friendly |
| ≥ 90 | 4 | Agent-Optimized | Highly composable, predictable, automation-ready |

The score uses a **weighted harmonic mean** across 6 dimensions — a low score in any dimension pulls the final score down and cannot be masked by highs elsewhere.

### The Six Dimensions

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| FC — Foundational Compliance | 16% | Structural validity, lint, ref resolution |
| DXJ — Developer Experience | 18% | Examples, docs, response coverage, tooling health |
| ARAX — AI-Readiness & Agent Experience | 24% | Semantic clarity, summaries, operationId quality |
| AU — Agent Usability | 20% | Complexity, distinctiveness, navigation, safety |
| SEC — Security | 12% | Auth coverage, auth strength, transport, hygiene |
| AID — AI Discoverability | 10% | Descriptive richness, domain tags, registry signals |

**Gating rule:** FC < 40 → Level 0 regardless of other scores. Fix structural issues first.

## Low-Level Operations (jentic-openapi-tools)

For direct manipulation during improvement passes, use `jentic-openapi-tools`:

```python
PYTHON = "~/.jentic/venv/bin/python"

from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.validator.core import OpenAPIValidator
from jentic.apitools.openapi.transformer.bundler.core import OpenAPIBundler

# Parse spec into a dict
parser = OpenAPIParser()
spec = parser.parse("file:///path/to/openapi.yaml")

# Validate and get diagnostics
validator = OpenAPIValidator()
result = validator.validate("file:///path/to/openapi.yaml")
for d in result.diagnostics:
    print(f"{d.severity}: {d.message}")

# Bundle (resolve external $refs)
bundler = OpenAPIBundler("redocly")
bundled = bundler.bundle("file:///path/to/openapi.yaml", return_type=dict)
```

Use `jentic-openapi-tools` to:
- Parse a spec for programmatic editing
- Validate after making changes (fast, no scoring overhead)
- Bundle specs with external references before scoring
- Check diagnostics to target specific fixes

Use `jentic-apitools score` after editing to get the updated JAIRF score.



When a user asks to improve an API spec, **always ask first:**

> "Should I make **breaking** or **non-breaking** improvements?
>
> - **Non-breaking** — adds descriptions, summaries, examples, operationIds, tags, fixes lint issues. Does not change paths, parameter names, response shapes, or anything a client depends on. Output: improved spec + an OpenAPI Overlay (the delta, reusable and auditable).
> - **Breaking** — anything goes: restructure paths, rename parameters, redesign schemas for better agent usability. Output: improved spec only."

Do not proceed until the user (or calling agent) confirms the mode.

### Spawning the Improvement Subagent

Once mode is confirmed:

1. Run the baseline score and save to a file (do not hold in context):
   ```bash
   ~/.jentic/venv/bin/python {skill_dir}/scripts/score_spec.py <spec> --no-details > /tmp/score-baseline.json
   cat /tmp/score-baseline.json
   ```

2. Spawn a subagent with `runTimeoutSeconds: 1200` (20 minutes) and the brief below.

> **Context efficiency rules for the spawning agent:**
> - Do NOT read the spec file into your own context before spawning
> - Pass file paths, not file contents
> - The JAIRF reference path is: `{skill_dir}/references/jairf-scoring-guide.md` — pass the path, do not copy the file

**Subagent task brief:**

```
You are improving an OpenAPI specification for AI-readiness.

Mode: <breaking|non-breaking>
Spec: <absolute-path>
Baseline score: <score> (Level <level>, Grade <grade>)
Skill dir: <skill_dir>
Score script: ~/.jentic/venv/bin/python <skill_dir>/scripts/score_spec.py
JAIRF reference: <skill_dir>/references/jairf-scoring-guide.md

## Improvement Loop

Run a maximum of 5 iterations. Stop early if score delta < 2 points or Level 4 reached.

For each iteration:
1. Write a Python edit script to apply improvements — use exec to run it, do NOT read the full spec into context
2. Run the score script and save output to /tmp/score-iter-N.json (not into context):
   `~/.jentic/venv/bin/python <skill_dir>/scripts/score_spec.py <spec> --no-details > /tmp/score-iter-N.json`
3. Read only the `summary` section from the score file:
   `python3 -c "import json; d=json.load(open('/tmp/score-iter-N.json')); print(json.dumps(d['summary'], indent=2))"`
4. Decide: if score improved >= 2 points, continue. Otherwise stop.

## Context efficiency rules

- NEVER read the full spec file into context — always use exec/Python scripts to edit
- NEVER read the full JAIRF reference into context — consult it via exec grep/search if needed
- Write edits as self-contained Python scripts that load, modify, and save the JSON/YAML file
- Keep score outputs out of context — save to /tmp files and read only the summary

## Edit pattern (use this, not read+write)

```python
# edit_spec.py — run with: ~/.jentic/venv/bin/python edit_spec.py
import json

with open('<spec>') as f:
    spec = json.load(f)

# Make targeted changes
spec['paths']['/businesses/search']['get']['summary'] = 'Search businesses by term and location'
# ... more changes ...

with open('<output-spec>', 'w') as f:
    json.dump(spec, f, indent=2)
```

## Non-breaking constraints (STRICT)

MUST NOT:
- Change any existing path, HTTP method, or operationId
- Remove or rename any existing parameter
- Change any existing response status code or schema shape
- Remove any existing field from a schema

MAY ONLY ADD:
- summary, description fields
- example / examples fields
- tags (operations + top-level tags array)
- operationId where missing
- New response codes where absent (404, 500, etc.)
- New non-required schema properties

## Output files

- <spec-basename>-improved.json — improved spec (same directory as input)
- <spec-basename>-overlay.yaml — OpenAPI Overlay 1.0.0 (non-breaking only, same directory)

## Report when done

- Baseline score → final score (level, grade)
- Iterations completed
- Changes made by dimension
- Output file paths
- If stopped due to 5-iteration cap AND last delta was >= 2 points: flag this clearly and ask the user whether to spawn another round of improvements
```

### OpenAPI Overlay Format (non-breaking output)

The overlay file must conform to OpenAPI Overlay 1.0.0. For the full spec and examples see `references/openapi-overlay-spec.md`.

Quick structure:

```yaml
overlay: 1.0.0
info:
  title: AI-readiness improvements for <API name>
  version: 1.0.0
extends: ./<original-spec-filename>
actions:
  - target: "$.paths['/example'].get"
    update:
      summary: "Retrieve a single example resource by ID"
      description: "Returns the full representation of an example..."
  - target: "$.paths['/example'].get.parameters[?(@.name=='id')]"
    update:
      description: "The unique identifier of the example resource"
```

Key rules:
- `target` is a JSONPath expression (RFC 9535) identifying what to update
- `update` merges new values into the target object; appends to arrays
- `remove: true` removes the target (avoid in non-breaking mode)
- Actions applied in order — later actions override earlier ones
- `extends` should point to the original spec (relative path)

**FC (low score = structural problems)**
- Validate and get diagnostics: `OpenAPIValidator().validate("file:///path/to/spec.yaml")`
- Fix all error and warning diagnostics before attempting other improvements
- Resolve broken `$ref` references — use `OpenAPIBundler` to check bundling succeeds
- Fix impossible schema constraints (`minimum > maximum`, contradictory types, etc.)

**DXJ (low score = poor documentation/examples)**
- Add `example` or `examples` to request bodies and responses
- Ensure every operation has at least `200`, `4XX`, and `500` responses defined
- Add descriptions to parameters and schema properties

**ARAX (low score = poor semantic clarity)**
- Add `summary` to every operation (concise, action-oriented: "List unread messages")
- Add `description` to operations, parameters, and key schema properties
- Add unique, consistent `operationId` to every operation (camelCase or snake_case throughout)
- Use specific types (`string` with `format: email`, enums) instead of bare strings

**AU (low score = hard for agents to use)**
- If many endpoints: consider whether the spec should be split
- Add pagination metadata (Link headers or cursor fields in responses)
- Use clear verb-object operationIds (`createPayment`, `listUsers`)

**SEC (low score = auth/security issues)**
- Hardcoded credentials anywhere → SEC capped at 20, must remove
- Sensitive operations (POST/PUT/DELETE) must have security requirements
- Use HTTPS for all server URLs
- Prefer strong auth schemes: OAuth2, OIDC, Bearer JWT over API key in query param

**AID (low score = hard to discover)**
- Add rich `info.description` explaining what the API does and who it's for
- Use `tags` consistently to group operations by domain
- Add `externalDocs` links

## JAIRF Reference

For the full JAIRF scoring specification — exact signal formulas, normalization rules, gating caps, and conformance requirements — see:

```
references/jairf-scoring-guide.md
```

Load this when you need to understand exactly how a score is calculated or want to make precise improvement recommendations.

## Decision Guide

| Situation | Action |
|-----------|--------|
| Need baseline score for a spec | `~/.jentic/venv/bin/python {skill_dir}/scripts/score_spec.py <file>` |
| Score is low but unclear why | Check per-dimension breakdown; lowest dimension = highest priority |
| FC < 40 | Fix structural/lint issues before anything else — gating rule |
| User says "improve this API" | Ask breaking vs non-breaking before spawning subagent |
| Non-breaking improvement | Subagent loop + output improved spec + overlay |
| Breaking improvement | Subagent loop + output improved spec only |
| Need to explain a score to a stakeholder | Load `references/jairf-scoring-guide.md` for the full framework |
| Spec has hardcoded credentials | Must remove — SEC hard-capped at 20 until fixed |
| Want to track improvement over time | Save JSON output with `--output` and compare across runs |
