TEMPLATE_CONTENT = """
apiVersion: hyperpod.sagemaker.aws/v1
kind: InferenceEndpointConfig
metadata:
  name: {{ metadata_name or endpoint_name }}
  namespace: {{ namespace }}
spec:
  endpointName: {{ endpoint_name }}
  instanceType: {{ instance_type }}
  modelName: {{ model_name }}
  modelVersion: {{ model_version or "" }}
  
  metrics:
    enabled: {{ metrics_enabled or False }}
  
  modelSourceConfig:
    modelSourceType: {{ model_source_type }}
    modelLocation: {{ model_location or "" }}
    prefetchEnabled: {{ prefetch_enabled or False }}
{%- if model_source_type == "s3" %}
    s3Storage:
      bucketName: {{ s3_bucket_name }}
      region: {{ s3_region }}
{%- elif model_source_type == "fsx" %}
    fsxStorage:
      dnsName: {{ fsx_dns_name }}
      fileSystemId: {{ fsx_file_system_id }}
      mountName: {{ fsx_mount_name or "" }}
{%- endif %}
  
  tlsConfig:
    tlsCertificateOutputS3Uri: {{ tls_certificate_output_s3_uri or "" }}

  worker:
    environmentVariables:
  {%- if env %}
  {%- for key, val in env.items() %}
      - name: {{ key }}
        value: "{{ val }}"
  {%- endfor %}
  {%- else %}
      []
  {%- endif %}
    image: {{ image_uri }}
    modelInvocationPort:
      containerPort: {{ container_port }}
    modelVolumeMount:
      name: {{ model_volume_mount_name }}
      mountPath: {{ model_volume_mount_path }}
    resources:
{%- if resources_limits %}
      limits:
{%-   for key, val in resources_limits.items() %}
        {{ key }}: {{ val }}
{%-   endfor %}
{%- else %}
      {}
{%- endif %}
{%- if resources_requests %}
      requests:
{%-   for key, val in resources_requests.items() %}
        {{ key }}: {{ val }}
{%-   endfor %}
{%- endif %}

  autoScalingSpec:
    cloudWatchTrigger:
{%- if dimensions %}
      dimensions:
{%-   for dim_key, dim_val in dimensions.items() %}
        - name: {{ dim_key }}
          value: {{ dim_val }}
{%-   endfor %}
{%- endif %}
      metricCollectionPeriod: {{ metric_collection_period }}
      metricCollectionStartTime: {{ metric_collection_start_time }}
      metricName: {{ metric_name or "" }}
      metricStat: {{ metric_stat }}
      metricType: {{ metric_type }}
      minValue: {{ min_value }}
      name: {{ cloud_watch_trigger_name or "" }}
      namespace: {{ cloud_watch_trigger_namespace or "" }}
      targetValue: {{ target_value or "" }}
      useCachedMetrics: {{ use_cached_metrics or False }}
      
  invocationEndpoint: "{{ invocation_endpoint }}"

{% if intelligent_routing_enabled is not none %}  intelligentRoutingSpec:
    enabled: {{ intelligent_routing_enabled }}
{% if routing_strategy is not none %}    routingStrategy: "{{ routing_strategy }}"{% endif %}{% endif %}
{% if enable_l1_cache is not none or enable_l2_cache is not none or cache_config_file is not none %}  kvCacheSpec:
{% if enable_l1_cache is not none %}    enableL1Cache: {{ enable_l1_cache }}{% endif %}
{% if enable_l2_cache is not none %}    enableL2Cache: {{ enable_l2_cache }}{% endif %}
{% if l2_cache_backend is not none or l2_cache_local_url is not none %}    l2CacheSpec:
{% if l2_cache_backend is not none %}      l2CacheBackend: "{{ l2_cache_backend }}"{% endif %}
{% if l2_cache_local_url is not none %}      l2CacheLocalUrl: "{{ l2_cache_local_url }}"{% endif %}
{% endif %}
{% if cache_config_file is not none %}    cacheConfigFile: "{{ cache_config_file }}"{% endif %}
{% endif %}
"""