# ADR-0004: Ephemeral unauthenticated core lab

Status: Proposed

## Context

Authorization would obscure the stateless-core learning objective, but form elicitation normally requires authenticated client and user identity binding.

## Decision

Keep PLAN-001 synthetic, rate-limited, and ephemeral with no auth provider; disclose elicitation identity binding as deferred and require deploy–verify–destroy lifecycle enforcement.

## Consequences

The lab does not claim production security or full elicitation security conformance. Real data, persistent hosting, and non-simulated remediation remain forbidden until a later authorization plan.

## Related

- [PRD — Security posture](../../stateless-mcp-incident-lab-prd/PRD.md)
- [PLAN-001 — Technology choices and Non-goals](../../stateless-mcp-incident-lab-prd/PLAN-001-stateless-core.md)
- [ADR-0003 — ECS Fargate and ALB](0003-fargate-alb-streamable-http.md)
