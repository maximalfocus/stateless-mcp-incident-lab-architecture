# Stateless MCP Incident Lab architecture

Layer-symmetric architecture contracts for the Stateless MCP Incident Lab. This repository is upstream of conformance, implementation, infrastructure, CI/CD, and acceptance artifacts.

## ADR index

| ADR | Status | Decision | Pinned by |
|---|---|---|---|
| [ADR-0001](adr/0001-independent-raw-sdk-realizations.md) | Proposed | Independent raw and SDK realizations behind one contract | Future `architecture/` conformance round |
| [ADR-0002](adr/0002-dynamodb-explicit-application-state.md) | Proposed | DynamoDB for explicit application state across replicas | Future persistence/infra conformance round |
| [ADR-0003](adr/0003-fargate-alb-streamable-http.md) | Proposed | ECS Fargate and ALB for Streamable HTTP and SSE | Future transport/infra conformance round |
| [ADR-0004](adr/0004-ephemeral-unauthenticated-core-lab.md) | Proposed | Ephemeral synthetic deployment with auth deferred | Future security/infra conformance round |

## Directories

- `adr/` — proposed and accepted architecture decisions.
- `diagrams/` — Mermaid source and rendered deployment diagrams.
- `rules/` — byte-faithful implementation boundary rules derived from architecture goldens.

## Lifecycle

These stubs record PRD-level decisions only. `/cdd-author` promotes an ADR to `Accepted` when a conformance round cites it, after updating the complete ADR surface and running architecture peer review. Accepted ADRs are append-only and are superseded by new ADRs rather than edited in place.
