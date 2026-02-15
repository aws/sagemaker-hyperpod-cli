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
        *)
            echo "Unknown option $1"
            echo "Usage: $0 [--auto-approve] [--step-by-step] [--skip-dependencies-migration] [--cluster-name NAME] [--region REGION] [--helm-namespace NAMESPACE] [--s3-mountpoint-role-arn ARN] [--fsx-role-arn ARN]"
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

# Function to backup trust policy
# Function to rollback changes
rollback() {
    print_error "=== ROLLBACK INITIATED ==="
    print_info "Backup directory: $BACKUP_DIR"
    
    # Delete new roles if they were created
    if [[ -f "$BACKUP_DIR/alb-role-name-new.txt" ]]; then
        NEW_ALB_ROLE=$(cat "$BACKUP_DIR/alb-role-name-new.txt")
        print_info "Deleting new ALB role: $NEW_ALB_ROLE"
        aws iam list-attached-role-policies --role-name "$NEW_ALB_ROLE" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null | xargs -n1 -I{} aws iam detach-role-policy --role-name "$NEW_ALB_ROLE" --policy-arn {} 2>/dev/null
        aws iam delete-role --role-name "$NEW_ALB_ROLE" 2>/dev/null || print_warning "Failed to delete new ALB role"
    fi
    
    if [[ -f "$BACKUP_DIR/keda-role-name-new.txt" ]]; then
        NEW_KEDA_ROLE=$(cat "$BACKUP_DIR/keda-role-name-new.txt")
        print_info "Deleting new KEDA role: $NEW_KEDA_ROLE"
        aws iam list-attached-role-policies --role-name "$NEW_KEDA_ROLE" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null | xargs -n1 -I{} aws iam detach-role-policy --role-name "$NEW_KEDA_ROLE" --policy-arn {} 2>/dev/null
        aws iam delete-role --role-name "$NEW_KEDA_ROLE" 2>/dev/null || print_warning "Failed to delete new KEDA role"
    fi
    
    # Scale Helm deployment back up if it was scaled down
    if [[ -f "$BACKUP_DIR/helm-scaled-down.flag" ]]; then
        print_info "Deleting addon deployments and restoring Helm deployment..."
        kubectl delete deployment hyperpod-inference-controller-manager -n hyperpod-inference-system --ignore-not-found=true
        kubectl delete deployment hyperpod-inference-alb -n hyperpod-inference-system --ignore-not-found=true
        kubectl delete deployment keda-operator keda-operator-metrics-apiserver keda-admission-webhooks -n hyperpod-inference-system --ignore-not-found=true
        
        # Check if Helm deployment was deleted, if so run helm rollback
        if ! kubectl get deployment hyperpod-inference-operator-controller-manager -n hyperpod-inference-system >/dev/null 2>&1; then
            print_info "Running Helm rollback..."
            helm rollback hyperpod-inference-operator 1 -n kube-system || print_warning "Failed to rollback Helm release"
        else
            kubectl scale deployment hyperpod-inference-operator-controller-manager --replicas=1 -n hyperpod-inference-system || print_warning "Failed to scale Helm deployment back up"
        fi
    fi

    # Remove tags from ALB resources
    if [[ -f "$BACKUP_DIR/alb-arns.txt" ]]; then
        print_info "Removing tags from ALB resources..."
        while read -r alb_arn; do
            aws elbv2 remove-tags --resource-arns "$alb_arn" --tag-keys "CreatedBy" --region "$AWS_REGION" 2>/dev/null || true
        done < "$BACKUP_DIR/alb-arns.txt"
    fi

    # Remove tags from ACM certificates
    if [[ -f "$BACKUP_DIR/acm-arns.txt" ]]; then
        print_info "Removing tags from ACM certificates..."
        while read -r cert_arn; do
            aws acm remove-tags-from-certificate --certificate-arn "$cert_arn" --tags Key="CreatedBy" --region "$AWS_REGION" 2>/dev/null || true
        done < "$BACKUP_DIR/acm-arns.txt"
    fi

    # Remove tags from S3 objects
    if [[ -f "$BACKUP_DIR/s3-objects.txt" ]]; then
        print_info "Removing tags from S3 objects..."
        while read -r line; do
            bucket=$(echo "$line" | cut -d'|' -f1)
            key=$(echo "$line" | cut -d'|' -f2)
            aws s3api delete-object-tagging --bucket "$bucket" --key "$key" 2>/dev/null || true
        done < "$BACKUP_DIR/s3-objects.txt"
    fi

    # Scale ALB controller back up if it was scaled down
    if [[ -f "$BACKUP_DIR/alb-scaled-down.flag" ]]; then
        print_info "Scaling ALB controller back up..."
        kubectl scale deployment hyperpod-inference-operator-alb --replicas=2 -n kube-system || print_warning "Failed to scale ALB controller back up"
    fi

    # Scale KEDA operator back up if it was scaled down
    if [[ -f "$BACKUP_DIR/keda-scaled-down.flag" ]]; then
        print_info "Scaling KEDA operator back up..."
        kubectl scale deployment keda-operator --replicas=1 -n kube-system || print_warning "Failed to scale KEDA operator back up"
    fi

    # Scale KEDA metrics apiserver back up if it was scaled down
    if [[ -f "$BACKUP_DIR/keda-metrics-scaled-down.flag" ]]; then
        print_info "Scaling KEDA metrics apiserver back up..."
        kubectl scale deployment keda-operator-metrics-apiserver --replicas=1 -n kube-system || print_warning "Failed to scale KEDA metrics apiserver back up"
    fi

    # Scale KEDA admission webhooks back up if it was scaled down
    if [[ -f "$BACKUP_DIR/keda-webhooks-scaled-down.flag" ]]; then
        print_info "Scaling KEDA admission webhooks back up..."
        kubectl scale deployment keda-admission-webhooks --replicas=1 -n kube-system || print_warning "Failed to scale KEDA admission webhooks back up"
    fi
    
    # Remove addon if it was installed
    if [[ -f "$BACKUP_DIR/addon-installed.flag" ]]; then
        print_info "Removing addon..."
        aws eks delete-addon --cluster-name "$CLUSTER_NAME" --addon-name amazon-sagemaker-hyperpod-inference --region "$AWS_REGION" --preserve || print_warning "Failed to remove addon"
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
EXECUTION_ROLE_ARN=$(echo "$HELM_VALUES" | jq -r '.executionRoleArn // empty')
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
            print_info "Tagging ALB: $ALB_ARN"
            aws elbv2 add-tags --resource-arns "$ALB_ARN" --tags Key="$TAG_KEY",Value="$TAG_VALUE" --region "$AWS_REGION" || print_warning "Failed to tag ALB: $ALB_ARN"
            echo "$ALB_ARN" >> "$BACKUP_DIR/alb-arns.txt"
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
        print_info "Tagging ACM certificate: $cert_arn"
        aws acm add-tags-to-certificate --certificate-arn "$cert_arn" --tags Key="$TAG_KEY",Value="$TAG_VALUE" --region "$AWS_REGION" || print_warning "Failed to tag ACM certificate: $cert_arn"
        echo "$cert_arn" >> "$BACKUP_DIR/acm-arns.txt"
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
                aws s3api put-object-tagging --bucket "$bucket" --key "$cert_key" --tagging "TagSet=[{Key=$TAG_KEY,Value=$TAG_VALUE}]" 2>/dev/null || true
                echo "$bucket|$cert_key" >> "$BACKUP_DIR/s3-objects.txt"
            fi
        done
    fi
done

print_success "Resource tagging completed"

# Extract HyperPod cluster ID for unique role naming
HYPERPOD_CLUSTER_ID=$(echo "$HYPERPOD_CLUSTER_ARN" | cut -d'/' -f2 | cut -c1-8)

# Get OIDC issuer URL for trust policies
print_info "Getting OIDC issuer URL for cluster..."
OIDC_ISSUER=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" --query "cluster.identity.oidc.issuer" --output text | sed 's|https://||')
print_success "OIDC Issuer: $OIDC_ISSUER"

# Create new Execution Role for addon
print_info "Creating new execution role for addon..."
NEW_EXECUTION_ROLE_NAME="SageMakerHyperPodInference-${HYPERPOD_CLUSTER_ID}-execution-role"

# Create trust policy based on existing execution role
EXISTING_EXECUTION_ROLE_NAME=$(echo "$EXECUTION_ROLE_ARN" | cut -d'/' -f2)
EXISTING_TRUST_POLICY=$(aws iam get-role --role-name "$EXISTING_EXECUTION_ROLE_NAME" --query 'Role.AssumeRolePolicyDocument' --output json)

# Update the service account name in the trust policy
EXECUTION_TRUST_POLICY=$(echo "$EXISTING_TRUST_POLICY" | sed 's/system:serviceaccount:hyperpod-inference-system:hyperpod-inference-operator-controller-manager/system:serviceaccount:hyperpod-inference-system:hyperpod-inference-controller-manager/g')

# Create role
echo "$EXECUTION_TRUST_POLICY" > /tmp/execution-trust-policy.json
NEW_EXECUTION_ROLE_ARN=$(aws iam create-role \
    --role-name "$NEW_EXECUTION_ROLE_NAME" \
    --assume-role-policy-document file:///tmp/execution-trust-policy.json \
    --query 'Role.Arn' --output text 2>/dev/null || \
    aws iam get-role --role-name "$NEW_EXECUTION_ROLE_NAME" --query 'Role.Arn' --output text)

# Attach managed policy
aws iam attach-role-policy --role-name "$NEW_EXECUTION_ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/AmazonSageMakerHyperPodInferenceAccess"

# Create S3 permissions for TLS buckets
S3_BUCKET_RESOURCES=""
S3_OBJECT_RESOURCES=""
for bucket in "${TLS_BUCKETS[@]}"; do
    if [[ -n "$bucket" ]]; then
        S3_BUCKET_RESOURCES="$S3_BUCKET_RESOURCES\"arn:aws:s3:::$bucket\","
        S3_OBJECT_RESOURCES="$S3_OBJECT_RESOURCES\"arn:aws:s3:::$bucket/*\","
    fi
done
S3_BUCKET_RESOURCES=${S3_BUCKET_RESOURCES%,}
S3_OBJECT_RESOURCES=${S3_OBJECT_RESOURCES%,}

# Create inline policy for TLS buckets
S3_INLINE_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TLSBucketDeleteObjectsPermission",
      "Effect": "Allow",
      "Action": ["s3:DeleteObject"],
      "Resource": [$S3_OBJECT_RESOURCES],
      "Condition": {
        "StringEquals": {
          "aws:ResourceAccount": "\${aws:PrincipalAccount}"
        }
      }
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
      "Condition": {
        "StringEquals": {
          "aws:ResourceAccount": "\${aws:PrincipalAccount}"
        }
      }
    }
  ]
}
EOF
)

echo "$S3_INLINE_POLICY" > /tmp/s3-inline-policy.json
aws iam put-role-policy --role-name "$NEW_EXECUTION_ROLE_NAME" --policy-name "TLSBucketsAccess" --policy-document file:///tmp/s3-inline-policy.json

print_success "New execution role created: $NEW_EXECUTION_ROLE_ARN"

# Create JumpStart Gated Model role
print_info "Creating JumpStart Gated Model role..."
JS_GATED_MODEL_ROLE_NAME="js-gated-role-${HYPERPOD_CLUSTER_ID}"

# Create JS Gated Model trust policy
JS_GATED_MODEL_TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sagemaker.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):oidc-provider/$OIDC_ISSUER"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringLike": {
          "$OIDC_ISSUER:aud": "sts.amazonaws.com",
          "$OIDC_ISSUER:sub": "system:serviceaccount:*:hyperpod-inference-service-account*"
        }
      }
    }
  ]
}
EOF
)

# Create role
echo "$JS_GATED_MODEL_TRUST_POLICY" > /tmp/js-gated-model-trust-policy.json
JS_GATED_MODEL_ROLE_ARN=$(aws iam create-role \
    --role-name "$JS_GATED_MODEL_ROLE_NAME" \
    --assume-role-policy-document file:///tmp/js-gated-model-trust-policy.json \
    --query 'Role.Arn' --output text 2>/dev/null || \
    aws iam get-role --role-name "$JS_GATED_MODEL_ROLE_NAME" --query 'Role.Arn' --output text)

# Attach managed policy
aws iam attach-role-policy --role-name "$JS_GATED_MODEL_ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/AmazonSageMakerHyperPodGatedModelAccess"

print_success "JumpStart Gated Model role created: $JS_GATED_MODEL_ROLE_ARN"

# Get ALB role ARN from Helm values or service account
ALB_ROLE_ARN=$(echo "$HELM_VALUES" | jq -r '.alb.serviceAccount.roleArn // empty')
if [[ -z "$ALB_ROLE_ARN" || "$ALB_ROLE_ARN" == "null" ]]; then
    ALB_SA_ANNOTATION=$(kubectl get serviceaccount aws-load-balancer-controller -n "$HELM_NAMESPACE" -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}' 2>/dev/null || echo "")
    ALB_ROLE_ARN="$ALB_SA_ANNOTATION"
fi

# Get KEDA role ARN from Helm values or service account
KEDA_ROLE_ARN=$(echo "$HELM_VALUES" | jq -r '.keda.podIdentity.aws.irsa.roleArn // empty')
if [[ -z "$KEDA_ROLE_ARN" || "$KEDA_ROLE_ARN" == "null" ]]; then
    KEDA_SA_ANNOTATION=$(kubectl get serviceaccount keda-operator -n "$HELM_NAMESPACE" -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}' 2>/dev/null || echo "")
    KEDA_ROLE_ARN="$KEDA_SA_ANNOTATION"
fi

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

# Collect required information (with auto-derived defaults)
if [[ -z "$CLUSTER_NAME" ]]; then
    prompt_user "Enter your EKS cluster name:" CLUSTER_NAME
fi
if [[ -z "$AWS_REGION" ]]; then
    prompt_user "Enter your AWS region:" AWS_REGION
fi

# Show auto-derived values and allow override
echo -e "${GREEN}Auto-derived values:${NC}"
echo "HyperPod Cluster ARN: $HYPERPOD_CLUSTER_ARN"
echo "Execution Role ARN: $EXECUTION_ROLE_ARN"
echo "ALB Role ARN: $ALB_ROLE_ARN"
echo "KEDA Role ARN: $KEDA_ROLE_ARN"
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
echo

# Validate required values
if [[ -z "$HYPERPOD_CLUSTER_ARN" ]]; then
    prompt_user "HyperPod Cluster ARN not found. Enter manually:" HYPERPOD_CLUSTER_ARN
fi
if [[ -z "$EXECUTION_ROLE_ARN" ]]; then
    prompt_user "Execution Role ARN not found. Enter manually:" EXECUTION_ROLE_ARN
fi
if [[ -z "$ALB_ROLE_ARN" ]]; then
    prompt_user "ALB Role ARN not found. Enter manually:" ALB_ROLE_ARN
fi
if [[ -z "$KEDA_ROLE_ARN" ]]; then
    prompt_user "KEDA Role ARN not found. Enter manually:" KEDA_ROLE_ARN
fi
if [[ -z "$TLS_BUCKET_NAME" ]]; then
    prompt_user "TLS Bucket Name not found. Enter manually:" TLS_BUCKET_NAME
fi

# Step 1: Create new ALB role (keep old role for rollback)
print_info "Step 1: Creating new ALB role..."
confirm_action "Create new ALB role for addon (old role preserved for rollback)"

OLD_ALB_ROLE_NAME=$(echo "$ALB_ROLE_ARN" | cut -d'/' -f2)
echo "$OLD_ALB_ROLE_NAME" > "$BACKUP_DIR/alb-role-name-original.txt"

NEW_ALB_ROLE_NAME="SageMakerHP-ALB-${HYPERPOD_CLUSTER_ID}-addon"
echo "$NEW_ALB_ROLE_NAME" > "$BACKUP_DIR/alb-role-name-new.txt"
ALB_TRUST_POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Federated": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):oidc-provider/$OIDC_ISSUER"},
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {"StringEquals": {"$OIDC_ISSUER:aud": "sts.amazonaws.com", "$OIDC_ISSUER:sub": "system:serviceaccount:hyperpod-inference-system:aws-load-balancer-controller"}}
    }]
}
EOF
)
echo "$ALB_TRUST_POLICY" > /tmp/alb-trust-policy-new.json
ALB_ROLE_ARN=$(aws iam create-role --role-name "$NEW_ALB_ROLE_NAME" --assume-role-policy-document file:///tmp/alb-trust-policy-new.json --query 'Role.Arn' --output text 2>/dev/null || aws iam get-role --role-name "$NEW_ALB_ROLE_NAME" --query 'Role.Arn' --output text)

OLD_ALB_POLICIES=$(aws iam list-attached-role-policies --role-name "$OLD_ALB_ROLE_NAME" --query 'AttachedPolicies[].PolicyArn' --output text)
for policy in $OLD_ALB_POLICIES; do
    aws iam attach-role-policy --role-name "$NEW_ALB_ROLE_NAME" --policy-arn "$policy"
done
print_success "New ALB role created: $ALB_ROLE_ARN"

# Step 2: Create new KEDA role (keep old role for rollback)
print_info "Step 2: Creating new KEDA role..."
confirm_action "Create new KEDA role for addon (old role preserved for rollback)"

OLD_KEDA_ROLE_NAME=$(echo "$KEDA_ROLE_ARN" | cut -d'/' -f2)
echo "$OLD_KEDA_ROLE_NAME" > "$BACKUP_DIR/keda-role-name-original.txt"

NEW_KEDA_ROLE_NAME="SageMakerHP-KEDA-${HYPERPOD_CLUSTER_ID}-addon"
echo "$NEW_KEDA_ROLE_NAME" > "$BACKUP_DIR/keda-role-name-new.txt"
KEDA_TRUST_POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "sagemaker.amazonaws.com"},
        "Action": "sts:AssumeRole"
    },{
        "Effect": "Allow",
        "Principal": {"Federated": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):oidc-provider/$OIDC_ISSUER"},
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {"StringLike": {"$OIDC_ISSUER:sub": "system:serviceaccount:hyperpod-inference-system:keda-operator"}}
    }]
}
EOF
)
echo "$KEDA_TRUST_POLICY" > /tmp/keda-trust-policy-new.json
KEDA_ROLE_ARN=$(aws iam create-role --role-name "$NEW_KEDA_ROLE_NAME" --assume-role-policy-document file:///tmp/keda-trust-policy-new.json --query 'Role.Arn' --output text 2>/dev/null || aws iam get-role --role-name "$NEW_KEDA_ROLE_NAME" --query 'Role.Arn' --output text)

OLD_KEDA_POLICIES=$(aws iam list-attached-role-policies --role-name "$OLD_KEDA_ROLE_NAME" --query 'AttachedPolicies[].PolicyArn' --output text)
for policy in $OLD_KEDA_POLICIES; do
    aws iam attach-role-policy --role-name "$NEW_KEDA_ROLE_NAME" --policy-arn "$policy"
done
print_success "New KEDA role created: $KEDA_ROLE_ARN"

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
        --addon-version v1.14.1-eksbuild.1 \
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
        --addon-version v1.6.0-eksbuild.1 \
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
        --addon-version v1.18.2-eksbuild.2 \
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
print_info "Step 7: Installing Inference operator addon..."
confirm_action "Install amazon-sagemaker-hyperpod-inference addon with OVERWRITE"

ADDON_CONFIG=$(cat <<EOF
{
  "executionRoleArn": "$NEW_EXECUTION_ROLE_ARN",
  "tlsCertificateS3Bucket": "$TLS_BUCKET_NAME",
  "hyperpodClusterArn": "$HYPERPOD_CLUSTER_ARN",
  "jumpstartGatedModelDownloadRoleArn": "$JS_GATED_MODEL_ROLE_ARN",
  "alb": {
    "enabled": true,
    "serviceAccount": {
      "create": true,
      "roleArn": "$ALB_ROLE_ARN"
    }
  },
  "keda": {
    "enabled": true,
    "auth": {
      "aws": {
        "irsa": {
          "enabled": true,
          "roleArn": "$KEDA_ROLE_ARN"
        }
      }
    }
  }
}
EOF
)

aws eks create-addon \
    --cluster-name "$CLUSTER_NAME" \
    --addon-name amazon-sagemaker-hyperpod-inference \
    --addon-version v1.0.0-eksbuild.1 \
    --resolve-conflicts OVERWRITE \
    --configuration-values "$ADDON_CONFIG" \
    --region "$AWS_REGION"

touch "$BACKUP_DIR/addon-installed.flag"
print_success "Inference operator addon installed"

# Step 8: Wait for addon to be active
print_info "Step 8: Waiting for addon to become active..."
while true; do
    STATUS=$(aws eks describe-addon \
        --cluster-name "$CLUSTER_NAME" \
        --addon-name amazon-sagemaker-hyperpod-inference \
        --region "$AWS_REGION" \
        --query "addon.status" --output text)
    
    if [[ "$STATUS" == "ACTIVE" ]]; then
        print_success "Addon is now ACTIVE"
        break
    elif [[ "$STATUS" == "CREATE_FAILED" ]]; then
        print_error "Addon creation failed"
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

# Step 9: Clean up old service accounts and deployments
print_info "Step 9: Cleaning up old service accounts and deployments..."
print_warning "This will permanently delete old Helm resources. The addon is now managing the operator."
confirm_action "Proceed with cleanup of old Helm resources"

kubectl delete serviceaccount aws-load-balancer-controller -n kube-system --ignore-not-found=true
kubectl delete serviceaccount keda-operator -n keda --ignore-not-found=true
kubectl delete serviceaccount keda-operator-metrics-reader -n keda --ignore-not-found=true

# Clean up old deployments
confirm_action "Delete old hyperpod-inference-operator deployments from kube-system namespace"
kubectl delete deployment hyperpod-inference-operator-alb -n kube-system --ignore-not-found=true
kubectl delete deployment hyperpod-inference-operator-metrics -n kube-system --ignore-not-found=true
kubectl delete deployment keda-admission-webhooks -n kube-system --ignore-not-found=true
kubectl delete deployment keda-operator -n kube-system --ignore-not-found=true
kubectl delete deployment keda-operator-metrics-apiserver -n kube-system --ignore-not-found=true

# Install metrics server addon post cleanup
print_info "Installing metrics-server addon post cleanup..."
confirm_action "Install metrics-server addon"
aws eks create-addon \
    --cluster-name "$CLUSTER_NAME" \
    --addon-name metrics-server \
    --addon-version v0.7.2-eksbuild.4 \
    --region "$AWS_REGION" || print_warning "Metrics server addon may already exist"

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
                --addon-version v1.14.1-eksbuild.1 \
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
                --addon-version v1.6.0-eksbuild.1 \
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
                --addon-version v1.18.2-eksbuild.2 \
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
                --addon-version v0.7.2-eksbuild.4 \
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
