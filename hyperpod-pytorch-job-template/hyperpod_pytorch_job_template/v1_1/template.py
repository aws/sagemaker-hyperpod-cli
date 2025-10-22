TEMPLATE_CONTENT = """
apiVersion: sagemaker.amazonaws.com/v1
kind: HyperPodPyTorchJob
metadata:
  name: {{ job_name }}
  namespace: {{ namespace }}
{%- if queue_name or priority %}
  labels:
{%-   if queue_name %}
    kueue.x-k8s.io/queue-name: {{ queue_name }}
{%-   endif %}
{%-   if priority %}
    kueue.x-k8s.io/priority-class: {{ priority }}
{%-   endif %}
{%- endif %}
{%- if preferred_topology or required_topology %}
  annotations:
{%-   if preferred_topology %}
    kueue.x-k8s.io/podset-preferred-topology: {{ preferred_topology }}
{%-   endif %}
{%-   if required_topology %}
    kueue.x-k8s.io/podset-required-topology: {{ required_topology }}
{%-   endif %}
{%- endif %}
spec:
{%- if tasks_per_node %}
  nprocPerNode: "{{ tasks_per_node }}"
{%- endif %}
  replicaSpecs:
    - name: pod
    {%- if node_count %}
      replicas: {{ node_count }}
    {%- endif %}
      template:
        metadata:
          name: {{ job_name }}
          namespace: {{ namespace }}
{%-       if queue_name or priority %}
          labels:
{%-         if queue_name %}
            kueue.x-k8s.io/queue-name: {{ queue_name }}
{%-         endif %}
{%-         if priority %}
            kueue.x-k8s.io/priority-class: {{ priority }}
{%-         endif %}
{%-       endif %}
{%-       if preferred_topology or required_topology %}
          annotations:
{%-         if preferred_topology %}
            kueue.x-k8s.io/podset-preferred-topology: {{ preferred_topology }}
{%-         endif %}
{%-         if required_topology %}
            kueue.x-k8s.io/podset-required-topology: {{ required_topology }}
{%-         endif %}
{%-       endif %}
        spec:
          containers:
            - name: pytorch-job-container
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
{%-               if vol.read_only is defined %}
                  readOnly: {{ vol.read_only }}
{%-               endif %}
{%-             endfor %}
{%-           endif %}
              resources:
{%-           if accelerators or vcpu or memory %}
                requests:
{%-             if accelerators %}
                  nvidia.com/gpu: {{ accelerators }}
{%-             endif %}
{%-             if vcpu %}
                  cpu: {{ vcpu }}
{%-             endif %}
{%-             if memory %}
                  memory: {{ memory }}Gi
{%-             endif %}
{%-           else %}
                requests:
                  nvidia.com/gpu: "0"
{%-           endif %}
{%-           if accelerators_limit or vcpu_limit or memory_limit %}
                limits:
{%-             if accelerators_limit %}
                  nvidia.com/gpu: {{ accelerators_limit }}
{%-             endif %}
{%-             if vcpu_limit %}
                  cpu: {{ vcpu_limit }}
{%-             endif %}
{%-             if memory_limit %}
                  memory: {{ memory_limit }}Gi
{%-             endif %}
{%-           else %}
                limits:
                  nvidia.com/gpu: "0"
{%-           endif %}
{%-         if instance_type or label_selector or deep_health_check_passed_nodes_only %}
          nodeSelector:
{%-           if instance_type %}
            node.kubernetes.io/instance-type: {{ instance_type }}
{%-           endif %}
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
{%-               if vol.read_only is defined %}
                readOnly: {{ vol.read_only }}
{%-               endif %}
{%-             endif %}
{%-           endfor %}
{%-         endif %}
{%- if max_retry %}
  runPolicy:
    cleanPodPolicy: "None"
    jobMaxRetryCount: {{ max_retry }}
{%- endif %}"""
