TEMPLATE_CONTENT = """
apiVersion: sagemaker.amazonaws.com/v1
kind: HyperPodPyTorchJob
metadata:
  name: {{ job_name }}
  namespace: {{ namespace }}
{%- if queue_name or priority %}
  labels:
    kueue.x-k8s.io/queue-name: {{ queue_name or "" }}
    kueue.x-k8s.io/priority-class: {{ priority or "" }}
{%- endif %}
spec:
{%- if tasks_per_node %}
  nprocPerNode: "{{ tasks_per_node }}"
{%- endif %}
  replicaSpecs:
    - name: pod
      replicas: {{ node_count or 1 }}
      template:
        metadata:
          name: {{ job_name }}
          namespace: {{ namespace }}
{%-       if queue_name or priority %}
          labels:
            kueue.x-k8s.io/queue-name: {{ queue_name or "" }}
            kueue.x-k8s.io/priority-class: {{ priority or "" }}
{%-       endif %}
        spec:
          containers:
            - name: container-name
              image: {{ image }}
{%-           if pull_policy %}
              imagePullPolicy: {{ pull_policy }}
{%-           endif %}
{%-           if command %}
              command: {{ command | tojson }}
{%-           endif %}
{%-           if args %}
              args: {{ args | tojson }}
{%-           endif %}
{%-           if environment %}
              env:
{%-             for key, value in environment.items() %}
                - name: {{ key }}
                  value: "{{ value }}"
{%-             endfor %}
{%-           endif %}
{%-           if volume %}
              volumeMounts:
{%-             for vol in volume %}
                - name: {{ vol.name }}
                  mountPath: {{ vol.mount_path }}
                  readOnly: {{ vol.read_only | lower if vol.read_only else false }}
{%-             endfor %}
{%-           endif %}
              resources:
                requests:
                  nvidia.com/gpu: "0"
                limits:
                  nvidia.com/gpu: "0"
{%-         if instance_type or label_selector or deep_health_check_passed_nodes_only %}
          nodeSelector:
            node.kubernetes.io/instance-type: {{ instance_type or "" }}
{%-           if label_selector %}
{%-             for key, value in label_selector.items() %}
            {{ key }}: {{ value }}
{%-             endfor %}
{%-           endif %}
{%-           if deep_health_check_passed_nodes_only %}
            deep-health-check-passed: "true"
{%-           endif %}
{%-         endif %}
{%-         if service_account_name %}
          serviceAccountName: {{ service_account_name }}
{%-         endif %}
{%-         if scheduler_type %}
          schedulerName: {{ scheduler_type }}
{%-         endif %}
{%-         if volume %}
          volumes:
{%-           for vol in volume %}
            - name: {{ vol.name }}
{%-             if vol.type == "hostPath" %}
              hostPath:
                path: {{ vol.path }}
{%-             elif vol.type == "pvc" %}
              persistentVolumeClaim:
                claimName: {{ vol.claim_name }}
{%-             endif %}
{%-           endfor %}
{%-         endif %}
{%- if max_retry %}
  runPolicy:
    cleanPodPolicy: "None"
    jobMaxRetryCount: {{ max_retry }}
{%- endif %}"""
