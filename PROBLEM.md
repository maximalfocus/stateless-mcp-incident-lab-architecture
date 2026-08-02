# Problem charter: Stateless MCP Incident Lab architecture

## Problem

The project has two independent implementations, local and AWS deployment paths, explicit application state, and a deliberate security scope. Without standalone architecture contracts, conformance and implementation could encode incompatible assumptions or silently couple the raw and SDK realizations.

## Scope

Review ADRs, diagrams, and boundary rules against the approved sibling PRD and active PLAN. At scaffold time, only structural completeness and faithful representation of PRD-level decisions are in scope. Substantive promotion occurs lazily when `/cdd-author` creates citing goldens.

## Non-goals

- Promoting any ADR before a citing conformance round exists.
- Authoring deployment diagrams, implementation boundary YAML, conformance goldens, or implementation code during scaffold review.
- Reopening user-approved product scope unless an ADR directly contradicts the sibling PRD or PLAN.

## Acceptance criteria

1. Every ADR records Status, Context, Decision, Consequences, and Related source anchors.
2. Proposed stubs do not claim downstream validation that has not occurred.
3. README has exactly one row per ADR, each status agrees with its file, and each `Pinned by` cell honestly names a future conformance round while the ADR remains Proposed.
4. Diagrams and rules are empty until a citing conformance or acceptance round owns them.
5. No ADR contradicts `../stateless-mcp-incident-lab-prd/PRD.md` or `PLAN-001-stateless-core.md`.
6. README declares the future append-only Accepted-ADR lifecycle; once Accepted ADRs or boundary rules exist, the gate must compare history and parse every YAML file with a real loader.

## Verification

```bash
python3 scripts/verify-architecture.py
git diff --check
git status --short
```

The verifier pins the four-file ADR set, non-empty required sections and exclusive Proposed statuses, exact README rows/pinning state, all Markdown links, recursively empty diagram/rule directories, wrapper/wikilink absence, the scaffold date from git history, and reconciliation with the sibling PLAN. Later reviews extend the gate for rendered diagrams, history-based append-only checks, YAML parsing, and conformance citation closure.

## Residuals

- ADR decisions remain Proposed until citing conformance rounds promote them.
- Deployment diagrams and implementation boundary YAML do not exist yet by design.
- Append-only history enforcement and YAML parsing activate only when Accepted ADRs or boundary rules exist.
