{{/*
Resource name: <namePrefix>-<suffix>, truncated to the 63-character Kubernetes limit
(same approach as jupyter-k8s's resourceName helper).
Takes a dict with .suffix and .context (the root context).
*/}}
{{- define "resource-ownership.resourceName" -}}
{{- $prefix := .context.Values.namePrefix }}
{{- $suffix := .suffix }}
{{- $maxLen := sub 62 (len $suffix) | int }}
{{- printf "%s-%s" (trunc $maxLen $prefix | trimSuffix "-") $suffix | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "resource-ownership.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end }}

{{/*
Selector labels for the webhook pods.
*/}}
{{- define "resource-ownership.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/component: webhook
{{- end }}

{{/*
Every namespace the webhook and the policy skip: excludedNamespaces plus the release namespace.
*/}}
{{- define "resource-ownership.excludedNamespaces" -}}
{{- $ns := concat .Values.excludedNamespaces (list (include "resource-ownership.namespaceName" .)) | uniq }}
{{- toJson $ns }}
{{- end }}

{{/*
Webhook image tag: image.tag, or the published tag this chart version is tested with. Ignored when
image.digest is set.
*/}}
{{- define "resource-ownership.webhookImageTag" -}}
{{- .Values.image.tag | default "1.0.20.0_1.0.3.0" }}
{{- end }}

{{/*
Resolve the webhook image URI.
Priority for region:
  1. .Values.region (explicit setting)
  2. .Values.global.region (global setting from parent chart)
  3. the nodes' topology.kubernetes.io/region label (detected at install, as the resource
     monitor and health monitoring agent subcharts do)
  4. fail — region is required
A region that isn't in the region→account mapping fails rendering and lists the supported ones.

Priority for image URI:
  1. .Values.image.override (full URI override, skips all resolution)
  2. Constructed from region→account mapping + repository name + "@" + image.digest, which pins
     one image (a tag can be moved to another)
  3. Constructed from region→account mapping + repository name + ":" + tag
*/}}
{{- define "resource-ownership.imageUri" -}}
{{- if .Values.image.override -}}
  {{- .Values.image.override -}}
{{- else -}}
{{- $region := include "resource-ownership.requestedRegion" . -}}
{{- if not $region -}}
  {{- fail "region is required when image.override is not set and it could not be detected from the nodes' topology.kubernetes.io/region label. Set region or global.region." -}}
{{- end -}}

{{/* Region to ECR account ID mapping */}}
{{- $regionAccountMap := dict
  "ap-northeast-1" "167660772520"
  "ap-south-1" "350868604920"
  "ap-south-2" "682032008207"
  "ap-southeast-1" "238902833166"
  "ap-southeast-2" "410543484366"
  "eu-central-1" "259738048750"
  "eu-north-1" "939593443514"
  "eu-west-1" "124013160849"
  "eu-west-2" "414154849790"
  "sa-east-1" "720443608875"
  "us-east-1" "955788910749"
  "us-east-2" "945058679767"
  "us-west-1" "194358183338"
  "us-west-2" "756082469455"
-}}

{{- $accountId := index $regionAccountMap $region -}}
{{- if not $accountId -}}
  {{- fail (printf "Unsupported AWS region: %s (supported: %s). Set image.override explicitly for non-standard regions." $region (keys $regionAccountMap | sortAlpha | join ", ")) -}}
{{- end -}}

{{- if .Values.image.digest -}}
{{- printf "%s.dkr.ecr.%s.amazonaws.com/hyperpod-resource-ownership-webhook@%s" $accountId $region .Values.image.digest -}}
{{- else -}}
{{- printf "%s.dkr.ecr.%s.amazonaws.com/hyperpod-resource-ownership-webhook:%s" $accountId $region (include "resource-ownership.webhookImageTag" .) -}}
{{- end -}}
{{- end -}}
{{- end }}

{{/*
Value for WEBHOOK_VERSION, which the webhook logs at startup: the override URI, else the digest,
else the tag.
*/}}
{{- define "resource-ownership.webhookImageVersion" -}}
{{- if .Values.image.override }}
{{- .Values.image.override }}
{{- else if .Values.image.digest }}
{{- .Values.image.digest }}
{{- else }}
{{- include "resource-ownership.webhookImageTag" . }}
{{- end }}
{{- end }}

{{/*
Namespace the webhook and its objects are installed into: .Values.namespace (default
aws-hyperpod). The parent HyperPodHelmChart is installed into kube-system, so this subchart doesn't
use the release namespace, as the Ray endpoint operator and resource monitor subcharts do.
*/}}
{{- define "resource-ownership.namespaceName" -}}
{{- .Values.namespace | default "aws-hyperpod" }}
{{- end }}

{{/*
Region of the cluster: .Values.region, global.region, then the nodes'
topology.kubernetes.io/region label (lookup only answers against a live cluster, so helm template
and client-side dry runs need region or global.region). Empty when none is found.
*/}}
{{- define "resource-ownership.requestedRegion" -}}
{{- $region := .Values.region -}}
{{- if and (not $region) .Values.global .Values.global.region -}}
{{- $region = .Values.global.region -}}
{{- end -}}
{{- if not $region -}}
{{- $nodes := lookup "v1" "Node" "" "" -}}
{{- if $nodes -}}
{{- range $nodes.items -}}
{{- if and (not $region) .metadata.labels (index .metadata.labels "topology.kubernetes.io/region") -}}
{{- $region = index .metadata.labels "topology.kubernetes.io/region" -}}
{{- end -}}
{{- end -}}
{{- end -}}
{{- end -}}
{{- $region -}}
{{- end -}}
