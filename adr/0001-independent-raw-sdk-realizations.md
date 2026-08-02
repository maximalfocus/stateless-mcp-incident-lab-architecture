# ADR-0001: Independent raw and SDK realizations

Status: Proposed

## Context

The learning goal requires comparing MCP wire mechanics with official SDK abstractions without accidental shared implementation logic.

## Decision

Use two independent TypeScript repositories, each containing a client and server behind hexagonal boundaries, proving one shared conformance contract and four-way interoperability matrix.

## Consequences

Domain logic is intentionally reimplemented, increasing work while making behavioral divergence observable. Shared artifacts are limited to contracts, fixtures, and acceptance scenarios.

## Related

- `../../stateless-mcp-incident-lab-prd/PRD.md` — Goals and Product topology
- `../../stateless-mcp-incident-lab-prd/PLAN-001-stateless-core.md` — Approach
