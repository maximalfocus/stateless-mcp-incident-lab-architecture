# Problem

Define an AWS-deployable, bootstrap-free architecture for the stateless MCP incident lab under restricted account permissions.

## Scope

- CloudFront generated hostname and default TLS certificate
- Private ALB reached through a CloudFront VPC origin
- Trusted viewer-IP propagation and regional WAF rate limiting
- Private ECS tasks with NAT egress
- Asset-free split CloudFormation templates
- Direct CloudFormation deployment and deterministic teardown
- ADR consistency with infrastructure conformance

## Non-goals

- Custom hostname or ACM certificate
- CDK bootstrap stack
- Public ALB or public task ENIs
- Persistent production infrastructure

## Acceptance criteria

1. ADR-0005 uses only AWS-supported CloudFormation fields.
2. Viewer identity cannot be forged through client-supplied forwarding headers.
3. Architecture and conformance contracts agree.
4. No certificate, hostname, or CDK-bootstrap capability is required.
5. Deployment and teardown ordering are explicit and acyclic.
6. Architecture files and shipped YAML/JSON parse successfully.

## Verification

```bash
python3 scripts/audit.py
python3 - <<'PY'
import json
from pathlib import Path
for path in Path('.').rglob('*.json'):
    json.loads(path.read_text())
print('JSON parse: PASS')
PY
python3 - <<'PY'
from pathlib import Path
text = '\n'.join(p.read_text() for p in Path('.').rglob('*.md'))
for stale in ('CertificateArn', 'internet-facing ALB', 'ForwardedIPConfig` using the last'):
    assert stale not in text, stale
print('stale topology sweep: PASS')
PY
```

Cross-repo review additionally compares ADR-0005 with sibling conformance contracts INFRA-004–006 and INFRA-010.

## Residuals

- Real AWS deployment evidence belongs to the deployment phase, not this architecture repository.
