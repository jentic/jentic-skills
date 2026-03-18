You are given a user's goal and an Arazzo workflow YAML. Generate test input parameters for executing this workflow in a sandbox environment.

## User Goal
{GOAL}

## Arazzo Workflow
{YAML_CONTENT}

## Instructions

Examine the workflow's `inputs` section and any `parameters` on individual steps.

### Deriving Values
- If the goal mentions specific values (e.g., "Discord channel 123", "ticker AAPL"), use those exact values for the corresponding parameters
- For parameters not mentioned in the goal, generate realistic but safe test values
- For enum/constrained fields, pick a valid option from the allowed values

### By Parameter Type
- **Strings**: Use realistic values (e.g., "test-user-1", "Hello from sandbox")
- **Numbers/Integers**: Use small, reasonable values (e.g., 1, 10, 100)
- **Booleans**: Default to true unless context suggests otherwise
- **Arrays**: Provide 1-2 example items
- **Objects**: Populate required fields only

### What NOT To Generate
- Real API keys, tokens, or credentials — use placeholders like "test-key-xxx"
- Excessively large values (long strings, big arrays)
- Null values for required parameters

### Required vs Optional
- Always include all required parameters
- Include optional parameters only if they are relevant to the goal

### Output Format
Return ONLY a valid JSON object matching the workflow's expected inputs.
No markdown fencing, no explanation, no commentary.
If the workflow has no inputs, return: {}
