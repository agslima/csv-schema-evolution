# Changelog

All notable changes to this project are documented in this file.

This changelog provides **human-readable release notes**, summarizing
major changes, security improvements, and potential upgrade impacts.
It is not a raw commit log.

The project follows semantic versioning (`MAJOR.MINOR.PATCH`).

---

## [v2.0.1] – 2025-12-27

### Security & Supply-Chain Integrity

This release focuses on **software supply-chain security** and build integrity.

**Highlights**
- Introduced a **SLSA Level 3–aligned CI/CD pipeline**
- Added cryptographic guarantees for container images
- Improved auditability and release trust

**Key Changes**
- Artifact signing using **Cosign (keyless, OIDC-based)**
- Digest-pinned image signing and verification
- Generation and attestation of **SBOMs (SPDX)**
- Build provenance attestation via GitHub Actions
- Hardened CI with pinned actions and controlled permissions
- Verified, GPG-signed release tags enforced in CI

**Upgrade Impact**
- No API changes
- No data migration required
- Consumers can now cryptographically verify image authenticity and provenance

---

## [v2.0.0] – 2025-11-21

### Architecture & Feature Redesign (Breaking Changes)

This release represents a **major architectural evolution** of the project.

**Highlights**
- Complete project restructuring
- Introduction of persistence, testing, and observability
- Initial compliance alignment with **LGPD**

**Key Changes**
- Migration to **FastAPI async architecture**
- Introduction of **MongoDB** for persistence
- Added **unit and integration tests**
- Implemented a **heuristic classification algorithm**
- Added structured logging and observability hooks
- Introduced cryptographic mechanisms to minimally meet LGPD requirements

**Breaking Changes**
- API behavior and internal data flow changed
- Deployment model updated to support database-backed workflows

**Upgrade Impact**
- Existing users must review deployment and configuration
- Database setup is now required
- API consumers should validate behavior against updated endpoints

---

## [v1.0.0] – 2024-08-01

### Initial Release

**Highlights**
- First public version of the project
- Focused on data transformation logic

**Key Features**
- Core transformation algorithm
- REST API built with FastAPI
- Stateless execution model

**Limitations**
- No persistence layer
- No formal testing strategy
- No security or compliance guarantees

---

## Release Notes Policy

- Release notes are written manually to ensure clarity
- Notes focus on **what changed**, **why it matters**, and **upgrade impact**
- Security and breaking changes are always explicitly documented
