# Arazzo Semantic Fix

The Arazzo YAML you generated passed structural lint but has **semantic issues** — problems with the workflow's logic, completeness, or correctness relative to the user's goal.

## What You May Do

These are **logic/completeness issues**. Fix them using information from your earlier API discovery:

- **Add `onSuccess: [{name: done, type: end}]`** to steps that have `onFailure` goto but no `onSuccess` handler (prevents sequential fall-through)
- **Add unix-tools steps** (jq, awk, date, sed, base64) for missing transforms, formatting, comparisons, or arithmetic
- **Replace hardcoded dates** with `dateNow` + `awk` + `dateParse` steps that compute the value at runtime
- **Add pagination** via the drain-queue pattern (fetch page, check hasMore, goto loop)
- **Fix string vs numeric comparisons** by adding an `awk` step for numeric comparison
- **Format array output** for human readability using `jq` before embedding in messages
- **Fix malformed interpolation**: Replace `${...}` with `{...}` — dollar-brace is not valid Arazzo expression syntax

## Constraints

- **Use only discovered operationIds** from API search/load
- **Keep the existing API vendor** — if the workflow uses the wrong vendor's API and the correct one is not available, this cannot be fixed here
- **Preserve all existing steps** in the workflow
- **Leave authentication to the platform** — the Jentic platform handles auth at runtime
- **Retain UNKNOWN markers** unless you have actual evidence to replace them with
- **Stay within unix-tools capabilities** for any added computation steps

## Evidence-Only Principle

Every value in the corrected Arazzo must come from:

1. **Your earlier discovery**: operationIds, parameters, response schemas you saw during API search/load
2. **Arazzo spec rules**: structural requirements (onSuccess/onFailure semantics, goto targets)
3. **The original document**: values that were already correct

## Output Format

Output the **complete corrected Arazzo YAML** inside a ```generated_arazzo fenced code block. Do NOT output just the changed parts — output the full document.

---

## Semantic Issues

{SEMANTIC_ISSUES}
