#!/usr/bin/env python3
"""Build marketplace index, graph report, and quality dashboard data."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from run_rigorbench import run_benchmark


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "skills.json"
GRAPH = ROOT / "graphs" / "skill_graph.json"
PLATFORMS = ROOT / "platforms" / "platform_test_matrix.json"
MARKETPLACE_INDEX = ROOT / "marketplace" / "index.json"
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    if not path.exists():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT).as_posix()}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_normalized_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_output(*args: str) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    except Exception:
        return None
    return result.stdout.strip()


def git_last_updated(path: Path) -> str | None:
    rel = path.relative_to(ROOT).as_posix()
    return git_output("log", "-1", "--format=%cs", "--", rel)


def skill_last_updated(entry: dict[str, Any], path: Path) -> str | None:
    configured = entry.get("last_updated")
    if configured:
        return configured
    return git_last_updated(path)


def platform_path(template: str, entry: dict[str, Any]) -> str:
    return template.replace("<category>", entry.get("category", "meta")).replace("<name>", entry["name"])


def graph_edges_by_source(graph: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in graph.get("edges", []):
        by_source[edge["from"]].append(edge)
    return by_source


def graph_edges_by_target(graph: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in graph.get("edges", []):
        by_target[edge["to"]].append(edge)
    return by_target


def hard_cycles(nodes: set[str], graph: dict[str, Any]) -> list[list[str]]:
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in graph.get("edges", []):
        if edge.get("type") == "hard":
            adjacency[edge["from"]].append(edge["to"])

    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> None:
        if node in visiting:
            cycles.append(stack[stack.index(node):] + [node])
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for target in adjacency.get(node, []):
            visit(target)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(nodes):
        visit(node)
    return cycles


def build_mermaid(graph: dict[str, Any]) -> str:
    lines = ["```mermaid", "graph TD"]
    for node in graph.get("nodes", []):
        node_id = node["id"]
        label = node_id.replace("-", " ")
        lines.append(f'  {node_id.replace("-", "_")}["{label}"]')
    rendered_edges = set()
    for edge in graph.get("edges", []):
        source = edge["from"].replace("-", "_")
        target = edge["to"].replace("-", "_")
        label = edge.get("type", "edge")
        rendered = (source, target, label)
        if rendered in rendered_edges:
            continue
        rendered_edges.add(rendered)
        lines.append(f"  {source} -->|{label}| {target}")
    lines.append("```")
    return "\n".join(lines)


def registry_lifecycle(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "owner": entry.get("owner", "core-platform"),
        "status": entry.get("status", "active"),
        "deprecated": bool(entry.get("deprecated", False)),
        "replaced_by": entry.get("replaced_by"),
        "migration_path": entry.get("migration_path"),
    }


def build_platform_data(platforms: dict[str, Any], entry: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for platform in platforms.get("platforms", []):
        rows.append(
            {
                "id": platform["id"],
                "display_name": platform["display_name"],
                "install_path": platform_path(platform["install_path_template"], entry),
                "known_limits": platform.get("known_limits", []),
            }
        )
    return rows


def risk_level(result: dict[str, Any], lifecycle: dict[str, Any]) -> str:
    if lifecycle["deprecated"] or result.get("regressions") or result.get("failures"):
        return "high"
    if result.get("pass_rate", 0) < 1.0:
        return "medium"
    return "low"


def build_all_reports() -> dict[str, Any]:
    registry = load_json(REGISTRY)
    graph = load_json(GRAPH)
    platforms = load_json(PLATFORMS)
    benchmark = run_benchmark()
    edges_from = graph_edges_by_source(graph)
    edges_to = graph_edges_by_target(graph)
    registered = {entry["name"] for entry in registry["skills"]}
    edge_nodes = {edge["from"] for edge in graph.get("edges", [])} | {edge["to"] for edge in graph.get("edges", [])}
    node_stage_map = {node["id"]: node.get("stages", []) for node in graph.get("nodes", [])}
    covered_stages = sorted({stage for stages in node_stage_map.values() for stage in stages})
    required_stages = sorted(graph.get("required_stages", []))
    skills = []
    for entry in registry["skills"]:
        name = entry["name"]
        result = benchmark["results"][name]
        lifecycle = registry_lifecycle(entry)
        dependencies = sorted({edge["to"] for edge in edges_from.get(name, []) if edge.get("type") == "hard"})
        soft_dependencies = sorted({edge["to"] for edge in edges_from.get(name, []) if edge.get("type") == "soft"})
        skill_file = ROOT / entry["path"] / "SKILL.md"
        row = {
            "name": name,
            "version": entry["version"],
            "path": entry["path"],
            "type": entry.get("type"),
            "category": entry.get("category"),
            "summary": entry.get("summary"),
            **lifecycle,
            "dependencies": dependencies,
            "soft_dependencies": soft_dependencies,
            "dependents": sorted({edge["from"] for edge in edges_to.get(name, [])}),
            "platforms": build_platform_data(platforms, entry),
            "stages": node_stage_map.get(name, []),
            "quality": {
                "passed": result["passed"],
                "total": result["total"],
                "pass_rate": result["pass_rate"],
                "score": round(result["pass_rate"] * 100, 2),
                "case_types": result["case_types"],
                "failures": result["failures"],
                "regressions": result.get("regressions", []),
            },
            "last_updated": skill_last_updated(entry, skill_file),
        }
        row["risk_level"] = risk_level(result, lifecycle)
        skills.append(row)

    average_pass_rate = round(sum(skill["quality"]["pass_rate"] for skill in skills) / len(skills), 4)
    regression_count = sum(len(skill["quality"].get("regressions", [])) for skill in skills)
    high_risk = sorted(skill["name"] for skill in skills if skill["risk_level"] == "high")
    stale = sorted(skill["name"] for skill in skills if not skill.get("last_updated"))

    marketplace_index = {
        "schema_version": 1,
        "kind": "our-skills-marketplace-index",
        "project": registry["project"],
        "version": registry["version"],
        "release": registry["release_policy"]["current_release"],
        "source_registry": "skills.json",
        "source_registry_sha256": sha256_normalized_text(REGISTRY),
        "platforms": platforms["platforms"],
        "skills": skills,
    }

    graph_report = {
        "schema_version": 1,
        "kind": "our-skills-skill-graph-report",
        "version": registry["version"],
        "node_count": len(registered),
        "edge_count": len(graph.get("edges", [])),
        "isolated_skills": sorted(registered - edge_nodes),
        "hard_cycles": hard_cycles(registered, graph),
        "stage_coverage": {
            "required": required_stages,
            "covered": covered_stages,
            "missing": sorted(set(required_stages) - set(covered_stages)),
        },
        "nodes": [
            {
                "id": skill["name"],
                "stages": skill["stages"],
                "dependencies": skill["dependencies"],
                "dependents": skill["dependents"],
                "risk_level": skill["risk_level"],
            }
            for skill in skills
        ],
        "edges": graph.get("edges", []),
        "mermaid": build_mermaid(graph),
    }

    quality_dashboard = {
        "schema_version": 1,
        "kind": "our-skills-quality-dashboard",
        "version": registry["version"],
        "release": registry["release_policy"]["current_release"],
        "summary": {
            "skill_count": len(skills),
            "average_pass_rate": average_pass_rate,
            "regression_count": regression_count,
            "high_risk_skills": high_risk,
            "stale_skills": stale,
        },
        "skills": [
            {
                "name": skill["name"],
                "owner": skill["owner"],
                "status": skill["status"],
                "deprecated": skill["deprecated"],
                "replaced_by": skill["replaced_by"],
                "migration_path": skill["migration_path"],
                "pass_rate": skill["quality"]["pass_rate"],
                "passed": skill["quality"]["passed"],
                "total": skill["quality"]["total"],
                "regressions": skill["quality"]["regressions"],
                "last_updated": skill["last_updated"],
                "risk_level": skill["risk_level"],
            }
            for skill in skills
        ],
    }

    return {
        "marketplace_index": marketplace_index,
        "graph_report": graph_report,
        "quality_dashboard": quality_dashboard,
    }


def quality_markdown(dashboard: dict[str, Any]) -> str:
    lines = [
        f"# Quality Dashboard: {dashboard['release']}",
        "",
        f"- Skills: {dashboard['summary']['skill_count']}",
        f"- Average pass rate: {dashboard['summary']['average_pass_rate']:.2f}",
        f"- Regression count: {dashboard['summary']['regression_count']}",
        f"- High-risk skills: {', '.join(dashboard['summary']['high_risk_skills']) or 'none'}",
        "",
        "| Skill | Owner | Status | Pass Rate | Regressions | Last Updated | Risk |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for skill in dashboard["skills"]:
        lines.append(
            "| {name} | {owner} | {status} | {pass_rate:.2f} | {regressions} | {last_updated} | {risk_level} |".format(
                name=skill["name"],
                owner=skill["owner"],
                status=skill["status"],
                pass_rate=skill["pass_rate"],
                regressions=len(skill["regressions"]),
                last_updated=skill["last_updated"] or "unknown",
                risk_level=skill["risk_level"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def graph_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Skill Graph Report: v{report['version']}",
        "",
        f"- Nodes: {report['node_count']}",
        f"- Edges: {report['edge_count']}",
        f"- Isolated skills: {', '.join(report['isolated_skills']) or 'none'}",
        f"- Hard cycles: {len(report['hard_cycles'])}",
        f"- Missing stages: {', '.join(report['stage_coverage']['missing']) or 'none'}",
        "",
        report["mermaid"],
        "",
        "| Skill | Stages | Dependencies | Dependents | Risk |",
        "|---|---|---|---|---|",
    ]
    for node in report["nodes"]:
        lines.append(
            "| {id} | {stages} | {dependencies} | {dependents} | {risk_level} |".format(
                id=node["id"],
                stages=", ".join(node["stages"]) or "none",
                dependencies=", ".join(node["dependencies"]) or "none",
                dependents=", ".join(node["dependents"]) or "none",
                risk_level=node["risk_level"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def report_outputs() -> dict[Path, str]:
    reports = build_all_reports()
    outputs: dict[Path, str] = {}
    outputs[MARKETPLACE_INDEX] = json.dumps(reports["marketplace_index"], indent=2, ensure_ascii=False) + "\n"
    outputs[REPORTS / "quality-dashboard.json"] = json.dumps(reports["quality_dashboard"], indent=2, ensure_ascii=False) + "\n"
    outputs[REPORTS / "quality-dashboard.md"] = quality_markdown(reports["quality_dashboard"])
    outputs[REPORTS / "skill-graph-report.json"] = json.dumps(reports["graph_report"], indent=2, ensure_ascii=False) + "\n"
    outputs[REPORTS / "skill-graph-report.md"] = graph_markdown(reports["graph_report"])
    return outputs


def write_reports() -> list[Path]:
    paths = []
    for path, content in report_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def check_reports() -> list[str]:
    mismatches = []
    for path, expected in report_outputs().items():
        if not path.exists():
            mismatches.append(f"missing {path.relative_to(ROOT).as_posix()}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            mismatches.append(f"stale {path.relative_to(ROOT).as_posix()}")
    return mismatches


def write_release_reports(output_dir: Path, release: str) -> list[Path]:
    reports = build_all_reports()
    sidecars = {
        output_dir / f"our-skills-{release}.marketplace-index.json": reports["marketplace_index"],
        output_dir / f"our-skills-{release}.quality-dashboard.json": reports["quality_dashboard"],
        output_dir / f"our-skills-{release}.skill-graph-report.json": reports["graph_report"],
    }
    paths = []
    for path, data in sidecars.items():
        write_json(path, data)
        paths.append(path)
    return paths
