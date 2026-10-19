{{/*
Expand the name of the chart.
*/}}
{{- define "hyperpod-ray-endpoint-operator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "hyperpod-ray-endpoint-operator.fullname" -}}
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
Namespace for generated references.
Defaults to "hyperpod-ray" unless overridden via values.
*/}}
{{- define "hyperpod-ray-endpoint-operator.namespaceName" -}}
{{- .Values.namespace | default "hyperpod-ray" }}
{{- end }}

{{/*
Resource name with proper truncation for Kubernetes 63-character limit.
Takes a dict with:
  - .suffix: Resource name suffix (e.g., "metrics", "webhook")
  - .context: Template context (root context with .Values, .Release, etc.)
Dynamically calculates safe truncation to ensure total name length <= 63 chars.
*/}}
{{- define "hyperpod-ray-endpoint-operator.resourceName" -}}
{{- $fullname := include "hyperpod-ray-endpoint-operator.fullname" .context }}
{{- $suffix := .suffix }}
{{- $maxLen := sub 62 (len $suffix) | int }}
{{- if gt (len $fullname) $maxLen }}
{{- printf "%s-%s" (trunc $maxLen $fullname | trimSuffix "-") $suffix | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" $fullname $suffix | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
ServiceAccount name to use.
If serviceAccount.enable is false and serviceAccount.name is set, use that name.
Otherwise, use the standard resourceName helper with "controller-manager" suffix.
*/}}
{{- define "hyperpod-ray-endpoint-operator.serviceAccountName" -}}
{{- if and (hasKey .Values.serviceAccount "enable") (not .Values.serviceAccount.enable) .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name }}
{{- else }}
{{- include "hyperpod-ray-endpoint-operator.resourceName" (dict "suffix" "controller-manager" "context" .) }}
{{- end }}
{{- end }}

{{/*
Resolve the container image tag.
Defaults to the pinned operator version when .Values.image.tag is not set.
Reused by both imageUri and the manager's OPERATOR_VERSION env var.
*/}}
{{- define "hyperpod-ray-endpoint-operator.imageTag" -}}
{{- .Values.image.tag | default "1.0.188.0_1.0.19.0" -}}
{{- end }}

{{/*
Resolve the container image URI.
Priority for region:
  1. .Values.region (explicit setting)
  2. .Values.global.region (global setting from parent chart)
  3. fail — region is required

Priority for image URI:
  1. .Values.image.override (full URI override, skips all resolution)
  2. Constructed from region→account mapping + repository name + tag
*/}}
{{- define "hyperpod-ray-endpoint-operator.imageUri" -}}
{{- if .Values.image.override -}}
  {{- .Values.image.override -}}
{{- else -}}
{{- $region := "" -}}
{{- if .Values.region -}}
  {{- $region = .Values.region -}}
{{- else if and .Values.global .Values.global.region -}}
  {{- $region = .Values.global.region -}}
{{- else -}}
  {{- fail "region is required when image.override is not set. Set region or global.region." -}}
{{- end -}}

{{/* Region to ECR account ID mapping */}}
{{- $regionAccountMap := dict
  "ca-central-1" "983936648948"
  "us-east-1" "622623004016"
  "us-east-2" "084149021266"
  "us-west-1" "647106553245"
  "us-west-2" "148286033537"
  "eu-west-1" "125579686045"
  "eu-west-2" "391701072240"
  "eu-central-1" "368999588123"
  "eu-north-1" "064032700373"
  "eu-south-2" "984149068489"
  "ap-northeast-1" "325771561645"
  "ap-northeast-2" "883353268341"
  "ap-south-1" "883218392248"
  "ap-south-2" "392424878547"
  "ap-southeast-1" "850032337960"
  "ap-southeast-2" "504110891989"
  "ap-southeast-3" "772699011045"
  "ap-southeast-4" "357229908674"
  "sa-east-1" "126458881049"
-}}

{{- $accountId := index $regionAccountMap $region -}}
{{- if not $accountId -}}
  {{- fail (printf "Unsupported AWS region: %s. Set image.override explicitly for non-standard regions." $region) -}}
{{- end -}}

{{- $imageTag := include "hyperpod-ray-endpoint-operator.imageTag" . -}}
{{- printf "%s.dkr.ecr.%s.amazonaws.com/hyperpod-ray-endpoint-operator:%s" $accountId $region $imageTag -}}
{{- end -}}
{{- end }}
