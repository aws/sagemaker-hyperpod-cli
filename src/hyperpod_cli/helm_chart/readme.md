# Building, Packaging, and Testing Helm Charts

This guide walks you through the process of creating, packaging, and testing HyperPod Helm chart.

## 1. Set Up Your Helm Environment

Before starting, make sure Helm is installed on your machine. You can install Helm using the following commands:

```bash
chmod 700 get_helm.sh
./get_helm.sh
```
## 2. Package structure

| Chart Name                   | Usage                                                                                                                                                                                   | Enable by default | Notes |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|-------|
| Cluster role and binding     | Defines cluster-wide roles and bindings for Kubernetes resources, allowing cluster administrators to assign and manage permissions across the entire cluster.                           | No                |       |
| Deep health check            | Implements advanced health checks for Kubernetes services and pods to ensure deep monitoring of resource status and functionality beyond basic liveness and readiness probes.           | Yes               |       |
| Health monitoring agent      | Deploys an agent to continuously monitor the health of Kubernetes applications, providing detailed insights and alerting for potential issues.                                          | Yes               |       |
| Job auto restart             | Configures automatic restart policies for Kubernetes jobs, ensuring failed or terminated jobs are restarted based on predefined conditions for high availability.                       | Yes               |       |
| Kueue                        | Manages Kubernetes workloads using the Kueue scheduling framework, enabling resource queuing and prioritization for jobs across multiple clusters or queues.                            | No                |       |
| MLflow                       | Installs the MLflow platform for managing machine learning experiments, tracking models, and storing model artifacts in a scalable manner within the Kubernetes cluster.                | No                |       |
| MPI Operators                | Orchestrates MPI (Message Passing Interface) jobs on Kubernetes, providing an efficient way to manage distributed machine learning or high-performance computing (HPC) workloads.       | Yes               |       |
| namespaced-role-and-bindings | Creates roles and role bindings within a specific namespace to manage fine-grained access control for Kubernetes resources in a limited scope.                                          | No                |       |
| neuron-device-plugin         | Deploys the AWS Neuron device plugin for Kubernetes, enabling support for AWS Inferentia chips to accelerate machine learning model inference workloads.                                | Yes               |       |
| storage                      | Manages persistent storage resources for Kubernetes applications, ensuring that data is retained and accessible across pod restarts and cluster upgrades.                               | No                |       |
| training-operators           | Installs operators for managing various machine learning training jobs, such as TensorFlow, PyTorch, and MXNet, providing native Kubernetes support for distributed training workloads. | Yes               |       |

## 3. Test the Chart Locally

To ensure that your chart is properly defined, use the helm lint command:

```
helm lint src/hyperpod_cli/helm_chart/HyperPodHelmChart

```

## 4. Deployment

Prerequisites:
To use the resiliency feature of Compass, run the following command to install the necessary permissions before executing the create-cluster command for the Hyperpod Cluster.

Additionally, note that Kueue, MLflow, and other optional components are disabled by default. If you wish to enable them, you'll need to manually update the values.yaml file in the main chart by setting the corresponding feature flags to true.

Notes:

1. If you plan to use Kueue, please run ./install_dependencies.sh. This script installs certain CRDs directly via commands, rather than using Helm charts.

2. Below dependencies is the default release name. helm install <dependencies> is the example.

### Step Zero:

* update helm chart dependencies. 

Command: 

```
helm dependencies update src/hyperpod_cli/helm_chart/HyperPodHelmChart
```
* It ensures that all the sub-charts required by the main chart are fetched and properly set up before deploying the main chart. It doesn’t actually deploy the chart itself but prepares it by ensuring all dependencies are resolved.

### Step One:

* Install the Helm chart that includes all the dependencies. 
    * command: 
```
helm install dependencies src/hyperpod_cli/helm_chart/HyperPodHelmChart --dry-run
```
helm will output template which will apply to k8s cluster.

If the resource already exists, avoid running the install command again, as it may cause conflicts. Instead, use the following command to upgrade the existing release while preserving the current configuration. This ensures that your current settings are maintained without overwriting them:

```
helm upgrade <release_name> HyperPodHelmChart --reuse-values --namespace kube-system
```

To find your release name, run:

```
helm list --namespace kube-system
```

This is necessary to prevent resource duplication and configuration conflicts, ensuring a smooth upgrade process without disrupting existing resources.

### Step Two:

Deploying a Helm Chart to Your Kubernetes Cluster
To install and deploy the Helm chart to your Kubernetes cluster, use the following command:

```
helm install dependencies src/hyperpod_cli/helm_chart/HyperPodHelmChart --namespace kube-system
```

This command deploys the Helm chart to your cluster with custom configurations applied, as specified in the values.yaml file. Please note that only certain versions of dependencies will be deployed based on the configuration specified in the values.yaml.

3. An important thing to note here is the Health Monitoring Agent container image URI. If you intend to use the iamge from another region, please see below list to find relevant region's URI.
```
IAD 767398015722.dkr.ecr.us-east-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
PDX 905418368575.dkr.ecr.us-west-2.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
CMH 851725546812.dkr.ecr.us-east-2.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
SFO 011528288828.dkr.ecr.us-west-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
FRA 211125453373.dkr.ecr.eu-central-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
ARN 654654141839.dkr.ecr.eu-north-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
DUB 533267293120.dkr.ecr.eu-west-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
LHR 011528288831.dkr.ecr.eu-west-2.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
NRT 533267052152.dkr.ecr.ap-northeast-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
BOM 011528288864.dkr.ecr.ap-south-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
SIN 905418428165.dkr.ecr.ap-southeast-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
SYD 851725636348.dkr.ecr.ap-southeast-2.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
GRU 025066253954.dkr.ecr.sa-east-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.277.0_1.0.27.0
```

### FAQ

* ServiceAccount "neuron-device-plugin" in namespace "kube-system" exists and cannot be imported into the current release

```
This means dependencies already installed. You can change the name of the dependencies if you want another dependencies
```
To see dependencies already existed or not

```
kubectl get serviceaccount neuron-device-plugin -n kube-system

NAME                   SECRETS   AGE
neuron-device-plugin   0         9m48s
```

* add new dependencies subchart

1. Make sure you run 

```
helm lint HyperPodHelmChart
```

2. Add chart metadata in the main Chart.yaml

```
  - name: storage
    version: "0.1.0"
    repository: "file://charts/storage"
    condition: storage.enabled  
```

version here should points to subchart major version.

*  invalid ownership metadata; label validation error: missing key "app.kubernetes.io/managed-by": must be set to "Helm"; annotation validation error: missing key "meta.helm.sh/release-name": must be set to "new-release"; annotation validation error: missing key "meta.helm.sh/release-namespace": must be set to "kubesystem"

this means that some of the resource is manually installed without helm control. You need to manual label the resource 

```
kubectl label pod training-operator-64c768746c-d6zjz -n kubeflow app.kubernetes.io/managed-by=Helm
kubectl annotate pod training-operator-64c768746c-d6zjz -n kubeflow meta.helm.sh/release-name=dependencies
kubectl annotate pod training-operator-64c768746c-d6zjz -n kubeflow meta.helm.sh/release-namespace=kubeflow

pod/training-operator-64c768746c-d6zjz labeled
pod/training-operator-64c768746c-d6zjz annotated
pod/training-operator-64c768746c-d6zjz annotated
```

* if the resource still exists

run to delete the namespace and rerun the command. Notes: some resource is cluster level, you might manual delete it.

```
kubectl delete namespace kubeflow
```

* Check the resource applies to K8s cluster

```
helm template dependencies HyperPodHelmChart --namespace kubeflow

```
it will return the resource yaml generated by helm chart