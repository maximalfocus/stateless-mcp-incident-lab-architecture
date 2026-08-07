#!/usr/bin/env python3
"""Structural and sibling-consistency gate for accepted architecture contracts."""
from __future__ import annotations

import json
import re
import shutil
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
        "accepted_commit": "8aacb4f73caab65cff80f69459162e6c9a066337",
        "title": "# ADR-0001: Independent raw and SDK realizations",
        "decision": "Independent raw and SDK realizations behind one contract",
        "pinned": "`ARCH-001`–`ARCH-004`",
        "conformance": "ARCH-001 through ARCH-004",
    },
    "0002-dynamodb-explicit-application-state.md": {
        "accepted_commit": "8aacb4f73caab65cff80f69459162e6c9a066337",
        "title": "# ADR-0002: DynamoDB for explicit application state",
        "decision": "DynamoDB for explicit application state across replicas",
        "pinned": "`ARCH-005`",
        "conformance": "ARCH-005",
    },
    "0003-fargate-alb-streamable-http.md": {
        "accepted_commit": "8aacb4f73caab65cff80f69459162e6c9a066337",
        "title": "# ADR-0003: ECS Fargate and ALB for Streamable HTTP",
        "decision": "ECS Fargate and ALB for Streamable HTTP and SSE",
        "pinned": "`ARCH-006`",
        "conformance": "ARCH-006",
    },
    "0004-ephemeral-unauthenticated-core-lab.md": {
        "accepted_commit": "8aacb4f73caab65cff80f69459162e6c9a066337",
        "title": "# ADR-0004: Ephemeral unauthenticated core lab",
        "decision": "Ephemeral synthetic deployment with auth deferred",
        "pinned": "`ARCH-006`",
        "conformance": "ARCH-006",
    },
    "0005-cloudfront-managed-https-origin-alb.md": {
        "accepted_commit": "4ac43996c70eeff4bac4ec8af086a8349f009813",
        "title": "# ADR-0005: CloudFront-managed HTTPS with a private origin ALB",
        "decision": "CloudFront-managed HTTPS with a private origin ALB",
        "pinned": "`INFRA-004`, `INFRA-010`",
        "conformance": "INFRA-004 and INFRA-010",
        "cited_ids": ["INFRA-004", "INFRA-010"],
        "extends": "0003-fargate-alb-streamable-http.md",
    },
    "0006-trusted-viewer-ip-waf-key.md": {
        "accepted_commit": "7866136cd3486de8bdd6412e53b98ec6390f5b9c",
        "title": "# ADR-0006: Trusted CloudFront viewer key for regional WAF rate limiting",
        "decision": "Trusted CloudFront viewer key for regional WAF rate limiting",
        "pinned": "`INFRA-005`",
        "conformance": "INFRA-005",
        "cited_ids": ["INFRA-005"],
        "supersedes": "0005-cloudfront-managed-https-origin-alb.md",
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
    if contract and headings != [contract["title"]]:
        fail(f"{path.name}: expected exactly one H1 matching its ADR number and indexed title")
    expected_status = contract.get("status", "Accepted") if contract else ""
    statuses = re.findall(r"^Status:\s*(\S.*)$", body, re.MULTILINE)
    if statuses != [expected_status]:
        fail(f"{path.name}: expected exactly one {expected_status} status, found {statuses}")

    # Accepted bytes are pinned to the reviewed promotion commit, not a mutable ref search.
    if expected_status == "Accepted":
        try:
            accepted_commit = contract["accepted_commit"] if contract else ""
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", accepted_commit, "HEAD"],
                cwd=ROOT,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            accepted = subprocess.check_output(
                ["git", "show", f"{accepted_commit}:{path.relative_to(ROOT)}"],
                cwd=ROOT,
                text=True,
            )
            if body != accepted:
                fail(f"{path.name}: Accepted ADR differs from pinned commit {accepted_commit[:12]}; supersede it instead")
        except (OSError, subprocess.CalledProcessError, KeyError) as exc:
            fail(f"{path.name}: cannot verify pinned Accepted ADR: {exc}")
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
        if contract and "extends" in contract:
            extends = re.findall(r"^- Extends: \[[^]]+\]\(([^)]+)\)$", related[0], re.MULTILINE)
            if extends != [contract["extends"]]:
                fail(f"{path.name}: expected one exact Extends relation to {contract['extends']}")
        if contract and "supersedes" in contract:
            supersedes = re.findall(r"^- Supersedes(?: [^:]+)?: \[[^]]+\]\(([^)]+)\)$", related[0], re.MULTILINE)
            if supersedes != [contract["supersedes"]]:
                fail(f"{path.name}: expected one exact Supersedes relation to {contract['supersedes']}")

conformance_root = ROOT.parent / "stateless-mcp-incident-lab-conformance" / "conformance"
if not conformance_root.is_dir():
    fail(f"missing sibling conformance suite: {conformance_root}")
else:
    disk_ids: set[str] = set()
    for test_path in conformance_root.rglob("test.json"):
        try:
            test = json.loads(test_path.read_text(encoding="utf-8"))
            if isinstance(test.get("spec_id"), str):
                disk_ids.add(test["spec_id"])
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"cannot parse sibling conformance metadata {test_path}: {exc}")
    for name, contract in adr_contracts.items():
        for spec_id in contract.get("cited_ids", []):
            if spec_id not in disk_ids:
                fail(f"{name}: cited conformance ID {spec_id} does not exist in sibling suite")

readme = read(ROOT / "README.md")
row_re = re.compile(r"^\| \[ADR-([0-9]{4})\]\(adr/([^)]+)\) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", re.MULTILINE)
rows = row_re.findall(readme)
if len(rows) != len(expected):
    fail(f"README must contain exactly {len(expected)} parseable ADR rows, found {len(rows)}")
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
    expected_status = contract.get("status", "Accepted")
    if filename != name or status != expected_status or decision != contract["decision"] or pinned != contract["pinned"]:
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
    "from_glob": "contract-prefix-globstar-subset-over-source-path",
    "import_pattern": "portable-ecmascript-python-regex-search-over-canonical-import",
    "module_pattern": "contract-prefix-globstar-subset-over-source-directory",
    "canonical_import": "bare packages remain unchanged; relative and aliased imports resolve to workspace-root TypeScript source paths",
}
framework_pattern = r"^(@modelcontextprotocol/sdk(?:/|$)|node:(?:http|https|http2|net|tls)$|(?:http|https)$|@aws-sdk/|aws-sdk(?:/|$)|undici(?:/|$)|express(?:/|$)|fastify(?:/|$))"
common_deny = [
    {"id": "domain-to-application", "from_glob": "src/domain/**", "import_pattern": r"^src/application(?:/|$)"},
    {"id": "domain-to-adapters", "from_glob": "src/domain/**", "import_pattern": r"^src/adapters(?:/|$)"},
    {"id": "domain-to-frameworks", "from_glob": "src/domain/**", "import_pattern": framework_pattern},
    {"id": "application-to-adapters", "from_glob": "src/application/**", "import_pattern": r"^src/adapters(?:/|$)"},
    {"id": "application-to-frameworks", "from_glob": "src/application/**", "import_pattern": framework_pattern},
    {"id": "inbound-to-outbound-adapters", "from_glob": "src/adapters/inbound/**", "import_pattern": r"^src/adapters/outbound(?:/|$)"},
    {"id": "outbound-to-inbound-adapters", "from_glob": "src/adapters/outbound/**", "import_pattern": r"^src/adapters/inbound(?:/|$)"},
]
expected_boundaries = [
    {"id": "domain-public-api", "from_glob": "src/**", "module_pattern": "src/domain/*/", "allowed_entry": "index.ts", "same_module": "allow"},
    {"id": "application-public-api", "from_glob": "src/**", "module_pattern": "src/application/*/", "allowed_entry": "index.ts", "same_module": "allow"},
    {"id": "inbound-adapter-public-api", "from_glob": "src/**", "module_pattern": "src/adapters/inbound/*/", "allowed_entry": "index.ts", "same_module": "allow"},
    {"id": "outbound-adapter-public-api", "from_glob": "src/**", "module_pattern": "src/adapters/outbound/*/", "allowed_entry": "index.ts", "same_module": "allow"},
]
raw_only = {"id": "raw-sdk-dependency", "from_glob": "src/**", "import_pattern": r"^@modelcontextprotocol/sdk(?:/|$)"}
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

# Prove every declared import regex bites on deep/barrel imports without catching near misses.
pattern_cases = {
    raw_only["import_pattern"]: (["@modelcontextprotocol/sdk", "@modelcontextprotocol/sdk/server/mcp.js"], ["@modelcontextprotocol/sdk-tools"]),
    r"^src/application(?:/|$)": (["src/application", "src/application/use-cases/open.ts"], ["src/application-kit"]),
    r"^src/adapters(?:/|$)": (["src/adapters", "src/adapters/inbound/mcp.ts"], ["src/adapters-old"]),
    r"^src/adapters/outbound(?:/|$)": (["src/adapters/outbound", "src/adapters/outbound/dynamodb.ts"], ["src/adapters/outbound-old"]),
    r"^src/adapters/inbound(?:/|$)": (["src/adapters/inbound", "src/adapters/inbound/mcp.ts"], ["src/adapters/inbound-old"]),
    framework_pattern: (
        ["node:http", "node:http2", "node:net", "node:tls", "https", "@aws-sdk/client-dynamodb", "aws-sdk", "undici", "express", "fastify", "@modelcontextprotocol/sdk/client/index.js"],
        ["my-http", "@aws-sdkish/client", "expressive", "fastify-tools"],
    ),
}
declared_patterns = {rule["import_pattern"] for rule in common_deny + [raw_only]}
if declared_patterns != set(pattern_cases):
    fail(f"import_pattern fixtures lack closure: unproven={sorted(declared_patterns-set(pattern_cases))} stale={sorted(set(pattern_cases)-declared_patterns)}")
node = shutil.which("node")
if node is None:
    fail("Node.js is required to verify ECMAScript regex behavior; install Node.js 18 or newer")
for pattern, (positives, negatives) in pattern_cases.items():
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        fail(f"import_pattern is invalid in Python {pattern!r}: {exc}")
        continue
    if node:
        payload = json.dumps([pattern, positives, negatives])
        script = "const [p,yes,no]=JSON.parse(process.argv[1]);const r=new RegExp(p);if(yes.some(x=>!r.test(x))||no.some(x=>r.test(x)))process.exit(1)"
        try:
            subprocess.run([node, "-e", script, payload], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            fail(f"import_pattern has different or incorrect ECMAScript behavior {pattern!r}")
    for value in positives:
        if not compiled.search(value):
            fail(f"import_pattern {pattern!r} misses required import {value!r}")
    for value in negatives:
        if compiled.search(value):
            fail(f"import_pattern {pattern!r} catches near-miss import {value!r}")

# Prove closure and decisive behavior for every path/module glob and public entry rule.
glob_cases = {
    "src/domain/**": (["src/domain/entity.ts", "src/domain/incident/internal/rule.ts"], ["src/domainish/entity.ts"]),
    "src/application/**": (["src/application/use-case.ts", "src/application/incidents/open.ts"], ["src/application-kit/open.ts"]),
    "src/adapters/inbound/**": (["src/adapters/inbound/mcp.ts", "src/adapters/inbound/http/routes.ts"], ["src/adapters/inbound-old/http.ts"]),
    "src/adapters/outbound/**": (["src/adapters/outbound/dynamodb.ts", "src/adapters/outbound/store/client.ts"], ["src/adapters/outbound-old/store.ts"]),
    "src/**": (["src/index.ts", "src/domain/incident/entity.ts"], ["test/domain/entity.ts"]),
    "src/domain/*/": (["src/domain/incident"], ["src/domain/incident/internal", "src/domainish/incident"]),
    "src/application/*/": (["src/application/incidents"], ["src/application/incidents/internal", "src/application-kit/incidents"]),
    "src/adapters/inbound/*/": (["src/adapters/inbound/mcp"], ["src/adapters/inbound/mcp/internal", "src/adapters/inbound-old/mcp"]),
    "src/adapters/outbound/*/": (["src/adapters/outbound/dynamodb"], ["src/adapters/outbound/dynamodb/internal", "src/adapters/outbound-old/dynamodb"]),
}
declared_globs = {rule["from_glob"] for rule in common_deny + [raw_only] + expected_boundaries} | {rule["module_pattern"] for rule in expected_boundaries}
if declared_globs != set(glob_cases):
    fail(f"glob fixtures lack closure: unproven={sorted(declared_globs-set(glob_cases))} stale={sorted(set(glob_cases)-declared_globs)}")
def contract_glob_matches(pattern: str, value: str) -> bool:
    """Evaluate the contract's closed gitignore-style subset without dialect drift."""
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/") + "/"
        return value.startswith(prefix) and len(value) > len(prefix)
    if pattern.endswith("/*/"):
        prefix = pattern[:-2]
        if not value.startswith(prefix):
            return False
        tail = value[len(prefix):].strip("/")
        return bool(tail) and "/" not in tail
    fail(f"unsupported contract glob: {pattern}")
    return False

for pattern, (positives, negatives) in glob_cases.items():
    for value in positives:
        if not contract_glob_matches(pattern, value):
            fail(f"glob {pattern!r} misses required path {value!r}")
    for value in negatives:
        if contract_glob_matches(pattern, value):
            fail(f"glob {pattern!r} catches near-miss path {value!r}")

def public_entry_allowed(importer: str, target: str, rule: dict[str, str]) -> bool:
    prefix = rule["module_pattern"][:-2]
    if not target.startswith(prefix):
        return True
    remainder = target[len(prefix):]
    if "/" not in remainder:
        # module_pattern governs immediate child directories; a layer-root file is
        # not a module member and carries no public-entry obligation.
        return True
    module_name = remainder.split("/", 1)[0]
    root = f"{prefix}{module_name}/"
    if rule["same_module"] == "allow" and importer.startswith(root):
        return True
    return target == root + rule["allowed_entry"]

for rule in expected_boundaries:
    # Derive the layer directory independently of the resolver's own slicing so a
    # malformed module root cannot cancel itself out across fixture and resolver.
    layer = rule["module_pattern"].replace("*/", "")
    alpha, beta = layer + "alpha/", layer + "beta/"
    external_importer = "src/other/caller.ts"
    if not public_entry_allowed(alpha + "service.ts", alpha + "entity.ts", rule):
        fail(f"{rule['id']}: same-module internal import should be allowed")
    if not public_entry_allowed(external_importer, alpha + "index.ts", rule):
        fail(f"{rule['id']}: cross-module public entry should be allowed")
    if public_entry_allowed(external_importer, alpha + "entity.ts", rule):
        fail(f"{rule['id']}: cross-module internal import should be denied")
    if public_entry_allowed(alpha + "service.ts", beta + "entity.ts", rule):
        fail(f"{rule['id']}: sibling-module internal import should be denied")
    if not public_entry_allowed(alpha + "service.ts", beta + "index.ts", rule):
        fail(f"{rule['id']}: sibling-module public entry should be allowed")
    if not public_entry_allowed(external_importer, layer + "shared.ts", rule):
        fail(f"{rule['id']}: layer-root file outside any module must not be governed")
    if contract_glob_matches(rule["module_pattern"], layer.rstrip("/") + "ish"):
        fail(f"{rule['id']}: prefix-colliding sibling directory must not match the module glob")

# Validate links and leaked harness syntax across deliverable text files.
link_re = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
wrapper_re = re.compile("<" + r"/?(?:(?:antml|tool):)?(?:function_calls|function_results|content|invoke|parameter)(?:\s+[^>]*)?/?>")
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
    if path.suffix.lower() in {".md", ".mmd", ".txt"}:
        for target in link_re.findall(body):
            clean = target.split("#", 1)[0]
            if not clean or re.match(r"^[a-z][a-z0-9+.-]*:", clean, re.IGNORECASE):
                continue
            resolved = (path.parent / clean).resolve()
            if ROOT.parent not in [resolved, *resolved.parents]:
                fail(f"link escapes project family: {path.relative_to(ROOT)} -> {target}")
            elif not resolved.exists():
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
architecture_row_pattern = re.compile(
    rf"^\| Architecture \| `stateless-mcp-incident-lab-architecture` \| Scaffolded {re.escape(scaffold_date)} with 4 Proposed ADR stubs; "
    r"all 4 are now `Status: Accepted`, .+ with `ARCH-001`–`ARCH-006` citations reserved for the active `/cdd-author` round \|$"
)
if len(architecture_rows) != 1 or not architecture_row_pattern.fullmatch(architecture_rows[0]):
    fail("sibling PLAN architecture row does not preserve repo, scaffold date, count, status, and citation reservation")

if (ROOT / "PROBLEM.md").exists():
    fail("retired peerreview control file present: PROBLEM.md")

if errors:
    print("FAIL: architecture verification")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)
accepted_count = sum(contract.get("status", "Accepted") == "Accepted" for contract in adr_contracts.values())
proposed_count = sum(contract.get("status", "Accepted") == "Proposed" for contract in adr_contracts.values())
print(f"PASS: architecture verification ({accepted_count} Accepted, {proposed_count} Proposed ADRs; 2 boundary rule sets; scaffolded {scaffold_date})")
