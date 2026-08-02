#!/usr/bin/env python3
"""Mutation tests proving the architecture verifier fails closed."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
PRD = ROOT.parent / "stateless-mcp-incident-lab-prd"


def replace(path: Path, old: str, new: str) -> None:
    body = path.read_text(encoding="utf-8")
    if old not in body:
        raise AssertionError(f"mutation anchor absent in {path}: {old!r}")
    path.write_text(body.replace(old, new, 1), encoding="utf-8")


def append(path: Path, value: str) -> None:
    path.write_text(path.read_text(encoding="utf-8") + value, encoding="utf-8")


def run(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/verify-architecture.py"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def mutate(name: str, operation: Callable[[Path, Path], None]) -> None:
    with tempfile.TemporaryDirectory(prefix="architecture-mutation-") as temp:
        family = Path(temp)
        repo = family / ROOT.name
        prd = family / PRD.name
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(PRD, prd, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        operation(repo, prd)
        result = run(repo)
        if result.returncode == 0:
            raise AssertionError(f"FALSE PASS: {name}\n{result.stdout}")
        print(f"RED: {name}")


def main() -> None:
    baseline = run(ROOT)
    if baseline.returncode != 0:
        raise SystemExit(f"baseline failed:\n{baseline.stdout}")

    mutations: list[tuple[str, Callable[[Path, Path], None]]] = [
        ("ADR status", lambda r, _p: replace(r / "adr/0001-independent-raw-sdk-realizations.md", "Status: Accepted", "Status: Proposed")),
        ("Accepted ADR body", lambda r, _p: append(r / "adr/0001-independent-raw-sdk-realizations.md", "\nmutation\n")),
        ("ADR H1", lambda r, _p: replace(r / "adr/0002-dynamodb-explicit-application-state.md", "# ADR-0002", "# ADR-0099")),
        ("README pin", lambda r, _p: replace(r / "README.md", "`ARCH-005`", "`ARCH-999`")),
        ("malformed YAML", lambda r, _p: append(r / "rules/typescript-sdk-boundaries.yaml", "\n: [\n")),
        ("unknown YAML key", lambda r, _p: append(r / "rules/typescript-sdk-boundaries.yaml", "\nunknown_contract: true\n")),
        ("wrong YAML field type", lambda r, _p: replace(r / "rules/typescript-sdk-boundaries.yaml", "from_glob: src/domain/**", "from_glob: 7")),
        ("common rule drift", lambda r, _p: replace(r / "rules/typescript-sdk-boundaries.yaml", "^src/application(?:/|$)", "^src/app(?:/|$)")),
        ("raw SDK deep-import gap", lambda r, _p: replace(r / "rules/typescript-raw-boundaries.yaml", "^@modelcontextprotocol/sdk(?:/|$)", "^@modelcontextprotocol/sdk$")),
        ("extra rule artifact", lambda r, _p: (r / "rules/extra.yml").write_text("version: 1\n", encoding="utf-8")),
        ("inline opening wrapper tag", lambda r, _p: append(r / "README.md", "\nprefix " + "<" + "invoke name=\"Write\"> suffix\n")),
        ("inline namespaced wrapper tag", lambda r, _p: append(r / "requirements.txt", "\nprefix " + "<" + "/antml:parameter> suffix\n")),
        ("outer function-results wrapper", lambda r, _p: append(r / "README.md", "\n" + "<" + "function_results>\n")),
        ("pinned acceptance commit", lambda r, _p: replace(r / "scripts/verify-architecture.py", "8aacb4f73caab65cff80f69459162e6c9a066337", "0f569cc000000000000000000000000000000000")),
        ("premature diagram", lambda r, _p: (r / "diagrams/deployment.mmd").write_text("flowchart LR\n", encoding="utf-8")),
        ("stale sibling PLAN status", lambda _r, p: replace(p / "PLAN-001-stateless-core.md", "all 4 are now `Status: Accepted`", "all 4 remain Proposed")),
    ]
    for name, operation in mutations:
        mutate(name, operation)
    print(f"PASS: verifier mutation suite ({len(mutations)} red cases)")


if __name__ == "__main__":
    main()
