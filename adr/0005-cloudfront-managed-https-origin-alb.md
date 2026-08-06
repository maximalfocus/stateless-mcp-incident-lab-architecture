# ADR-0005: CloudFront-managed HTTPS with a restricted origin ALB

Status: Proposed

## Context

The ephemeral acceptance account cannot provision an ACM certificate, a custom hostname, or the CDK bootstrap stack. Public transit must still use HTTPS, preserve request-scoped SSE and disconnect behavior, and route to both horizontally scaled ECS Fargate services without introducing deployment assets that require CDK bootstrap.

## Decision

Use the generated CloudFront distribution hostname and default CloudFront certificate as the only public endpoint. CloudFront forwards to an internet-facing ALB over HTTP, but the ALB security group admits port 80 only from the AWS-managed CloudFront origin-facing prefix list; the ALB has no unrestricted public ingress. Keep the regional WAF associated with the ALB, deploy an asset-free synthesized CloudFormation template directly with `aws cloudformation deploy`, and verify/destroy it with CloudFormation and service-specific inventory commands.

## Consequences

No custom DNS, ACM certificate, or CDK bootstrap is required, while ECS/Fargate replica routing and ordinary HTTP streaming remain available. Public TLS terminates at CloudFront and the origin hop is plaintext inside the restricted CloudFront-to-ALB path. The deployment must prove that direct non-CloudFront ALB access is denied, the distribution preserves SSE/no-buffer semantics and forwards required MCP headers, the managed prefix list exists in the target region, and teardown removes the distribution before origin resources.

## Related

- [PRD — Deployment](../../stateless-mcp-incident-lab-prd/PRD.md)
- [PLAN-001 — Deployment target](../../stateless-mcp-incident-lab-prd/PLAN-001-stateless-core.md)
- [ADR-0003 — ECS Fargate and ALB](0003-fargate-alb-streamable-http.md)
- Conformance: INFRA-004 and INFRA-010
