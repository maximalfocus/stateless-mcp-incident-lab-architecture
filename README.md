# Stateless MCP Incident Lab architecture

Layer-symmetric architecture contracts for the Stateless MCP Incident Lab. This repository is upstream of conformance, implementation, infrastructure, CI/CD, and acceptance artifacts.

## ADR index

| ADR | Status | Decision | Pinned by |
|---|---|---|---|
| [ADR-0001](adr/0001-independent-raw-sdk-realizations.md) | Accepted | Independent raw and SDK realizations behind one contract | `ARCH-001`–`ARCH-004` |
| [ADR-0002](adr/0002-dynamodb-explicit-application-state.md) | Accepted | DynamoDB for explicit application state across replicas | `ARCH-005` |
| [ADR-0003](adr/0003-fargate-alb-streamable-http.md) | Accepted | ECS Fargate and ALB for Streamable HTTP and SSE | `ARCH-006` |
| [ADR-0004](adr/0004-ephemeral-unauthenticated-core-lab.md) | Accepted | Ephemeral synthetic deployment with auth deferred | `ARCH-006` |

## Directories

- `adr/` — proposed and accepted architecture decisions.
- `diagrams/` — Mermaid source and rendered deployment diagrams.
- `rules/` — byte-faithful implementation boundary rules derived from architecture goldens.

`diagrams/` remains intentionally empty until deployed topology is verified. `rules/` contains the raw and SDK implementation boundary contracts pinned by `ARCH-001`–`ARCH-004`.

## Lifecycle

`/cdd-author` promoted these PRD-level decisions to `Accepted` when the backend conformance round pinned them. Accepted ADRs are append-only and are superseded by new ADRs rather than edited in place.

`scripts/verify-architecture.py` enforces accepted-ADR immutability against git history and parses every boundary YAML with a real loader. Rendered-diagram verification is activated when acceptance authors the first deployment diagram.

## Validation

Install the pinned parser with `python3 -m pip install -r requirements.txt`, then run `python3 scripts/verify-architecture.py`.
