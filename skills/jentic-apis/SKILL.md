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

Install `jentic-apitools`:

```bash
pip install jentic-apitools
# or from source:
pip install -e /path/to/jentic-apitools/packages/score \
            -e /path/to/jentic-apitools/packages/analyze \
            -e /path/to/jentic-apitools/packages/common \
            -e /path/to/jentic-apitools/packages/cli
```

Verify:
```bash
jentic-apitools --version
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

1. **Score** — get baseline + dimension breakdown
2. **Identify** — find the lowest-scoring dimensions
3. **Fix** — apply targeted improvements (see JAIRF guide below)
4. **Re-score** — verify improvement

### Quick Wins by Dimension

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
| Need to explain a score to a stakeholder | Load `references/jairf-scoring-guide.md` for the full framework |
| Spec has hardcoded credentials | Must remove — SEC hard-capped at 20 until fixed |
| Want to track improvement over time | Save JSON output with `--output` and compare across runs |
