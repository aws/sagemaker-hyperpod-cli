{{- define "validateRequiredValues" -}}

{{- if not $.Values.executionRoleArn -}}
{{- fail "executionRoleArn must be set via the --set executionRoleArn=<arn> flag" -}}
{{- end}}

{{- if not .Values.region }}
{{- fail "A valid region is required!" }}
{{- end }}

{{- $region := .Values.region -}}

{{- if not (hasKey .Values.image.repositoryDomainMap $region) -}}
{{- fail "Unsupported AWS Region" -}}
{{- end -}}

{{- $_ := set .Values.image "repository" (index .Values.image.repositoryDomainMap $region) -}}