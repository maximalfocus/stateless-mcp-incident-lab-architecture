# ADR-0005: CloudFront-managed HTTPS with a private origin ALB

Status: Proposed

## Context

The ephemeral acceptance account cannot provision an ACM certificate, a custom hostname, or the CDK bootstrap stack. Public transit must still use HTTPS, preserve request-scoped SSE and disconnect behavior, and route to both horizontally scaled ECS Fargate services without deployment assets or staging resources that require bootstrap.

## Decision

Use the generated CloudFront distribution hostname and default CloudFront certificate as the only publicly reachable application endpoint. CloudFront reaches an internal ALB through a CloudFront VPC origin over HTTP; the ALB security group admits its listener port only from the AWS-managed CloudFront origin-facing prefix list. Keep the regional WAF associated with the ALB and configure its rate rule with `ForwardedIPConfig` using the last `X-Forwarded-For` address: CloudFront appends its observed viewer address after any client-supplied values, and the private origin prevents a non-CloudFront caller from forging that position.

Configure the distribution with all MCP methods (`GET`, `HEAD`, `OPTIONS`, `POST`, `PUT`, `PATCH`, and `DELETE`), caching disabled, and an origin request policy that forwards all viewer headers except `Host`, including `Accept`, `Content-Type`, `Authorization`, `Origin`, `Mcp-Session-Id`, `MCP-Protocol-Version`, and `Last-Event-ID`. Set the origin response timeout to 60 seconds and require SSE heartbeats no more than 15 seconds apart so an otherwise idle stream remains live; deployed acceptance still proves response streaming and client-disconnect propagation end to end.

Synthesize two asset-free, non-nested stacks with `BootstraplessSynthesizer`, which rejects file/image assets and omits bootstrap roles and version rules. The edge stack owns the VPC, internal ALB, target groups, ALB and task security groups, regional WAF, VPC origin, and CloudFront distribution; the workload stack owns ECR, ECS/Fargate, DynamoDB, Secrets Manager, and logs while importing edge outputs. Tasks use public subnets and public IPs solely for outbound AWS API/ECR access, have no inbound route except their imported task security groups, and allow outbound TLS only; this avoids NAT and endpoint cost without making task ports publicly reachable. Gate each synthesized template at no more than CloudFormation's 51,200-byte inline `TemplateBody` limit and reject any bootstrap parameter/rule or asset manifest, then create/update it directly with CloudFormation rather than `cdk deploy`. Deploy the edge stack first, bootstrap the workload at zero desired tasks, push immutable images, then update the workload to two tasks per realization. Teardown reverses that dependency: workload first, then edge; CloudFormation disables and deletes the distribution before deleting its VPC origin and ALB, and the lifecycle verifies both stack inventories are empty.

## Consequences

No custom DNS, ACM certificate, CDK bootstrap stack, template staging bucket, or publicly reachable plaintext origin is required. ECS/Fargate replica routing remains intact, while CloudFront becomes an additional streaming and header-policy hop that must be verified in AWS. Distribution creation and deletion can take tens of minutes, edge exports cannot change while the workload imports them, and edge iteration therefore requires workload teardown first. A staging bucket plus one large stack was rejected because it adds a bootstrap-like resource and leaves the original repository/service ordering problem coupled; private tasks plus NAT or multiple VPC endpoints were rejected for an ephemeral lab because they add standing cost and template size without improving inbound isolation over no-ingress public-IP tasks.

The workload uses native ECR `EmptyOnDelete` and CloudFormation's default force-delete behavior for Secrets Manager so teardown is not blocked by pushed images or a recovery window. The deployment must prove the VPC-origin security path works (the AWS documentation permits either the managed prefix list or the service-managed VPC-origin security group), direct ALB access is impossible, WAF observes distinct viewer addresses, required methods and headers transit unchanged, SSE is not buffered or cached, heartbeat and disconnect behavior survive the distribution, synthesized templates contain no bootstrap references/assets and stay within the inline limit, and teardown leaves no distribution, VPC-origin ENI, stack resource, image repository, or pending secret behind. The cited INFRA-004 and INFRA-010 conformance tests still describe the superseded certificate-terminated public ALB topology, so they must be evolved downstream before this ADR is accepted.

## Related

- [PRD — Deployment](../../stateless-mcp-incident-lab-prd/PRD.md)
- [PLAN-001 — Deployment target](../../stateless-mcp-incident-lab-prd/PLAN-001-stateless-core.md)
- Extends: [ADR-0003 — ECS Fargate and ALB](0003-fargate-alb-streamable-http.md)
- Conformance: INFRA-004 and INFRA-010
