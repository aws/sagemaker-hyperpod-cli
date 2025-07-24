KUBERNETES_CUSTOM_ENDPOINT_TEMPLATE = """### Please keep template file unchanged ###
apiVersion: hyperpod.sagemaker.aws/v1
kind: HPEndpoint
metadata:
  name: "{{ endpoint_name }}"
  namespace: "{{ namespace }}"
spec:
  instanceType: "{{ instance_type }}"
  modelName:    "{{ model_name }}"
{% if model_version is not none %}  modelVersion: "{{ model_version }}"
{% endif %}
  env:
{% if env %}    
{% for key, val in env.items() %}    - name:  "{{ key }}"
      value: "{{ val }}"
{% endfor %}{% else %}    []
{% endif %}
  metrics:
    enabled: {{ metrics_enabled }}
  modelSourceConfig:
    modelSourceType: "{{ model_source_type }}"
{% if model_location is not none %}    modelLocation:   "{{ model_location }}"
{% endif %}    prefetchEnabled: {{ prefetch_enabled }}
{% if model_source_type == "s3" %}    s3Storage:
      bucketName: "{{ s3_bucket_name }}"
      region:     "{{ s3_region }}"
{% elif model_source_type == "fsx" %}    fsxStorage:
      dnsName:       "{{ fsx_dns_name }}"
      fileSystemId:  "{{ fsx_file_system_id }}"
{% if fsx_mount_name is not none %}      mountName:     "{{ fsx_mount_name }}"
{% endif %}{% endif %}
  tlsConfig:
{% if tls_certificate_output_s3_uri is not none %}    certificateOutputS3Uri: "{{ tls_certificate_output_s3_uri }}"
{% else %}    {}
{% endif %}
  worker:
    image:         "{{ image_uri }}"
    containerPort: {{ container_port }}
    volumeMount:
      name:       "{{ model_volume_mount_name }}"
      mountPath:  "{{ model_volume_mount_path }}"
    resources:
{% if resources_limits %}      limits:
{% for key, val in resources_limits.items() %}        {{ key }}: "{{ val }}"
{% endfor %}{% else %}      {}
{% endif %}{% if resources_requests %}
      requests:
{% for key, val in resources_requests.items() %}        {{ key }}: "{{ val }}"
{% endfor %}{% endif %}
  autoScalingSpec:
    cloudWatchTrigger:
{% if dimensions %}      dimensions:
{% for dim_key, dim_val in dimensions.items() %}        - name:  "{{ dim_key }}"
          value: "{{ dim_val }}"
{% endfor %}{% else %}      []
{% endif %}      metricCollectionPeriod: {{ metric_collection_period }}
      metricCollectionStartTime: {{ metric_collection_start_time }}
      metricName: "{{ metric_name }}"
      metricStat: "{{ metric_stat }}"
      type:       "{{ metric_type }}"
      minValue:   {{ min_value }}
      name:       "{{ cloud_watch_trigger_name }}"
      namespace:  "{{ cloud_watch_trigger_namespace }}"
      targetValue: {{ target_value }}
      useCachedMetrics: {{ use_cached_metrics }}
  invocationEndpoint: "{{ invocation_endpoint }}"

"""