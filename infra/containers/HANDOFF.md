# Container handoff
Scope: infra/containers plus docs/container-deployment.md only. Added multi-stage frontend/Python image, two explicit Compose profiles, loopback binding, shared named volume, nonroot user, read-only root filesystem, health probes and single-worker topology. Reuses existing lock, startup and storage semantics without API changes. Docker absent: no image build, service run or container-case pass claimed. Fixed E-path business adapters explicitly unsupported. Parent may integrate CI only after Linux acceptance; no real model/network execution performed.

Validation: Python AST passed; PyYAML missing so YAML parser check not performed. Added Dockerfile-specific context allowlist. Docker config/build/health/lock behavior remain unverified in Linux.

Corrected packaging after parent review: COPY infra/sqlite/ and matching Dockerfile.dockerignore allowlist, 001_initial.sql source presence checked; optional EVAL_AUTH_CONFIG passed to both services with empty default. No Docker execution performed.
