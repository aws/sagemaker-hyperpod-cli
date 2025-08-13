# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
KUBERNETES_PYTORCH_JOB_TEMPLATE = """### Please keep template file unchanged ###
apiVersion: sagemaker.amazonaws.com/v1
kind: HyperPodPyTorchJob
metadata:
  name: "{{ job_name }}"
  namespace: "{{ namespace }}"
{% if queue_name or priority %}  labels:
{% if queue_name %}    kueue.x-k8s.io/queue-name: "{{ queue_name }}"
{% endif %}{% if priority %}    kueue.x-k8s.io/priority-class: "{{ priority }}"
{% endif %}{% endif %}spec:
{% if tasks_per_node %}  nprocPerNode: "{{ tasks_per_node }}"
{% endif %}  replicaSpecs:
    - name: "pod"
{% if node_count %}      replicas: {{ node_count }}
{% endif %}      template:
        metadata:
          name: "{{ job_name }}"
{% if namespace %}          namespace: "{{ namespace }}"
{% endif %}{% if queue_name or priority %}          labels:
{% if queue_name %}            kueue.x-k8s.io/queue-name: "{{ queue_name }}"
{% endif %}{% if priority %}            kueue.x-k8s.io/priority-class: "{{ priority }}"
{% endif %}{% endif %}        spec:
          containers:
            - name: "container-name"
              image: "{{ image }}"
{% if pull_policy %}              imagePullPolicy: "{{ pull_policy }}"
{% endif %}{% if command %}              command: {{ command | tojson }}
{% endif %}{% if args %}              args: {{ args | tojson }}
{% endif %}{% if environment %}              env:
{% for key, value in environment.items() %}                - name: "{{ key }}"
                  value: "{{ value }}"
{% endfor %}{% endif %}{% if volume %}              volumeMounts:
{% for vol in volume %}                - name: "{{ vol.name }}"
                  mountPath: "{{ vol.mount_path }}"
{% if vol.read_only is not none and vol.read_only != "" %}                  readOnly: {{ vol.read_only | lower }}
{% endif %}{% endfor %}{% endif %}              resources:
                requests:
                  nvidia.com/gpu: "0"
                limits:
                  nvidia.com/gpu: "0"
{% if instance_type or label_selector or deep_health_check_passed_nodes_only %}          nodeSelector:
{% if instance_type %}            node.kubernetes.io/instance-type: "{{ instance_type }}"
{% endif %}{% if label_selector %}{% for key, value in label_selector.items() %}            {{ key }}: "{{ value }}"
{% endfor %}{% endif %}{% if deep_health_check_passed_nodes_only %}            deep-health-check-passed: "true"
{% endif %}{% endif %}{% if service_account_name %}          serviceAccountName: "{{ service_account_name }}"
{% endif %}{% if scheduler_type %}          schedulerName: "{{ scheduler_type }}"
{% endif %}{% if volume %}          volumes:
{% for vol in volume %}            - name: "{{ vol.name }}"
{% if vol.type == "hostPath" %}              hostPath:
                path: "{{ vol.path }}"
{% elif vol.type == "pvc" %}              persistentVolumeClaim:
                claimName: "{{ vol.claim_name }}"
{% endif %}{% endfor %}{% endif %}{% if max_retry %}  runPolicy:
    cleanPodPolicy: "None"
    jobMaxRetryCount: {{ max_retry }}
{% endif %}"""
