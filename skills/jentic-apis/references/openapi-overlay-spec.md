# OpenAPI Overlay Specification v1.0.0

**Version:** 1.0.0  
**Released:** 2024-10-17  
**Source:** https://spec.openapis.org/overlay/v1.0.0  
**License:** Apache 2.0

---

## Introduction

The Overlay Specification defines a document format for information that augments an existing OpenAPI description yet remains separate from the OpenAPI description's source document(s).

The main purpose is to provide a way to repeatably apply transformations to one or many OpenAPI descriptions. Use cases include:
- Updating descriptions
- Adding metadata to be consumed by another tool
- Removing certain elements before sharing with partners

An Overlay is a JSON or YAML structure containing an ordered list of **Action Objects** applied to the target document. Each Action Object has a `target` (JSONPath expression) and a modifier type (`update` or `remove`).

---

## Schema

### Overlay Object (root)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `overlay` | string | ✅ | MUST be the version number of the Overlay Specification (e.g. `"1.0.0"`) |
| `info` | Info Object | ✅ | Metadata about the overlay |
| `extends` | string | — | URI reference to the target OpenAPI document this overlay applies to |
| `actions` | [Action Object] | ✅ | Ordered list of actions. MUST contain at least one value. |

Actions are applied in sequential order. Later actions override earlier ones.

### Info Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ | Human-readable description of the overlay's purpose |
| `version` | string | ✅ | Version identifier for the overlay document |

### Action Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target` | string | ✅ | JSONPath expression selecting nodes in the target document |
| `description` | string | — | Human-readable description of the action |
| `update` | Any | — | Object to merge into the selected node(s), or value to append if target is array |
| `remove` | boolean | — | If true, the selected node is removed. Default: false |

**Important:** The result of the `target` JSONPath expression MUST be zero or more objects or arrays (not primitives). To update a primitive property, select the **containing object** and include the property in `update`.

---

## Examples

### Structured overlay (mirror document structure)

```yaml
overlay: 1.0.0
info:
  title: Structured Overlay
  version: 1.0.0
actions:
  - target: '$'
    update:
      info:
        x-overlay-applied: structured-overlay
      paths:
        '/':
          summary: 'The root resource'
          get:
            summary: 'Retrieve the root resource'
            x-rate-limit: 100
        '/pets':
          get:
            summary: 'Retrieve a list of pets'
            x-rate-limit: 100
```

### Targeted overlay (precise updates)

```yaml
overlay: 1.0.0
info:
  title: Targeted Overlay
  version: 1.0.0
actions:
  - target: $.paths['/foo'].get
    update:
      description: This is the new description
  - target: $.paths['/bar'].get
    update:
      description: This is the updated description
  - target: $.paths['/bar']
    update:
      post:
        description: Updated description of a child object
        x-safe: false
```

### Wildcard overlay (update many nodes at once)

```yaml
overlay: 1.0.0
info:
  title: Update many objects at once
  version: 1.0.0
actions:
  - target: $.paths.*.get
    update:
      x-safe: true
  - target: $.paths.*.get.parameters[?@.name=='filter' && @.in=='query']
    update:
      schema:
        $ref: '/components/schemas/filterSchema'
```

### Array modification (add/remove elements)

```yaml
# Add an array element
overlay: 1.0.0
info:
  title: Add an array element
  version: 1.0.0
actions:
  - target: $.paths.*.get.parameters
    update:
      name: newParam
      in: query

# Remove an array element
overlay: 1.0.0
info:
  title: Remove an array element
  version: 1.0.0
actions:
  - target: $.paths.*.get.parameters[?@.name == 'dummy']
    remove: true
```

### Pointing at a specific target document

```yaml
overlay: 1.0.0
info:
  title: Overlay for My API
  version: 1.0.0
extends: './openapi.yaml'   # relative path
actions:
  - target: $.paths['/users'].get
    update:
      summary: List all users
```

---

## Key Rules

1. **Sequential application** — actions are applied in order; each action sees the result of the previous
2. **Recursive merge** — `update` properties are recursively merged; new properties are added, existing ones overwritten
3. **Array append** — if the target is an array, `update` value is appended (not merged)
4. **Primitive values** — cannot update a primitive directly; select its parent object and set the property via `update`
5. **Primitive array items** — cannot replace or remove individual primitive array items; replace the whole array
6. **`remove: true`** — removes the selected node from its containing map or array
7. **`extends`** is optional — if omitted, tooling decides which document to apply the overlay to

---

## JSONPath Quick Reference (RFC 9535)

| Expression | Selects |
|-----------|---------|
| `$` | Root of the document |
| `$.paths` | The `paths` object |
| `$.paths['/users']` | A specific path item |
| `$.paths['/users'].get` | The GET operation on `/users` |
| `$.paths.*.get` | All GET operations |
| `$.paths.*.*.parameters` | All parameters on all operations |
| `$.paths.*.get.parameters[?@.name=='q']` | Parameter named `q` on all GET operations |
| `$.components.schemas.*` | All schemas in components |

---

## Common AI-Readiness Improvement Patterns

These are the most common overlay actions when improving OpenAPI specs for JAIRF scoring:

```yaml
overlay: 1.0.0
info:
  title: AI-readiness improvements
  version: 1.0.0
extends: ./openapi.yaml
actions:
  # Add summary to an operation
  - target: $.paths['/users'].get
    update:
      summary: List all users in the organisation

  # Add description to a parameter
  - target: $.paths['/users'].get.parameters[?@.name=='limit']
    update:
      description: Maximum number of users to return. Defaults to 20, maximum 100.

  # Add operationId
  - target: $.paths['/users'].get
    update:
      operationId: listUsers

  # Add example to a response schema property (via containing object)
  - target: $.components.schemas.User.properties.email
    update:
      description: The user's email address
      example: user@example.com

  # Add a 404 response to an operation
  - target: $.paths['/users/{id}'].get
    update:
      responses:
        '404':
          description: User not found

  # Add tags to an operation
  - target: $.paths['/users'].get
    update:
      tags:
        - Users
```
