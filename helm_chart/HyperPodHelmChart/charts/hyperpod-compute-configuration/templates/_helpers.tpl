{{/*
Chart name, truncated to 63 characters (Kubernetes name limit).
*/}}
{{- define "hyperpod-compute-configuration.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Name for a webhook resource: "<chart name>-webhook", truncated to 63 characters. All webhook
resources (ServiceAccount, Deployment, Service, PodDisruptionBudget, Certificate) share it.
*/}}
{{- define "hyperpod-compute-configuration.webhookName" -}}
{{- printf "%s-webhook" (include "hyperpod-compute-configuration.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Labels on every webhook resource.
*/}}
{{- define "hyperpod-compute-configuration.webhookLabels" -}}
app.kubernetes.io/name: {{ include "hyperpod-compute-configuration.name" . }}
app.kubernetes.io/component: webhook
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end }}

{{/*
Selector labels: the subset that identifies the webhook pods (must not change across upgrades).
*/}}
{{- define "hyperpod-compute-configuration.webhookSelectorLabels" -}}
app.kubernetes.io/name: {{ include "hyperpod-compute-configuration.name" . }}
app.kubernetes.io/component: webhook
{{- end }}

{{/*
Webhook image tag: webhook.image.tag, or the published tag this chart version is tested with.
*/}}
{{- define "hyperpod-compute-configuration.webhookImageTag" -}}
{{- .Values.webhook.image.tag | default "1.0.26.0_1.0.5.0" }}
{{- end }}

{{/*
Namespace the webhook and its objects are installed into: .Values.namespace (default
aws-hyperpod). The parent HyperPodHelmChart is installed into kube-system, so this subchart doesn't
use the release namespace, as the Ray endpoint operator and resource ownership subcharts do.
*/}}
{{- define "hyperpod-compute-configuration.namespaceName" -}}
{{- .Values.namespace | default "aws-hyperpod" }}
{{- end }}

{{/*
Region of the cluster: .Values.region, global.region, then the nodes'
topology.kubernetes.io/region label (lookup only answers against a live cluster, so helm template
and client-side dry runs need region or global.region). Empty when none is found.
*/}}
{{- define "hyperpod-compute-configuration.requestedRegion" -}}
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
  1. .Values.webhook.image.override (full URI override, skips all resolution)
  2. Constructed from region→account mapping + repository name + tag
*/}}
{{- define "hyperpod-compute-configuration.webhookImage" -}}
{{- if .Values.webhook.image.override -}}
{{- if not (regexMatch "@sha256:[a-f0-9]{64}$" .Values.webhook.image.override) -}}
  {{- fail (printf "webhook.image.override must pin a digest, <repository>@sha256:<64 hex>; got %q" .Values.webhook.image.override) -}}
{{- end -}}
  {{- .Values.webhook.image.override -}}
{{- else -}}
{{- $region := include "hyperpod-compute-configuration.requestedRegion" . -}}
{{- if not $region -}}
  {{- fail "region is required when webhook.image.override is not set and it could not be detected from the nodes' topology.kubernetes.io/region label. Set region or global.region." -}}
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
  {{- fail (printf "Unsupported AWS region: %s (supported: %s). Set webhook.image.override explicitly for non-standard regions." $region (keys $regionAccountMap | sortAlpha | join ", ")) -}}
{{- end -}}

{{- if .Values.webhook.image.digest -}}
{{- if not (regexMatch "^sha256:[a-f0-9]{64}$" .Values.webhook.image.digest) -}}
  {{- fail (printf "webhook.image.digest must be sha256:<64 hex>; got %q" .Values.webhook.image.digest) -}}
{{- end -}}
{{- printf "%s.dkr.ecr.%s.amazonaws.com/hyperpod-compute-configuration-webhook@%s" $accountId $region .Values.webhook.image.digest -}}
{{- else -}}
{{- printf "%s.dkr.ecr.%s.amazonaws.com/hyperpod-compute-configuration-webhook:%s" $accountId $region (include "hyperpod-compute-configuration.webhookImageTag" .) -}}
{{- end -}}
{{- end -}}
{{- end }}

{{/*
Value for WEBHOOK_VERSION, which the webhook logs at startup: the override URI, else the digest,
else the tag.
*/}}
{{- define "hyperpod-compute-configuration.webhookImageVersion" -}}
{{- if .Values.webhook.image.override }}
{{- .Values.webhook.image.override }}
{{- else if .Values.webhook.image.digest }}
{{- .Values.webhook.image.digest }}
{{- else }}
{{- include "hyperpod-compute-configuration.webhookImageTag" . }}
{{- end }}
{{- end }}

{{/*
Workload kinds the webhook handles: the webhook name prefix, the API group and resource, and the
path suffix shared by the mutating ("/mutate-<path>") and validating ("/validate-<path>")
handlers.
A kind marked "blocked: true" is temporarily unsupported. It keeps its webhook entries (dropping
them would leave cert-manager's caBundle behind in an entry Helm no longer manages, failing the
upgrade), but the admission policies skip it, so the unsupported-kinds policy rejects a labelled
object of that kind in every namespace.
*/}}
{{- define "hyperpod-compute-configuration.webhookKinds" -}}
- id: rayjobs
  group: ray.io
  resource: rayjobs
  path: ray-io-v1-rayjob
  # Container resources, the instance-type nodeSelector, and the affinity (which can rule out the
  # instance type) in the head or any worker group's pod template
  computeChanged: >-
    object.?spec.?rayClusterSpec.?headGroupSpec.?template.?spec.?containers.orValue([]).map(c, c.?resources.orValue({}))
    != oldObject.?spec.?rayClusterSpec.?headGroupSpec.?template.?spec.?containers.orValue([]).map(c, c.?resources.orValue({}))
    || object.?spec.?rayClusterSpec.?workerGroupSpecs.orValue([]).map(g, g.?template.?spec.?containers.orValue([]).map(c, c.?resources.orValue({})))
    != oldObject.?spec.?rayClusterSpec.?workerGroupSpecs.orValue([]).map(g, g.?template.?spec.?containers.orValue([]).map(c, c.?resources.orValue({})))
    || object.?spec.?rayClusterSpec.?headGroupSpec.?template.?spec.?nodeSelector[?'node.kubernetes.io/instance-type'].orValue('')
    != oldObject.?spec.?rayClusterSpec.?headGroupSpec.?template.?spec.?nodeSelector[?'node.kubernetes.io/instance-type'].orValue('')
    || object.?spec.?rayClusterSpec.?workerGroupSpecs.orValue([]).map(g, g.?template.?spec.?nodeSelector[?'node.kubernetes.io/instance-type'].orValue(''))
    != oldObject.?spec.?rayClusterSpec.?workerGroupSpecs.orValue([]).map(g, g.?template.?spec.?nodeSelector[?'node.kubernetes.io/instance-type'].orValue(''))
    || object.?spec.?rayClusterSpec.?headGroupSpec.?template.?spec.?affinity.orValue({})
    != oldObject.?spec.?rayClusterSpec.?headGroupSpec.?template.?spec.?affinity.orValue({})
    || object.?spec.?rayClusterSpec.?workerGroupSpecs.orValue([]).map(g, g.?template.?spec.?affinity.orValue({}))
    != oldObject.?spec.?rayClusterSpec.?workerGroupSpecs.orValue([]).map(g, g.?template.?spec.?affinity.orValue({}))
  # A worker group the old object doesn't have, by name
  groupsAdded: >-
    object.?spec.?rayClusterSpec.?workerGroupSpecs.orValue([]).exists(g,
    !oldObject.?spec.?rayClusterSpec.?workerGroupSpecs.orValue([]).exists(o, o.?groupName.orValue('') == g.?groupName.orValue('')))
- id: pytorchjobs
  group: kubeflow.org
  resource: pytorchjobs
  path: kubeflow-org-v1-pytorchjob
  # TEMPORARILY BLOCKED: the admission policies treat Kubeflow PyTorchJob as unsupported, so a
  # labelled one is rejected in every namespace. Its webhook entries stay, because removing them
  # leaves cert-manager's caBundle behind in a half-removed entry and the upgrade fails. Remove
  # this line to re-enable the kind.
  blocked: true
  # Container resources, the instance-type nodeSelector, and the affinity in any replica type's pod
  # template (Master, Worker)
  computeChanged: >-
    size(object.?spec.?pytorchReplicaSpecs.orValue({})) != size(oldObject.?spec.?pytorchReplicaSpecs.orValue({}))
    || object.?spec.?pytorchReplicaSpecs.orValue({}).exists(k,
    !(k in oldObject.?spec.?pytorchReplicaSpecs.orValue({}))
    || object.spec.pytorchReplicaSpecs[k].?template.?spec.?containers.orValue([]).map(c, c.?resources.orValue({}))
    != oldObject.spec.pytorchReplicaSpecs[k].?template.?spec.?containers.orValue([]).map(c, c.?resources.orValue({}))
    || object.spec.pytorchReplicaSpecs[k].?template.?spec.?nodeSelector[?'node.kubernetes.io/instance-type'].orValue('')
    != oldObject.spec.pytorchReplicaSpecs[k].?template.?spec.?nodeSelector[?'node.kubernetes.io/instance-type'].orValue('')
    || object.spec.pytorchReplicaSpecs[k].?template.?spec.?affinity.orValue({})
    != oldObject.spec.pytorchReplicaSpecs[k].?template.?spec.?affinity.orValue({}))
  # A replica type the old object doesn't have
  groupsAdded: >-
    object.?spec.?pytorchReplicaSpecs.orValue({}).exists(k, !(k in oldObject.?spec.?pytorchReplicaSpecs.orValue({})))
- id: hyperpodpytorchjobs
  group: sagemaker.amazonaws.com
  resource: hyperpodpytorchjobs
  path: sagemaker-amazonaws-com-v1-hyperpodpytorchjob
  # Container resources, the instance-type nodeSelector, and the affinity in any replica spec's pod
  # template
  computeChanged: >-
    object.?spec.?replicaSpecs.orValue([]).map(r, r.?template.?spec.?containers.orValue([]).map(c, c.?resources.orValue({})))
    != oldObject.?spec.?replicaSpecs.orValue([]).map(r, r.?template.?spec.?containers.orValue([]).map(c, c.?resources.orValue({})))
    || object.?spec.?replicaSpecs.orValue([]).map(r, r.?template.?spec.?nodeSelector[?'node.kubernetes.io/instance-type'].orValue(''))
    != oldObject.?spec.?replicaSpecs.orValue([]).map(r, r.?template.?spec.?nodeSelector[?'node.kubernetes.io/instance-type'].orValue(''))
    || object.?spec.?replicaSpecs.orValue([]).map(r, r.?template.?spec.?affinity.orValue({}))
    != oldObject.?spec.?replicaSpecs.orValue([]).map(r, r.?template.?spec.?affinity.orValue({}))
  # A replica name the old object doesn't have
  groupsAdded: >-
    object.?spec.?replicaSpecs.orValue([]).exists(r,
    !oldObject.?spec.?replicaSpecs.orValue([]).exists(o, o.?name.orValue('') == r.?name.orValue('')))
- id: inferenceendpointconfigs
  group: inference.sagemaker.aws.amazon.com
  resource: inferenceendpointconfigs
  path: inference-sagemaker-aws-amazon-com-v1-inferenceendpointconfig
  # Instance type, worker resources, and instanceTypes and nodeAffinity (which can't be used with
  # a compute configuration)
  computeChanged: >-
    object.?spec.?instanceType.orValue('') != oldObject.?spec.?instanceType.orValue('')
    || object.?spec.?instanceTypes.orValue([]) != oldObject.?spec.?instanceTypes.orValue([])
    || object.?spec.?nodeAffinity.orValue({}) != oldObject.?spec.?nodeAffinity.orValue({})
    || object.?spec.?worker.?resources.orValue({}) != oldObject.?spec.?worker.?resources.orValue({})
  # Only one group, which can't be added
  groupsAdded: "false"
{{- end }}

{{/*
Namespace label that turns on enforcement when set to "enabled". The key is part of the
feature's API (Studio and admins set it), so it isn't a value.
*/}}
{{- define "hyperpod-compute-configuration.enforcementLabel" -}}
compute.configuration.sagemaker.amazonaws.com/enforcement
{{- end }}

{{/*
Entries for a MutatingWebhookConfiguration or ValidatingWebhookConfiguration, one per kind.
- enforced false: every namespace except kube-system, with failurePolicy Ignore, so an outage
  never blocks anyone (the mutating webhook).
- enforced true: only namespaces labelled <enforcementLabel>=enabled, with failurePolicy Fail,
  so nothing gets through unchecked (the validating webhook). The webhook's own namespace is
  never enforced, so an outage can't stop the webhook from restarting.
Only workloads that reference a compute configuration are sent to the webhook.
Arguments: "context" (the root context), "type" ("mutate" or "validate"), "operations" and
"enforced".
*/}}
{{- define "hyperpod-compute-configuration.webhookEntries" -}}
{{- $ctx := .context }}
{{- $enforced := .enforced | default false }}
{{- range $kind := fromYamlArray (include "hyperpod-compute-configuration.webhookKinds" $ctx) }}
- name: {{ $kind.id }}.compute.configuration.sagemaker.amazonaws.com
  admissionReviewVersions: [v1]
  clientConfig:
    service:
      name: {{ include "hyperpod-compute-configuration.webhookName" $ctx }}
      namespace: {{ include "hyperpod-compute-configuration.namespaceName" $ctx }}
      path: /{{ $.type }}-{{ $kind.path }}
      port: 443
  rules:
  - apiGroups: [{{ $kind.group | quote }}]
    apiVersions: [v1]
    operations: {{ toJson $.operations }}
    resources: [{{ $kind.resource }}]
    scope: Namespaced
  failurePolicy: {{ ternary "Fail" "Ignore" $enforced }}
  timeoutSeconds: {{ $ctx.Values.webhook.timeoutSeconds }}
  sideEffects: None
  matchPolicy: Exact
  {{- if eq $.type "mutate" }}
  # If a later mutating webhook changes the object, call this one once more. It runs at most
  # once more and doesn't guarantee our values end up last; the validating webhook catches that.
  reinvocationPolicy: IfNeeded
  {{- end }}
  {{- if has "UPDATE" $.operations }}
  # Updates reach the webhook only when they can matter: the configuration label changed,
  # apply-latest is set, (mutating only) a group was added, or (validating only) compute or the
  # applied-uid, applied-generation or applied-snapshot stamp changed (the mutating webhook
  # manages the stamp, so the validating webhook must see edits to it). Kueue, autoscaler and other
  # controller updates are filtered out, so a webhook outage can't block them.
  matchConditions:
  - name: create-or-relevant-update
    expression: >-
      request.operation != 'UPDATE'
      || object.metadata.?labels[?'compute.configuration.sagemaker.amazonaws.com/name'].orValue('')
      != oldObject.metadata.?labels[?'compute.configuration.sagemaker.amazonaws.com/name'].orValue('')
      || object.metadata.?annotations[?'compute.configuration.sagemaker.amazonaws.com/apply-latest'].orValue('') == 'true'
      {{- if eq $.type "mutate" }}
      || ({{ $kind.groupsAdded }})
      {{- end }}
      {{- if eq $.type "validate" }}
      || ({{ $kind.computeChanged }})
      {{- range $a := list "applied-uid" "applied-generation" "applied-snapshot" }}
      || object.metadata.?annotations[?'compute.configuration.sagemaker.amazonaws.com/{{ $a }}'].orValue('')
      != oldObject.metadata.?annotations[?'compute.configuration.sagemaker.amazonaws.com/{{ $a }}'].orValue('')
      {{- end }}
      {{- end }}
  {{- end }}
  namespaceSelector:
    matchExpressions:
    {{- if $enforced }}
    - key: {{ include "hyperpod-compute-configuration.enforcementLabel" $ctx }}
      operator: In
      values: [enabled]
    {{- end }}
    - key: kubernetes.io/metadata.name
      operator: NotIn
      values: [kube-system{{ if $enforced }}, {{ include "hyperpod-compute-configuration.namespaceName" $ctx }}{{ end }}]
  # Only workloads that reference a compute configuration (on updates, before or after the change).
  objectSelector:
    matchExpressions:
    - key: compute.configuration.sagemaker.amazonaws.com/name
      operator: Exists
{{- end }}
{{- end }}
