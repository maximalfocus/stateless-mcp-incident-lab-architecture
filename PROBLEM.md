# Problem charter: Stateless MCP Incident Lab architecture

## Problem

The project has two independent implementations, local and AWS deployment paths, explicit application state, and a deliberate security scope. Without standalone architecture contracts, conformance and implementation could encode incompatible assumptions or silently couple the raw and SDK realizations.

## Scope

Review ADRs, diagrams, and boundary rules against the approved sibling PRD and active PLAN. At scaffold time, only structural completeness and faithful representation of PRD-level decisions are in scope. Substantive promotion occurs lazily when `/cdd-author` creates citing goldens.

## Acceptance criteria

1. Every ADR records Status, Context, Decision, Consequences, and Related source anchors.
2. Proposed stubs do not claim downstream validation that has not occurred.
3. README status and pinning rows agree with ADR files.
4. Diagrams and rules are empty until a citing conformance or acceptance round owns them.
5. No ADR contradicts `../stateless-mcp-incident-lab-prd/PRD.md` or `PLAN-001-stateless-core.md`.
6. Accepted ADRs are append-only and all boundary rules parse with a real YAML loader.

## Verification

```bash
grep -L '^Status: \(Proposed\|Accepted\|Deprecated\|Superseded\)$' adr/*.md
grep -rnE '^[[:space:]]*</(content|invoke|parameter)>[[:space:]]*$' .
find diagrams rules -type f ! -name .gitkeep -print
```

At scaffold time all commands must produce no output. Later reviews extend the gate for diagrams, YAML parsing, and citation closure.

## Residuals

- ADR decisions remain Proposed until citing conformance rounds promote them.
- Deployment diagrams and implementation boundary YAML do not exist yet by design.
