#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "click"]
# ///
"""
jentic-mini.py — CLI client for a Jentic Mini (self-hosted) instance.

Usage:
  uv run scripts/jentic-mini.py search "send an email"
  uv run scripts/jentic-mini.py inspect GET/api.stripe.com/v1/payment_intents
  uv run scripts/jentic-mini.py execute GET/api.github.com/repos/octocat/Hello-World
  uv run scripts/jentic-mini.py --json search "create a payment"

Environment:
  JENTIC_MINI_URL      Base URL of your Jentic Mini instance (default: http://localhost:8900)
  JENTIC_MINI_API_KEY  Toolkit key (tk_...) or admin key for your instance
"""

import json
import os
import sys

import click
import httpx

BASE_URL = os.environ.get("JENTIC_MINI_URL", "http://localhost:8900").rstrip("/")
API_KEY = os.environ.get("JENTIC_MINI_API_KEY", "")

HEADERS = {"X-Jentic-API-Key": API_KEY} if API_KEY else {}


def _get(path: str, params: dict = None) -> dict:
    r = httpx.get(f"{BASE_URL}{path}", headers=HEADERS, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def _post(path: str, body: dict = None) -> dict:
    r = httpx.post(f"{BASE_URL}{path}", headers=HEADERS, json=body or {}, timeout=60)
    r.raise_for_status()
    return r.json()


@click.group()
@click.option("--json", "output_json", is_flag=True, default=False, help="Output raw JSON")
@click.pass_context
def cli(ctx, output_json):
    ctx.ensure_object(dict)
    ctx.obj["json"] = output_json


@cli.command()
@click.argument("query")
@click.option("--limit", "-n", default=10, help="Number of results")
@click.pass_context
def search(ctx, query, limit):
    """Search the catalog by natural language intent."""
    data = _get("/search", {"q": query, "n": limit})
    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return
    for item in data:
        t = item.get("type", "operation")
        id_ = item.get("id") or item.get("slug", "")
        summary = item.get("summary", "")
        score = item.get("score", 0)
        click.echo(f"[{t}] {id_}")
        click.echo(f"  {summary}")
        click.echo(f"  score: {score}  inspect: {item.get('_links', {}).get('inspect', '')}")
        click.echo()


@cli.command()
@click.argument("capability_id")
@click.pass_context
def inspect(ctx, capability_id):
    """Inspect a capability (operation or workflow) — shows schema and auth requirements."""
    data = _get(f"/inspect/{capability_id}")
    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return
    click.echo(f"ID: {data.get('id')}")
    click.echo(f"Type: {data.get('type')}")
    click.echo(f"Summary: {data.get('summary', '')}")
    click.echo()
    if "parameters" in data:
        click.echo("Parameters:")
        for p in data["parameters"]:
            req = " (required)" if p.get("required") else ""
            click.echo(f"  {p.get('in','?')}.{p['name']}{req}: {p.get('schema', {}).get('type', '?')}")
    if "auth" in data:
        click.echo("\nAuth:")
        for a in data["auth"]:
            click.echo(f"  {a.get('type')}: {a.get('instruction', '')}")
    if "broker_url" in data:
        click.echo(f"\nBroker URL: {data['broker_url']}")


@cli.command()
@click.argument("capability_id")
@click.option("--inputs", default="{}", help="JSON inputs for the operation")
@click.option("--simulate", is_flag=True, default=False, help="Simulate — don't send to upstream API")
@click.pass_context
def execute(ctx, capability_id, inputs, simulate):
    """Execute an operation or workflow via the broker."""
    # For operations, the broker URL pattern is /{upstream_host}/{path}
    # capability_id format: METHOD/host/path → broker URL: /host/path (with method as HTTP verb)
    # For workflows, use POST /{jentic_host}/workflows/{slug}
    try:
        inputs_dict = json.loads(inputs)
    except json.JSONDecodeError:
        click.echo(f"Error: --inputs must be valid JSON", err=True)
        sys.exit(1)

    # Parse capability_id to get broker URL and method
    parts = capability_id.split("/", 1)
    if len(parts) != 2:
        click.echo(f"Error: capability_id must be METHOD/host/path (e.g. GET/api.stripe.com/v1/customers)", err=True)
        sys.exit(1)

    method, rest = parts
    broker_url = f"{BASE_URL}/{rest}"

    extra_headers = {**HEADERS}
    if simulate:
        extra_headers["X-Jentic-Simulate"] = "true"

    # Split inputs into path params (used to format URL) and body/query
    # For now, pass all as query params for GET, body for POST/PUT/PATCH
    if method.upper() in ("GET", "DELETE", "HEAD"):
        r = httpx.request(method.upper(), broker_url, headers=extra_headers, params=inputs_dict, timeout=60)
    else:
        r = httpx.request(method.upper(), broker_url, headers=extra_headers, json=inputs_dict, timeout=60)

    if ctx.obj["json"]:
        try:
            click.echo(json.dumps(r.json(), indent=2))
        except Exception:
            click.echo(r.text)
        return

    click.echo(f"Status: {r.status_code}")
    try:
        click.echo(json.dumps(r.json(), indent=2))
    except Exception:
        click.echo(r.text)


@cli.command()
@click.pass_context
def apis(ctx):
    """List all registered APIs in the catalog."""
    data = _get("/apis")
    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return
    items = data if isinstance(data, list) else data.get("apis", data.get("items", []))
    for api in items:
        click.echo(f"{api.get('id', api.get('name', '?'))}: {api.get('title', api.get('summary', ''))}")


if __name__ == "__main__":
    cli(obj={})
