#!/bin/bash
# hpmigrate-ansible.sh — generate the SSM inventory then run a migration playbook.
#
# Subcommands: snapshot | converge | validate
#
# Example:
#   HPM_BUCKET=s3://my-artifacts HPM_RUN_ID=20260101-1200 \
#   ./bin/hpmigrate-ansible.sh snapshot --cluster src --region us-west-2 \
#       --group controller-machine
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "${HERE}"

SUB="${1:-}"; shift || true
case "${SUB}" in
  snapshot) PLAYBOOK=playbooks/snapshot.yml ;;
  converge) PLAYBOOK=playbooks/converge.yml ;;
  validate) PLAYBOOK=playbooks/validate.yml ;;
  *) echo "Usage: $0 {snapshot|converge|validate} --cluster N --region R [--group G]"; exit 1 ;;
esac

CLUSTER=""; REGION=""; GROUP=""
while [ $# -gt 0 ]; do
  case "$1" in
    --cluster) CLUSTER="$2"; shift 2 ;;
    --region)  REGION="$2";  shift 2 ;;
    --group)   GROUP="$2";   shift 2 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done
[ -n "${CLUSTER}" ] && [ -n "${REGION}" ] || { echo "need --cluster and --region"; exit 1; }

: "${HPM_BUCKET:?set HPM_BUCKET=s3://...}"
: "${HPM_RUN_ID:=$(date +%Y%m%d-%H%M%S)}"
export HPM_BUCKET HPM_RUN_ID

echo ">> generating SSM inventory for ${CLUSTER} (${REGION})"
python3 bin/gen_inventory.py --cluster "${CLUSTER}" --region "${REGION}" \
  --group "${GROUP}" --bucket "${HPM_BUCKET}" > inventory.generated.ini
cat inventory.generated.ini

echo ">> running ${PLAYBOOK} (run_id=${HPM_RUN_ID})"
ansible-playbook "${PLAYBOOK}" \
  -e "hpm_bucket=${HPM_BUCKET}" \
  -e "hpm_run_id=${HPM_RUN_ID}" \
  -e "target_cluster=${CLUSTER}" \
  -e "target_region=${REGION}"
