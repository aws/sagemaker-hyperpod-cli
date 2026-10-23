#!/bin/bash
# Migration script to transition HyperPod Inference Operator from Helm to EKS Addon deployment

set -e

# Parse command line arguments
AUTO_APPROVE=false
STEP_BY_STEP=false
SKIP_DEPENDENCY_MIGRATE=false
CLUSTER_NAME=""
AWS_REGION=""
HELM_NAMESPACE=""
S3_MOUNTPOINT_ROLE_ARN=""
FSX_ROLE_ARN=""
# Optional customer-provided roles for the addon. When a flag is not passed, the
# script creates the role with the same trust and permissions the HyperPod
# Inference addon CloudFormation flow uses (addon-iam-roles-cfn-template).
USER_EXECUTION_ROLE_ARN=""
USER_ALB_ROLE_ARN=""
USER_KEDA_ROLE_ARN=""
USER_JS_GATED_ROLE_ARN=""
# amazon-sagemaker-hyperpod-inference addon version. Empty = use the EKS default version for the
# cluster's Kubernetes version (resolved at runtime). Override with --addon-version.
ADDON_VERSION=""

usage() {
    echo "Usage: $0 [--auto-approve] [--step-by-step] [--skip-dependencies-migration]"
    echo "          [--cluster-name NAME] [--region REGION] [--helm-namespace NAMESPACE]"
    echo "          [--s3-mountpoint-role-arn ARN] [--fsx-role-arn ARN]"
    echo "          [--execution-role-arn ARN] [--alb-role-arn ARN] [--keda-role-arn ARN]"
    echo "          [--jumpstart-gated-role-arn ARN] [--addon-version VERSION]"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        --step-by-step)
            STEP_BY_STEP=true
            shift
            ;;
        --skip-dependencies-migration)
            SKIP_DEPENDENCY_MIGRATE=true
            shift
            ;;
        --cluster-name)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --helm-namespace)
            HELM_NAMESPACE="$2"
            shift 2
            ;;
        --s3-mountpoint-role-arn)
            S3_MOUNTPOINT_ROLE_ARN="$2"
            shift 2
            ;;
        --fsx-role-arn)
            FSX_ROLE_ARN="$2"
            shift 2
            ;;
        --execution-role-arn)
            USER_EXECUTION_ROLE_ARN="$2"
            shift 2
            ;;
        --alb-role-arn)
            USER_ALB_ROLE_ARN="$2"
            shift 2
            ;;
        --keda-role-arn)
            USER_KEDA_ROLE_ARN="$2"
            shift 2
            ;;
        --jumpstart-gated-role-arn)
            USER_JS_GATED_ROLE_ARN="$2"
            shift 2
            ;;
        --addon-version)
            ADDON_VERSION="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            usage
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Backup directory
BACKUP_DIR="/tmp/hyperpod-migration-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Function to print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to delete a role this script created (inline + managed policies first)
delete_created_role() {
    local role_name="$1"
    aws iam list-attached-role-policies --role-name "$role_name" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null | tr '\t' '\n' | grep -v '^$' | while read -r arn; do
        aws iam detach-role-policy --role-name "$role_name" --policy-arn "$arn" 2>/dev/null || true
    done
    aws iam list-role-policies --role-name "$role_name" --query 'PolicyNames[]' --output text 2>/dev/null | tr '\t' '\n' | grep -v '^$' | while read -r pname; do
        aws iam delete-role-policy --role-name "$role_name" --policy-name "$pname" 2>/dev/null || true
    done
    aws iam delete-role --role-name "$role_name" 2>/dev/null || print_warning "Failed to delete role: $role_name"
}

# Function to rollback changes
rollback() {
    # Rollback must not re-enter the error handler or stop half-way
    trap - ERR INT TERM
    set +e
    print_error "=== ROLLBACK INITIATED ==="
    print_info "Backup directory: $BACKUP_DIR"
    local addon_ns="hyperpod-inference-system"
    local helm_ns="${HELM_NAMESPACE:-kube-system}"
    local addon_installed=false
    [[ -f "$BACKUP_DIR/addon-installed.flag" ]] && addon_installed=true

    # Model resources (JumpStartModel, InferenceEndpointConfig) and their CRDs are never deleted by
    # this rollback. Save them first so they can be restored by hand if anything goes wrong.
    kubectl get jumpstartmodels,inferenceendpointconfigs -A -o yaml > "$BACKUP_DIR/model-crs-at-rollback.yaml" 2>/dev/null \
        && print_info "Model resources saved to $BACKUP_DIR/model-crs-at-rollback.yaml"

    # 1. Remove the add-on. --preserve is required: the add-on owns the inference CRDs, and deleting it
    #    without --preserve would delete every model resource. Its controllers keep running until the
    #    Helm controllers are back (step 4).
    if [[ "$addon_installed" == "true" ]]; then
        print_info "Removing addon (keeping its Kubernetes resources)..."
        if aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name amazon-sagemaker-hyperpod-inference --region "$AWS_REGION" >/dev/null 2>&1; then
            aws eks delete-addon --cluster-name "$CLUSTER_NAME" --addon-name amazon-sagemaker-hyperpod-inference \
                --region "$AWS_REGION" --preserve >/dev/null || print_warning "Failed to remove addon"
            aws eks wait addon-deleted --cluster-name "$CLUSTER_NAME" --addon-name amazon-sagemaker-hyperpod-inference \
                --region "$AWS_REGION" || print_warning "Timed out waiting for addon deletion"
        fi

        # 2. The add-on took over shared objects (CRD conversion webhook, ALB/KEDA webhooks, KEDA external
        #    metrics APIService, service accounts). Re-apply the Helm release so they point back at the Helm
        #    controllers. Objects now owned by other EKS add-ons are skipped.
        print_info "Restoring Helm release objects..."
        local skip_s3=false skip_metrics=false
        aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name aws-mountpoint-s3-csi-driver --region "$AWS_REGION" >/dev/null 2>&1 && skip_s3=true
        aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name metrics-server --region "$AWS_REGION" >/dev/null 2>&1 && skip_metrics=true
        if helm get manifest hyperpod-inference-operator -n "$helm_ns" > "$BACKUP_DIR/helm-manifest.yaml" 2>/dev/null; then
            kubectl create --dry-run=client -o json -f "$BACKUP_DIR/helm-manifest.yaml" 2>/dev/null \
              | jq -s --argjson s3 "$skip_s3" --argjson ms "$skip_metrics" '
                  [ .[] | if .kind == "List" then .items[] else . end
                    | select(($s3 | not) or ((.kind == "DaemonSet" and .metadata.name == "s3-csi-node") or (.kind == "CSIDriver" and .metadata.name == "s3.csi.aws.com") | not))
                    | select(($ms | not) or ((.kind == "APIService" and .metadata.name == "v1beta1.metrics.k8s.io") or (.kind == "Deployment" and .metadata.name == "hyperpod-inference-operator-metrics") | not)) ]
                  | {apiVersion: "v1", kind: "List", items: .}' > "$BACKUP_DIR/helm-restore.json" \
              && kubectl apply --server-side --force-conflicts --field-manager=helm -f "$BACKUP_DIR/helm-restore.json" >/dev/null \
              && print_success "Helm release objects restored" \
              || print_warning "Failed to restore Helm objects; see $BACKUP_DIR/helm-manifest.yaml"
        else
            print_warning "Could not read the Helm release manifest"
        fi
    fi

    # 3. Scale the Helm controllers back up (no-op for ones already restored above)
    if [[ -f "$BACKUP_DIR/helm-scaled-down.flag" ]]; then
        print_info "Scaling Helm inference operator back up..."
        kubectl scale deployment hyperpod-inference-operator-controller-manager --replicas=1 -n "$addon_ns" || print_warning "Failed to scale Helm deployment back up"
    fi
    [[ -f "$BACKUP_DIR/alb-scaled-down.flag" ]] && { kubectl scale deployment hyperpod-inference-operator-alb --replicas=2 -n "$helm_ns" || print_warning "Failed to scale ALB controller back up"; }
    [[ -f "$BACKUP_DIR/keda-scaled-down.flag" ]] && { kubectl scale deployment keda-operator --replicas=1 -n "$helm_ns" || print_warning "Failed to scale KEDA operator back up"; }
    [[ -f "$BACKUP_DIR/keda-metrics-scaled-down.flag" ]] && { kubectl scale deployment keda-operator-metrics-apiserver --replicas=1 -n "$helm_ns" || print_warning "Failed to scale KEDA metrics apiserver back up"; }
    [[ -f "$BACKUP_DIR/keda-webhooks-scaled-down.flag" ]] && { kubectl scale deployment keda-admission-webhooks --replicas=1 -n "$helm_ns" || print_warning "Failed to scale KEDA admission webhooks back up"; }

    # 4. Once the Helm controllers are ready, remove the add-on's controllers
    if [[ "$addon_installed" == "true" ]]; then
        print_info "Waiting for Helm controllers to become ready..."
        local d
        for d in hyperpod-inference-operator-alb keda-operator keda-operator-metrics-apiserver keda-admission-webhooks; do
            kubectl rollout status deployment "$d" -n "$helm_ns" --timeout=10m >/dev/null 2>&1 || print_warning "$helm_ns/$d is not ready yet"
        done
        # Becomes Ready only after the cluster inference watcher is re-enabled (can take several minutes)
        kubectl rollout status deployment hyperpod-inference-operator-controller-manager -n "$addon_ns" --timeout=20m >/dev/null 2>&1 \
            || print_warning "Helm inference operator is not ready yet; it becomes ready once the cluster inference watcher is enabled"
        print_info "Removing addon controllers..."
        kubectl delete deployment -n "$addon_ns" --ignore-not-found=true \
            hyperpod-inference-controller-manager hyperpod-inference-alb keda-operator keda-operator-metrics-apiserver keda-admission-webhooks
    fi

    # 5. Remove only the tags this script added
    if [[ -f "$BACKUP_DIR/alb-arns.txt" ]]; then
        print_info "Removing tags from ALB resources..."
        while read -r alb_arn; do
            aws elbv2 remove-tags --resource-arns "$alb_arn" --tag-keys "CreatedBy" --region "$AWS_REGION" 2>/dev/null || true
        done < "$BACKUP_DIR/alb-arns.txt"
    fi
    if [[ -f "$BACKUP_DIR/acm-arns.txt" ]]; then
        print_info "Removing tags from ACM certificates..."
        while read -r cert_arn; do
            aws acm remove-tags-from-certificate --certificate-arn "$cert_arn" --tags Key="CreatedBy" --region "$AWS_REGION" 2>/dev/null || true
        done < "$BACKUP_DIR/acm-arns.txt"
    fi
    if [[ -f "$BACKUP_DIR/s3-objects.txt" ]]; then
        print_info "Restoring tags on S3 objects..."
        while read -r line; do
            bucket=$(echo "$line" | cut -d'|' -f1)
            key=$(echo "$line" | cut -d'|' -f2)
            orig=$(echo "$line" | cut -d'|' -f3-)
            if [[ -z "$orig" || "$orig" == '{"TagSet":[]}' ]]; then
                aws s3api delete-object-tagging --bucket "$bucket" --key "$key" 2>/dev/null || true
            else
                aws s3api put-object-tagging --bucket "$bucket" --key "$key" --tagging "$orig" 2>/dev/null || true
            fi
        done < "$BACKUP_DIR/s3-objects.txt"
    fi

    # 6. Delete the IAM roles this script created, last, so no controller loses its credentials mid-way
    #    (customer-provided or pre-existing roles are left untouched)
    if [[ -f "$BACKUP_DIR/created-roles.txt" ]]; then
        while read -r created_role; do
            [[ -z "$created_role" ]] && continue
            print_info "Deleting role created by migration: $created_role"
            delete_created_role "$created_role"
        done < "$BACKUP_DIR/created-roles.txt"
    fi

    print_info "Rollback completed. Check backup directory for original configurations: $BACKUP_DIR"
    exit 1
}

# Function to handle errors and ask for rollback
handle_error() {
    local error_line="${BASH_LINENO[0]}"
    local error_command="${BASH_COMMAND}"
    
    print_error "=== MIGRATION FAILED ==="
    print_error "Error at line $error_line: $error_command"
    print_info "Backup directory: $BACKUP_DIR"
    
    # Check if addon is ACTIVE - if so, don't rollback
    if [[ -n "$CLUSTER_NAME" && -n "$AWS_REGION" ]]; then
        ADDON_STATUS=$(aws eks describe-addon \
            --cluster-name "$CLUSTER_NAME" \
            --addon-name amazon-sagemaker-hyperpod-inference \
            --region "$AWS_REGION" \
            --query "addon.status" --output text 2>/dev/null || echo "NOT_FOUND")
        
        if [[ "$ADDON_STATUS" == "ACTIVE" ]]; then
            print_warning "Addon is ACTIVE - core migration succeeded"
            print_warning "Dependency migration failed, this should not cause an issue since the helm version of the dependencies exist, please manually migrate dependencies to addons if they are installed via Inference operator helm for managing updates"
            print_info "Failed command: $error_command"
            print_info "Backup files preserved in: $BACKUP_DIR"
            exit 0
        fi
    fi
    
    echo -e "${YELLOW}Do you want to rollback the migration? (y/N):${NC}"
    read -r rollback_confirm
    if [[ "$rollback_confirm" =~ ^[Yy]$ ]]; then
        rollback
    else
        print_info "Rollback skipped. Backup files preserved in: $BACKUP_DIR"
        print_info "You can manually rollback later using the backup files."
        exit 1
    fi
}

# Trap to handle script interruption
trap 'handle_error' ERR INT TERM

# Function to prompt for user input
prompt_user() {
    local prompt="$1"
    local var_name="$2"
    echo -e "${YELLOW}$prompt${NC}"
    read -r "$var_name"
}

# Function to confirm action
confirm_action() {
    local action="$1"
    if [[ "$AUTO_APPROVE" == "true" ]]; then
        print_info "Auto-approving: $action"
        return 0
    fi
    echo -e "${YELLOW}About to: $action${NC}"
    echo -e "${YELLOW}Continue? (y/N):${NC}"
    read -r confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_error "Operation cancelled by user"
        exit 1
    fi
}

# Like confirm_action, but for a detected problem: never auto-approved.
# In --auto-approve mode the script stops so a misconfiguration cannot slip through unattended.
confirm_risk() {
    local action="$1"
    if [[ "$AUTO_APPROVE" == "true" ]]; then
        print_error "Refusing to auto-approve: $action"
        print_error "Fix the issue above and re-run, or re-run without --auto-approve to accept it explicitly."
        exit 1
    fi
    confirm_action "$action"
}

# Function to pause between steps
pause_step() {
    if [[ "$STEP_BY_STEP" == "true" ]]; then
        echo -e "${BLUE}Press Enter to continue to next step...${NC}"
        read -r
    fi
}

print_info "=== Amazon SageMaker HyperPod Inference Operator Migration Script ==="
print_info "This script will migrate from public Helm installation to EKS AddOn"
if [[ "$AUTO_APPROVE" == "true" ]]; then
    print_info "Running in auto-approve mode - no confirmation prompts except in case of rollback needed"
fi
echo

# Cluster name and region are needed before any AWS/kubectl call below
if [[ -z "$CLUSTER_NAME" ]]; then
    prompt_user "Enter your EKS cluster name:" CLUSTER_NAME
fi
if [[ -z "$AWS_REGION" ]]; then
    prompt_user "Enter your AWS region:" AWS_REGION
fi

# Validate the format of customer-provided role ARNs (same pattern the addon schema enforces)
ROLE_ARN_PATTERN='^arn:aws:iam::[0-9]{12}:role/.+$'
for provided_arn in "$USER_EXECUTION_ROLE_ARN" "$USER_ALB_ROLE_ARN" "$USER_KEDA_ROLE_ARN" "$USER_JS_GATED_ROLE_ARN"; do
    if [[ -n "$provided_arn" && ! "$provided_arn" =~ $ROLE_ARN_PATTERN ]]; then
        print_error "Invalid IAM role ARN: $provided_arn"
        exit 1
    fi
done

# Create an IAM role if it does not exist; record it for rollback only if this script created it.
# Usage: create_or_get_role <role-name> <trust-policy-file>   (prints the role ARN)
create_or_get_role() {
    local role_name="$1"
    local trust_file="$2"
    local arn
    if arn=$(aws iam create-role \
            --role-name "$role_name" \
            --assume-role-policy-document "file://$trust_file" \
            --path "/" \
            --query 'Role.Arn' --output text 2>/dev/null); then
        echo "$role_name" >> "$BACKUP_DIR/created-roles.txt"
    else
        # Role already exists (e.g. previous run). Reuse it and make sure the trust policy is the expected one.
        arn=$(aws iam get-role --role-name "$role_name" --query 'Role.Arn' --output text) || return 1
        aws iam update-assume-role-policy --role-name "$role_name" --policy-document "file://$trust_file" >/dev/null || return 1
    fi
    [[ -n "$arn" && "$arn" != "None" ]] || return 1
    echo "$arn"
}

# Warn if a customer-provided role cannot be assumed by the addon's service account.
# Usage: check_role_trust <role-arn> <service-account-subject>
check_role_trust() {
    local role_arn="$1"
    local expected_sub="$2"
    local role_name trust
    role_name=$(echo "$role_arn" | awk -F'role/' '{print $2}' | awk -F'/' '{print $NF}')
    if ! trust=$(aws iam get-role --role-name "$role_name" --query 'Role.AssumeRolePolicyDocument' --output json 2>/dev/null); then
        print_error "Provided role not found or not readable: $role_arn"
        exit 1
    fi
    if ! echo "$trust" | grep -q "$expected_sub" && ! echo "$trust" | grep -q 'system:serviceaccount:\*'; then
        print_warning "Role $role_arn does not appear to trust '$expected_sub'."
        print_warning "The addon will not be able to assume it unless the trust policy allows that service account."
        print_warning "Helm-era roles trust different service accounts (kube-system:aws-load-balancer-controller,"
        print_warning "kube-system:keda-operator, hyperpod-inference-system:hyperpod-inference-operator-controller-manager)."
        print_warning "Add the addon subject to the role's trust policy (keep the Helm subject if you want rollback to work)."
        confirm_risk "Continue with role $role_arn anyway"
    fi
}

# Warn if a customer-provided execution role cannot read/write the TLS buckets used by existing models.
# AmazonSageMakerHyperPodInferenceAccess does not grant access to customer TLS buckets, so the role needs
# explicit S3 permissions on every bucket (the script adds these itself only to roles it creates).
# Usage: check_tls_bucket_access <role-arn> <bucket>...
check_tls_bucket_access() {
    local role_arn="$1"; shift
    local bucket decisions missing=() acm_decisions
    # The operator tags everything it writes with CreatedBy=HyperPodInference, and the managed policy
    # (AmazonSageMakerHyperPodInferenceAccess) conditions on that tag, so pass it to the simulation.
    local ctx=("ContextKeyName=aws:ResourceAccount,ContextKeyValues=${ACCOUNT_ID},ContextKeyType=string"
               "ContextKeyName=aws:PrincipalAccount,ContextKeyValues=${ACCOUNT_ID},ContextKeyType=string"
               "ContextKeyName=s3:ExistingObjectTag/CreatedBy,ContextKeyValues=HyperPodInference,ContextKeyType=string"
               "ContextKeyName=s3:RequestObjectTag/CreatedBy,ContextKeyValues=HyperPodInference,ContextKeyType=string"
               "ContextKeyName=aws:RequestTag/CreatedBy,ContextKeyValues=HyperPodInference,ContextKeyType=string"
               "ContextKeyName=aws:ResourceTag/CreatedBy,ContextKeyValues=HyperPodInference,ContextKeyType=string"
               "ContextKeyName=aws:TagKeys,ContextKeyValues=CreatedBy,ContextKeyType=stringList"
               "ContextKeyName=aws:RequestedRegion,ContextKeyValues=${AWS_REGION},ContextKeyType=string")
    for bucket in "$@"; do
        [[ -z "$bucket" ]] && continue
        if ! decisions=$(aws iam simulate-principal-policy \
                --policy-source-arn "$role_arn" \
                --action-names s3:GetObject s3:PutObject s3:PutObjectTagging s3:DeleteObject \
                --resource-arns "arn:aws:s3:::${bucket}/migration-access-check" \
                --context-entries "${ctx[@]}" \
                --query 'EvaluationResults[].EvalDecision' --output text 2>/dev/null); then
            print_warning "Could not simulate S3 access for $role_arn (needs iam:SimulatePrincipalPolicy). Verify manually that it can Get/Put/Delete objects in: $*"
            return 0
        fi
        if [[ "$(echo "$decisions" | tr '\t' '\n' | grep -c '^allowed$')" -lt 4 ]]; then
            missing+=("$bucket")
        fi
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        print_warning "Execution role $role_arn may be missing s3:GetObject/PutObject/PutObjectTagging/DeleteObject on TLS bucket(s): ${missing[*]}"
        print_warning "AmazonSageMakerHyperPodInferenceAccess only covers buckets named hyperpod-tls*."
        print_warning "Existing models using these buckets can fail certificate operations after migration."
        print_warning "See the TLSBucketsAccess policy in the migration doc and attach it to this role."
        confirm_risk "Continue with execution role $role_arn anyway"
    fi
    # TLS certificates are imported into ACM and tagged CreatedBy=HyperPodInference
    acm_decisions=$(aws iam simulate-principal-policy \
            --policy-source-arn "$role_arn" \
            --action-names acm:ImportCertificate acm:AddTagsToCertificate acm:DeleteCertificate \
            --resource-arns "arn:aws:acm:${AWS_REGION}:${ACCOUNT_ID}:certificate/migration-access-check" \
            --context-entries "${ctx[@]}" \
            --query 'EvaluationResults[].EvalDecision' --output text 2>/dev/null) || return 0
    if [[ "$(echo "$acm_decisions" | tr '\t' '\n' | grep -c '^allowed$')" -lt 3 ]]; then
        print_warning "Execution role $role_arn may be missing acm:ImportCertificate/AddTagsToCertificate/DeleteCertificate."
        print_warning "New models will fail to import their TLS certificate. Attach AmazonSageMakerHyperPodInferenceAccess."
        confirm_risk "Continue with execution role $role_arn anyway"
    fi
}

# Configure kubectl for EKS cluster first
if [[ -n "$CLUSTER_NAME" && -n "$AWS_REGION" ]]; then
    print_info "Configuring kubectl for EKS cluster: $CLUSTER_NAME in region: $AWS_REGION"
    aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$AWS_REGION" || {
        print_error "Failed to configure kubectl for EKS cluster"
        exit 1
    }
    print_success "kubectl configured successfully"
fi

# Pre-migration validation
print_info "=== Pre-migration Validation ==="

# Check if inference addon is already installed
if aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name amazon-sagemaker-hyperpod-inference --region "$AWS_REGION" >/dev/null 2>&1; then
    print_info "Inference addon is already installed, no migration needed. Exiting."
    exit 0
fi

# Check if hyperpod-inference-system namespace exists
if ! kubectl get namespace hyperpod-inference-system >/dev/null 2>&1; then
    print_error "hyperpod-inference-system namespace does not exist"
    exit 1
fi
print_success "hyperpod-inference-system namespace exists"

# Check if hyperpod-inference-operator-controller-manager is running
if ! kubectl get deployment hyperpod-inference-operator-controller-manager -n hyperpod-inference-system >/dev/null 2>&1; then
    print_error "hyperpod-inference-operator-controller-manager deployment not found"
    exit 1
fi
print_success "hyperpod-inference-operator-controller-manager deployment exists"

# Check if helm deployment exists in kube-system
if ! helm list -n kube-system | grep -q hyperpod; then
    print_error "No hyperpod helm deployment found in kube-system namespace"
    exit 1
fi
print_success "Helm deployment found in kube-system"

print_success "Pre-migration validation completed"
echo

# Auto-derive values from Helm deployment
print_info "Auto-deriving configuration from existing Helm deployment..."

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    print_error "Helm is not installed or not in PATH"
    exit 1
fi

# Get Helm namespace (auto-detect or default to kube-system if not provided)
if [[ -z "$HELM_NAMESPACE" ]]; then
    print_info "Auto-detecting Helm namespace for hyperpod-inference-operator..."
    HELM_NAMESPACE=$(helm list -A | grep "hyperpod-inference-operator" | awk '{print $2}' | head -1)
    if [[ -z "$HELM_NAMESPACE" ]]; then
        print_error "Could not auto-detect Helm namespace. Available releases:"
        helm list -A | grep hyperpod || print_warning "No hyperpod releases found"
        exit 1
    else
        print_success "Found hyperpod-inference-operator in namespace: $HELM_NAMESPACE"
    fi
fi

# Check if the Helm release exists first
print_info "Checking for Helm release 'hyperpod-inference-operator' in namespace '$HELM_NAMESPACE'..."
if ! helm list -n "$HELM_NAMESPACE" -q | grep -q "^hyperpod-inference-operator$"; then
    print_error "Helm release 'hyperpod-inference-operator' not found in namespace '$HELM_NAMESPACE'"
    print_info "Available releases in namespace '$HELM_NAMESPACE':"
    helm list -n "$HELM_NAMESPACE" || print_warning "Could not list releases"
    print_info "All releases across namespaces:"
    helm list -A | grep hyperpod || print_warning "No hyperpod releases found"
    exit 1
fi

# Get Helm values with timeout
print_info "Retrieving Helm values..."
HELM_VALUES=$(helm get values hyperpod-inference-operator -n "$HELM_NAMESPACE" -o json 2>/dev/null || echo "{}")

if [[ "$HELM_VALUES" == "{}" ]]; then
    print_error "Could not retrieve Helm values. Command timed out or failed."
    print_info "Please check:"
    print_info "1. Kubectl context is correct: $(kubectl config current-context)"
    print_info "2. Namespace exists: kubectl get ns $HELM_NAMESPACE"
    print_info "3. Release exists: helm list -n $HELM_NAMESPACE"
    exit 1
fi

print_success "Successfully retrieved Helm configuration"

# Extract values from Helm
HYPERPOD_CLUSTER_ARN=$(echo "$HELM_VALUES" | jq -r '.hyperpodClusterArn // empty')
HELM_EXECUTION_ROLE_ARN=$(echo "$HELM_VALUES" | jq -r '.executionRoleArn // empty')
TLS_BUCKET_NAME=$(echo "$HELM_VALUES" | jq -r '.tlsCertificateS3Bucket // empty' | sed 's|^s3://||')
TLS_BUCKETS=("$TLS_BUCKET_NAME")

# Get JS models and IEC models deployed on the cluster
print_info "Getting JS models and IEC models deployed on the cluster..."
JS_MODELS=$(kubectl get jsmodels -A -o json 2>/dev/null || echo '{"items":[]}')
IEC_MODELS=$(kubectl get inferenceendpointconfigs -A -o json 2>/dev/null || echo '{"items":[]}')

# Get unique set of TLS buckets from models
JS_BUCKETS=$(echo "$JS_MODELS" | jq -r '.items[].spec.tlsCertificateS3Bucket // empty' 2>/dev/null | sed 's|^s3://||' | grep -v '^$' || true)
IEC_BUCKETS=$(echo "$IEC_MODELS" | jq -r '.items[].spec.tlsCertificateS3Bucket // empty' 2>/dev/null | sed 's|^s3://||' | grep -v '^$' || true)

# Get TLS buckets from status as well
JS_STATUS_BUCKETS=$(echo "$JS_MODELS" | jq -r '.items[].status.tlsCertificateS3Bucket // empty' 2>/dev/null | sed 's|^s3://||' | grep -v '^$' || true)
IEC_STATUS_BUCKETS=$(echo "$IEC_MODELS" | jq -r '.items[].status.tlsCertificateS3Bucket // empty' 2>/dev/null | sed 's|^s3://||' | grep -v '^$' || true)

# Combine all buckets and get unique set
ALL_BUCKETS=$(echo -e "$TLS_BUCKET_NAME\n$JS_BUCKETS\n$IEC_BUCKETS\n$JS_STATUS_BUCKETS\n$IEC_STATUS_BUCKETS" | grep -v '^$' | sort -u || true)
TLS_BUCKETS=($(echo "$ALL_BUCKETS" | tr '\n' ' '))

# Tag ALB resources, ACM imports, S3 TLS certificates
print_info "Tagging resources with HyperPodInference tags..."
TAG_KEY="CreatedBy"
TAG_VALUE="HyperPodInference"

# Extract ALB ARNs from ingress resources created by inference models
INGRESS_HOSTNAMES=$(kubectl get ingress -A -o json | jq -r '.items[] | select(.metadata.name | test("alb-.*")) | .status.loadBalancer.ingress[]?.hostname // empty' 2>/dev/null | grep -v '^$' || true)

# Get ALB ARNs from hostnames and tag them
for hostname in $INGRESS_HOSTNAMES; do
    if [[ -n "$hostname" ]]; then
        ALB_ARN=$(aws elbv2 describe-load-balancers --region "$AWS_REGION" --query "LoadBalancers[?DNSName=='$hostname'].LoadBalancerArn" --output text 2>/dev/null || true)
        if [[ -n "$ALB_ARN" && "$ALB_ARN" != "None" ]]; then
            EXISTING_TAG=$(aws elbv2 describe-tags --resource-arns "$ALB_ARN" --region "$AWS_REGION" --query "TagDescriptions[0].Tags[?Key=='$TAG_KEY'].Value | [0]" --output text 2>/dev/null || true)
            if [[ "$EXISTING_TAG" == "$TAG_VALUE" ]]; then
                print_info "ALB already tagged: $ALB_ARN"
            else
                print_info "Tagging ALB: $ALB_ARN"
                # Only tags added by this script are recorded, so rollback never strips the operator's own tags
                aws elbv2 add-tags --resource-arns "$ALB_ARN" --tags Key="$TAG_KEY",Value="$TAG_VALUE" --region "$AWS_REGION" \
                    && echo "$ALB_ARN" >> "$BACKUP_DIR/alb-arns.txt" || print_warning "Failed to tag ALB: $ALB_ARN"
            fi
        fi
    fi
done

# Extract ACM ARNs from ingress annotations and model status
INGRESS_ACM_ARNS=$(kubectl get ingress -A -o json | jq -r '.items[] | select(.metadata.name | test("alb-.*")) | .metadata.annotations["alb.ingress.kubernetes.io/certificate-arn"] // empty' 2>/dev/null | grep -v '^$' || true)
JS_ACM_ARNS=$(echo "$JS_MODELS" | jq -r '.items[].status.certificateArn // empty' 2>/dev/null | grep -v '^$' || true)
IEC_ACM_ARNS=$(echo "$IEC_MODELS" | jq -r '.items[].status.tlsCertificate.certificateARN // empty' 2>/dev/null | grep -v '^$' || true)

# Tag ACM certificates created by inference
for cert_arn in $INGRESS_ACM_ARNS $JS_ACM_ARNS $IEC_ACM_ARNS; do
    if [[ -n "$cert_arn" ]]; then
        grep -qx "$cert_arn" "$BACKUP_DIR/acm-seen.txt" 2>/dev/null && continue
        echo "$cert_arn" >> "$BACKUP_DIR/acm-seen.txt"
        EXISTING_TAG=$(aws acm list-tags-for-certificate --certificate-arn "$cert_arn" --region "$AWS_REGION" --query "Tags[?Key=='$TAG_KEY'].Value | [0]" --output text 2>/dev/null || true)
        if [[ "$EXISTING_TAG" == "$TAG_VALUE" ]]; then
            print_info "ACM certificate already tagged: $cert_arn"
        else
            print_info "Tagging ACM certificate: $cert_arn"
            aws acm add-tags-to-certificate --certificate-arn "$cert_arn" --tags Key="$TAG_KEY",Value="$TAG_VALUE" --region "$AWS_REGION" \
                && echo "$cert_arn" >> "$BACKUP_DIR/acm-arns.txt" || print_warning "Failed to tag ACM certificate: $cert_arn"
        fi
    fi
done

# Tag S3 TLS certificates used by inference models
JS_CERT_KEYS=$(echo "$JS_MODELS" | jq -r '.items[].status.tlsCertificateS3Key // empty' 2>/dev/null | grep -v '^$' || true)
IEC_CERT_KEYS=$(echo "$IEC_MODELS" | jq -r '.items[].status.tlsCertificateS3Key // empty' 2>/dev/null | grep -v '^$' || true)

for bucket in "${TLS_BUCKETS[@]}"; do
    if [[ -n "$bucket" ]]; then
        # Tag specific certificate objects
        for cert_key in $JS_CERT_KEYS $IEC_CERT_KEYS; do
            if [[ -n "$cert_key" ]]; then
                # put-object-tagging replaces the whole tag set: merge with existing tags and save the
                # original set so rollback restores it exactly.
                ORIG_TAGS=$(aws s3api get-object-tagging --bucket "$bucket" --key "$cert_key" --query 'TagSet' --output json 2>/dev/null) || continue
                if echo "$ORIG_TAGS" | jq -e --arg k "$TAG_KEY" --arg v "$TAG_VALUE" 'any(.[]; .Key==$k and .Value==$v)' >/dev/null; then
                    continue
                fi
                MERGED_TAGS=$(echo "$ORIG_TAGS" | jq -c --arg k "$TAG_KEY" --arg v "$TAG_VALUE" '{TagSet: ([.[] | select(.Key != $k)] + [{Key:$k, Value:$v}])}')
                if aws s3api put-object-tagging --bucket "$bucket" --key "$cert_key" --tagging "$MERGED_TAGS" 2>/dev/null; then
                    echo "$bucket|$cert_key|$(echo "$ORIG_TAGS" | jq -c '{TagSet: .}')" >> "$BACKUP_DIR/s3-objects.txt"
                fi
            fi
        done
    fi
done

print_success "Resource tagging completed"

# Get OIDC issuer URL for trust policies
print_info "Getting OIDC issuer URL for cluster..."
OIDC_ISSUER=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" --query "cluster.identity.oidc.issuer" --output text | sed 's|https://||')
print_success "OIDC Issuer: $OIDC_ISSUER"

# Get S3 role ARN from Helm values or service account
if [[ -z "$S3_MOUNTPOINT_ROLE_ARN" ]]; then
    S3_HELM_ROLE=$(echo "$HELM_VALUES" | jq -r '.s3.serviceAccount.roleArn // empty')
    if [[ -n "$S3_HELM_ROLE" && "$S3_HELM_ROLE" != "null" ]]; then
        S3_MOUNTPOINT_ROLE_ARN="$S3_HELM_ROLE"
    else
        S3_SA_ANNOTATION=$(kubectl get serviceaccount s3-csi-driver-sa -n kube-system -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}' 2>/dev/null || echo "")
        S3_MOUNTPOINT_ROLE_ARN="$S3_SA_ANNOTATION"
    fi
fi

# Get FSX role ARN from Helm values or service account
if [[ -z "$FSX_ROLE_ARN" ]]; then
    FSX_HELM_ROLE=$(echo "$HELM_VALUES" | jq -r '.fsx.serviceAccount.roleArn // empty')
    if [[ -n "$FSX_HELM_ROLE" && "$FSX_HELM_ROLE" != "null" ]]; then
        FSX_ROLE_ARN="$FSX_HELM_ROLE"
    else
        FSX_SA_ANNOTATION=$(kubectl get serviceaccount fsx-csi-controller-sa -n kube-system -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}' 2>/dev/null || echo "")
        FSX_ROLE_ARN="$FSX_SA_ANNOTATION"
    fi
fi

# Function to check if CSI driver exists
check_csi_driver() {
    local provisioner="$1"
    local friendly="$2"
    
    # Try with error capture
    if kubectl get csidriver "$provisioner" >/dev/null 2>&1 || \
       kubectl get csidrivers.storage.k8s.io "$provisioner" >/dev/null 2>&1; then
        return 0
    fi
    
    # Capture error for better diagnostics
    err_msg="$(kubectl get csidriver "$provisioner" 2>&1 || true)"
    [ -z "$err_msg" ] && err_msg="$(kubectl get csidrivers.storage.k8s.io "$provisioner" 2>&1 || true)"
    
    if echo "$err_msg" | grep -qiE 'forbidden|permission|unauthorized|cannot.*get'; then
        print_error "$friendly check failed: RBAC insufficient to read CSIDriver $provisioner"
        exit 2
    fi
    
    return 1
}

# Check if S3 CSI driver already exists
if check_csi_driver "s3.csi.aws.com" "S3 CSI driver"; then
    print_info "S3 CSI driver already exists, skipping S3 addon installation"
    SKIP_S3_ADDON=true
else
    if [[ -z "$S3_MOUNTPOINT_ROLE_ARN" ]]; then
        S3_SA_ANNOTATION=$(kubectl get serviceaccount s3-csi-driver-sa -n kube-system -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}' 2>/dev/null || echo "")
        S3_MOUNTPOINT_ROLE_ARN="$S3_SA_ANNOTATION"
    fi
    SKIP_S3_ADDON=false
fi

# Check if FSX CSI driver already exists
if check_csi_driver "fsx.csi.aws.com" "FSX CSI driver"; then
    print_info "FSX CSI driver already exists, skipping FSX addon installation"
    SKIP_FSX_ADDON=true
else
    if [[ -z "$FSX_ROLE_ARN" ]]; then
        FSX_SA_ANNOTATION=$(kubectl get serviceaccount fsx-csi-controller-sa -n kube-system -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}' 2>/dev/null || echo "")
        FSX_ROLE_ARN="$FSX_SA_ANNOTATION"
    fi
    SKIP_FSX_ADDON=false
fi

# Show auto-derived values
echo -e "${GREEN}Auto-derived values:${NC}"
echo "HyperPod Cluster ARN: $HYPERPOD_CLUSTER_ARN"
echo "Helm Execution Role ARN (not reused by addon): $HELM_EXECUTION_ROLE_ARN"
echo "TLS Bucket Name: $TLS_BUCKET_NAME"
if [[ "$SKIP_S3_ADDON" == "false" ]]; then
    echo "S3 Mountpoint Role ARN: $S3_MOUNTPOINT_ROLE_ARN"
else
    echo "S3 Mountpoint: Skipping (CSI driver exists)"
fi
if [[ "$SKIP_FSX_ADDON" == "false" ]]; then
    echo "FSX Role ARN: $FSX_ROLE_ARN"
else
    echo "FSX: Skipping (CSI driver exists)"
fi
echo -e "${GREEN}Addon roles (provided via flags, or created by this script):${NC}"
echo "Execution Role: ${USER_EXECUTION_ROLE_ARN:-<will be created>}"
echo "ALB Controller Role: ${USER_ALB_ROLE_ARN:-<will be created>}"
echo "KEDA Role: ${USER_KEDA_ROLE_ARN:-<will be created>}"
echo "JumpStart Gated Model Role: ${USER_JS_GATED_ROLE_ARN:-<will be created>}"
echo

# Validate required values
if [[ -z "$HYPERPOD_CLUSTER_ARN" ]]; then
    prompt_user "HyperPod Cluster ARN not found. Enter manually:" HYPERPOD_CLUSTER_ARN
fi
if [[ -z "$TLS_BUCKET_NAME" ]]; then
    prompt_user "TLS Bucket Name not found. Enter manually:" TLS_BUCKET_NAME
    TLS_BUCKETS+=("$TLS_BUCKET_NAME")
fi

# Extract HyperPod cluster ID for unique role naming
HYPERPOD_CLUSTER_ID=$(echo "$HYPERPOD_CLUSTER_ARN" | cut -d'/' -f2 | cut -c1-8)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OIDC_PROVIDER_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/${OIDC_ISSUER}"

# Addon service accounts (all in the addon namespace hyperpod-inference-system)
EXECUTION_SA_SUB="system:serviceaccount:hyperpod-inference-system:hyperpod-inference-controller-manager"
ALB_SA_SUB="system:serviceaccount:hyperpod-inference-system:aws-load-balancer-controller"
KEDA_SA_SUB="system:serviceaccount:hyperpod-inference-system:keda-operator"
JS_GATED_SA_SUB="system:serviceaccount:*:hyperpod-inference-service-account*"

# Pre-flight: addon configuration constraints (checked before any role or cluster change)
# The addon configuration schema requires the bucket name to contain "tls"
TLS_BUCKET_PATTERN='^[a-z0-9][a-z0-9.-]*tls[a-z0-9.-]*[a-z0-9]$'
if [[ ! "$TLS_BUCKET_NAME" =~ $TLS_BUCKET_PATTERN ]]; then
    print_error "TLS bucket name '$TLS_BUCKET_NAME' is not accepted by the addon (the name must contain 'tls')."
    print_info "Create a bucket whose name contains 'tls', grant the execution role access to it, and re-run."
    print_info "Existing models keep using their current buckets (covered by the TLSBucketsAccess policy)."
    exit 1
fi
print_success "TLS bucket name is valid for the addon"

K8S_VERSION=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" --query 'cluster.version' --output text)
SUPPORTED_VERSIONS=$(aws eks describe-addon-versions \
    --addon-name amazon-sagemaker-hyperpod-inference \
    --kubernetes-version "$K8S_VERSION" \
    --region "$AWS_REGION" \
    --query 'addons[].addonVersions[].addonVersion' --output text 2>/dev/null || true)
if [[ -z "$ADDON_VERSION" ]]; then
    # Resolve the EKS default version for this Kubernetes version (what create-addon would pick
    # without --addon-version). Resolved explicitly so the configuration below matches its schema.
    print_info "Resolving default amazon-sagemaker-hyperpod-inference addon version for Kubernetes $K8S_VERSION..."
    ADDON_VERSION=$(aws eks describe-addon-versions \
        --addon-name amazon-sagemaker-hyperpod-inference \
        --kubernetes-version "$K8S_VERSION" \
        --region "$AWS_REGION" \
        --query 'addons[0].addonVersions[?compatibilities[?defaultVersion==`true`]].addonVersion | [0]' \
        --output text 2>/dev/null || true)
    if [[ -z "$ADDON_VERSION" || "$ADDON_VERSION" == "None" ]]; then
        print_error "Could not determine the default addon version for Kubernetes $K8S_VERSION in $AWS_REGION."
        print_info "Available versions: ${SUPPORTED_VERSIONS:-none}"
        print_info "Re-run with --addon-version <version>."
        exit 1
    fi
    print_success "Using default addon version: $ADDON_VERSION"
else
    print_info "Validating requested addon version $ADDON_VERSION for this cluster..."
    if ! echo "$SUPPORTED_VERSIONS" | tr '\t' '\n' | grep -qx "$ADDON_VERSION"; then
        print_error "Addon version $ADDON_VERSION is not available for Kubernetes $K8S_VERSION in $AWS_REGION."
        print_info "Available versions: ${SUPPORTED_VERSIONS:-none}"
        print_info "Re-run with --addon-version <version> using one of the versions above."
        exit 1
    fi
    print_success "Addon version $ADDON_VERSION is supported on Kubernetes $K8S_VERSION"
fi

# The inferenceGateway configuration key exists from v2.0.0 (where the gateway is enabled by default).
# Older versions reject unknown keys, so only send it when the version supports it.
ADDON_MAJOR_VERSION=$(echo "$ADDON_VERSION" | sed -E 's/^v([0-9]+)\..*/\1/')
if [[ "$ADDON_MAJOR_VERSION" =~ ^[0-9]+$ ]] && (( ADDON_MAJOR_VERSION >= 2 )); then
    DISABLE_INFERENCE_GATEWAY=true
else
    DISABLE_INFERENCE_GATEWAY=false
fi

# ---------------------------------------------------------------------------
# Step 1: Addon IAM roles
# Trust and permissions mirror the HyperPod Inference addon CloudFormation flow
# (the same trust and permissions the HyperPod console add-on setup uses). Helm-era roles
# are left untouched so the rollback on failure can restore Helm.
# ---------------------------------------------------------------------------
print_info "Step 1: Preparing IAM roles for the addon..."

# Validate every customer-provided role before creating anything, so a bad role stops the
# migration with no partial changes.
[[ -n "$USER_EXECUTION_ROLE_ARN" ]] && check_role_trust "$USER_EXECUTION_ROLE_ARN" "$EXECUTION_SA_SUB"
if [[ -n "$USER_EXECUTION_ROLE_ARN" ]]; then
    print_info "TLS bucket(s) in use by this cluster: ${TLS_BUCKETS[*]}"
    check_tls_bucket_access "$USER_EXECUTION_ROLE_ARN" "${TLS_BUCKETS[@]}"
fi
[[ -n "$USER_JS_GATED_ROLE_ARN" ]] && check_role_trust "$USER_JS_GATED_ROLE_ARN" "hyperpod-inference-service-account"
[[ -n "$USER_ALB_ROLE_ARN" ]] && check_role_trust "$USER_ALB_ROLE_ARN" "$ALB_SA_SUB"
[[ -n "$USER_KEDA_ROLE_ARN" ]] && check_role_trust "$USER_KEDA_ROLE_ARN" "$KEDA_SA_SUB"

# 1a. Inference operator execution role
if [[ -n "$USER_EXECUTION_ROLE_ARN" ]]; then
    print_info "Using provided execution role: $USER_EXECUTION_ROLE_ARN"
    NEW_EXECUTION_ROLE_ARN="$USER_EXECUTION_ROLE_ARN"
else
    confirm_action "Create execution role for addon"
    NEW_EXECUTION_ROLE_NAME="SageMakerHyperPodInference-${HYPERPOD_CLUSTER_ID}-execution-role"
    cat > /tmp/execution-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "sagemaker.amazonaws.com"},
      "Action": "sts:AssumeRole"
    },
    {
      "Effect": "Allow",
      "Principal": {"Federated": "${OIDC_PROVIDER_ARN}"},
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringLike": {
          "${OIDC_ISSUER}:aud": "sts.amazonaws.com",
          "${OIDC_ISSUER}:sub": "${EXECUTION_SA_SUB}"
        }
      }
    }
  ]
}
EOF
    NEW_EXECUTION_ROLE_ARN=$(create_or_get_role "$NEW_EXECUTION_ROLE_NAME" /tmp/execution-trust-policy.json)
    aws iam attach-role-policy --role-name "$NEW_EXECUTION_ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/AmazonSageMakerHyperPodInferenceAccess"

    # TLS buckets already used by existing models (Helm values + JumpStartModel/InferenceEndpointConfig specs and status),
    # so the addon operator can keep reading/rotating their certificates.
    S3_OBJECT_RESOURCES=""
    for bucket in "${TLS_BUCKETS[@]}"; do
        if [[ -n "$bucket" ]]; then
            S3_OBJECT_RESOURCES="$S3_OBJECT_RESOURCES\"arn:aws:s3:::$bucket/*\","
        fi
    done
    S3_OBJECT_RESOURCES=${S3_OBJECT_RESOURCES%,}
    if [[ -n "$S3_OBJECT_RESOURCES" ]]; then
        cat > /tmp/s3-inline-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TLSBucketDeleteObjectsPermission",
      "Effect": "Allow",
      "Action": ["s3:DeleteObject"],
      "Resource": [$S3_OBJECT_RESOURCES],
      "Condition": {"StringEquals": {"aws:ResourceAccount": "\${aws:PrincipalAccount}"}}
    },
    {
      "Sid": "TLSBucketGetObjectAccess",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": [$S3_OBJECT_RESOURCES]
    },
    {
      "Sid": "TLSBucketPutObjectAccess",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:PutObjectTagging"],
      "Resource": [$S3_OBJECT_RESOURCES],
      "Condition": {"StringEquals": {"aws:ResourceAccount": "\${aws:PrincipalAccount}"}}
    }
  ]
}
EOF
        aws iam put-role-policy --role-name "$NEW_EXECUTION_ROLE_NAME" --policy-name "TLSBucketsAccess" --policy-document file:///tmp/s3-inline-policy.json
    fi
    print_success "Execution role ready: $NEW_EXECUTION_ROLE_ARN"
fi

# 1b. JumpStart gated model download role
if [[ -n "$USER_JS_GATED_ROLE_ARN" ]]; then
    print_info "Using provided JumpStart gated model role: $USER_JS_GATED_ROLE_ARN"
    JS_GATED_MODEL_ROLE_ARN="$USER_JS_GATED_ROLE_ARN"
else
    confirm_action "Create JumpStart gated model role for addon"
    JS_GATED_MODEL_ROLE_NAME="js-gated-role-${HYPERPOD_CLUSTER_ID}"
    cat > /tmp/js-gated-model-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "sagemaker.amazonaws.com"},
      "Action": "sts:AssumeRole"
    },
    {
      "Effect": "Allow",
      "Principal": {"Federated": "${OIDC_PROVIDER_ARN}"},
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringLike": {
          "${OIDC_ISSUER}:aud": "sts.amazonaws.com",
          "${OIDC_ISSUER}:sub": "${JS_GATED_SA_SUB}"
        }
      }
    }
  ]
}
EOF
    JS_GATED_MODEL_ROLE_ARN=$(create_or_get_role "$JS_GATED_MODEL_ROLE_NAME" /tmp/js-gated-model-trust-policy.json)
    aws iam attach-role-policy --role-name "$JS_GATED_MODEL_ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/AmazonSageMakerHyperPodGatedModelAccess"
    print_success "JumpStart gated model role ready: $JS_GATED_MODEL_ROLE_ARN"
fi

# 1c. AWS Load Balancer Controller role
if [[ -n "$USER_ALB_ROLE_ARN" ]]; then
    print_info "Using provided ALB controller role: $USER_ALB_ROLE_ARN"
    ALB_ROLE_ARN="$USER_ALB_ROLE_ARN"
else
    confirm_action "Create ALB controller role for addon (Helm-era role preserved for rollback)"
    NEW_ALB_ROLE_NAME="SageMakerHP-ALB-${HYPERPOD_CLUSTER_ID}-addon"
    cat > /tmp/alb-trust-policy-new.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "${OIDC_PROVIDER_ARN}"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "${OIDC_ISSUER}:aud": "sts.amazonaws.com",
        "${OIDC_ISSUER}:sub": "${ALB_SA_SUB}"
      }
    }
  }]
}
EOF
    cat > /tmp/alb-permissions-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iam:CreateServiceLinkedRole"],
      "Resource": "*",
      "Condition": {"StringEquals": {"iam:AWSServiceName": "elasticloadbalancing.amazonaws.com"}}
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeAccountAttributes",
        "ec2:DescribeAddresses",
        "ec2:DescribeAvailabilityZones",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeVpcs",
        "ec2:DescribeVpcPeeringConnections",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeInstances",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeTags",
        "ec2:GetCoipPoolUsage",
        "ec2:DescribeCoipPools",
        "ec2:GetSecurityGroupsForVpc",
        "ec2:DescribeIpamPools",
        "ec2:DescribeRouteTables",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeLoadBalancerAttributes",
        "elasticloadbalancing:DescribeListeners",
        "elasticloadbalancing:DescribeListenerCertificates",
        "elasticloadbalancing:DescribeSSLPolicies",
        "elasticloadbalancing:DescribeRules",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeTargetGroupAttributes",
        "elasticloadbalancing:DescribeTargetHealth",
        "elasticloadbalancing:DescribeTags",
        "elasticloadbalancing:DescribeTrustStores",
        "elasticloadbalancing:DescribeListenerAttributes",
        "elasticloadbalancing:DescribeCapacityReservation"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:DescribeUserPoolClient",
        "acm:ListCertificates",
        "acm:DescribeCertificate",
        "iam:ListServerCertificates",
        "iam:GetServerCertificate",
        "waf-regional:GetWebACL",
        "waf-regional:GetWebACLForResource",
        "waf-regional:AssociateWebACL",
        "waf-regional:DisassociateWebACL",
        "wafv2:GetWebACL",
        "wafv2:GetWebACLForResource",
        "wafv2:AssociateWebACL",
        "wafv2:DisassociateWebACL",
        "shield:GetSubscriptionState",
        "shield:DescribeProtection",
        "shield:CreateProtection",
        "shield:DeleteProtection"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["ec2:AuthorizeSecurityGroupIngress", "ec2:RevokeSecurityGroupIngress"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["ec2:CreateSecurityGroup"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["ec2:CreateTags"],
      "Resource": "arn:aws:ec2:*:*:security-group/*",
      "Condition": {
        "StringEquals": {"ec2:CreateAction": "CreateSecurityGroup"},
        "Null": {"aws:RequestTag/elbv2.k8s.aws/cluster": "false"}
      }
    },
    {
      "Effect": "Allow",
      "Action": ["ec2:CreateTags", "ec2:DeleteTags"],
      "Resource": "arn:aws:ec2:*:*:security-group/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/elbv2.k8s.aws/cluster": "true",
          "aws:ResourceTag/elbv2.k8s.aws/cluster": "false"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": ["ec2:AuthorizeSecurityGroupIngress", "ec2:RevokeSecurityGroupIngress", "ec2:DeleteSecurityGroup"],
      "Resource": "*",
      "Condition": {"Null": {"aws:ResourceTag/elbv2.k8s.aws/cluster": "false"}}
    },
    {
      "Effect": "Allow",
      "Action": ["elasticloadbalancing:CreateLoadBalancer", "elasticloadbalancing:CreateTargetGroup"],
      "Resource": "*",
      "Condition": {"Null": {"aws:RequestTag/elbv2.k8s.aws/cluster": "false"}}
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:CreateListener",
        "elasticloadbalancing:DeleteListener",
        "elasticloadbalancing:CreateRule",
        "elasticloadbalancing:DeleteRule"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["elasticloadbalancing:AddTags", "elasticloadbalancing:RemoveTags"],
      "Resource": [
        "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
        "arn:aws:elasticloadbalancing:*:*:loadbalancer/net/*/*",
        "arn:aws:elasticloadbalancing:*:*:loadbalancer/app/*/*"
      ],
      "Condition": {
        "Null": {
          "aws:RequestTag/elbv2.k8s.aws/cluster": "true",
          "aws:ResourceTag/elbv2.k8s.aws/cluster": "false"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": ["elasticloadbalancing:AddTags", "elasticloadbalancing:RemoveTags"],
      "Resource": [
        "arn:aws:elasticloadbalancing:*:*:listener/net/*/*/*",
        "arn:aws:elasticloadbalancing:*:*:listener/app/*/*/*",
        "arn:aws:elasticloadbalancing:*:*:listener-rule/net/*/*/*",
        "arn:aws:elasticloadbalancing:*:*:listener-rule/app/*/*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:ModifyLoadBalancerAttributes",
        "elasticloadbalancing:SetIpAddressType",
        "elasticloadbalancing:SetSecurityGroups",
        "elasticloadbalancing:SetSubnets",
        "elasticloadbalancing:DeleteLoadBalancer",
        "elasticloadbalancing:ModifyTargetGroup",
        "elasticloadbalancing:ModifyTargetGroupAttributes",
        "elasticloadbalancing:DeleteTargetGroup",
        "elasticloadbalancing:ModifyListenerAttributes",
        "elasticloadbalancing:ModifyCapacityReservation",
        "elasticloadbalancing:ModifyIpPools"
      ],
      "Resource": "*",
      "Condition": {"Null": {"aws:ResourceTag/elbv2.k8s.aws/cluster": "false"}}
    },
    {
      "Effect": "Allow",
      "Action": ["elasticloadbalancing:AddTags"],
      "Resource": [
        "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
        "arn:aws:elasticloadbalancing:*:*:loadbalancer/net/*/*",
        "arn:aws:elasticloadbalancing:*:*:loadbalancer/app/*/*"
      ],
      "Condition": {
        "StringEquals": {"elasticloadbalancing:CreateAction": ["CreateTargetGroup", "CreateLoadBalancer"]},
        "Null": {"aws:RequestTag/elbv2.k8s.aws/cluster": "false"}
      }
    },
    {
      "Effect": "Allow",
      "Action": ["elasticloadbalancing:RegisterTargets", "elasticloadbalancing:DeregisterTargets"],
      "Resource": "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:SetWebAcl",
        "elasticloadbalancing:ModifyListener",
        "elasticloadbalancing:AddListenerCertificates",
        "elasticloadbalancing:RemoveListenerCertificates",
        "elasticloadbalancing:ModifyRule",
        "elasticloadbalancing:SetRulePriorities"
      ],
      "Resource": "*"
    }
  ]
}
EOF
    ALB_ROLE_ARN=$(create_or_get_role "$NEW_ALB_ROLE_NAME" /tmp/alb-trust-policy-new.json)
    aws iam put-role-policy --role-name "$NEW_ALB_ROLE_NAME" --policy-name "HyperPodInferenceAlbControllerAccess" --policy-document file:///tmp/alb-permissions-policy.json
    print_success "ALB controller role ready: $ALB_ROLE_ARN"
fi

# 1d. KEDA role
if [[ -n "$USER_KEDA_ROLE_ARN" ]]; then
    print_info "Using provided KEDA role: $USER_KEDA_ROLE_ARN"
    KEDA_ROLE_ARN="$USER_KEDA_ROLE_ARN"
else
    confirm_action "Create KEDA role for addon (Helm-era role preserved for rollback)"
    NEW_KEDA_ROLE_NAME="SageMakerHP-KEDA-${HYPERPOD_CLUSTER_ID}-addon"
    cat > /tmp/keda-trust-policy-new.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "${OIDC_PROVIDER_ARN}"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "${OIDC_ISSUER}:aud": "sts.amazonaws.com",
        "${OIDC_ISSUER}:sub": "${KEDA_SA_SUB}"
      }
    }
  }]
}
EOF
    cat > /tmp/keda-permissions-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["cloudwatch:GetMetricData", "cloudwatch:GetMetricStatistics", "cloudwatch:ListMetrics"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["aps:QueryMetrics", "aps:GetLabels", "aps:GetSeries", "aps:GetMetricMetadata"],
      "Resource": "*"
    }
  ]
}
EOF
    KEDA_ROLE_ARN=$(create_or_get_role "$NEW_KEDA_ROLE_NAME" /tmp/keda-trust-policy-new.json)
    aws iam put-role-policy --role-name "$NEW_KEDA_ROLE_NAME" --policy-name "HyperPodInferenceKedaAccess" --policy-document file:///tmp/keda-permissions-policy.json
    print_success "KEDA role ready: $KEDA_ROLE_ARN"
fi

rm -f /tmp/execution-trust-policy.json /tmp/s3-inline-policy.json /tmp/js-gated-model-trust-policy.json \
      /tmp/alb-trust-policy-new.json /tmp/alb-permissions-policy.json \
      /tmp/keda-trust-policy-new.json /tmp/keda-permissions-policy.json
pause_step

# Step 4: Create S3 mountpoint role and install addon if needed
# Check if S3 addon already exists
if aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name aws-mountpoint-s3-csi-driver --region "$AWS_REGION" >/dev/null 2>&1; then
    print_info "S3 mountpoint addon already exists, skipping installation"
    SKIP_S3_ADDON=true
elif check_csi_driver "s3.csi.aws.com" "S3 CSI driver"; then
    print_info "S3 CSI driver already exists, skipping S3 addon installation"
    SKIP_S3_ADDON=true
else
    SKIP_S3_ADDON=false
fi

# Create or reuse S3 mountpoint role
if [[ "$SKIP_S3_ADDON" == "false" ]]; then
    if [[ -z "$S3_MOUNTPOINT_ROLE_ARN" ]]; then
        print_info "Step 4a: Creating S3 mountpoint role..."
        S3_ROLE_NAME="${CLUSTER_NAME}-${HYPERPOD_CLUSTER_ID}-s3-csi-driver-role"
    
    # Create S3 mountpoint policy
    S3_POLICY_NAME="${CLUSTER_NAME}-s3-csi-driver-policy"
    S3_POLICY_DOC=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MountpointFullBucketAccess",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["arn:aws:s3:::*"]
    },
    {
      "Sid": "MountpointObjectReadAccess",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:AbortMultipartUpload", "s3:DeleteObject"],
      "Resource": ["arn:aws:s3:::*/*"]
    }
  ]
}
EOF
)
    
    # Create policy
    echo "$S3_POLICY_DOC" > /tmp/s3-policy.json
    S3_POLICY_ARN=$(aws iam create-policy \
        --policy-name "$S3_POLICY_NAME" \
        --policy-document file:///tmp/s3-policy.json \
        --query 'Policy.Arn' --output text 2>/dev/null || \
        aws iam get-policy --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$S3_POLICY_NAME" --query 'Policy.Arn' --output text)
    
    # Create S3 role trust policy
    S3_TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):oidc-provider/$OIDC_ISSUER"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "$OIDC_ISSUER:aud": "sts.amazonaws.com",
          "$OIDC_ISSUER:sub": "system:serviceaccount:kube-system:s3-csi-driver-sa"
        }
      }
    }
  ]
}
EOF
)
    
    # Create role
    echo "$S3_TRUST_POLICY" > /tmp/s3-trust-policy.json
    S3_MOUNTPOINT_ROLE_ARN=$(aws iam create-role \
        --role-name "$S3_ROLE_NAME" \
        --assume-role-policy-document file:///tmp/s3-trust-policy.json \
        --path "/" \
        --query 'Role.Arn' --output text 2>/dev/null || \
        aws iam get-role --role-name "$S3_ROLE_NAME" --query 'Role.Arn' --output text)
    
    # Attach policy to role
    aws iam attach-role-policy --role-name "$S3_ROLE_NAME" --policy-arn "$S3_POLICY_ARN"
    
    print_success "S3 mountpoint role created: $S3_MOUNTPOINT_ROLE_ARN"
    else
        print_info "Reusing existing S3 mountpoint role: $S3_MOUNTPOINT_ROLE_ARN"
    fi
fi

# Step 4b: Create FSX role and install addon if needed
# Check if FSX addon already exists
if aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name aws-fsx-csi-driver --region "$AWS_REGION" >/dev/null 2>&1; then
    print_info "FSX addon already exists, skipping installation"
    SKIP_FSX_ADDON=true
elif check_csi_driver "fsx.csi.aws.com" "FSX CSI driver"; then
    print_info "FSX CSI driver already exists, skipping FSX addon installation"
    SKIP_FSX_ADDON=true
else
    SKIP_FSX_ADDON=false
fi

# Create or reuse FSX role
if [[ "$SKIP_FSX_ADDON" == "false" ]]; then
    if [[ -z "$FSX_ROLE_ARN" ]]; then
        print_info "Step 4b: Creating FSX role..."
        FSX_ROLE_NAME="${CLUSTER_NAME}-fsx-csi-driver-role-${HYPERPOD_CLUSTER_ID}"
    
    # Create FSX role trust policy
    FSX_TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):oidc-provider/$OIDC_ISSUER"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "$OIDC_ISSUER:aud": "sts.amazonaws.com",
          "$OIDC_ISSUER:sub": "system:serviceaccount:kube-system:fsx-csi-controller-sa"
        }
      }
    }
  ]
}
EOF
)
    
    # Create role
    echo "$FSX_TRUST_POLICY" > /tmp/fsx-trust-policy.json
    FSX_ROLE_ARN=$(aws iam create-role \
        --role-name "$FSX_ROLE_NAME" \
        --assume-role-policy-document file:///tmp/fsx-trust-policy.json \
        --path "/" \
        --query 'Role.Arn' --output text 2>/dev/null || \
        aws iam get-role --role-name "$FSX_ROLE_NAME" --query 'Role.Arn' --output text)
    
    # Attach AWS managed policy
    aws iam attach-role-policy --role-name "$FSX_ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/AmazonFSxFullAccess"
    
    print_success "FSX role created: $FSX_ROLE_ARN"
    else
        print_info "Reusing existing FSX role: $FSX_ROLE_ARN"
    fi
fi

# Step 4c: Validate TLS S3 bucket
print_info "Step 4c: Validating TLS S3 bucket..."
if aws s3 ls "s3://$TLS_BUCKET_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
    print_success "TLS S3 bucket exists: $TLS_BUCKET_NAME"
else
    print_error "TLS S3 bucket does not exist: $TLS_BUCKET_NAME"
    print_info "Please create the bucket first or provide an existing bucket name"
    exit 1
fi


# Step 5: Install dependency addons
print_info "Step 5: Installing dependency addons..."

# S3 Mountpoint CSI Driver
if [[ "$SKIP_S3_ADDON" == "false" && -n "$S3_MOUNTPOINT_ROLE_ARN" ]]; then
    confirm_action "Install aws-mountpoint-s3-csi-driver addon"
    aws eks create-addon \
        --cluster-name "$CLUSTER_NAME" \
        --addon-name aws-mountpoint-s3-csi-driver \
        --service-account-role-arn "$S3_MOUNTPOINT_ROLE_ARN" \
        --region "$AWS_REGION" \
        --resolve-conflicts OVERWRITE || print_warning "S3 Mountpoint addon may already exist"
elif [[ "$SKIP_S3_ADDON" == "true" ]]; then
    print_info "Skipping S3 addon installation - CSI driver already exists"
fi

# FSX CSI Driver
if [[ "$SKIP_FSX_ADDON" == "false" && -n "$FSX_ROLE_ARN" ]]; then
    confirm_action "Install aws-fsx-csi-driver addon"
    aws eks create-addon \
        --cluster-name "$CLUSTER_NAME" \
        --addon-name aws-fsx-csi-driver \
        --service-account-role-arn "$FSX_ROLE_ARN" \
        --region "$AWS_REGION" \
        --resolve-conflicts OVERWRITE || print_warning "FSX addon may already exist"
elif [[ "$SKIP_FSX_ADDON" == "true" ]]; then
    print_info "Skipping FSX addon installation - CSI driver already exists"
fi

# Step 4c: Check if cert-manager exists, install addon if not
if kubectl get deployment cert-manager -n cert-manager >/dev/null 2>&1; then
    print_info "Cert Manager already exists, skipping addon installation"
elif aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name cert-manager --region "$AWS_REGION" >/dev/null 2>&1; then
    print_info "Cert Manager addon already exists, skipping installation"
else
    confirm_action "Install cert-manager addon"
    aws eks create-addon \
        --cluster-name "$CLUSTER_NAME" \
        --addon-name cert-manager \
        --region "$AWS_REGION" || print_warning "Cert manager addon may already exist"
fi

print_success "Dependency addons installation completed"

# Step 6: Scale down Helm deployment
print_info "Step 6: Scaling down Helm deployment..."

# Check if deployment exists and scale to 0
if kubectl get deployment hyperpod-inference-operator-controller-manager -n hyperpod-inference-system >/dev/null 2>&1; then
    confirm_action "Scale down hyperpod-inference-operator-controller-manager deployment in hyperpod-inference-system namespace"
    kubectl scale deployment hyperpod-inference-operator-controller-manager --replicas=0 -n hyperpod-inference-system || print_warning "Failed to scale deployment"
    touch "$BACKUP_DIR/helm-scaled-down.flag"
    print_success "Helm deployment scaled down"
else
    print_warning "Deployment hyperpod-inference-operator-controller-manager not found in hyperpod-inference-system namespace"
fi

# Scale down ALB controller deployment
if kubectl get deployment hyperpod-inference-operator-alb -n kube-system >/dev/null 2>&1; then
    confirm_action "Scale down hyperpod-inference-operator-alb deployment in kube-system namespace"
    kubectl scale deployment hyperpod-inference-operator-alb --replicas=0 -n kube-system || print_warning "Failed to scale ALB controller"
    touch "$BACKUP_DIR/alb-scaled-down.flag"
    print_success "ALB controller deployment scaled down"
else
    print_warning "ALB controller deployment not found in kube-system namespace"
fi

# Scale down KEDA operator deployment
if kubectl get deployment keda-operator -n kube-system >/dev/null 2>&1; then
    confirm_action "Scale down keda-operator deployment in kube-system namespace"
    kubectl scale deployment keda-operator --replicas=0 -n kube-system || print_warning "Failed to scale KEDA operator"
    touch "$BACKUP_DIR/keda-scaled-down.flag"
    print_success "KEDA operator deployment scaled down"
else
    print_warning "KEDA operator deployment not found in kube-system namespace"
fi

# Scale down KEDA metrics apiserver deployment
if kubectl get deployment keda-operator-metrics-apiserver -n kube-system >/dev/null 2>&1; then
    confirm_action "Scale down keda-operator-metrics-apiserver deployment in kube-system namespace"
    kubectl scale deployment keda-operator-metrics-apiserver --replicas=0 -n kube-system || print_warning "Failed to scale KEDA metrics apiserver"
    touch "$BACKUP_DIR/keda-metrics-scaled-down.flag"
    print_success "KEDA metrics apiserver deployment scaled down"
else
    print_warning "KEDA metrics apiserver deployment not found in kube-system namespace"
fi

# Scale down KEDA admission webhooks deployment
if kubectl get deployment keda-admission-webhooks -n kube-system >/dev/null 2>&1; then
    confirm_action "Scale down keda-admission-webhooks deployment in kube-system namespace"
    kubectl scale deployment keda-admission-webhooks --replicas=0 -n kube-system || print_warning "Failed to scale KEDA admission webhooks"
    touch "$BACKUP_DIR/keda-webhooks-scaled-down.flag"
    print_success "KEDA admission webhooks deployment scaled down"
else
    print_warning "KEDA admission webhooks deployment not found in kube-system namespace"
fi

# Step 7: Install Inference operator addon
print_info "Step 7: Installing Inference operator addon $ADDON_VERSION..."
confirm_action "Install amazon-sagemaker-hyperpod-inference addon $ADDON_VERSION with OVERWRITE"

# Configuration follows the addon configuration schema of the resolved version.
# - inferenceGateway defaults to enabled in v2.x; it is disabled here so the migration does not install
#   the Inference Gateway control plane (it was not part of the Helm installation). Enable it later
#   with `aws eks update-addon` once its IAM role is set up.
# - jq builds the JSON so values are escaped correctly.
ADDON_CONFIG=$(jq -n -c \
    --arg executionRoleArn "$NEW_EXECUTION_ROLE_ARN" \
    --arg tlsBucket "$TLS_BUCKET_NAME" \
    --arg hyperpodClusterArn "$HYPERPOD_CLUSTER_ARN" \
    --arg jsGatedRoleArn "$JS_GATED_MODEL_ROLE_ARN" \
    --arg albRoleArn "$ALB_ROLE_ARN" \
    --arg kedaRoleArn "$KEDA_ROLE_ARN" \
    --argjson disableGateway "$DISABLE_INFERENCE_GATEWAY" \
    '{
      executionRoleArn: $executionRoleArn,
      tlsCertificateS3Bucket: $tlsBucket,
      hyperpodClusterArn: $hyperpodClusterArn,
      jumpstartGatedModelDownloadRoleArn: $jsGatedRoleArn,
      alb: {
        enabled: true,
        serviceAccount: { create: true, roleArn: $albRoleArn }
      },
      keda: {
        enabled: true,
        auth: { aws: { irsa: { enabled: true, roleArn: $kedaRoleArn } } }
      }
    } + (if $disableGateway then { inferenceGateway: { enabled: false } } else {} end)')
echo "$ADDON_CONFIG" > "$BACKUP_DIR/addon-configuration.json"
print_info "Addon configuration saved to $BACKUP_DIR/addon-configuration.json"

aws eks create-addon \
    --cluster-name "$CLUSTER_NAME" \
    --addon-name amazon-sagemaker-hyperpod-inference \
    --addon-version "$ADDON_VERSION" \
    --resolve-conflicts OVERWRITE \
    --configuration-values "$ADDON_CONFIG" \
    --region "$AWS_REGION"

touch "$BACKUP_DIR/addon-installed.flag"
print_success "Inference operator addon installation started"

# Step 8: Wait for addon to be active
print_info "Step 8: Waiting for addon to become active..."
ADDON_WAIT_TIMEOUT_SECONDS=1800
ADDON_WAIT_START=$(date +%s)
while true; do
    STATUS=$(aws eks describe-addon \
        --cluster-name "$CLUSTER_NAME" \
        --addon-name amazon-sagemaker-hyperpod-inference \
        --region "$AWS_REGION" \
        --query "addon.status" --output text)
    
    if [[ "$STATUS" == "ACTIVE" ]]; then
        print_success "Addon is now ACTIVE"
        break
    elif [[ "$STATUS" == "CREATE_FAILED" || "$STATUS" == "DEGRADED" ]]; then
        print_error "Addon status: $STATUS"
        aws eks describe-addon \
            --cluster-name "$CLUSTER_NAME" \
            --addon-name amazon-sagemaker-hyperpod-inference \
            --region "$AWS_REGION" \
            --query "addon.health.issues[].[code,message]" --output text || true
        # Do not continue to Helm cleanup with an unhealthy addon
        handle_error
    elif (( $(date +%s) - ADDON_WAIT_START > ADDON_WAIT_TIMEOUT_SECONDS )); then
        print_error "Timed out after ${ADDON_WAIT_TIMEOUT_SECONDS}s waiting for addon (last status: $STATUS)"
        handle_error
    else
        print_info "Addon status: $STATUS. Waiting..."
        sleep 30
    fi
done

# Step 8b: Delete old Helm deployment now that addon is active
print_info "Step 8b: Deleting old Helm deployment..."
if kubectl get deployment hyperpod-inference-operator-controller-manager -n hyperpod-inference-system >/dev/null 2>&1; then
    confirm_action "Delete hyperpod-inference-operator-controller-manager deployment from hyperpod-inference-system namespace"
    kubectl delete deployment hyperpod-inference-operator-controller-manager -n hyperpod-inference-system || print_warning "Failed to delete deployment"
    print_success "Old Helm deployment deleted"
else
    print_warning "Deployment already removed or not found"
fi

# Install the metrics-server addon BEFORE removing the Helm metrics-server, so the metrics API
# (kubectl top, HPA, KEDA CPU/memory triggers) never goes away. OVERWRITE is required: the Helm
# chart owns the v1beta1.metrics.k8s.io APIService, and without it the addon goes CREATE_FAILED
# (ConfigurationConflict) while the Helm metrics-server is already deleted.
print_info "Installing metrics-server addon (takes over the metrics API from the Helm metrics-server)..."
confirm_action "Install metrics-server addon"
if aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name metrics-server --region "$AWS_REGION" >/dev/null 2>&1; then
    print_info "metrics-server addon already exists"
else
    aws eks create-addon \
        --cluster-name "$CLUSTER_NAME" \
        --addon-name metrics-server \
        --resolve-conflicts OVERWRITE \
        --region "$AWS_REGION" >/dev/null
fi
if aws eks wait addon-active --cluster-name "$CLUSTER_NAME" --addon-name metrics-server --region "$AWS_REGION"; then
    print_success "metrics-server addon is ACTIVE"
    METRICS_ADDON_ACTIVE=true
else
    print_warning "metrics-server addon did not become ACTIVE; keeping the Helm metrics-server in place"
    aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name metrics-server --region "$AWS_REGION" \
        --query 'addon.health.issues[].[code,message]' --output text || true
    METRICS_ADDON_ACTIVE=false
fi

# Step 9: Clean up old service accounts and deployments
print_info "Step 9: Cleaning up old service accounts and deployments..."
print_warning "This will permanently delete old Helm resources. The addon is now managing the operator."
confirm_action "Proceed with cleanup of old Helm resources"

# The Helm chart installs ALB and KEDA into the Helm release namespace (kube-system by default)
kubectl delete serviceaccount aws-load-balancer-controller -n "$HELM_NAMESPACE" --ignore-not-found=true
kubectl delete serviceaccount keda-operator -n "$HELM_NAMESPACE" --ignore-not-found=true
kubectl delete serviceaccount keda-metrics-server -n "$HELM_NAMESPACE" --ignore-not-found=true

# Clean up old deployments
confirm_action "Delete old hyperpod-inference-operator deployments from $HELM_NAMESPACE namespace"
kubectl delete deployment hyperpod-inference-operator-alb -n "$HELM_NAMESPACE" --ignore-not-found=true
if [[ "$METRICS_ADDON_ACTIVE" == "true" ]]; then
    kubectl delete deployment hyperpod-inference-operator-metrics -n "$HELM_NAMESPACE" --ignore-not-found=true
fi
kubectl delete deployment keda-admission-webhooks -n "$HELM_NAMESPACE" --ignore-not-found=true
kubectl delete deployment keda-operator -n "$HELM_NAMESPACE" --ignore-not-found=true
kubectl delete deployment keda-operator-metrics-apiserver -n "$HELM_NAMESPACE" --ignore-not-found=true

print_success "Old service accounts and deployments cleaned up"

# Step 10: Migrate Helm-installed dependencies to addons
if [[ "$SKIP_DEPENDENCY_MIGRATE" == "false" ]]; then
    print_info "Step 10: Migrating Helm-installed dependencies to addons..."
    
    # Check if S3 CSI was installed via inference operator Helm
    if kubectl get daemonset -n kube-system -l app.kubernetes.io/instance=hyperpod-inference-operator | grep -q s3-csi-node; then
        print_info "S3 CSI driver was installed via inference operator Helm"
        if ! aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name aws-mountpoint-s3-csi-driver --region "$AWS_REGION" >/dev/null 2>&1; then
            confirm_action "Delete Helm-installed S3 CSI driver and install as addon"
            kubectl delete daemonset -n kube-system -l app.kubernetes.io/instance=hyperpod-inference-operator,app.kubernetes.io/name=s3 --ignore-not-found=true
            kubectl delete deployment -n kube-system -l app.kubernetes.io/instance=hyperpod-inference-operator,app.kubernetes.io/name=s3 --ignore-not-found=true
            
            # Create S3 role if not exists
            if [[ -z "$S3_MOUNTPOINT_ROLE_ARN" ]]; then
                S3_ROLE_NAME="${CLUSTER_NAME}-${HYPERPOD_CLUSTER_ID}-s3-csi-driver-role"
                S3_POLICY_NAME="${CLUSTER_NAME}-s3-csi-driver-policy"
                S3_POLICY_DOC=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MountpointFullBucketAccess",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["arn:aws:s3:::*"]
    },
    {
      "Sid": "MountpointObjectReadAccess",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:AbortMultipartUpload", "s3:DeleteObject"],
      "Resource": ["arn:aws:s3:::*/*"]
    }
  ]
}
EOF
)
                echo "$S3_POLICY_DOC" > /tmp/s3-policy.json
                S3_POLICY_ARN=$(aws iam create-policy \
                    --policy-name "$S3_POLICY_NAME" \
                    --policy-document file:///tmp/s3-policy.json \
                    --query 'Policy.Arn' --output text 2>/dev/null || \
                    aws iam get-policy --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$S3_POLICY_NAME" --query 'Policy.Arn' --output text)
                
                S3_TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):oidc-provider/$OIDC_ISSUER"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "$OIDC_ISSUER:aud": "sts.amazonaws.com",
          "$OIDC_ISSUER:sub": "system:serviceaccount:kube-system:s3-csi-driver-sa"
        }
      }
    }
  ]
}
EOF
)
                echo "$S3_TRUST_POLICY" > /tmp/s3-trust-policy.json
                S3_MOUNTPOINT_ROLE_ARN=$(aws iam create-role \
                    --role-name "$S3_ROLE_NAME" \
                    --assume-role-policy-document file:///tmp/s3-trust-policy.json \
                    --path "/" \
                    --query 'Role.Arn' --output text 2>/dev/null || \
                    aws iam get-role --role-name "$S3_ROLE_NAME" --query 'Role.Arn' --output text)
                aws iam attach-role-policy --role-name "$S3_ROLE_NAME" --policy-arn "$S3_POLICY_ARN"
                print_success "S3 role created: $S3_MOUNTPOINT_ROLE_ARN"
            fi
            
            # Install S3 addon
            aws eks create-addon \
                --cluster-name "$CLUSTER_NAME" \
                --addon-name aws-mountpoint-s3-csi-driver \
                --service-account-role-arn "$S3_MOUNTPOINT_ROLE_ARN" \
                --region "$AWS_REGION" \
                --resolve-conflicts OVERWRITE
            print_success "S3 CSI driver migrated to addon"
        else
            print_info "S3 addon already exists, skipping migration"
        fi
    fi
    
    # Check if FSX CSI was installed via inference operator Helm
    if kubectl get daemonset -n kube-system -l app.kubernetes.io/instance=hyperpod-inference-operator | grep -q fsx-csi-node; then
        print_info "FSX CSI driver was installed via inference operator Helm"
        if ! aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name aws-fsx-csi-driver --region "$AWS_REGION" >/dev/null 2>&1; then
            confirm_action "Delete Helm-installed FSX CSI driver and install as addon"
            kubectl delete daemonset fsx-csi-node -n kube-system -l app.kubernetes.io/instance=hyperpod-inference-operator --ignore-not-found=true
            kubectl delete deployment fsx-csi-controller -n kube-system -l app.kubernetes.io/instance=hyperpod-inference-operator --ignore-not-found=true
            
            # Create FSX role if not exists
            if [[ -z "$FSX_ROLE_ARN" ]]; then
                FSX_ROLE_NAME="${CLUSTER_NAME}-fsx-csi-driver-role-${HYPERPOD_CLUSTER_ID}"
                FSX_TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):oidc-provider/$OIDC_ISSUER"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "$OIDC_ISSUER:aud": "sts.amazonaws.com",
          "$OIDC_ISSUER:sub": "system:serviceaccount:kube-system:fsx-csi-controller-sa"
        }
      }
    }
  ]
}
EOF
)
                echo "$FSX_TRUST_POLICY" > /tmp/fsx-trust-policy.json
                FSX_ROLE_ARN=$(aws iam create-role \
                    --role-name "$FSX_ROLE_NAME" \
                    --assume-role-policy-document file:///tmp/fsx-trust-policy.json \
                    --path "/" \
                    --query 'Role.Arn' --output text 2>/dev/null || \
                    aws iam get-role --role-name "$FSX_ROLE_NAME" --query 'Role.Arn' --output text)
                aws iam attach-role-policy --role-name "$FSX_ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/AmazonFSxFullAccess"
                print_success "FSX role created: $FSX_ROLE_ARN"
            fi
            
            # Install FSX addon
            aws eks create-addon \
                --cluster-name "$CLUSTER_NAME" \
                --addon-name aws-fsx-csi-driver \
                --service-account-role-arn "$FSX_ROLE_ARN" \
                --region "$AWS_REGION" \
                --resolve-conflicts OVERWRITE
            print_success "FSX CSI driver migrated to addon"
        else
            print_info "FSX addon already exists, skipping migration"
        fi
    fi
    
    # Check if cert-manager was installed via inference operator Helm
    if kubectl get deployment -n cert-manager -l app.kubernetes.io/instance=hyperpod-inference-operator | grep -q cert-manager; then
        print_info "Cert-manager was installed via inference operator Helm"
        if ! aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name cert-manager --region "$AWS_REGION" >/dev/null 2>&1; then
            confirm_action "Delete Helm-installed cert-manager and install as addon"
            kubectl delete deployment cert-manager -n cert-manager -l app.kubernetes.io/instance=hyperpod-inference-operator --ignore-not-found=true
            kubectl delete deployment cert-manager-cainjector -n cert-manager -l app.kubernetes.io/instance=hyperpod-inference-operator --ignore-not-found=true
            kubectl delete deployment cert-manager-webhook -n cert-manager -l app.kubernetes.io/instance=hyperpod-inference-operator --ignore-not-found=true
            
            # Install cert-manager addon
            aws eks create-addon \
                --cluster-name "$CLUSTER_NAME" \
                --addon-name cert-manager \
                --region "$AWS_REGION" \
                --resolve-conflicts OVERWRITE
            print_success "Cert-manager migrated to addon"
        else
            print_info "Cert-manager addon already exists, skipping migration"
        fi
    fi
    
    # Check if metrics-server was installed via inference operator Helm
    # TODO: Improve metrics-server detection - currently uses generic "metrics" grep which may match other deployments
    if kubectl get deployment -n kube-system -l app.kubernetes.io/instance=hyperpod-inference-operator | grep -q metrics; then
        print_info "Metrics-server was installed via inference operator Helm"
        if ! aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name metrics-server --region "$AWS_REGION" >/dev/null 2>&1; then
            confirm_action "Delete Helm-installed metrics-server and install as addon"
            kubectl get deployment -n kube-system -l app.kubernetes.io/instance=hyperpod-inference-operator -o name | grep metrics | xargs -r kubectl delete -n kube-system || true
            
            # Install metrics-server addon
            aws eks create-addon \
                --cluster-name "$CLUSTER_NAME" \
                --addon-name metrics-server \
                --region "$AWS_REGION" \
                --resolve-conflicts OVERWRITE
            print_success "Metrics-server migrated to addon"
        else
            print_info "Metrics-server addon already exists, skipping migration"
        fi
    fi
    
    print_success "Dependency migration completed"
else
    print_info "Skipping dependency migration (--skip-dependencies-migration flag provided)"
fi

# Cleanup temp files
rm -f /tmp/alb-trust-policy.json /tmp/keda-trust-policy.json /tmp/inference-trust-policy.json

print_success "=== Migration completed successfully! ==="

print_info "Summary:"
print_info "- Cluster: $CLUSTER_NAME"
print_info "- TLS Bucket: $TLS_BUCKET_NAME"
print_info "- Addon Status: ACTIVE"
print_info "- Backup Directory: $BACKUP_DIR"
print_info ""
print_info "You can now manage the inference operator through EKS AddOns."
print_info "Backup files are preserved in case rollback is needed."
