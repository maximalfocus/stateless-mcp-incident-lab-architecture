# ADR-0003: ECS Fargate and ALB for Streamable HTTP

Status: Proposed

## Context

The selected protocol envelope includes request-scoped SSE progress and disconnect cancellation as well as horizontal replica routing.

## Decision

Deploy each server realization as at least two ECS Fargate tasks behind an ALB; use Nginx and containers for the corresponding local topology.

## Consequences

The topology preserves ordinary HTTP streaming behavior and replica visibility but costs more than a minimal Lambda deployment and needs explicit proxy-buffering verification.

## Related

- [PRD — Deployment](../../stateless-mcp-incident-lab-prd/PRD.md)
- [PLAN-001 — Approach alternative 4](../../stateless-mcp-incident-lab-prd/PLAN-001-stateless-core.md)
- [ADR-0004 — Ephemeral unauthenticated core lab](0004-ephemeral-unauthenticated-core-lab.md)
