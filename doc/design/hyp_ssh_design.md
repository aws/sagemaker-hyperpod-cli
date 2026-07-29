# Design: `hyp ssh` — Direct Terminal SSH into HyperPod Spaces

## Overview

Add a `hyp ssh hyp-space --name <workspace>` command that establishes an interactive SSH session to a HyperPod Space (notebook workspace) via AWS Systems Manager (SSM) Session Manager.

Today, the CLI supports `vscode-remote` and `kiro-remote` connection types which open IDE-specific protocol URLs. This feature extends that to provide a direct terminal SSH experience without requiring any IDE.

## User Experience

```bash
# SSH into a workspace
hyp ssh hyp-space --name my-workspace

# With explicit namespace
hyp ssh hyp-space --name my-workspace --namespace team-ns

# With region override
hyp ssh hyp-space --name my-workspace --region us-west-2
```

Output:
```
Connecting to space 'my-workspace'...
Starting SSH session to 'mi-0abc123def456'...
Use 'exit' or Ctrl+D to end the session.

root@workspace-pod:~#
```

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  hyp ssh    │────▶│ WorkspaceConnection│────▶│ SSM Managed Instance│
│  (CLI)      │     │ CRD (ssh-remote)  │     │ (Space Pod)         │
└─────────────┘     └──────────────────┘     └─────────────────────┘
       │                     │                         │
       │  1. create CRD      │  2. returns URL         │
       │─────────────────────▶                         │
       │                     │                         │
       │  3. parse target    │                         │
       │◀────────────────────│                         │
       │                                               │
       │  4. aws ssm start-session --target <id>       │
       │──────────────────────────────────────────────▶│
       │                                               │
       │  5. Interactive terminal session              │
       │◀─────────────────────────────────────────────▶│
```

### Flow

1. CLI calls `HPSpace.get(name)` to verify the space exists and is Available
2. CLI calls `space.create_space_access(connection_type="ssh-remote")` which creates a `WorkspaceConnection` CRD
3. The SageMaker Spaces operator provisions/returns the SSM managed instance target
4. CLI parses the `workspaceConnectionUrl` from the CRD status to extract the SSM target ID
5. CLI invokes `aws ssm start-session --target <instance-id> --region <region>` as a subprocess
6. User gets an interactive terminal session

### Connection URL Format

The `workspaceConnectionUrl` returned by the operator for `ssh-remote` type:

```
ssm://<managed-instance-id>?documentName=AWS-StartSSHSession&portNumber=22
```

Or alternatively:
```
https://<endpoint>/session?target=<managed-instance-id>&documentName=AWS-StartSSHSession
```

## Implementation

### New Files

| File | Purpose |
|------|---------|
| `src/sagemaker/hyperpod/cli/commands/ssh.py` | CLI command + SSM session logic |
| `test/unit_tests/cli/test_ssh.py` | Unit tests |

### Modified Files

| File | Change |
|------|--------|
| `src/sagemaker/hyperpod/cli/hyp_cli.py` | Register `ssh` command group |
| `src/sagemaker/hyperpod/space/hyperpod_space.py` | Add `ssh()` SDK method |

### Key Design Decisions

1. **Reuse `create_space_access` with `ssh-remote` type** — No new CRD or API needed. The existing `WorkspaceConnection` CRD supports arbitrary `{ide}-remote` patterns. We use `ssh-remote` as the connection type.

2. **SSM as transport** — HyperPod doesn't expose SSH ports. The Spaces operator registers an SSM Advanced On-Premises Instance for each space. This is the same mechanism used by `vscode-remote`.

3. **Subprocess for session** — We use `subprocess.run()` with stdin/stdout/stderr passthrough for a fully interactive terminal. This is the same pattern used by `aws ssm start-session` directly.

4. **No SSH key management** — SSM handles authentication via IAM. No SSH keys needed.

## Prerequisites

- AWS Session Manager Plugin installed locally
- Valid AWS credentials with `ssm:StartSession` permission
- Space must be in `Available` status (running)
- SageMaker Spaces Add-on installed on the cluster

## SDK Usage

```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

space = HPSpace.get(name="my-workspace")
ssh_info = space.ssh()
# Returns: {"SpaceConnectionType": "ssh-remote", "SpaceConnectionUrl": "ssm://mi-..."}
```

## Testing

- Unit tests mock the K8s API and subprocess calls
- Integration tests require a live HyperPod cluster with Spaces add-on
- Manual testing: `hyp ssh hyp-space --name <space> --debug` shows the SSM command

## Future Extensions

- `hyp ssh hyp-space --name ws --command "nvidia-smi"` — run a single command
- `hyp scp` — file transfer via SSM
- SSH config generation for `~/.ssh/config` ProxyCommand integration
