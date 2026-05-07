TEMPLATE_CONTENT = """
apiVersion: inference.sagemaker.aws.amazon.com/v1
kind: InferenceEndpointConfig
metadata:
  name: {{ metadata_name or endpoint_name }}
  namespace: {{ namespace }}
spec:
  endpointName: {{ endpoint_name }}
{%- if instance_type %}
  instanceType: {{ instance_type }}
{%- endif %}
{%- if instance_types %}
  instanceTypes:
{%-   for it in instance_types.split(",") %}
    - {{ it.strip() }}
{%-   endfor %}
{%- endif %}
  modelName: {{ model_name }}
  modelVersion: {{ model_version or "" }}
{%- if replicas is not none %}
  replicas: {{ replicas }}
{%- endif %}
{%- if initial_replica_count is not none and initial_replica_count != "" %}
  InitialReplicaCount: {{ initial_replica_count }}
{%- endif %}
{%- if max_deploy_time_in_seconds is not none %}
  maxDeployTimeInSeconds: {{ max_deploy_time_in_seconds }}
{%- endif %}
{%- if tags %}
  tags:
{%-   for tag_name, tag_value in tags.items() %}
    - name: {{ tag_name }}
      value: "{{ tag_value }}"
{%-   endfor %}
{%- endif %}


  metrics:
    enabled: {{ metrics_enabled or False }}
{%-   if metrics_scrape_interval_seconds %}
    metricsScrapeIntervalSeconds: {{ metrics_scrape_interval_seconds }}
{%-   endif %}
{%-   if model_metrics_path or model_metrics_port %}
    modelMetrics:
{%-     if model_metrics_path %}
      path: "{{ model_metrics_path }}"
{%-     endif %}
{%-     if model_metrics_port %}
      port: {{ model_metrics_port }}
{%-     endif %}
{%-   endif %}

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
{%- elif model_source_type == "huggingface" %}
    huggingFaceModel:
      modelId: {{ huggingface_model_id }}
{%- if huggingface_commit_sha %}
      commitSHA: {{ huggingface_commit_sha }}
{%- endif %}
{%- if huggingface_token_secret_name and huggingface_token_secret_key %}
      tokenSecretRef:
        name: {{ huggingface_token_secret_name }}
        key: {{ huggingface_token_secret_key }}
{%- endif %}
{%- endif %}


  tlsConfig:
    tlsCertificateOutputS3Uri: {{ tls_certificate_output_s3_uri or "" }}
{%- if custom_certificate_acm_arn and custom_certificate_domain_name %}
    customCertificateConfig:
      acmArn: "{{ custom_certificate_acm_arn }}"
      domainName: "{{ custom_certificate_domain_name }}"
{%- endif %}

{%- if node_affinity %}
  nodeAffinity: {{ node_affinity | tojson }}
{%- endif %}

{%- if kubernetes %}
  kubernetes: {{ kubernetes | tojson }}
{%- endif %}

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
{%- if worker_args %}
    args:
{%-   for arg in worker_args.split(",") %}
      - "{{ arg.strip() }}"
{%-   endfor %}
{%- endif %}
{%- if worker_command %}
    command:
{%-   for cmd in worker_command.split(",") %}
      - "{{ cmd.strip() }}"
{%-   endfor %}
{%- endif %}
{%- if working_dir %}
    workingDir: "{{ working_dir }}"
{%- endif %}
{%- if probes %}
    probes: {{ probes | tojson }}
{%- endif %}
{%- if max_concurrent_requests or max_queue_size or overflow_status_code %}
    requestLimits:
{%-   if max_concurrent_requests %}
      maxConcurrentRequests: {{ max_concurrent_requests }}
{%-   endif %}
{%-   if max_queue_size %}
      maxQueueSize: {{ max_queue_size }}
{%-   endif %}
{%-   if overflow_status_code %}
      overflowStatusCode: {{ overflow_status_code }}
{%-   endif %}
{%- endif %}

{%- if auto_scaling_spec %}
  autoScalingSpec: {{ auto_scaling_spec | tojson }}
{%- else %}
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
{%- endif %}

  invocationEndpoint: "{{ invocation_endpoint }}"

{%- if intelligent_routing_enabled is defined and intelligent_routing_enabled is not none and intelligent_routing_enabled != "" %}
  intelligentRoutingSpec:
    enabled: {{ intelligent_routing_enabled }}
{%-   if routing_strategy %}
    routingStrategy: "{{ routing_strategy }}"
{%-   endif %}
{%- endif %}

{%- if (enable_l1_cache is defined and enable_l1_cache is not none and enable_l1_cache != "") or (enable_l2_cache is defined and enable_l2_cache is not none and enable_l2_cache != "") or cache_config_file %}
  kvCacheSpec:
{%-   if enable_l1_cache is defined and enable_l1_cache is not none and enable_l1_cache != "" %}
    enableL1Cache: {{ enable_l1_cache }}
{%-   endif %}
{%-   if enable_l2_cache is defined and enable_l2_cache is not none and enable_l2_cache != "" %}
    enableL2Cache: {{ enable_l2_cache }}
{%-   endif %}
{%-   if l2_cache_backend or l2_cache_local_url %}
    l2CacheSpec:
{%-     if l2_cache_backend %}
      l2CacheBackend: "{{ l2_cache_backend }}"
{%-     endif %}
{%-     if l2_cache_local_url %}
      l2CacheLocalUrl: "{{ l2_cache_local_url }}"
{%-     endif %}
{%-   endif %}
{%-   if cache_config_file %}
    cacheConfigFile: "{{ cache_config_file }}"
{%-   endif %}
{%- endif %}

{%- if load_balancer_health_check_path or load_balancer_routing_algorithm %}
  loadBalancer:
{%-   if load_balancer_health_check_path %}
    healthCheckPath: "{{ load_balancer_health_check_path }}"
{%-   endif %}
{%-   if load_balancer_routing_algorithm %}
    routingAlgorithm: "{{ load_balancer_routing_algorithm }}"
{%-   endif %}
{%- endif %}

{%- if data_capture %}
  dataCapture: {{ data_capture | tojson }}
{%- endif %}

{%- if dns_hosted_zone_id %}
  dnsConfig:
    hostedZoneId: "{{ dns_hosted_zone_id }}"
{%- endif %}
"""