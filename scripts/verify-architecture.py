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


adr_contracts = {
    "0001-independent-raw-sdk-realizations.md": {
        "title": "# ADR-0001: Independent raw and SDK realizations",
        "decision": "Independent raw and SDK realizations behind one contract",
        "pinned": "`ARCH-001`–`ARCH-004`",
        "conformance": "ARCH-001 through ARCH-004",
    },
    "0002-dynamodb-explicit-application-state.md": {
        "title": "# ADR-0002: DynamoDB for explicit application state",
        "decision": "DynamoDB for explicit application state across replicas",
        "pinned": "`ARCH-005`",
        "conformance": "ARCH-005",
    },
    "0003-fargate-alb-streamable-http.md": {
        "title": "# ADR-0003: ECS Fargate and ALB for Streamable HTTP",
        "decision": "ECS Fargate and ALB for Streamable HTTP and SSE",
        "pinned": "`ARCH-006`",
        "conformance": "ARCH-006",
    },
    "0004-ephemeral-unauthenticated-core-lab.md": {
        "title": "# ADR-0004: Ephemeral unauthenticated core lab",
        "decision": "Ephemeral synthetic deployment with auth deferred",
        "pinned": "`ARCH-006`",
        "conformance": "ARCH-006",
    },
}
expected = set(adr_contracts)
adr_dir = ROOT / "adr"
actual = {p.name for p in adr_dir.glob("*.md")} if adr_dir.is_dir() else set()
if actual != expected:
    fail(f"ADR set differs: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")

required_sections = ["Context", "Decision", "Consequences", "Related"]
for path in sorted(adr_dir.glob("*.md")):
    body = read(path)
    contract = adr_contracts.get(path.name)
    headings = re.findall(r"^# .+$", body, re.MULTILINE)
    if contract and headings[:1] != [contract["title"]]:
        fail(f"{path.name}: H1 does not match its ADR number and indexed title")
    statuses = re.findall(r"^Status:\s*(\S.*)$", body, re.MULTILINE)
    if statuses != ["Accepted"]:
        fail(f"{path.name}: expected exactly one Accepted status, found {statuses}")

    # Once an Accepted version exists anywhere in history, its bytes are immutable.
    try:
        commits = subprocess.check_output(
            ["git", "log", "--all", "--follow", "--reverse", "-SStatus: Accepted", "--format=%H", "--", str(path.relative_to(ROOT))],
            cwd=ROOT,
            text=True,
        ).splitlines()
        if not commits:
            fail(f"{path.name}: Accepted ADR has no acceptance commit in git history")
        else:
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
        conformance = [value.replace("`", "") for value in re.findall(r"^- Conformance: (.+)$", related[0], re.MULTILINE)]
        if contract and conformance != [contract["conformance"]]:
            fail(f"{path.name}: Related conformance citation differs from the ADR index")

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
    filename, status, decision, pinned = row
    contract = adr_contracts[name]
    if filename != name or status != "Accepted" or decision != contract["decision"] or pinned != contract["pinned"]:
        fail(f"README contract mismatch for ADR-{number}")
if "Accepted ADRs are append-only" not in readme:
    fail("README does not declare the Accepted-ADR append-only lifecycle")

diagrams = ROOT / "diagrams"
if not diagrams.is_dir():
    fail("missing directory: diagrams/")
elif {str(path.relative_to(diagrams)) for path in diagrams.rglob("*")} != {".gitkeep"}:
    fail("diagrams/ must remain empty until deployed acceptance authors a verified topology")

rules = ROOT / "rules"
rule_names = {"typescript-raw-boundaries.yaml", "typescript-sdk-boundaries.yaml"}
actual_rule_entries = {str(path.relative_to(rules)) for path in rules.rglob("*")} if rules.is_dir() else set()
if actual_rule_entries != rule_names:
    fail(f"boundary rule set differs: expected={sorted(rule_names)} actual={sorted(actual_rule_entries)}")
matching = {
    "from_glob": "posix-glob-over-source-path",
    "import_pattern": "ecmascript-regex-search-over-canonical-import",
    "module_pattern": "posix-glob-over-source-directory",
    "canonical_import": "bare packages remain unchanged; relative and aliased imports resolve to workspace-root source paths",
}
framework_pattern = r"^(@modelcontextprotocol/sdk(?:/|$)|node:(?:http|https)$|(?:http|https)$|@aws-sdk/|aws-sdk(?:/|$))"
common_deny = [
    {"id": "domain-to-application", "from_glob": "src/domain/**/*", "import_pattern": r"^src/application(?:/|$)"},
    {"id": "domain-to-adapters", "from_glob": "src/domain/**/*", "import_pattern": r"^src/adapters(?:/|$)"},
    {"id": "domain-to-frameworks", "from_glob": "src/domain/**/*", "import_pattern": framework_pattern},
    {"id": "application-to-adapters", "from_glob": "src/application/**/*", "import_pattern": r"^src/adapters(?:/|$)"},
    {"id": "application-to-frameworks", "from_glob": "src/application/**/*", "import_pattern": framework_pattern},
    {"id": "inbound-to-outbound-adapters", "from_glob": "src/adapters/inbound/**/*", "import_pattern": r"^src/adapters/outbound(?:/|$)"},
]
expected_boundaries = [
    {"id": "domain-public-api", "from_glob": "src/**/*", "module_pattern": "src/domain/*/", "allowed_entry": "index.ts", "same_module": "allow"},
    {"id": "application-public-api", "from_glob": "src/**/*", "module_pattern": "src/application/*/", "allowed_entry": "index.ts", "same_module": "allow"},
    {"id": "inbound-adapter-public-api", "from_glob": "src/**/*", "module_pattern": "src/adapters/inbound/*/", "allowed_entry": "index.ts", "same_module": "allow"},
    {"id": "outbound-adapter-public-api", "from_glob": "src/**/*", "module_pattern": "src/adapters/outbound/*/", "allowed_entry": "index.ts", "same_module": "allow"},
]
raw_only = {"id": "raw-sdk-dependency", "from_glob": "src/**/*", "import_pattern": r"^@modelcontextprotocol/sdk(?:/|$)"}
expected_rules = {
    "typescript-raw-boundaries.yaml": {
        "schema_version": 2, "implementation": "typescript-raw", "architecture": "hexagonal", "source_root": "src",
        "matching": matching, "deny": common_deny + [raw_only], "boundaries": expected_boundaries,
    },
    "typescript-sdk-boundaries.yaml": {
        "schema_version": 2, "implementation": "typescript-sdk", "architecture": "hexagonal", "source_root": "src",
        "matching": matching, "deny": common_deny, "boundaries": expected_boundaries,
    },
}
for name in sorted(actual_rule_entries & rule_names):
    path = rules / name
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"{name}: invalid YAML: {exc}")
        continue
    if data != expected_rules[name]:
        fail(f"{name}: parsed contract differs from the exact approved boundary schema")

# Prove the regex dialect bites on deep/barrel imports without catching near misses.
pattern_cases = {
    raw_only["import_pattern"]: (["@modelcontextprotocol/sdk", "@modelcontextprotocol/sdk/server/mcp.js"], ["@modelcontextprotocol/sdk-tools"]),
    r"^src/application(?:/|$)": (["src/application", "src/application/use-cases/open.js"], ["src/application-kit"]),
    r"^src/adapters(?:/|$)": (["src/adapters", "src/adapters/inbound/mcp.js"], ["src/adapters-old"]),
    r"^src/adapters/outbound(?:/|$)": (["src/adapters/outbound", "src/adapters/outbound/dynamodb.js"], ["src/adapters/outbound-old"]),
    framework_pattern: (["node:http", "https", "@aws-sdk/client-dynamodb", "aws-sdk", "@modelcontextprotocol/sdk/client/index.js"], ["node:http2", "my-http", "@aws-sdkish/client"]),
}
for pattern, (positives, negatives) in pattern_cases.items():
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        fail(f"invalid import_pattern regex {pattern!r}: {exc}")
        continue
    for value in positives:
        if not compiled.search(value):
            fail(f"import_pattern {pattern!r} misses required import {value!r}")
    for value in negatives:
        if compiled.search(value):
            fail(f"import_pattern {pattern!r} catches near-miss import {value!r}")

# Validate links and leaked harness syntax across deliverable text files.
link_re = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
wrapper_re = re.compile(r"^\s*</?(?:(?:antml|tool):)?(?:content|invoke|parameter)(?:\s+[^>]*)?>\s*$", re.MULTILINE)
for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    try:
        body = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    if path.suffix.lower() in {".md", ".mmd", ".txt"} and re.search(r"\[\[[^]]+\]\]", body):
        fail(f"wikilink found in {path.relative_to(ROOT)}")
    if wrapper_re.search(body):
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
        "4 Proposed ADR stubs",
        "all 4 are now `Status: Accepted`",
        "`ARCH-001`–`ARCH-006` citations reserved",
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
