# ADR-0006: Trusted CloudFront viewer key for regional WAF rate limiting

Status: Accepted

## Context

ADR-0005 requires regional WAF rate limiting to distinguish the viewer address that CloudFront observes without trusting client-supplied forwarding headers. Its original `ForwardedIPConfig.Position=LAST` mechanism is not deployable: AWS WAF rate statements accept only `HeaderName` and `FallbackBehavior` in `ForwardedIPConfig`; `Position` belongs to `IPSetForwardedIPConfig`.

## Decision

Supersede only ADR-0005's viewer-IP rate-key mechanism. Associate a CloudFront viewer-request function with every behavior. The function overwrites `x-incident-viewer-ip` with `event.viewer.ip`. Configure the regional WAF rate statement with `AggregateKeyType=CUSTOM_KEYS` and a header custom key named `x-incident-viewer-ip`, using a `NONE` text transformation. Keep the WAF associated with the internal ALB and preserve ADR-0005's managed-prefix-list-only ALB ingress.

The function executes at the trusted public edge before origin forwarding. A client cannot directly reach the private ALB, and a client-provided value with the same name is overwritten rather than appended. The implementation and deployed acceptance must prove that the function is associated with default, `/raw/*`, and `/sdk/*` behaviors and that distinct viewer addresses produce distinct WAF aggregation keys.

## Consequences

The template uses fields supported by the CloudFormation WAF schema and no longer depends on ambiguous `X-Forwarded-For` ordering. The dedicated header is security-sensitive infrastructure metadata and must not be logged by application containers. CloudFront Functions add an edge code resource but no CDK file asset, so bootstrapless inline synthesis remains valid.

## Related

- [PRD — Deployment](../../stateless-mcp-incident-lab-prd/PRD.md)
- [PLAN-001 — Deployment target](../../stateless-mcp-incident-lab-prd/PLAN-001-stateless-core.md)
- Supersedes viewer-IP mechanism in: [ADR-0005 — CloudFront-managed HTTPS](0005-cloudfront-managed-https-origin-alb.md)
- Conformance: INFRA-005
