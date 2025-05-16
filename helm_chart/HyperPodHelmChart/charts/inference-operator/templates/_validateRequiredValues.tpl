{{- define "validateRequiredValues" -}}
{{- if not $.Values.defaultIAMRoleArnForDeployments -}}
{{- fail "defaultIAMRoleArnForDeployments must be set via the --set defaultIAMRoleArnForDeployments=<arn> flag" -}}
{{- end -}}
{{- if not $.Values.controllerImage -}}
{{- fail "controllerImage must be set via the --set controllerImage=<Repository> flag" -}}
{{- end -}}
{{- end -}}
