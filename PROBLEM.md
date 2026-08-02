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
3. README status and pinning rows agree with ADR files.
4. Diagrams and rules are empty until a citing conformance or acceptance round owns them.
5. No ADR contradicts `../stateless-mcp-incident-lab-prd/PRD.md` or `PLAN-001-stateless-core.md`.
6. Accepted ADRs are append-only and all boundary rules parse with a real YAML loader.

## Verification

```bash
python3 scripts/verify-architecture.py
git diff --check
git status --short
```

The verifier pins the four-file ADR set, required sections and Proposed statuses, README parity, sibling-source links, empty diagram/rule directories, wrapper/wikilink absence, and reconciliation with the sibling PLAN. Later reviews extend the gate for rendered diagrams, YAML parsing, and conformance citation closure.

## Residuals

- ADR decisions remain Proposed until citing conformance rounds promote them.
- Deployment diagrams and implementation boundary YAML do not exist yet by design.
