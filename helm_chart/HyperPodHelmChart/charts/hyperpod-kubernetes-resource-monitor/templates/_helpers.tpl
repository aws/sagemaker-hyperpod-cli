{{/*
Expand the name of the chart.
*/}}
{{- define "hyperpod-cluster-monitoring-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "hyperpod-cluster-monitoring-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "hyperpod-cluster-monitoring-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "hyperpod-cluster-monitoring-agent.labels" -}}
helm.sh/chart: {{ include "hyperpod-cluster-monitoring-agent.chart" . }}
{{ include "hyperpod-cluster-monitoring-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "hyperpod-cluster-monitoring-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "hyperpod-cluster-monitoring-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app: cluster-monitoring-agent
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "hyperpod-cluster-monitoring-agent.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "hyperpod-cluster-monitoring-agent.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Convert necessaryDaemonsets list to JSON string
*/}}
{{- define "hyperpod-cluster-monitoring-agent.necessaryDaemonsetsJson" -}}
{{- $daemonsets := list }}
{{- range .Values.monitoring.necessaryDaemonsets }}
{{- $daemonsets = append $daemonsets (dict "name" .name "namespace" .namespace) }}
{{- end }}
{{- $daemonsets | toJson }}
{{- end }}

{{/*
Region whose HyperPod ECR repository the image is requested from: .Values.region, global.region,
then the nodes' topology.kubernetes.io/region label. Empty when none is set.
*/}}
{{- define "hyperpod-cluster-monitoring-agent.requestedRegion" -}}
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
HyperPod ECR account of a region (the argument), the same map as health-monitoring-agent.
Empty for an unmapped region.
*/}}
{{- define "hyperpod-cluster-monitoring-agent.ecrAccount" -}}
{{- $accounts := dict
  "us-east-1" "767398015722"
  "us-west-2" "905418368575"
  "us-east-2" "851725546812"
  "us-west-1" "011528288828"
  "eu-central-1" "211125453373"
  "eu-north-1" "654654141839"
  "eu-west-1" "533267293120"
  "eu-west-2" "011528288831"
  "eu-south-2" "626887787726"
  "ap-northeast-1" "533267052152"
  "ap-south-1" "011528288864"
  "ap-southeast-1" "905418428165"
  "ap-southeast-2" "851725636348"
  "ap-southeast-3" "971422672635"
  "ap-southeast-4" "084375568333"
  "ca-central-1" "843976229209"
  "sa-east-1" "025066253954"
-}}
{{- index $accounts . | default "" -}}
{{- end -}}

{{/*
Image URI. image.repository overrides the repository. Otherwise the image comes from the HyperPod ECR
repository of the requested region. A region with no repository (unset, or not in the map) uses
us-east-1, as health-monitoring-agent does. An unmapped region is not a template failure: this chart
is a subchart of the HyperPod Helm chart, where a failure would abort the whole install, and the
installer always passes the cluster's region. The fallback is recorded in the Deployment annotation
sagemaker.amazonaws.com/image-region-fallback.
*/}}
{{- define "hyperpod-cluster-monitoring-agent.image" -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- if .Values.image.repository -}}
{{- printf "%s:%s" .Values.image.repository $tag -}}
{{- else -}}
{{- $region := include "hyperpod-cluster-monitoring-agent.requestedRegion" . -}}
{{- $account := include "hyperpod-cluster-monitoring-agent.ecrAccount" $region -}}
{{- if not $account -}}
{{- $region = "us-east-1" -}}
{{- $account = include "hyperpod-cluster-monitoring-agent.ecrAccount" $region -}}
{{- end -}}
{{- printf "%s.dkr.ecr.%s.amazonaws.com/hyperpod-cluster-monitoring-agent:%s" $account $region $tag -}}
{{- end -}}
{{- end -}}

{{/*
The requested region when it has no HyperPod ECR repository and the image falls back to us-east-1;
empty otherwise. An unset region is the documented default, not a fallback.
*/}}
{{- define "hyperpod-cluster-monitoring-agent.imageRegionFallback" -}}
{{- if not .Values.image.repository -}}
{{- $region := include "hyperpod-cluster-monitoring-agent.requestedRegion" . -}}
{{- if and $region (not (include "hyperpod-cluster-monitoring-agent.ecrAccount" $region)) -}}
{{- $region -}}
{{- end -}}
{{- end -}}
{{- end -}}
