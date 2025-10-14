{{/*
Expand the name of the chart.
*/}}
{{- define "health-monitoring-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "health-monitoring-agent.fullname" -}}
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
{{- define "health-monitoring-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "health-monitoring-agent.labels" -}}
helm.sh/chart: {{ include "health-monitoring-agent.chart" . }}
{{ include "health-monitoring-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "health-monitoring-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "health-monitoring-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Generate the health monitoring agent image URI based on AWS region
*/}}
{{- define "health-monitoring-agent.imageUri" -}}
{{- $region := "" -}}
{{- $imageTag := .Values.imageTag | default "1.0.935.0_1.0.282.0" -}}

{{/* Debug: Show image tag selection if debug is enabled */}}
{{- if .Values.debug -}}
  {{/* DEBUG: Image tag selection - Values.imageTag: {{ .Values.imageTag | default "not set" }}, Final imageTag: {{ $imageTag }} */}}
{{- end -}}

{{/* Try to get region from various sources in priority order */}}
{{- if .Values.region -}}
  {{/* 1. Explicit region setting (highest priority) */}}
  {{- $region = .Values.region -}}
  {{- if .Values.debug -}}
    {{/* DEBUG: Using explicit region setting: {{ $region }} */}}
  {{- end -}}
{{- else if and .Values.global .Values.global.region -}}
  {{/* 2. Global region setting */}}
  {{- $region = .Values.global.region -}}
  {{- if .Values.debug -}}
    {{/* DEBUG: Using global region setting: {{ $region }} */}}
  {{- end -}}
{{- else -}}
  {{/* 3. Try to detect region from Kubernetes cluster context */}}
  {{- $detectedRegion := "" -}}
  {{- if .Values.debug -}}
    {{/* DEBUG: Attempting automatic region detection... */}}
  {{- end -}}
  
  {{/* Note: cluster-info ConfigMap doesn't exist in EKS clusters, so we skip this method */}}
  {{- if .Values.debug -}}
    {{/* DEBUG: Skipping cluster-info ConfigMap lookup (not available in EKS clusters) */}}
  {{- end -}}
  
  {{/* Try alternative method: look for AWS node info */}}
  {{- if not $detectedRegion -}}
    {{- if .Values.debug -}}
      {{/* DEBUG: Trying to detect region from node labels... */}}
    {{- end -}}
    {{- $nodes := lookup "v1" "Node" "" "" -}}
    {{- if $nodes -}}
      {{- if .Values.debug -}}
        {{/* DEBUG: Found {{ len $nodes.items }} nodes, checking labels... */}}
      {{- end -}}
      {{- range $nodes.items -}}
        {{- if .metadata.labels -}}
          {{/* Check for topology.kubernetes.io/region label */}}
          {{- if index .metadata.labels "topology.kubernetes.io/region" -}}
            {{- $detectedRegion = index .metadata.labels "topology.kubernetes.io/region" -}}
            {{- if $.Values.debug -}}
              {{/* DEBUG: Found region from topology.kubernetes.io/region label: {{ $detectedRegion }} */}}
            {{- end -}}
            {{- break -}}
          {{- end -}}
          {{/* Check for failure-domain.beta.kubernetes.io/region label (legacy) */}}
          {{- if and (not $detectedRegion) (index .metadata.labels "failure-domain.beta.kubernetes.io/region") -}}
            {{- $detectedRegion = index .metadata.labels "failure-domain.beta.kubernetes.io/region" -}}
            {{- if $.Values.debug -}}
              {{/* DEBUG: Found region from failure-domain.beta.kubernetes.io/region label: {{ $detectedRegion }} */}}
            {{- end -}}
            {{- break -}}
          {{- end -}}
        {{- end -}}
      {{- end -}}
    {{- else -}}
      {{- if .Values.debug -}}
        {{/* DEBUG: No nodes found for region detection */}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
  
  {{/* Use detected region or fall back to default */}}
  {{- if $detectedRegion -}}
    {{- $region = $detectedRegion -}}
    {{- if .Values.debug -}}
      {{/* DEBUG: Using detected region: {{ $region }} */}}
    {{- end -}}
  {{- else -}}
    {{/* 4. Default fallback to us-east-1 */}}
    {{- $region = "us-east-1" -}}
    {{- if .Values.debug -}}
      {{/* DEBUG: No region detected, using default fallback: {{ $region }} */}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{/* Region to ECR account ID mapping */}}
{{- $regionAccountMap := dict 
  "us-east-1" "767398015722"
  "us-west-2" "905418368575"
  "us-east-2" "851725546812"
  "us-west-1" "011528288828"
  "eu-central-1" "211125453373"
  "eu-north-1" "654654141839"
  "eu-west-1" "533267293120"
  "eu-west-2" "011528288831"
  "ap-northeast-1" "533267052152"
  "ap-south-1" "011528288864"
  "ap-southeast-1" "905418428165"
  "ap-southeast-2" "851725636348"
  "sa-east-1" "025066253954"
-}}

{{/* Get the account ID for the region, default to us-west-2 account if region not found */}}
{{- $accountId := index $regionAccountMap $region | default "767398015722" -}}

{{/* Debug: Show final region and account mapping */}}
{{- if .Values.debug -}}
  {{/* DEBUG: Final region: {{ $region }}, Account ID: {{ $accountId }} */}}
{{- end -}}

{{/* Allow override of the full image URI if specified */}}
{{- if .Values.hmaimage -}}
  {{- if .Values.debug -}}
    {{/* DEBUG: Using override image URI: {{ .Values.hmaimage }} */}}
  {{- end -}}
  {{- .Values.hmaimage -}}
{{- else -}}
  {{- $finalImageUri := printf "%s.dkr.ecr.%s.amazonaws.com/hyperpod-health-monitoring-agent:%s" $accountId $region $imageTag -}}
  {{- if .Values.debug -}}
    {{/* DEBUG: Generated image URI: {{ $finalImageUri }} */}}
  {{- end -}}
  {{- $finalImageUri -}}
{{- end -}}
{{- end }}
