TEMPLATE_CONTENT = """
apiVersion: inference.sagemaker.aws.amazon.com/v1
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
    {% if accelerator_partition_type is not none %}acceleratorPartitionType: "{{ accelerator_partition_type }}"{% endif %}
    {% if accelerator_partition_validation is not none %}validations: 
    {% if accelerator_partition_validation is not none %}  acceleratorPartitionValidation: {{ accelerator_partition_validation }}{% endif %}
    {% endif %}
  tlsConfig:
    tlsCertificateOutputS3Uri: {{ tls_certificate_output_s3_uri or "" }}
"""