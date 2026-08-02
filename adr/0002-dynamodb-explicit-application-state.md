# ADR-0002: DynamoDB for explicit application state

Status: Proposed

## Context

Stateless MCP requests still need durable incident handles and at-most-once remediation effects that work across local and cloud replicas.

## Decision

Use DynamoDB Local and managed DynamoDB behind a persistence port, with opaque request-carried handles and conditional writes.

## Consequences

Local and AWS persistence semantics are intended to align, but data modeling follows DynamoDB constraints and the alignment requires deployed integration verification against the real service.

## Related

- [PRD — Domain and data model](../../stateless-mcp-incident-lab-prd/PRD.md)
- [PLAN-001 — Technology choices](../../stateless-mcp-incident-lab-prd/PLAN-001-stateless-core.md)
