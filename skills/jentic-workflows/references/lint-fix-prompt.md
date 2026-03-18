# Arazzo Lint Fix

The Arazzo YAML you generated has Spectral lint errors. Fix them following the rules below.

## What You May Fix

These are **structural/schema issues** that Spectral catches — fix them using information from your execution:

- Missing required fields (e.g., missing `in` on a parameter, missing `condition` on successCriteria)
- Invalid field values (e.g., `in` must be one of: path, query, header, cookie, body)
- Invalid runtime expressions (e.g., malformed `$response.body#/...` syntax)
- Schema violations (e.g., wrong types, missing `reference` properties on reusable objects)
- Incorrect YAML structure (e.g., wrong nesting, missing list items)

## Constraints

- **Use only observed operationIds** from execution
- **Use only observed source URLs** from API responses or tool calls
- **Use only observed extraction paths** from actual API responses
- **Use only observed parameters** that were part of the executed steps
- **Preserve the existing step set** from the execution
- **Retain UNKNOWN markers** unless you have actual evidence from the execution to replace them — if a field was marked UNKNOWN and you still don't have the information, keep it as UNKNOWN
- **Stay within unix-tools capabilities** for computation steps — if the original document omitted a step for this reason, do not reintroduce it
- **Leave authentication to the platform** — the Jentic platform handles auth at runtime
- **Mark gaps honestly** — if fixing an error requires information you don't have, leave a comment explaining what's needed

## Evidence-Only Principle

Every value in the corrected Arazzo must come from one of these sources:

1. **Execution trace**: operationIds, parameters, response structures you observed during Phase 1-2
2. **Arazzo spec rules**: structural requirements (field names, types, required properties)
3. **The original document**: values that were already correct

If a lint error cannot be fixed without inventing information, mark the field as `UNKNOWN: <what is needed>` and move on.

## Output Format

Output the **complete corrected Arazzo YAML** in a ```generated_arazzo fenced code block. Do NOT output just the changed parts — output the full document.

---

## Lint Errors

{LINT_ERRORS}
