---
name: jentic-workflows
description: >
  Generate Arazzo 1.0.1 workflow YAML from a natural-language goal or agent tool trace using Jentic API discovery.
  Use when asked to: generate a workflow, create an Arazzo file, build a workflow for X,
  mine a workflow, workflow generation, build an API workflow, create a multi-step workflow,
  produce an Arazzo spec, generate API automation, mine this trace, convert tool calls to a workflow,
  turn these API calls into a workflow, extract a workflow from agent trace.
---

# jentic-workflows

Generate Arazzo 1.0.1 workflow YAML from a natural-language goal or an agent tool trace. The agent executes the full pipeline natively — no subprocesses.

## Prerequisites

Run `bash scripts/setup.sh` once to verify `arazzo-validator` is available.

---

## Inputs

The skill accepts two input modes. Determine which applies from context:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `goal` | Natural-language workflow goal | — |
| `trace` | Agent tool trace / API call log (any format) | — |
| `output_dir` | Directory for output files | `~/workspace/workflows/` |
| `slug` | Filesystem-safe identifier | Derived from goal or trace summary |

**One of `goal` or `trace` is required.** If both are provided, `trace` takes precedence and `goal` is used as a description only.

**Slug derivation:** lowercase the goal/trace summary, replace spaces and special chars with hyphens, truncate to 60 chars.

---

## Pipeline Overview

**Goal mode:**
```
Goal → [Phase 1: Decompose + Discover] → [Phase 2: Lint/Fix] → [Phase 3: Semantic] → Output
```

**Trace mode:**
```
Trace → [Phase 1: Interpret + Map] → [Phase 2: Lint/Fix] → [Phase 3: Semantic] → Output
```

Phases 2 and 3 are identical in both modes.

Set `SKILL_DIR` = the absolute path of this skill directory (`skills/jentic-workflows/`).

---

## Phase 1 (Trace mode): Interpret + Map

Use this phase when a tool trace is provided instead of a natural-language goal.

### 1.T.1 Interpret the trace

Read the trace — it may be JSON tool call logs, structured text, a narrative description of API calls made, or any other format an agent might produce. Extract:

- The sequence of API calls made (endpoint, method, key inputs, key outputs)
- The data flowing between calls (what output from call N fed into call N+1)
- The apparent goal or intent of the sequence

Write a plain-language summary of what the trace is doing. This becomes the workflow description.

### 1.T.2 Map calls to Jentic operations

For each API call in the trace:

1. If the trace includes Jentic operation IDs (`op_...`) — use them directly, skip to load
2. Otherwise — search Jentic for each call by endpoint + method + API name:
   - Query: `"<API name> <HTTP method> <path or action>"` (e.g. `"Gmail GET messages list"`)
   - Select the best matching operation
3. Load the schema for each matched operation using `load_execution_info`
4. Write findings to scratchpad (same format as goal mode — see Phase 1.4)

**If a call in the trace cannot be matched to a Jentic operation:** mark it `UNKNOWN:<description>` in the scratchpad. If it is essential to the workflow, note it as a caveat. Do not reject the whole workflow — produce what is expressible and document the gaps.

### 1.T.3 Reconstruct data flow

From the trace, identify how outputs from each call feed into subsequent calls. Map these to Arazzo `$steps.<id>.outputs.<field>` references using JSON Pointers derived from the loaded schemas.

After completing 1.T.1–1.T.3, proceed directly to **Phase 2** (generation is implicit — the trace IS the workflow plan).

---

## Phase 1 (Goal mode): Generate

### 1.1 Read system prompt

Read `{SKILL_DIR}/references/system-prompt.md` into context using the `read` tool. This is the core generation instruction set — follow it precisely throughout Phase 1.

### 1.2 Decompose the goal

Before searching, decompose the goal into discrete steps. For each step, assess:
- Is it expressible as a single API call or a simple data mapping?
- Or does it require Turing-complete logic (conditional branches, complex math, loops with variable termination)?

**If the goal is not mineable** (no APIs plausibly exist for it, OR it requires Turing-complete logic):
- Write a rejection file to `{output_dir}/{slug}.REJECTED.md` explaining why
- Do NOT produce a broken or placeholder YAML
- Report the rejection to the user clearly
- Stop here — do not proceed to Phase 2

### 1.3 Discover APIs

Use the `jentic` skill for all API discovery. Do NOT duplicate its search/load instructions here — refer to that skill.

**Search strategy:**
- Run multiple targeted `search_apis` queries — one per step in the decomposed goal
- Use specific vendor names when mentioned (e.g. "GitHub", "Slack", "SendGrid")
- Use functional queries for generic steps (e.g. "send email", "post message to channel")
- Record promising operation IDs in your scratchpad

**Load schemas:**
- For each promising operation, call `load_execution_info` with its ID
- Extract: endpoint URL, HTTP method, required parameters, request body schema, response schema
- Record all field names and JSON Pointer paths in your scratchpad
- If a field value cannot be confirmed from the schema, mark it `UNKNOWN:<description>`

### 1.4 Write scratchpad

Create `{output_dir}/{slug}.scratchpad.md` and write working notes continuously:

```markdown
# Scratchpad: {goal}

## Goal Decomposition
- Step 1: [description] — Arazzo compatible: yes/no
- Step 2: ...

## API Discovery
### Step 1: [operation name]
- Operation ID: ...
- Endpoint: ...
- Method: ...
- Key parameters: ...
- Response fields used downstream: ...

## Data Flow
- Step 1 → Step 2: {$steps.step1.outputs.field} → inputs.param

## UNKNOWN Fields
- stepId.inputs.field: UNKNOWN:could not find in schema

## UNSUPPORTED_TRANSFORM Fields
- stepId: requires string formatting/math — marked UNSUPPORTED_TRANSFORM
```

### 1.5 Generate Arazzo YAML

Using the system prompt instructions and the loaded schemas, generate the Arazzo 1.0.1 YAML document.

Output the YAML in a fenced code block using the `generated_arazzo` marker:

````
```generated_arazzo
<yaml content>
```
````

**Key rules from the system prompt:**
- Every `workflowId` must be `kebab-case`
- Every `stepId` must be `kebab-case`
- `operationId` must match exactly what was returned by `load_execution_info`
- Use `$steps.<stepId>.outputs.<field>` for cross-step references (JSON Pointer syntax)
- Mark fields you couldn't find in schemas as `UNKNOWN:<description>`
- Mark steps requiring runtime logic beyond JSON Pointer as `UNSUPPORTED_TRANSFORM`
- Do not invent API fields — only use what the schema returned

Extract the YAML from the fenced block for use in Phase 2.

---

## Phase 2: Lint / Fix Loop

**Max retries: 3**

### 2.1 Write YAML to disk

```
mkdir -p {output_dir}
write YAML to {output_dir}/{slug}.arazzo.yaml
```

### 2.2 Run the validator

```bash
arazzo-validator {output_dir}/{slug}.arazzo.yaml --format json
```

Exit code 0 = valid. Non-zero = errors. Use `--format json` for structured output when parsing errors programmatically.

### 2.3 Evaluate lint result

- **No errors:** Phase 2 passed. Proceed to Phase 3.
- **Errors present:** Read `{SKILL_DIR}/references/lint-fix-prompt.md` into context. Analyse each error. Fix the YAML. Re-write `{slug}.arazzo.yaml`. Re-run `arazzo-validator`. Repeat up to 3 times total.
- **Still failing after 3 retries:** Save best attempt. Report lint errors clearly. Skip Phase 3. Proceed to Output.

**YAML extraction:** After each fix, extract the corrected YAML from the response's fenced ` ```generated_arazzo ` block (always the last such block if multiple appear).

**YAML post-processing:** After extracting, apply these two fixes before writing to disk:
1. Replace any `${$steps`, `${$inputs`, `${$response` patterns with `{$steps`, `{$inputs`, `{$response` — the leading `$` before `{` is invalid Arazzo
2. In `sourceDescriptions` URL fields only, replace `%2F` with `/`

---

## Phase 3: Semantic Validation / Fix Loop

**Skip if:** Phase 2 failed (lint errors remain) OR the YAML contains `UNKNOWN:` fields (semantic review is unreliable when schema gaps exist).

**Max retries: 2**

### 3.1 Read semantic validation prompt

Read `{SKILL_DIR}/references/semantic-validation-prompt.md` into context.

### 3.2 Review the YAML

Following the semantic validation prompt instructions, review `{slug}.arazzo.yaml` against the original goal:

- **Logical correctness:** Does each step do what the goal requires?
- **Step sequencing:** Are steps in the right order? Are dependencies respected?
- **Data flow:** Are `$steps.<id>.outputs.<field>` references pointing to real fields from loaded schemas?
- **JSON Pointer correctness:** Are all `$response.body#/path` expressions syntactically valid and matching the response schema?
- **Coverage:** Does the workflow cover all parts of the goal?

### 3.3 Fix semantic issues

If issues found:
1. Read `{SKILL_DIR}/references/semantic-fix-prompt.md` into context
2. Fix the YAML based on the issues
3. Re-run `arazzo-validator` to confirm no lint regressions
   - If lint regresses: read `lint-fix-prompt.md`, fix lint, re-run validator — up to 2 inner cycles before continuing
4. Repeat semantic validate → fix up to 2 times total

**Unfixable categories:** If issues are categorised as `wrong-api` or `binary-transfer`, do not retry — report them as caveats in the output summary.

---

## Output

### Save final YAML

Write the final YAML to `{output_dir}/{slug}.arazzo.yaml`.

### Write result summary

Append a summary section to `{output_dir}/{slug}.scratchpad.md`:

```markdown
## Result Summary

- **Goal:** {goal}
- **Output:** {slug}.arazzo.yaml
- **Phase 1:** Complete — {N} steps, {N} APIs discovered
- **Phase 2 (Lint):** PASSED / FAILED after {N} attempts
  - Lint errors remaining: {N} (list if any)
- **Phase 3 (Semantic):** PASSED / SKIPPED / FAILED after {N} attempts
  - fitness: full / partial / none
  - precision: correct / over-executes / has-bugs
  - soundness: sound / has-risks
- **UNKNOWN fields:** {N} (list if any)
- **UNSUPPORTED_TRANSFORM steps:** {N} (list if any)
- **Caveats:** {any warnings or limitations}
```

### Report to user

Provide a brief summary:
- Path to the generated YAML
- Lint status
- Semantic status
- Any UNKNOWN fields or UNSUPPORTED_TRANSFORM steps (these need manual review)
- Any caveats

---

## UNKNOWN and UNSUPPORTED_TRANSFORM

These two markers indicate areas requiring human review before the workflow can execute:

**`UNKNOWN:<description>`** — A field value that could not be determined from API schema discovery. The workflow structure is correct but this placeholder must be replaced with a real value.

**`UNSUPPORTED_TRANSFORM`** — A step that requires runtime logic (string formatting, arithmetic, conditional branching) beyond what Arazzo's JSON Pointer expressions support natively. The workflow outlines the intent but the transform must be implemented at runtime.

Neither marker should block output — they are informational annotations in the generated YAML.

---

## Example Invocation

> "Generate a workflow that gets today's weather for London and posts it to a Slack channel"

Expected output:
```
workflows/get-todays-weather-for-london-and-post-to-sla.arazzo.yaml
workflows/get-todays-weather-for-london-and-post-to-sla.scratchpad.md
```

---

## Bundled References

| File | Purpose |
|------|---------|
| `references/system-prompt.md` | Core generation instructions + Arazzo spec (read in Phase 1) |
| `references/lint-fix-prompt.md` | Lint error analysis + fix instructions (read on lint failure) |
| `references/semantic-validation-prompt.md` | Semantic review instructions (read in Phase 3) |
| `references/semantic-fix-prompt.md` | Semantic fix instructions (read on semantic failure) |


| `references/generate-inputs-prompt.md` | Test input generation prompt (future: sandbox validation) |

---

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| `arazzo-validator` not found | Run `bash scripts/setup.sh` |
| No APIs found for goal | Goal may not be mineable — output REJECTED explanation |
| YAML has many UNKNOWN fields | Run `search_apis` with more specific queries; load more operation schemas |
| Trace call can't be matched to Jentic op | Search by endpoint + method; if still not found, mark as UNKNOWN and note caveat |
