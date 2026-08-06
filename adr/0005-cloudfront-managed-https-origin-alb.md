# ADR-0005: CloudFront-managed HTTPS with a private origin ALB

Status: Proposed

## Context

The ephemeral acceptance account cannot provision an ACM certificate, a custom hostname, or the CDK bootstrap stack. Public transit must still use HTTPS, preserve request-scoped SSE and disconnect behavior, and route to both horizontally scaled ECS Fargate services without deployment assets or staging resources that require bootstrap.

## Decision

Use the generated CloudFront distribution hostname and default CloudFront certificate as the only publicly reachable application endpoint. CloudFront reaches an internal ALB through a CloudFront VPC origin over HTTP; the ALB security group admits its listener port only from the AWS-managed CloudFront origin-facing prefix list. Keep the regional WAF associated with the ALB and configure its rate rule with `ForwardedIPConfig` using the last `X-Forwarded-For` address, which is trustworthy because the origin is reachable only through CloudFront.

Configure the distribution with all MCP methods (`GET`, `HEAD`, `OPTIONS`, `POST`, `PUT`, `PATCH`, and `DELETE`), caching disabled, and an origin request policy that forwards all viewer headers except `Host`, including `Accept`, `Content-Type`, `Authorization`, `Origin`, `Mcp-Session-Id`, `MCP-Protocol-Version`, and `Last-Event-ID`. Set the origin response timeout to 60 seconds and require SSE heartbeats no more than 15 seconds apart so an otherwise idle stream remains live; deployed acceptance still proves response streaming and client-disconnect propagation end to end.

Synthesize two asset-free, non-nested stacks with `CliCredentialsStackSynthesizer`: an edge stack owning the VPC, internal ALB, target groups, regional WAF, VPC origin, and CloudFront distribution; and a workload stack owning ECR, ECS/Fargate, DynamoDB, Secrets Manager, and logs while importing edge outputs. Gate each synthesized template at no more than CloudFormation's 51,200-byte inline `TemplateBody` limit, and create/update it directly with CloudFormation rather than `cdk deploy`. Deploy the edge stack first, bootstrap the workload at zero desired tasks, push immutable images, then update the workload to two tasks per realization. Teardown reverses that dependency: workload first, then edge; CloudFormation disables and deletes the distribution before deleting its VPC origin and ALB, and the lifecycle verifies both stack inventories are empty.

## Consequences

No custom DNS, ACM certificate, CDK bootstrap stack, template staging bucket, or publicly reachable plaintext origin is required. ECS/Fargate replica routing remains intact, while CloudFront becomes an additional streaming and header-policy hop that must be verified in AWS. Distribution creation and deletion can take tens of minutes. The deployment must prove the managed prefix list exists, direct ALB access is impossible, WAF observes distinct viewer addresses, required methods and headers transit unchanged, SSE is not buffered or cached, heartbeat and disconnect behavior survive the distribution, both templates stay within the inline limit, and teardown leaves no distribution, VPC origin, stack resource, or image repository behind.

## Related

- [PRD — Deployment](../../stateless-mcp-incident-lab-prd/PRD.md)
- [PLAN-001 — Deployment target](../../stateless-mcp-incident-lab-prd/PLAN-001-stateless-core.md)
- Extends: [ADR-0003 — ECS Fargate and ALB](0003-fargate-alb-streamable-http.md)
- Conformance: INFRA-004 and INFRA-010
