# Release {{VERSION}}

## Overview

Provide a concise summary of this release.
Focus on **what changed**, **why it matters**, and **who is impacted**.

Example:
> This release strengthens supply-chain security by introducing SLSA Level 3–aligned
> provenance, cryptographic artifact signing, and improved CI/CD hardening.

---

## Highlights ✨

- Bullet-point the most important changes
- Emphasize security, stability, or architectural changes
- Avoid implementation details unless they impact users

Example:
- Introduced cryptographic signing for container images
- Added SBOM generation and provenance attestation
- Hardened CI/CD pipeline with pinned actions

---

## Security & Supply Chain 🔐

Describe any security-relevant changes clearly.

- New security controls
- Changes to trust model
- Vulnerability fixes (high-level, no sensitive details)

Example:
- Images are now signed using Cosign with GitHub OIDC
- Provenance is attached to release artifacts
- SBOMs are generated in SPDX format

---

## Breaking Changes (if any) ⚠️

Clearly describe any breaking changes and required actions.

- API changes
- Configuration changes
- Infrastructure changes

If none, state explicitly:

> No breaking changes in this release.

---

## Upgrade Impact 🔄

Explain what users need to know before upgrading.

- Required migrations
- Backward compatibility notes
- Recommended actions

Example:
- No database migrations required
- Existing deployments can upgrade without downtime
- Consumers may optionally verify image signatures

---

## Artifacts 📦

List released artifacts and where to find them.

Example:
- Docker Images:
  - `docker.io/<org>/csv-engine-backend:{{VERSION}}`
  - `docker.io/<org>/csv-engine-frontend:{{VERSION}}`
- SBOMs: Attached to this release
- Provenance: Published via GitHub attestations

---

## 🔍 Verification (Optional but Recommended)

Provide verification instructions for advanced users.

```bash
cosign verify \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  docker.io/<org>/csv-engine-backend:{{VERSION}}
```
---

## Additional Notes 📝

Any extra context:
- Known limitations
- Depreciations
- Follow-up work planned

---

## References 📚

- Changelog: CHANGELOG.md
- CI/CD Documentation: docs/ci-cd.md
- SLSA & Supply Chain: docs/slsa.md
