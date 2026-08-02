# ADR-0003: ECS Fargate and ALB for Streamable HTTP

Status: Proposed

## Context

The selected protocol envelope includes request-scoped SSE progress and disconnect cancellation as well as horizontal replica routing.

## Decision

Deploy each server realization as at least two ECS Fargate tasks behind an ALB; use Nginx and containers for the corresponding local topology.

## Consequences

The topology preserves ordinary HTTP streaming behavior and replica visibility but costs more than a minimal Lambda deployment and needs explicit proxy-buffering verification.

## Related

- `../../stateless-mcp-incident-lab-prd/PRD.md` — Deployment
- `../../stateless-mcp-incident-lab-prd/PLAN-001-stateless-core.md` — Approach alternative 4
