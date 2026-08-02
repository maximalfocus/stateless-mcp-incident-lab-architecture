#!/usr/bin/env python3
"""Structural and sibling-consistency gate for the architecture scaffold."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRD = ROOT.parent / "stateless-mcp-incident-lab-prd"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


expected = {
    "0001-independent-raw-sdk-realizations.md",
    "0002-dynamodb-explicit-application-state.md",
    "0003-fargate-alb-streamable-http.md",
    "0004-ephemeral-unauthenticated-core-lab.md",
}
actual = {p.name for p in (ROOT / "adr").glob("*.md")}
if actual != expected:
    fail(f"ADR set differs: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")

required_sections = ["Context", "Decision", "Consequences", "Related"]
for path in sorted((ROOT / "adr").glob("*.md")):
    body = path.read_text(encoding="utf-8")
    if not re.search(r"^Status: Proposed$", body, re.MULTILINE):
        fail(f"{path.name}: status is not Proposed")
    for heading in required_sections:
        if not re.search(rf"^## {heading}$", body, re.MULTILINE):
            fail(f"{path.name}: missing ## {heading}")
    for target in re.findall(r"`(\.\./\.\./stateless-mcp-incident-lab-prd/[^`]+\.md)`", body):
        if not (path.parent / target).resolve().is_file():
            fail(f"{path.name}: broken sibling source link {target}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
for name in sorted(expected):
    number = name[:4]
    if readme.count(f"(adr/{name})") != 1:
        fail(f"README must link ADR {number} exactly once")
    row = next((line for line in readme.splitlines() if f"ADR-{number}" in line), "")
    if "| Proposed |" not in row:
        fail(f"README status mismatch for ADR-{number}")

for directory in [ROOT / "diagrams", ROOT / "rules"]:
    files = {p.name for p in directory.iterdir() if p.is_file()}
    if files != {".gitkeep"}:
        fail(f"{directory.name}/ should contain only .gitkeep, found {sorted(files)}")

for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in {".md", ".json", ".yaml", ".yml"}:
        continue
    try:
        body = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    if re.search(r"^\s*</(content|invoke|parameter)>\s*$", body, re.MULTILINE):
        fail(f"wrapper tag leaked in {path.relative_to(ROOT)}")
    if re.search(r"\[\[[^]]+\]\]", body):
        fail(f"wikilink found in {path.relative_to(ROOT)}")

plan = PRD / "PLAN-001-stateless-core.md"
if not plan.is_file():
    fail("sibling PRD PLAN-001 is missing")
else:
    plan_body = plan.read_text(encoding="utf-8")
    architecture_rows = [line for line in plan_body.splitlines() if line.startswith("| Architecture |")]
    if len(architecture_rows) != 1:
        fail(f"expected one Architecture repo-family row, found {len(architecture_rows)}")
    elif "Scaffolded 2026-08-01 with 4 `Status: Proposed` ADR stubs" not in architecture_rows[0]:
        fail("sibling PLAN architecture row does not describe current scaffold")

for heading in ["Problem", "Scope", "Non-goals", "Acceptance criteria", "Verification", "Residuals"]:
    charter = (ROOT / "PROBLEM.md").read_text(encoding="utf-8")
    if not re.search(rf"^## {re.escape(heading)}$", charter, re.MULTILINE):
        fail(f"PROBLEM.md missing ## {heading}")

if errors:
    print("FAIL: architecture verification")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)
print("PASS: architecture scaffold verification (4 Proposed ADRs, sibling PLAN reconciled)")
