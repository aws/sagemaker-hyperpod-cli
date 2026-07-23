# TESTING — hpmigrate-ansible

Two layers of testing:

1. **Offline / CI** — syntax and lint. No AWS, no HyperPod. Runs on every push
   (see `.github/workflows/ci.yml`).
2. **Live** — end-to-end against real HyperPod clusters over SSM. Manual,
   gated, and destructive-adjacent (it creates users on a *target*). The
   checklist below is the authoritative pre-flight.

---

## 1. Offline / CI (fast, safe)

```bash
python3 -m pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml

# a) YAML lint + ansible-lint
yamllint .
ansible-lint

# b) Playbook syntax (no connection made)
ansible-playbook playbooks/snapshot.yml --syntax-check -i localhost, \
  -e hpm_bucket=s3://ci-noop -e hpm_run_id=ci
ansible-playbook playbooks/converge.yml --syntax-check -i localhost, \
  -e hpm_bucket=s3://ci-noop -e hpm_run_id=ci
ansible-playbook playbooks/validate.yml --syntax-check -i localhost, \
  -e hpm_bucket=s3://ci-noop -e hpm_run_id=ci
```

---

## 2. Live test checklist (HyperPod, over SSM)

> Do this first on a **throwaway pair** of small clusters, never on production
> capacity. The converge/validate steps must run against a **target** you are
> willing to mutate.

### 2.0 Prereqs on the runner host
- [ ] `awscli v2`, `session-manager-plugin`, `ansible-core`, collections from
      `requirements.yml`, `boto3` installed.
- [ ] Runner principal IAM: `sagemaker:DescribeCluster`, `sagemaker:ListClusterNodes`,
      `ssm:StartSession`/`TerminateSession` on `arn:aws:sagemaker:*:*:cluster/*`,
      and `s3:*Object`/`ListBucket` on the artifact bucket.
- [ ] Node execution role can read/write the artifact bucket prefix.
- [ ] `export HPM_BUCKET=s3://... HPM_RUN_ID=$(date +%Y%m%d-%H%M%S)`

### 2.1 Transport sanity (the риск area — validate FIRST)
The `community.aws.aws_ssm` plugin uses its own SSM document + S3 file transfer,
**not** an interactive shell. HyperPod wraps the login shell (drops into a nested
root `bash`), which historically broke stdout-scraping approaches. Confirm the
plugin tunnels cleanly through that wrapper before trusting the playbooks:
- [ ] `python3 bin/gen_inventory.py --cluster SRC --region R --group controller-machine --bucket $HPM_BUCKET`
      prints a `[controller]` host with `ansible_connection=community.aws.aws_ssm`.
- [ ] Raw ping over SSM:
      `ansible -i inventory.generated.ini controller -m ping`
      → expect `pong`. **If this hangs or errors**, the wrapper/plugin
      interaction is the culprit — fall back to the shell-based fan-out from
      `hyperpod-ansible/ci/run_ansible.sh` and file a note in the README.
- [ ] `ansible -i inventory.generated.ini controller -m command -a 'id'`
      returns `uid=0(root)` (confirms privilege + real command execution).
- [ ] `ansible -i inventory.generated.ini controller -m command -a 'aws s3 ls $HPM_BUCKET'`
      works from the node (confirms node role S3 access used by capture).

### 2.2 Snapshot (SOURCE, read-only)
- [ ] `./bin/hpmigrate-ansible.sh snapshot --cluster SRC --region R --group controller-machine`
- [ ] `aws s3 ls $HPM_BUCKET/$HPM_RUN_ID/ --recursive` shows
      `identity/{users,groups,ssh_inventory,identity_model}.json`,
      `slurm/{slurm.conf,gres.conf,sacctmgr_dump.cfg}`, `storage/shape.json`.
- [ ] `users.json` UID/GIDs match `getent passwd` on the source (spot-check a
      few, incl. members of `fsx-users`).
- [ ] `identity_model.json` correctly reports `local` vs `sssd`.
- [ ] `shape.json` correctly reports `fsx_only` vs `fsx_openzfs`.
- [ ] **Source unchanged**: re-run `getent passwd | wc -l` on source before/after
      → identical (no accidental writes).

### 2.3 Converge (TARGET)
- [ ] Run BEFORE data-move/mount so ownership lines up:
      `./bin/hpmigrate-ansible.sh converge --cluster TGT --region R --group controller-machine`
- [ ] `getent passwd <user>` on target shows **identical UID/GID** to source.
- [ ] `getent group fsx-users` GID matches source.
- [ ] Idempotency: run converge **again** → `changed=0`.
- [ ] SSSD case: on a directory-managed source, converge **skips** local user
      creation (check the debug line) and does not create local accounts.
- [ ] fsx_only case: no task attempts to touch `/home`.

### 2.4 Post-data-move .ssh perms
After DRA-import (`/fsx`) and, in Shape B, OpenZFS-restore (`/home`):
- [ ] Re-run converge (or just the `ssh_perms` role) so perms are enforced on the
      now-populated homes.
- [ ] For a sample user: `ls -ld ~/.ssh` → `700`, owned by the user;
      `ls -l ~/.ssh/authorized_keys` → `600`, owned by the user.
- [ ] Actually SSH in as a migrated user with their existing key → **succeeds**.

### 2.5 Validate (the gate)
- [ ] `./bin/hpmigrate-ansible.sh validate --cluster TGT --region R --group controller-machine`
      → `IDENTITY VALIDATION PASSED`.
- [ ] Negative test: on a scratch target, manually `usermod -u <different> <user>`,
      re-run validate → it **fails closed** with the mismatch message. Restore.

### 2.6 Slurm
- [ ] `sinfo` on target shows the source partitions.
- [ ] `sacctmgr show assoc` matches source associations/QOS.
- [ ] `gres.conf` customization (e.g. per-GPU booking) is present on target.

---

## 3. What is intentionally NOT tested here
- **Bulk data movement** (DRA export/import, OpenZFS backup/restore) — owned by
  the parent `hpmigrate` CLI, not Ansible. Ansible only enforces ownership/perms
  on the resulting files and validates identity.
- **Full slurmdbd `mysqldump`** — parent CLI, not Ansible.
- **Cluster/VPC/FSx provisioning** — CloudFormation via the parent CLI.
