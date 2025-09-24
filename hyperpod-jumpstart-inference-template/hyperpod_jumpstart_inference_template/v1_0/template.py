TEMPLATE_CONTENT = """
apiVersion: inference.sagemaker.aws.amazon.com/v1alpha1
kind: JumpStartModel
metadata:
  name:                {{ metadata_name or endpoint_name }}
  namespace:           {{ namespace or "default" }}
spec:
  model:
    acceptEula:               {{ accept_eula or false }}
    modelHubName:             "SageMakerPublicHub"
    modelId:                  {{ model_id }}
    modelVersion:             {{ model_version or "" }}
  sageMakerEndpoint:
    name:                     {{ endpoint_name or "" }}
  server:
    instanceType:             {{ instance_type }}
  tlsConfig:
    tlsCertificateOutputS3Uri: {{ tls_certificate_output_s3_uri or "" }}
"""