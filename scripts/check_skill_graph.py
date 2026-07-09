#!/usr/bin/env python3
"""Validate the skill graph for dead links, islands, hard cycles, and uncovered stages."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "skills.json"
GRAPH = ROOT / "graphs" / "skill_graph.json"
SKILL_NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)+")


def load_json(path: Path) -> Any:
    if not path.exists():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def frontmatter(content: str) -> str:
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    return match.group(1) if match else ""


def parse_related_skills(fm: str) -> list[str]:
    match = re.search(r"related_skills:\s*\[(.*?)\]", fm)
    if not match:
        return []
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def parse_loads(content: str) -> list[str]:
    names: list[str] = []
    for line in content.splitlines():
        if "**Loads:**" not in line:
            continue
        for candidate in re.findall(r"`([^`]+)`", line):
            if candidate.startswith("scripts/"):
                continue
            names.extend(SKILL_NAME_RE.findall(candidate))
    return names


def extract_hard_edges(registry: dict[str, Any]) -> set[tuple[str, str, str]]:
    registered = {entry["name"]: entry for entry in registry["skills"]}
    edges: set[tuple[str, str, str]] = set()
    for name, entry in registered.items():
        content = (ROOT / entry["path"] / "SKILL.md").read_text(encoding="utf-8")
        for target in parse_related_skills(frontmatter(content)):
            edges.add((name, target, "metadata.related_skills"))
        for target in parse_loads(content):
            edges.add((name, target, "Loads"))
    return edges


def hard_cycle(nodes: set[str], edges: list[dict[str, str]]) -> list[str] | None:
    graph: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge["type"] == "hard":
            graph[edge["from"]].append(edge["to"])

    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in visiting:
            return stack[stack.index(node):] + [node]
        if node in visited:
            return None
        visiting.add(node)
        stack.append(node)
        for target in graph.get(node, []):
            cycle = visit(target)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in sorted(nodes):
        cycle = visit(node)
        if cycle:
            return cycle
    return None


def main() -> int:
    try:
        registry = load_json(REGISTRY)
        graph = load_json(GRAPH)
        registered = {entry["name"] for entry in registry["skills"]}
        node_ids = {node["id"] for node in graph.get("nodes", [])}
        if node_ids != registered:
            raise AssertionError(f"graph nodes do not match registry: {sorted(node_ids ^ registered)}")

        edge_rows = graph.get("edges", [])
        edge_nodes = set()
        dead = []
        for edge in edge_rows:
            source = edge.get("from")
            target = edge.get("to")
            if source not in registered or target not in registered:
                dead.append(f"{source}->{target}")
            if edge.get("type") not in {"hard", "soft"}:
                raise AssertionError(f"edge has invalid type: {edge}")
            edge_nodes.update([source, target])
        if dead:
            raise AssertionError(f"dead links: {', '.join(dead)}")

        isolated = sorted(registered - edge_nodes)
        if isolated:
            raise AssertionError(f"isolated skills: {', '.join(isolated)}")

        extracted = extract_hard_edges(registry)
        declared = {
            (edge["from"], edge["to"], edge["source"])
            for edge in edge_rows
            if edge["type"] == "hard"
        }
        missing = sorted(extracted - declared)
        stale = sorted(declared - extracted)
        if missing:
            raise AssertionError(f"hard graph edges missing from graph: {missing}")
        if stale:
            raise AssertionError(f"stale hard graph edges: {stale}")

        cycle = hard_cycle(registered, edge_rows)
        if cycle:
            raise AssertionError(f"hard dependency cycle: {' -> '.join(cycle)}")

        required = set(graph.get("required_stages", []))
        covered = {stage for node in graph["nodes"] for stage in node.get("stages", [])}
        uncovered = sorted(required - covered)
        if uncovered:
            raise AssertionError(f"uncovered stages: {', '.join(uncovered)}")

    except AssertionError as exc:
        print(f"[FAIL] {exc}")
        return 1

    print(f"[OK] Skill graph covers {len(registered)} skills, {len(edge_rows)} edges, and {len(required)} stages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
