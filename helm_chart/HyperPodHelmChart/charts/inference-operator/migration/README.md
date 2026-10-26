# Migrating the HyperPod Inference Operator from Helm to the EKS add-on

This guide covers moving a cluster whose inference operator was installed with Helm (including the HyperPod
console quick-setup Helm path) to the `amazon-sagemaker-hyperpod-inference` EKS add-on, using
`helm_to_addon.sh`. Running models keep serving during the migration.

## Prerequisites

- AWS CLI v2, `kubectl`, `helm` 3 and `jq` on the machine running the script
- Credentials that can manage IAM roles, EKS add-ons, and read SageMaker, ELB, ACM and S3 in the cluster account
- `kubectl` access to the cluster as an administrator
- The cluster's EKS OIDC provider associated with IAM (required for the add-on's IAM roles)
- If you bring your own IAM roles, prepare them first: see [IAM roles](#iam-roles)

## Run the migration

```bash
./helm_to_addon.sh --cluster-name <EKS cluster name> --region <region>
```

| Option | Purpose |
|---|---|
| `--cluster-name`, `--region` | EKS cluster and region (prompted if omitted) |
| `--helm-namespace` | Namespace of the Helm release (auto-detected; `kube-system` for quick setup) |
| `--addon-version` | Add-on version to install. Default: the EKS default version for the cluster's Kubernetes version |
| `--execution-role-arn`, `--jumpstart-gated-role-arn`, `--alb-role-arn`, `--keda-role-arn` | Use your own IAM roles instead of having the script create them |
| `--s3-mountpoint-role-arn`, `--fsx-role-arn` | Roles for the S3 / FSx CSI driver add-ons, if the script installs them |
| `--auto-approve` | No confirmation prompts. Detected problems (wrong role trust, missing bucket access) still stop the script |
| `--step-by-step` | Pause between steps |
| `--skip-dependencies-migration` | Leave Helm-installed dependencies (S3 CSI, cert-manager, metrics-server) as they are |

What the script does:

1. Validates the cluster, add-on version and TLS bucket name, and any roles you passed. Nothing is changed if a check fails.
2. Creates the add-on IAM roles you did not provide.
3. Installs missing dependency add-ons (default EKS versions).
4. Scales down the Helm operator, ALB controller and KEDA, then installs the inference add-on with the
   Inference Gateway disabled, and waits for it to become ACTIVE.
5. Installs the metrics-server add-on, then removes the old Helm controllers.
6. Moves Helm-installed dependencies (for example the S3 CSI driver) to add-ons.

A backup directory (`/tmp/hyperpod-migration-backup-*`) records everything the script changed.

## IAM roles

The add-on runs its components in the `hyperpod-inference-system` namespace, so the roles used by the
Helm installation (whose service accounts live in `kube-system` / use different names) cannot be reused
as-is. The migration script leaves your Helm-era roles untouched (so the script's rollback on failure keeps working)
and uses a separate role for each add-on component.

You can bring your own role for any component. If you do not pass one, the script creates it with the
trust and permissions listed below (the same ones the HyperPod console / CloudFormation add-on flow uses).

| Flag | Add-on configuration key | Created role name if not passed |
|---|---|---|
| `--execution-role-arn` | `executionRoleArn` | `SageMakerHyperPodInference-<cluster-id>-execution-role` |
| `--jumpstart-gated-role-arn` | `jumpstartGatedModelDownloadRoleArn` | `js-gated-role-<cluster-id>` |
| `--alb-role-arn` | `alb.serviceAccount.roleArn` | `SageMakerHP-ALB-<cluster-id>-addon` |
| `--keda-role-arn` | `keda.auth.aws.irsa.roleArn` | `SageMakerHP-KEDA-<cluster-id>-addon` |

`<cluster-id>` is the first 8 characters of the HyperPod cluster ID. Roles the script creates are deleted
if the migration is rolled back; roles you pass in are never modified or deleted.

> **TLS buckets not named `hyperpod-tls*` need an extra policy.** The managed policy
> `AmazonSageMakerHyperPodInferenceAccess` only grants S3 access to buckets whose name starts with
> `hyperpod-tls`. If your cluster uses any other TLS certificate bucket — in the Helm values, or in the
> `tlsCertificateS3Bucket` of any JumpStartModel or InferenceEndpointConfig — the execution role must also
> have the [`TLSBucketsAccess`](#tls-certificate-buckets) policy listing those buckets.
>
> - If the script creates the execution role, it adds this policy for every bucket it finds.
> - If you pass your own role with `--execution-role-arn`, **you must add it yourself**. The script checks
>   access and stops before making any change if a bucket is not covered.
> - If you start using a new non-`hyperpod-tls*` bucket after migration, add it to the policy first, or
>   models using it will fail to read and write their TLS certificates.

### Bringing your own roles: what each role needs

Use this as the checklist for roles passed with the `--*-role-arn` flags. Trust subjects are listed in
[Trust policies](#trust-policies).

| Role | Required permissions | Add on top |
|---|---|---|
| Execution (`--execution-role-arn`) | AWS managed policy `AmazonSageMakerHyperPodInferenceAccess` | `TLSBucketsAccess` (below), only if a TLS bucket name does **not** start with `hyperpod-tls` |
| JumpStart gated model (`--jumpstart-gated-role-arn`) | AWS managed policy `AmazonSageMakerHyperPodGatedModelAccess` | — |
| ALB controller (`--alb-role-arn`) | AWS Load Balancer Controller policy (listed under [ALB controller role](#alb-controller-role)) | — |
| KEDA (`--keda-role-arn`) | CloudWatch + AMP read (listed under [KEDA role](#keda-role)) | Permissions for any other scaling triggers you use (for example SQS) |

**Certificate tagging.** The operator imports each model's TLS certificate into ACM and tags it
`CreatedBy=HyperPodInference`. `AmazonSageMakerHyperPodInferenceAccess` already includes
`acm:ImportCertificate`, `acm:AddTagsToCertificate` and `acm:DeleteCertificate` (scoped to that tag), so
nothing extra is needed if the managed policy is attached. A custom execution role without the managed policy
must grant those three actions; without `acm:AddTagsToCertificate` new models fail with
`failed to import ACM cert ... AccessDenied`. The quick-setup Helm execution role (`inf-<prefix>-io-role`) has
an inline policy that lacks this action, which is one more reason not to reuse it.

The script checks a provided execution role with `iam:SimulatePrincipalPolicy` (trust, S3 access on every
TLS bucket in use, and the ACM actions) and stops before making any change if something is missing.

#### Example: create your own add-on roles

Set these variables first. `CLUSTER_ID` is only used to name the roles; any unique suffix works.

```bash
export AWS_REGION=<region>
export CLUSTER_NAME=<EKS cluster name>
export CLUSTER_ID=<short unique suffix, e.g. first 8 characters of the HyperPod cluster ID>
export TLS_BUCKETS="<tls bucket 1> <tls bucket 2>"   # only buckets NOT named hyperpod-tls*; leave empty if none
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export OIDC_ISSUER=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" \
    --query cluster.identity.oidc.issuer --output text | sed 's|https://||')
export OIDC_PROVIDER_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/${OIDC_ISSUER}"
```

**Execution role** (`--execution-role-arn`)

```bash
cat > execution-trust.json <<EOF
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
        "StringEquals": {
          "${OIDC_ISSUER}:aud": "sts.amazonaws.com",
          "${OIDC_ISSUER}:sub": "system:serviceaccount:hyperpod-inference-system:hyperpod-inference-controller-manager"
        }
      }
    }
  ]
}
EOF
aws iam create-role --role-name "SageMakerHyperPodInference-${CLUSTER_ID}-execution-role" \
    --assume-role-policy-document file://execution-trust.json
aws iam attach-role-policy --role-name "SageMakerHyperPodInference-${CLUSTER_ID}-execution-role" \
    --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerHyperPodInferenceAccess

# Only if you use TLS buckets not named hyperpod-tls*
if [[ -n "$TLS_BUCKETS" ]]; then
  RESOURCES=$(for b in $TLS_BUCKETS; do printf '"arn:aws:s3:::%s/*",' "$b"; done); RESOURCES="[${RESOURCES%,}]"
  cat > tls-buckets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {"Sid": "TLSBucketDeleteObjectsPermission", "Effect": "Allow", "Action": ["s3:DeleteObject"],
     "Resource": ${RESOURCES}, "Condition": {"StringEquals": {"aws:ResourceAccount": "\${aws:PrincipalAccount}"}}},
    {"Sid": "TLSBucketGetObjectAccess", "Effect": "Allow", "Action": ["s3:GetObject"], "Resource": ${RESOURCES}},
    {"Sid": "TLSBucketPutObjectAccess", "Effect": "Allow", "Action": ["s3:PutObject", "s3:PutObjectTagging"],
     "Resource": ${RESOURCES}, "Condition": {"StringEquals": {"aws:ResourceAccount": "\${aws:PrincipalAccount}"}}}
  ]
}
EOF
  aws iam put-role-policy --role-name "SageMakerHyperPodInference-${CLUSTER_ID}-execution-role" \
      --policy-name TLSBucketsAccess --policy-document file://tls-buckets-policy.json
fi
```

**JumpStart gated model role** (`--jumpstart-gated-role-arn`)

```bash
cat > gated-trust.json <<EOF
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
          "${OIDC_ISSUER}:sub": "system:serviceaccount:*:hyperpod-inference-service-account*"
        }
      }
    }
  ]
}
EOF
aws iam create-role --role-name "js-gated-role-${CLUSTER_ID}" --assume-role-policy-document file://gated-trust.json
aws iam attach-role-policy --role-name "js-gated-role-${CLUSTER_ID}" \
    --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerHyperPodGatedModelAccess
```

**KEDA role** (`--keda-role-arn`)

```bash
cat > keda-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "${OIDC_PROVIDER_ARN}"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "${OIDC_ISSUER}:aud": "sts.amazonaws.com",
        "${OIDC_ISSUER}:sub": "system:serviceaccount:hyperpod-inference-system:keda-operator"
      }
    }
  }]
}
EOF
cat > keda-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["cloudwatch:GetMetricData", "cloudwatch:GetMetricStatistics", "cloudwatch:ListMetrics"], "Resource": "*"},
    {"Effect": "Allow", "Action": ["aps:QueryMetrics", "aps:GetLabels", "aps:GetSeries", "aps:GetMetricMetadata"], "Resource": "*"}
  ]
}
EOF
aws iam create-role --role-name "SageMakerHP-KEDA-${CLUSTER_ID}-addon" --assume-role-policy-document file://keda-trust.json
aws iam put-role-policy --role-name "SageMakerHP-KEDA-${CLUSTER_ID}-addon" \
    --policy-name HyperPodInferenceKedaAccess --policy-document file://keda-policy.json
# Add permissions for any other KEDA triggers you use (for example SQS) to this role.
```

**ALB controller role** (`--alb-role-arn`)

The permissions are the AWS Load Balancer Controller policy, in [`alb-controller-policy.json`](alb-controller-policy.json)
next to this guide.

```bash
cat > alb-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "${OIDC_PROVIDER_ARN}"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "${OIDC_ISSUER}:aud": "sts.amazonaws.com",
        "${OIDC_ISSUER}:sub": "system:serviceaccount:hyperpod-inference-system:aws-load-balancer-controller"
      }
    }
  }]
}
EOF
aws iam create-role --role-name "SageMakerHP-ALB-${CLUSTER_ID}-addon" --assume-role-policy-document file://alb-trust.json
aws iam put-role-policy --role-name "SageMakerHP-ALB-${CLUSTER_ID}-addon" \
    --policy-name HyperPodInferenceAlbControllerAccess --policy-document file://alb-controller-policy.json
```

Then run the migration with your roles:

```bash
./helm_to_addon.sh --cluster-name "$CLUSTER_NAME" --region "$AWS_REGION" \
  --execution-role-arn "arn:aws:iam::${ACCOUNT_ID}:role/SageMakerHyperPodInference-${CLUSTER_ID}-execution-role" \
  --jumpstart-gated-role-arn "arn:aws:iam::${ACCOUNT_ID}:role/js-gated-role-${CLUSTER_ID}" \
  --keda-role-arn "arn:aws:iam::${ACCOUNT_ID}:role/SageMakerHP-KEDA-${CLUSTER_ID}-addon" \
  --alb-role-arn "arn:aws:iam::${ACCOUNT_ID}:role/SageMakerHP-ALB-${CLUSTER_ID}-addon"
```

### Trust policies

All roles trust the cluster's EKS OIDC provider (`arn:aws:iam::<account>:oidc-provider/<oidc-issuer>`) with
`<oidc-issuer>:aud = sts.amazonaws.com` and the following service account subject (`<oidc-issuer>:sub`).
If you bring your own role, its trust policy must allow this subject.

| Role | Service account subject | Additional principal |
|---|---|---|
| Execution | `system:serviceaccount:hyperpod-inference-system:hyperpod-inference-controller-manager` | `sagemaker.amazonaws.com` (`sts:AssumeRole`) |
| JumpStart gated model | `system:serviceaccount:*:hyperpod-inference-service-account*` (StringLike) | `sagemaker.amazonaws.com` (`sts:AssumeRole`) |
| ALB controller | `system:serviceaccount:hyperpod-inference-system:aws-load-balancer-controller` | — |
| KEDA | `system:serviceaccount:hyperpod-inference-system:keda-operator` | — |

#### Reusing your Helm-era roles

The add-on uses different service accounts than the Helm chart, so **your Helm-era execution, ALB and KEDA
roles cannot be passed to the add-on as-is** — the add-on pods will fail to assume them.

| Role | Helm chart service account | Add-on service account |
|---|---|---|
| Execution | `hyperpod-inference-system:hyperpod-inference-operator-controller-manager` | `hyperpod-inference-system:hyperpod-inference-controller-manager` |
| ALB controller | `kube-system:aws-load-balancer-controller` | `hyperpod-inference-system:aws-load-balancer-controller` |
| KEDA | `kube-system:keda-operator` | `hyperpod-inference-system:keda-operator` |
| JumpStart gated model | `*:hyperpod-inference-service-account*` | unchanged |

To reuse a Helm-era role, add the add-on subject to its trust policy before running the script. Keep the
Helm subject as well, so the script can restore the Helm installation if the migration fails. For example, for KEDA:

```json
"Condition": {
  "StringEquals": {
    "<oidc-issuer>:aud": "sts.amazonaws.com",
    "<oidc-issuer>:sub": [
      "system:serviceaccount:kube-system:keda-operator",
      "system:serviceaccount:hyperpod-inference-system:keda-operator"
    ]
  }
}
```

The script checks the trust policy of every role you pass and asks for confirmation if the add-on subject
is missing.

### Permissions added to roles created by the script

#### Execution role

- AWS managed policy `arn:aws:iam::aws:policy/AmazonSageMakerHyperPodInferenceAccess`
- Inline policy `TLSBucketsAccess` (see below)

##### TLS certificate buckets

`AmazonSageMakerHyperPodInferenceAccess` grants S3 access only to buckets whose name starts with
`hyperpod-tls` (the quick-setup bucket, `hyperpod-tls-<prefix>-<id>`, is covered). Any other TLS bucket needs
explicit S3 permissions on the execution role. The script collects the buckets from:

- `tlsCertificateS3Bucket` in the Helm release values
- `spec.tlsCertificateS3Bucket` and `status.tlsCertificateS3Bucket` of every existing `JumpStartModel` and
  `InferenceEndpointConfig`

and adds this inline policy with one resource entry per bucket (`arn:aws:s3:::<bucket>/*`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TLSBucketDeleteObjectsPermission",
      "Effect": "Allow",
      "Action": ["s3:DeleteObject"],
      "Resource": ["arn:aws:s3:::<bucket-1>/*", "arn:aws:s3:::<bucket-2>/*"],
      "Condition": {"StringEquals": {"aws:ResourceAccount": "${aws:PrincipalAccount}"}}
    },
    {
      "Sid": "TLSBucketGetObjectAccess",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::<bucket-1>/*", "arn:aws:s3:::<bucket-2>/*"]
    },
    {
      "Sid": "TLSBucketPutObjectAccess",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:PutObjectTagging"],
      "Resource": ["arn:aws:s3:::<bucket-1>/*", "arn:aws:s3:::<bucket-2>/*"],
      "Condition": {"StringEquals": {"aws:ResourceAccount": "${aws:PrincipalAccount}"}}
    }
  ]
}
```

If you pass your own role with `--execution-role-arn`, the script does not modify it. It prints the
buckets in use and checks access with `iam:SimulatePrincipalPolicy`; if any bucket is not covered,
attach the policy above to your role. If you start using a new TLS bucket after migration, add it to this
policy too.

#### JumpStart gated model role

- AWS managed policy `arn:aws:iam::aws:policy/AmazonSageMakerHyperPodGatedModelAccess`

#### ALB controller role

Inline policy `HyperPodInferenceAlbControllerAccess` with the AWS Load Balancer Controller permissions:

- `iam:CreateServiceLinkedRole` for `elasticloadbalancing.amazonaws.com` only
- Read-only describe/get actions on EC2 (VPCs, subnets, security groups, instances, network interfaces,
  route tables, tags, addresses, AZs, internet gateways, VPC peering, CoIP pools, IPAM pools) and Elastic
  Load Balancing (load balancers, listeners, rules, target groups, target health, SSL policies, trust stores,
  tags, attributes, capacity reservations)
- `acm:ListCertificates`, `acm:DescribeCertificate`, `iam:ListServerCertificates`, `iam:GetServerCertificate`,
  `cognito-idp:DescribeUserPoolClient`, WAF Regional / WAFv2 web ACL get/associate/disassociate,
  Shield subscription/protection get/create/delete
- `ec2:CreateSecurityGroup`, `ec2:AuthorizeSecurityGroupIngress`, `ec2:RevokeSecurityGroupIngress`
- `ec2:CreateTags` / `ec2:DeleteTags` / `ec2:DeleteSecurityGroup` on security groups tagged
  `elbv2.k8s.aws/cluster`
- `elasticloadbalancing:CreateLoadBalancer`, `CreateTargetGroup` (only with the `elbv2.k8s.aws/cluster` request tag)
- `elasticloadbalancing:CreateListener`, `DeleteListener`, `CreateRule`, `DeleteRule`
- `elasticloadbalancing:AddTags` / `RemoveTags` on load balancers, target groups, listeners and listener rules
  (tag conditions on `elbv2.k8s.aws/cluster`)
- Modify/delete actions on load balancers and target groups tagged `elbv2.k8s.aws/cluster`
  (`ModifyLoadBalancerAttributes`, `SetIpAddressType`, `SetSecurityGroups`, `SetSubnets`, `DeleteLoadBalancer`,
  `ModifyTargetGroup`, `ModifyTargetGroupAttributes`, `DeleteTargetGroup`, `ModifyListenerAttributes`,
  `ModifyCapacityReservation`, `ModifyIpPools`)
- `elasticloadbalancing:RegisterTargets`, `DeregisterTargets` on target groups
- `elasticloadbalancing:SetWebAcl`, `ModifyListener`, `AddListenerCertificates`, `RemoveListenerCertificates`,
  `ModifyRule`, `SetRulePriorities`

#### KEDA role

Inline policy `HyperPodInferenceKedaAccess`:

- `cloudwatch:GetMetricData`, `cloudwatch:GetMetricStatistics`, `cloudwatch:ListMetrics`
- `aps:QueryMetrics`, `aps:GetLabels`, `aps:GetSeries`, `aps:GetMetricMetadata`

If your Helm-era KEDA role had extra permissions for other scaling triggers (for example SQS), pass your own
role with `--keda-role-arn`, or add those permissions to the created role after migration.

## Before and after you migrate: what to know

1. **Do not uninstall the Helm release or delete the Helm CloudFormation stack after migrating.** The Helm
   release still owns the inference CRDs and the `hyperpod-inference-system` namespace, which the add-on now
   uses (78 objects, 46 shared with the add-on). `helm uninstall` — which the quick-setup
   `InferenceOperatorMainStack` delete runs — deletes the CRDs, which deletes **every JumpStartModel and
   InferenceEndpointConfig**, and the add-on's namespace. Leave the release in place (or remove its release
   secret `sh.helm.release.v1.hyperpod-inference-operator.*` in kube-system so Helm forgets it).
2. **Scaling down the Helm operator disables the cluster inference watcher.** The next operator (add-on, or
   Helm after a rollback) re-enables it; it is Ready only after the watcher reaches `Enabled`, which took up
   to ~8 minutes. Running models keep serving throughout; new model changes wait until then.
3. **First spec change after migration rolls the model pods.** The add-on operator renders the pod template
   slightly differently, so the first change to a model triggers a rolling update. The surge pod needs spare
   capacity on the instance group; without it the new pod stays Pending and the old pods keep serving.
4. **TLS buckets not named `hyperpod-tls*` need the `TLSBucketsAccess` policy on the execution role.**
   `AmazonSageMakerHyperPodInferenceAccess` only covers `hyperpod-tls*` buckets. The script adds the policy to
   roles it creates; customers passing `--execution-role-arn` must add it themselves (the script stops if it
   is missing), and must update it before using any new non-`hyperpod-tls*` bucket. See [IAM roles](#iam-roles).
5. **Execution roles without the managed policy need ACM tagging.** New models import their TLS certificate into
   ACM and tag it; without `acm:AddTagsToCertificate` they fail with "failed to import ACM cert ... AccessDenied".
   The quick-setup Helm role (`inf-<prefix>-io-role`) lacks it. Roles with `AmazonSageMakerHyperPodInferenceAccess`
   are not affected.

## Recovery

### The script failed before the add-on was ACTIVE

The script asks whether to roll back (it never auto-approves this). Answer `y`. Running models keep serving
throughout. In order, the rollback:

1. saves all JumpStartModel and InferenceEndpointConfig resources to the backup directory
   (`model-crs-at-rollback.yaml`); model resources and their CRDs are never deleted,
2. removes the add-on with `--preserve`, so its controllers keep running for now,
3. re-applies the Helm release, so the webhooks, the KEDA metrics API and the CRD conversion webhook point
   back at the Helm controllers (objects now owned by other EKS add-ons are left alone),
4. scales the Helm operator, ALB controller and KEDA back up and waits for them,
5. removes the add-on's controllers,
6. removes only the tags it added, and deletes only the IAM roles it created (customer-provided roles are untouched).

Then check:

```bash
kubectl get deploy -n hyperpod-inference-system hyperpod-inference-operator-controller-manager   # 1/1 (may take ~8 min)
kubectl get deploy -n kube-system hyperpod-inference-operator-alb keda-operator keda-operator-metrics-apiserver keda-admission-webhooks
kubectl get jumpstartmodels,inferenceendpointconfigs -A
```

If the answer was `n`, the backup directory printed by the script (`/tmp/hyperpod-migration-backup-*`) lists
what was changed; fix the cause and re-run the script, or roll back manually with the same steps.

### The script failed after the add-on was ACTIVE

The add-on is managing the models; the script exits 0 with a warning that a later step (Helm cleanup or
dependency migration) failed. Re-running is not needed: finish the failed step by hand from the log, or leave
the remaining Helm resources (they are scaled down / unused).

If `metrics-server` shows `CREATE_FAILED` (older script versions):

```bash
aws eks delete-addon --cluster-name $CLUSTER --addon-name metrics-server
aws eks wait addon-deleted --cluster-name $CLUSTER --addon-name metrics-server
aws eks create-addon --cluster-name $CLUSTER --addon-name metrics-server --resolve-conflicts OVERWRITE
```

### Something is wrong after a completed migration

After the migration completes, fix forward on the add-on rather than going back to Helm. Running models keep
serving in all of these cases.

**Wrong configuration or role** — update the add-on configuration (start from the configuration the script
saved in its backup directory, `addon-configuration.json`):

```bash
aws eks describe-addon --cluster-name $CLUSTER --addon-name amazon-sagemaker-hyperpod-inference \
  --query addon.configurationValues --output text > addon-config.json
# edit addon-config.json, keep "inferenceGateway": {"enabled": false} unless you are enabling the gateway
aws eks update-addon --cluster-name $CLUSTER --addon-name amazon-sagemaker-hyperpod-inference \
  --configuration-values file://addon-config.json --resolve-conflicts OVERWRITE
```

**Problem with the add-on version** — move to another supported version:

```bash
aws eks describe-addon-versions --addon-name amazon-sagemaker-hyperpod-inference \
  --kubernetes-version <cluster k8s version> --query 'addons[0].addonVersions[].addonVersion'
aws eks update-addon --cluster-name $CLUSTER --addon-name amazon-sagemaker-hyperpod-inference \
  --addon-version <version> --resolve-conflicts OVERWRITE
```

**Add-on stuck in a failed state** — recreate it without touching running workloads. `--preserve` keeps the
add-on's controllers running while it is recreated:

```bash
aws eks describe-addon --cluster-name $CLUSTER --addon-name amazon-sagemaker-hyperpod-inference \
  --query addon.configurationValues --output text > addon-config.json
aws eks delete-addon --cluster-name $CLUSTER --addon-name amazon-sagemaker-hyperpod-inference --preserve
aws eks wait addon-deleted --cluster-name $CLUSTER --addon-name amazon-sagemaker-hyperpod-inference
aws eks create-addon --cluster-name $CLUSTER --addon-name amazon-sagemaker-hyperpod-inference \
  --addon-version <same version> --configuration-values file://addon-config.json --resolve-conflicts OVERWRITE
```

Do not run `helm rollback` after a completed migration: it fails, because the migration removed Helm-only
resources and other EKS add-ons now own parts of the old release. If you need to return to the Helm
installation, contact AWS Support.

### A model stopped reconciling (stuck in DeploymentInProgress)

After repeated reconcile errors the operator backs off. Fix the cause (for example IAM), then re-apply the
model or, if it still does not move, delete and re-create the CR from its saved YAML. Endpoints keep serving
from the existing pods until the CR is deleted.
