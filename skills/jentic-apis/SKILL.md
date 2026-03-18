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

Clone `jentic-apitools` and install from source:

```bash
git clone https://github.com/jentic/jentic-apitools.git ~/.jentic/jentic-apitools
cd ~/.jentic/jentic-apitools
pip install -e packages/common -e packages/analyze -e packages/score -e packages/cli
```

Verify:
```bash
jentic-apitools --version
```

If already cloned, pull latest:
```bash
cd ~/.jentic/jentic-apitools && git pull
```

## Score a Spec

```bash
# Score from a local file (table output)
jentic-apitools score openapi.yaml

# Score from a URL
jentic-apitools score https://example.com/openapi.json

# Machine-readable output
jentic-apitools score openapi.yaml --format json
jentic-apitools score openapi.yaml --format yaml

# Save results
jentic-apitools score openapi.yaml --format json --output score-report.json
```

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

## Improvement Loop

When a user asks to improve an API spec, **always ask first:**

> "Should I make **breaking** or **non-breaking** improvements?
>
> - **Non-breaking** — adds descriptions, summaries, examples, operationIds, tags, fixes lint issues. Does not change paths, parameter names, response shapes, or anything a client depends on. Output: improved spec + an OpenAPI Overlay (the delta, reusable and auditable).
> - **Breaking** — anything goes: restructure paths, rename parameters, redesign schemas for better agent usability. Output: improved spec only."

Do not proceed until the user (or calling agent) confirms the mode.

### Spawning the Improvement Subagent

Once mode is confirmed, spawn a subagent with:
- The spec file path
- The confirmed mode (`breaking` or `non-breaking`)
- The JAIRF reference (`references/jairf-scoring-guide.md`) in context
- The baseline score (run `jentic-apitools score` first so the subagent has a starting point)

**Subagent task brief:**

```
You are improving an OpenAPI specification for AI-readiness.

Mode: <breaking|non-breaking>
Spec: <path>
Baseline score: <score> (Level <level>)

Loop until you cannot meaningfully improve further (score delta < 2 points or Level 4 reached):
1. Read the current spec
2. Identify the lowest-scoring JAIRF dimension from the score output
3. Apply targeted improvements for that dimension (guided by jairf-scoring-guide.md)
4. Run: jentic-apitools score <spec> --format json
5. If score improved by >= 2 points, continue. Otherwise stop.

Non-breaking mode constraints — you MUST NOT:
- Change any path, HTTP method, or operationId that already exists
- Remove or rename any existing parameter (name, in, required)
- Change any existing response status code or response schema shape
- Remove any existing field from a schema
Only ADD: descriptions, summaries, examples, tags, new operationIds (where missing),
new response codes (where missing), new schema properties marked as non-required.

Output files:
- <spec-basename>-improved.yaml — the improved spec
- <spec-basename>-overlay.yaml — OpenAPI Overlay 1.0.0 (non-breaking mode only)

Report back:
- Baseline score + level
- Final score + level
- Number of improvement iterations
- Summary of changes made by dimension
- Output file paths
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
- Run a linter (`spectral lint`, `redocly lint`) and fix errors
- Resolve broken `$ref` references
- Fix impossible schema constraints (`minimum > maximum`, etc.)

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
| Need baseline score for a spec | `jentic-apitools score <file> --format json` |
| Score is low but unclear why | Check per-dimension breakdown; lowest dimension = highest priority |
| FC < 40 | Fix structural/lint issues before anything else — gating rule |
| User says "improve this API" | Ask breaking vs non-breaking before spawning subagent |
| Non-breaking improvement | Subagent loop + output improved spec + overlay |
| Breaking improvement | Subagent loop + output improved spec only |
| Need to explain a score to a stakeholder | Load `references/jairf-scoring-guide.md` for the full framework |
| Spec has hardcoded credentials | Must remove — SEC hard-capped at 20 until fixed |
| Want to track improvement over time | Save JSON output with `--output` and compare across runs |
