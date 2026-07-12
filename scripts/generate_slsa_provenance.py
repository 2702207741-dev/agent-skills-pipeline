#!/usr/bin/env python3
"""Generate an inspectable SLSA provenance v1 statement for a release artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?$")
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://slsa.dev/provenance/v1"
DEFAULT_BUILD_TYPE = "https://slsa-framework.github.io/github-actions-buildtypes/workflow/v1"
DEFAULT_BUILDER_ID = "https://github.com/actions/runner/github-hosted"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str | None:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def validate_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed


def default_source_uri() -> str:
    server = os.environ.get("GITHUB_SERVER_URL")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if server and repository:
        return f"{server.rstrip('/')}/{repository}"
    remote = git_output("remote", "get-url", "origin")
    if remote and remote.startswith("https://"):
        return remote.removesuffix(".git")
    return "https://github.com/2702207741-dev/agent-skills-pipeline"


def default_invocation_id(source_uri: str, commit: str) -> str:
    run_id = os.environ.get("GITHUB_RUN_ID")
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
    if run_id:
        return f"{source_uri}/actions/runs/{run_id}/attempts/{attempt}"
    return f"local:{commit.lower()}"


def resource_descriptor(path: Path) -> dict[str, Any]:
    return {
        "name": path.name,
        "uri": path.resolve().as_uri(),
        "digest": {"sha256": sha256(path)},
    }


def create_statement(args: argparse.Namespace) -> dict[str, Any]:
    artifact = Path(args.artifact).resolve()
    if not artifact.is_file():
        raise FileNotFoundError(f"artifact does not exist: {artifact}")

    byproducts = [Path(value).resolve() for value in args.byproduct]
    missing = [str(path) for path in byproducts if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"byproduct does not exist: {', '.join(missing)}")

    commit = args.source_commit or os.environ.get("GITHUB_SHA") or git_output("rev-parse", "HEAD")
    if not commit or not COMMIT_RE.fullmatch(commit):
        raise ValueError("source commit must be a full 40- or 64-character Git object id")

    source_uri = args.source_uri or default_source_uri()
    if not source_uri.startswith("https://"):
        raise ValueError("source URI must use https")

    started_on = args.started_on or utc_now()
    finished_on = args.finished_on or utc_now()
    if validate_timestamp(started_on, "started-on") > validate_timestamp(finished_on, "finished-on"):
        raise ValueError("started-on must not be after finished-on")

    workflow_ref = args.workflow_ref or os.environ.get("GITHUB_WORKFLOW_REF", "local")
    invocation_id = args.invocation_id or default_invocation_id(source_uri, commit)
    git_ref = os.environ.get("GITHUB_REF", "local")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "local")

    return {
        "_type": STATEMENT_TYPE,
        "subject": [
            {
                "name": artifact.name,
                "digest": {"sha256": sha256(artifact)},
            }
        ],
        "predicateType": PREDICATE_TYPE,
        "predicate": {
            "buildDefinition": {
                "buildType": args.build_type,
                "externalParameters": {
                    "repository": source_uri,
                    "workflow": {
                        "path": args.workflow_path,
                        "ref": workflow_ref,
                    },
                    "eventName": event_name,
                    "gitRef": git_ref,
                },
                "internalParameters": {
                    "runner": {
                        "os": os.environ.get("RUNNER_OS", sys.platform),
                        "architecture": os.environ.get("RUNNER_ARCH", "unknown"),
                    },
                    "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT", "local"),
                },
                "resolvedDependencies": [
                    {
                        "uri": f"git+{source_uri}@{commit.lower()}",
                        "digest": {"gitCommit": commit.lower()},
                    }
                ],
            },
            "runDetails": {
                "builder": {"id": args.builder_id},
                "metadata": {
                    "invocationId": invocation_id,
                    "startedOn": started_on,
                    "finishedOn": finished_on,
                },
                "byproducts": [resource_descriptor(path) for path in byproducts],
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, help="Release artifact to describe")
    parser.add_argument("--output", required=True, help="Destination JSON statement")
    parser.add_argument("--source-uri", help="HTTPS source repository URI")
    parser.add_argument("--source-commit", help="Full source Git object id")
    parser.add_argument("--workflow-path", default=".github/workflows/supply-chain.yml")
    parser.add_argument("--workflow-ref", help="GitHub workflow ref used for the build")
    parser.add_argument("--invocation-id", help="Stable URL or identifier for this build invocation")
    parser.add_argument("--builder-id", default=DEFAULT_BUILDER_ID)
    parser.add_argument("--build-type", default=DEFAULT_BUILD_TYPE)
    parser.add_argument("--started-on", help="ISO-8601 build start timestamp")
    parser.add_argument("--finished-on", help="ISO-8601 build finish timestamp")
    parser.add_argument("--byproduct", action="append", default=[], help="Sidecar produced by the build")
    args = parser.parse_args()

    try:
        statement = create_statement(args)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(statement, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"[FAIL] {exc}")
        return 1

    print(f"[OK] Wrote SLSA provenance statement: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
