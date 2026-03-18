#!/usr/bin/env python3
"""
score_spec.py — Score an OpenAPI spec using the JAIRF framework via jentic-apitools.

Usage:
  ~/.jentic/venv/bin/python score_spec.py <path-to-spec> [--no-details]

Output:
  JSON scorecard to stdout. Logs suppressed.
  Exit code 0 on success, 1 on error.

NOTE: This script uses jentic-apitools internal pipeline APIs directly because
the jentic-apitools CLI is not yet wired up. Replace with CLI once available.
"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path


def run_score(spec_path, no_details, output_file):
    """Run scoring and write result JSON to output_file."""
    logging.disable(logging.CRITICAL)

    from jentic.apitools.common.models import (
        OASJsonRequest,
        OASProcessConfiguration,
        OASRequestMeta,
        SpecSourceUrl,
    )
    from jentic.apitools.pipelines.pipelines import score_openapi

    file_uri = Path(spec_path).resolve().as_uri()
    work_dir = tempfile.mkdtemp(prefix="jentic-score-")

    oas_request = OASJsonRequest(
        spec=SpecSourceUrl(kind="url", url=file_uri),
        meta=OASRequestMeta(
            label=Path(spec_path).stem,
            output_dir=work_dir,
            oas_process_configuration=OASProcessConfiguration(
                include_diagnostics_in_score=True,
                skip_bundle=True,
            ),
        ),
    )

    result = score_openapi(oas_request, spec_url=file_uri)

    if not result.success:
        with open(output_file, "w") as f:
            json.dump({"error": result.error_message or "scoring failed"}, f)
        return False

    # Find scorecard in work_dir
    scorecard = None
    for root, dirs, files in os.walk(work_dir):
        for fname in files:
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath) as f:
                    content = f.read().strip()
                # Single JSON
                try:
                    obj = json.loads(content)
                    if isinstance(obj, dict) and "summary" in obj and "details" in obj:
                        scorecard = obj
                        break
                except json.JSONDecodeError:
                    pass
                # NDJSON
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict) and "summary" in obj and "details" in obj:
                            scorecard = obj
                            break
                    except Exception:
                        pass
                if scorecard:
                    break
            except Exception:
                pass
        if scorecard:
            break

    if not scorecard:
        with open(output_file, "w") as f:
            json.dump({"error": f"scorecard not found in {work_dir}"}, f)
        return False

    scorecard.pop("diagnostics", None)
    if no_details:
        scorecard.pop("details", None)

    with open(output_file, "w") as f:
        json.dump(scorecard, f, indent=2, default=str)

    return True


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path-to-spec> [--no-details]", file=sys.stderr)
        sys.exit(1)

    spec_path = sys.argv[1]
    no_details = "--no-details" in sys.argv

    if not Path(spec_path).exists():
        print(f"Error: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    # Write output to a temp file, redirecting all stdout/stderr during pipeline
    output_file = tempfile.mktemp(suffix=".json", prefix="jentic-result-")

    # Redirect stdout AND stderr to /dev/null during pipeline run
    # (structlog writes JSON log lines directly to stdout; OpenClaw captures stderr to app.log)
    devnull = open(os.devnull, "w")
    old_stdout = os.dup(1)
    old_stderr = os.dup(2)
    os.dup2(devnull.fileno(), 1)
    os.dup2(devnull.fileno(), 2)

    try:
        success = run_score(spec_path, no_details, output_file)
    finally:
        os.dup2(old_stdout, 1)
        os.dup2(old_stderr, 2)
        os.close(old_stdout)
        os.close(old_stderr)
        devnull.close()

    if not success:
        with open(output_file) as f:
            err = json.load(f)
        print(f"Error: {err.get('error', 'unknown')}", file=sys.stderr)
        os.unlink(output_file)
        sys.exit(1)

    with open(output_file) as f:
        print(f.read())
    os.unlink(output_file)


if __name__ == "__main__":
    main()
