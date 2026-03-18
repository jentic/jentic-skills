#!/usr/bin/env python3
"""
score_spec.py — Score an OpenAPI spec using the JAIRF framework via jentic-apitools.

Usage:
  ~/.jentic/venv/bin/python score_spec.py <path-to-spec> [--json] [--no-details]

Output:
  JSON scorecard to stdout (log lines suppressed).
  Exit code 0 on success, 1 on error.

NOTE: This script uses jentic-apitools internal pipeline APIs directly because
the jentic-apitools CLI (jentic-apitools score) is not yet wired up.
This script should be replaced by the CLI once it is implemented.
"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path-to-spec> [--json] [--no-details]", file=sys.stderr)
        sys.exit(1)

    spec_path = sys.argv[1]
    output_json = "--json" in sys.argv
    no_details = "--no-details" in sys.argv

    if not Path(spec_path).exists():
        print(f"Error: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    # Suppress all logging from jentic-apitools
    logging.disable(logging.CRITICAL)

    from jentic.apitools.common.models import (
        OASJsonRequest,
        OASProcessConfiguration,
        OASRequestMeta,
        SpecSourceUrl,
    )
    from jentic.apitools.pipelines.pipelines import score_openapi

    file_uri = Path(spec_path).resolve().as_uri()
    output_dir = tempfile.mkdtemp(prefix="jentic-score-")

    oas_request = OASJsonRequest(
        spec=SpecSourceUrl(kind="url", url=file_uri),
        meta=OASRequestMeta(
            label=Path(spec_path).stem,
            output_dir=output_dir,
            oas_process_configuration=OASProcessConfiguration(
                include_diagnostics_in_score=True,
                skip_bundle=True,
            ),
        ),
    )

    result = score_openapi(oas_request, spec_url=file_uri)

    if not result.success:
        print(f"Error: {result.error_message}", file=sys.stderr)
        sys.exit(1)

    # Find scorecard JSON in output dir (skip NDJSON log lines, find scorecard object)
    scorecard = None
    for root, dirs, files in os.walk(output_dir):
        for fname in files:
            if "score" in fname.lower() and fname.endswith(".json"):
                fpath = os.path.join(root, fname)
                with open(fpath) as f:
                    content = f.read()
                # May be NDJSON — find the scorecard object (not a log line)
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if "level" not in obj and ("summary" in obj or "details" in obj):
                            scorecard = obj
                            break
                    except Exception:
                        pass
                if scorecard:
                    break
        if scorecard:
            break

    if not scorecard:
        print(f"Error: no scorecard found in output dir: {output_dir}", file=sys.stderr)
        sys.exit(1)

    # Strip diagnostics from output (too verbose unless explicitly requested)
    scorecard.pop("diagnostics", None)
    if no_details and "details" in scorecard:
        del scorecard["details"]

    if output_json or True:  # Always JSON output for now
        print(json.dumps(scorecard, indent=2, default=str))
    else:
        # Human-readable summary
        s = scorecard.get("summary", {})
        print(f"\n{'='*50}")
        print(f"  {scorecard.get('apiMetadata', {}).get('name', 'API')}")
        print(f"{'='*50}")
        print(f"  Score:  {s.get('score', '?'):.1f}  |  Level: {s.get('level', '?')}  |  Grade: {s.get('grade', '?')}")
        print(f"\n  Dimensions:")
        for d in s.get("dimensions", []):
            bar = "█" * int(d["score"] / 5)
            print(f"    {d['kind']:6s} {d['score']:5.1f}  {d['grade']:3s}  {bar}")
        print()


if __name__ == "__main__":
    main()
