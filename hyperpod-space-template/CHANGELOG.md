## v1.1.0 (2026-04-20)

### Features

* Added `access_type` parameter to control who can connect to the workspace (`Public` or `OwnerOnly`)
* Added `env` parameter for specifying environment variables for the workspace container
* Added `access_strategy` parameter to reference a WorkspaceAccessStrategy
* Added `pod_security_context` parameter for pod-level security context configuration
* Added `container_security_context` parameter for container-level security context configuration
* Added `init_containers` parameter to run init containers before the workspace container starts
* Added `queue_name` and `priority` parameters for task governance support (Kueue integration)

### Changes

* Bumped minimum addon version from `0.1.1` to `0.1.6`

## v1.0.0 (2025-11-20)

### Features

* HyperPod Dev Spaces template for data scientists to create, manage, and access interactive ML development environments with configurable resource allocation and namespace isolation
