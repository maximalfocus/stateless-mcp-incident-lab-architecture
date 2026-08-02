#!/usr/bin/env python3
"""Structural and sibling-consistency gate for accepted architecture contracts."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PRD = ROOT.parent / "stateless-mcp-incident-lab-prd"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing file: {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
        return ""
    return path.read_text(encoding="utf-8")


def section_bodies(body: str, heading: str) -> list[str]:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    matches = list(pattern.finditer(body))
    result: list[str] = []
    for match in matches:
        tail = body[match.end() :]
        next_heading = re.search(r"^## ", tail, re.MULTILINE)
        result.append(tail[: next_heading.start() if next_heading else len(tail)].strip())
    return result


expected = {
    "0001-independent-raw-sdk-realizations.md",
    "0002-dynamodb-explicit-application-state.md",
    "0003-fargate-alb-streamable-http.md",
    "0004-ephemeral-unauthenticated-core-lab.md",
}
adr_dir = ROOT / "adr"
actual = {p.name for p in adr_dir.glob("*.md")} if adr_dir.is_dir() else set()
if actual != expected:
    fail(f"ADR set differs: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")

required_sections = ["Context", "Decision", "Consequences", "Related"]
for path in sorted(adr_dir.glob("*.md")):
    body = read(path)
    statuses = re.findall(r"^Status:\s*(\S.*)$", body, re.MULTILINE)
    if statuses != ["Accepted"]:
        fail(f"{path.name}: expected exactly one Accepted status, found {statuses}")

    # Once an Accepted version exists in history, its bytes are immutable.
    try:
        commits = subprocess.check_output(
            ["git", "log", "--reverse", "-SStatus: Accepted", "--format=%H", "--", str(path.relative_to(ROOT))],
            cwd=ROOT,
            text=True,
        ).splitlines()
        if commits:
            accepted = subprocess.check_output(
                ["git", "show", f"{commits[0]}:{path.relative_to(ROOT)}"],
                cwd=ROOT,
                text=True,
            )
            if body != accepted:
                fail(f"{path.name}: Accepted ADR differs from its first accepted version; supersede it instead")
    except (OSError, subprocess.CalledProcessError) as exc:
        fail(f"{path.name}: cannot verify Accepted ADR history: {exc}")
    for heading in required_sections:
        bodies = section_bodies(body, heading)
        if len(bodies) != 1 or not bodies[0]:
            fail(f"{path.name}: expected one non-empty ## {heading} section")
    related = section_bodies(body, "Related")
    if related:
        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", related[0])
        if not any(target.endswith("stateless-mcp-incident-lab-prd/PRD.md") for target in links):
            fail(f"{path.name}: Related lacks sibling PRD link")
        if not any(target.endswith("stateless-mcp-incident-lab-prd/PLAN-001-stateless-core.md") for target in links):
            fail(f"{path.name}: Related lacks sibling PLAN link")

readme = read(ROOT / "README.md")
row_re = re.compile(r"^\| \[ADR-([0-9]{4})\]\(adr/([^)]+)\) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", re.MULTILINE)
rows = row_re.findall(readme)
if len(rows) != 4:
    fail(f"README must contain exactly four parseable ADR rows, found {len(rows)}")
row_map = {number: (filename, status.strip(), decision.strip(), pinned.strip()) for number, filename, status, decision, pinned in rows}
if len(row_map) != len(rows):
    fail("README contains duplicate ADR rows")
for name in sorted(expected):
    number = name[:4]
    row = row_map.get(number)
    if row is None:
        fail(f"README missing ADR-{number}")
        continue
    filename, status, _decision, pinned = row
    if filename != name or status != "Accepted":
        fail(f"README mismatch for ADR-{number}: file={filename!r} status={status!r}")
    if not re.fullmatch(r"`ARCH-[0-9]{3}`(?: through |–)`ARCH-[0-9]{3}`|`ARCH-[0-9]{3}`", pinned):
        fail(f"README ADR-{number} Pinned by must name one or more ARCH spec IDs")
if "Accepted ADRs are append-only" not in readme:
    fail("README does not declare the Accepted-ADR append-only lifecycle")

diagrams = ROOT / "diagrams"
if not diagrams.is_dir():
    fail("missing directory: diagrams/")
elif {str(path.relative_to(diagrams)) for path in diagrams.rglob("*")} != {".gitkeep"}:
    fail("diagrams/ must remain empty until deployed acceptance authors a verified topology")

rules = ROOT / "rules"
expected_rules = {"typescript-raw-boundaries.yaml", "typescript-sdk-boundaries.yaml"}
actual_rules = {path.name for path in rules.glob("*.yaml")} if rules.is_dir() else set()
if actual_rules != expected_rules:
    fail(f"boundary rule set differs: missing={sorted(expected_rules-actual_rules)} extra={sorted(actual_rules-expected_rules)}")
common_deny = [
    {"id": "domain-to-application", "from_glob": "src/domain/**/*", "import_pattern": "src/application/**"},
    {"id": "domain-to-adapters", "from_glob": "src/domain/**/*", "import_pattern": "src/adapters/**"},
    {"id": "domain-to-frameworks", "from_glob": "src/domain/**/*", "import_pattern": "@modelcontextprotocol/sdk|node:http|@aws-sdk/.*"},
    {"id": "application-to-adapters", "from_glob": "src/application/**/*", "import_pattern": "src/adapters/**"},
    {"id": "inbound-to-outbound-adapters", "from_glob": "src/adapters/inbound/**/*", "import_pattern": "src/adapters/outbound/**"},
]
expected_boundaries = [
    {"id": "domain-public-api", "from_glob": "src/**/*", "module_pattern": "src/domain/*/", "allowed_entry": "index.ts"},
    {"id": "application-public-api", "from_glob": "src/**/*", "module_pattern": "src/application/*/", "allowed_entry": "index.ts"},
    {"id": "inbound-adapter-public-api", "from_glob": "src/**/*", "module_pattern": "src/adapters/inbound/*/", "allowed_entry": "index.ts"},
    {"id": "outbound-adapter-public-api", "from_glob": "src/**/*", "module_pattern": "src/adapters/outbound/*/", "allowed_entry": "index.ts"},
]
raw_only = {"id": "raw-sdk-dependency", "from_glob": "src/**/*", "import_pattern": "@modelcontextprotocol/sdk"}
expected_rules = {
    "typescript-raw-boundaries.yaml": {
        "version": 1, "implementation": "typescript-raw", "architecture": "hexagonal", "source_root": "src",
        "deny": common_deny + [raw_only], "boundaries": expected_boundaries,
    },
    "typescript-sdk-boundaries.yaml": {
        "version": 1, "implementation": "typescript-sdk", "architecture": "hexagonal", "source_root": "src",
        "deny": common_deny, "boundaries": expected_boundaries,
    },
}
for name in sorted(actual_rules):
    path = rules / name
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"{name}: invalid YAML: {exc}")
        continue
    if data != expected_rules[name]:
        fail(f"{name}: parsed contract differs from the exact approved boundary schema")

# Validate links and leaked harness syntax across deliverable text formats.
link_re = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
text_suffixes = {".md", ".json", ".yaml", ".yml", ".mmd", ".txt"}
for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in text_suffixes:
        continue
    body = read(path)
    if re.search(r"\[\[[^]]+\]\]", body):
        fail(f"wikilink found in {path.relative_to(ROOT)}")
    if re.search(r"^\s*</(content|invoke|parameter)>\s*$", body, re.MULTILINE):
        fail(f"wrapper tag leaked in {path.relative_to(ROOT)}")
    for target in link_re.findall(body):
        clean = target.split("#", 1)[0]
        if not clean or re.match(r"^[a-z][a-z0-9+.-]*:", clean, re.IGNORECASE):
            continue
        if not (path.parent / clean).resolve().exists():
            fail(f"broken link: {path.relative_to(ROOT)} -> {target}")

try:
    scaffold_date = subprocess.check_output(
        ["git", "log", "--reverse", "--format=%ad", "--date=short"],
        cwd=ROOT,
        text=True,
    ).splitlines()[0]
except (OSError, subprocess.CalledProcessError, IndexError) as exc:
    fail(f"cannot derive scaffold date from git history: {exc}")
    scaffold_date = ""

plan = PRD / "PLAN-001-stateless-core.md"
plan_body = read(plan)
architecture_rows = [line for line in plan_body.splitlines() if line.startswith("| Architecture |")]
if len(architecture_rows) != 1:
    fail(f"expected one Architecture repo-family row, found {len(architecture_rows)}")
elif not all(
    token in architecture_rows[0]
    for token in [
        "stateless-mcp-incident-lab-architecture",
        f"Scaffolded {scaffold_date}",
        "4 `Status: Proposed` ADR stubs",
    ]
):
    fail("sibling PLAN architecture row does not match repo, scaffold date, count, and status")

if (ROOT / "PROBLEM.md").exists():
    fail("retired peerreview control file present: PROBLEM.md")

if errors:
    print("FAIL: architecture verification")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)
print(f"PASS: architecture verification (4 Accepted ADRs, 2 boundary rule sets, scaffolded {scaffold_date})")
