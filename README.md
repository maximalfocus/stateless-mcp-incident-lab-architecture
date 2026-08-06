# Stateless MCP Incident Lab architecture

Layer-symmetric architecture contracts for the Stateless MCP Incident Lab. This repository is upstream of conformance, implementation, infrastructure, CI/CD, and acceptance artifacts.

## ADR index

| ADR | Status | Decision | Pinned by |
|---|---|---|---|
| [ADR-0001](adr/0001-independent-raw-sdk-realizations.md) | Accepted | Independent raw and SDK realizations behind one contract | `ARCH-001`–`ARCH-004` |
| [ADR-0002](adr/0002-dynamodb-explicit-application-state.md) | Accepted | DynamoDB for explicit application state across replicas | `ARCH-005` |
| [ADR-0003](adr/0003-fargate-alb-streamable-http.md) | Accepted | ECS Fargate and ALB for Streamable HTTP and SSE | `ARCH-006` |
| [ADR-0004](adr/0004-ephemeral-unauthenticated-core-lab.md) | Accepted | Ephemeral synthetic deployment with auth deferred | `ARCH-006` |
| [ADR-0005](adr/0005-cloudfront-managed-https-origin-alb.md) | Proposed | CloudFront-managed HTTPS with a restricted origin ALB | `INFRA-004`, `INFRA-010` |

## Directories

- `adr/` — accepted architecture decisions; future decisions begin as Proposed.
- `diagrams/` — reserved for Mermaid deployment sources and rendered artifacts after deployed acceptance.
- `rules/` — machine-consumable implementation boundary contracts that downstream architecture goldens must mirror exactly.

`diagrams/` remains intentionally empty until deployed topology is verified. `rules/` contains the raw and SDK contracts reserved for `ARCH-001`–`ARCH-004`; those golden files do not exist yet.

## Lifecycle

`/cdd-author` promoted these PRD-level decisions to `Accepted` before the backend conformance round cites them. Accepted ADRs are append-only and are superseded by new ADRs rather than edited in place.

`scripts/verify-architecture.py` enforces accepted-ADR immutability against git history and parses every boundary YAML with a real loader. Deployed acceptance must add diagram-fidelity checks in the same change that introduces the first deployment diagram; until then, the gate requires `diagrams/` to remain empty.

## Boundary matching contract

- `from_glob` and `module_pattern` use a closed prefix-globstar subset over workspace-relative paths: only `prefix/**` (all descendant files) and `prefix/*/` (one immediate child directory) are valid.
- `import_pattern` uses the Python/ECMAScript-compatible regex subset and is searched against a canonical import.
- Bare package specifiers remain unchanged. Relative and aliased imports resolve to workspace-root TypeScript source paths—including `.ts` source extensions—before matching.
- Public-entry checks operate on resolved source modules: cross-module imports must resolve to `index.ts`; imports within the same module are allowed.
- Runners must prove non-vacuity with root/deep paths, barrel/internal entries, and near misses for every assertion.

## Validation

Use Python 3.10+ and Node.js 18+ for the architecture gate. Install the pinned parser with `python3 -m pip install -r requirements.txt`, then run `python3 scripts/verify-architecture.py` and `python3 scripts/test-verify-architecture.py`.
