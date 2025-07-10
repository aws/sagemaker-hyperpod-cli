{{- define "validateRequiredValues" -}}

{{- if and $.Values.s3.enabled (not $.Values.s3.serviceAccountRoleArn) -}}
{{- fail "A valid role for the Mountpoint for s3 CSI driver must be set via the --set s3.serviceAccountRoleArn=<arn> flag." -}}
{{- end}}

{{- if not $.Values.executionRoleArn -}}
{{- fail "executionRoleArn must be set via the --set executionRoleArn=<arn> flag" -}}
{{- end}}

{{- if not $.Values.tlsCertificateS3Bucket}}
{{- fail "tlsCertificateS3Bucket must be set via the --set tlsCertificateS3Bucket=<s3 Bucket> flag" -}}
{{- else -}}
{{- if not (hasPrefix "s3://" $.Values.tlsCertificateS3Bucket) -}}
{{- $_ := set $.Values "tlsCertificateS3Bucket" (printf "s3://%s" $.Values.tlsCertificateS3Bucket) -}}
{{- end -}}
{{- end -}}

{{- if not .Values.region }}
{{- fail "A valid region is required!" }}
{{- end -}}

{{- if not .Values.eksClusterName }}
{{- fail "An EKS cluster name is required!" }}
{{- end -}}

{{- if and .Values.keda.enabled (not .Values.keda.podIdentity.aws.irsa.roleArn) }}
{{- fail "A valid role for the KEDA operator must be set via the --set keda.podIdentity.aws.irsa.roleArn=<arn> flag." }}
{{- end -}}

{{- if and .Values.alb.enabled (not .Values.alb.vpcId) }}
{{- fail "alb.vpcId must be set when alb.enabled=true" }}
{{- end -}}

{{- if and .Values.alb.enabled (and .Values.alb.serviceAccount.create (not .Values.alb.serviceAccount.roleArn)) }}
{{- fail "A valid role for the AWS Load Balancer Controller must be set via the --set alb.serviceAccount.roleArn=<arn> flag." }}
{{- end -}}

{{- $region := .Values.region -}}

{{- if not (hasKey .Values.image.repositoryDomainMap $region) -}}
{{- fail "Unsupported AWS Region" -}}
{{- end -}}

{{- if or (not (hasKey .Values.image "repository")) (not .Values.image.repository) -}}
{{- $_ := set .Values.image "repository" (index .Values.image.repositoryDomainMap $region) -}}
{{- end -}}

{{- end -}}
