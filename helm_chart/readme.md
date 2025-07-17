# Building, Packaging, and Testing Helm Charts

This guide walks cluster Admin users through the process of creating, packaging, and testing HyperPod Helm chart. More information in the official AWS documentation [here](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-install-packages-using-helm-chart.html).

## 1. Set Up Your Helm Environment

Before starting, make sure Helm is installed on your machine. You can install Helm using the following commands:

```bash
chmod 700 get_helm.sh
./get_helm.sh
```

## 2. Package structure

Here are the list of dependent charts and plugins that can be installed as part of the HyperPod Helm chart. Features required for HyperPod Resiliency as mentioned below are recommended to enable cluster resiliency. Features required for HyperPod Task Governance as mentioned below are optional but help set access control on your cluster.

More information about HyperPod task governance [here](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-governance.html).

More information about orchestration features for cluster admins [here](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks.html).

| Chart Name                   | Usage                                                                                                                                                                                   | Required For | Enable by default |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|-------------------|
| [Cluster role and binding](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-setup-rbac.html)     | Defines cluster-wide roles and bindings for Kubernetes resources, allowing cluster administrators to assign and manage permissions across the entire cluster.                           | HyperPod Task Governance             | No                |
| [Namespaced Role and Bindings](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-setup-rbac.html) | Creates roles and role bindings within a specific namespace to manage fine-grained access control for Kubernetes resources in a limited scope.                                          | HyperPod Task Governance             | No                |
| [Team role and binding](#5-create-team-role)        | Defines cluster and namespaced roles and bindings, allowing cluster administrators to create scientist roles with sufficient permissions to submit jobs to the accessible teams.        | HyperPod Task Governance             | No                |
| [Deep health check](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-deep-health-checks.html)            | Implements advanced health checks for Kubernetes services and pods to ensure deep monitoring of resource status and functionality beyond basic liveness and readiness probes.           | HyperPod Resiliency             | Yes               |
| [Health monitoring agent](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-resiliency-health-monitoring-agent.html)      | Deploys an agent to continuously monitor the health of Kubernetes applications, providing detailed insights and alerting for potential issues.                                          | HyperPod Resiliency             | Yes               |
| Job auto restart             | Configures automatic restart policies for Kubernetes jobs, ensuring failed or terminated jobs are restarted based on predefined conditions for high availability.                       | HyperPod Resiliency             | Yes               |
| MLflow                       | Installs the MLflow platform for managing machine learning experiments, tracking models, and storing model artifacts in a scalable manner within the Kubernetes cluster.                |              | No                |
| [MPI Operator](https://www.kubeflow.org/docs/components/trainer/legacy-v1/user-guides/mpi/)                 | Orchestrates MPI (Message Passing Interface) jobs on Kubernetes, providing an efficient way to manage distributed machine learning or high-performance computing (HPC) workloads.       | HyperPod Resiliency with MPIJobs            | Yes               |
| Storage                      | Manages persistent storage resources for Kubernetes applications, ensuring that data is retained and accessible across pod restarts and cluster upgrades.                               |              | No                |
| [Kubeflow Training Operator](https://www.kubeflow.org/docs/components/trainer/legacy-v1/overview/)            | Installs operators for managing various machine learning training jobs, such as TensorFlow, PyTorch, and MXNet, providing native Kubernetes support for distributed training workloads. |              | Yes               |
| HyperPod patching            | Deploys the RBAC and controller resources needed for orchestrating rolling updates and patching workflows in SageMaker HyperPod clusters. Includes pod eviction and node monitoring.    | HyperPod Resiliency             | Yes               |
| hyperpod-inference-operator  | Installs the HyperPod Inference Operator and its dependencies to the cluster, allowing cluster deployment and inferencing of JumpStart, s3-hosted, and FSx-hosted models                | No                | 

> **_Note_** The `mpijob` scheme is disabled in the Training Operator helm chart to avoid conflicting with the MPI Operator. 

If you would like to disable a helm chart that is enabled by default, such as the Training Operator, pass in `--set trainingOperators.enabled=false` when installing or upgrading the main chart or set the following in the values.yaml file.
```
trainingOperators:
  enabled: false
```

If you would like to enable a helm chart that is disabled by default, such as the Storage chart, pass in `--set storage.enabled=true` when installing or upgrading the main chart of set the following in the values.yaml file.
```
storage:
  enabled: true
```

---

The following plugins are only required for HyperPod Resiliency if you are using the following supported devices, such as GPU/Neuron instances, unless you install these plugins on your own. 

| Plugin Name                   | Usage                                                                                                                                                                                   | Required For | Enable by default |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|-------------------|
| neuron-device-plugin         | Deploys the AWS Neuron device plugin for Kubernetes, enabling support for AWS Inferentia chips to accelerate machine learning model inference workloads.                                | HyperPod Resiliency with AWS Neuron             | Yes               |
| aws-efa-k8s-device-plugin    | This plugin enables AWS Elastic Fabric Adapter (EFA) metrics on the EKS clusters.                                                                                                        | HyperPod Resiliency with AWS EFA             | Yes               |
| nvidia-device-plugin         | This plugin is a Daemon set that exposes number of GPUs on each node, keeps track health metrics, and enables running GPU enabled containers in EKS clusters.                                 | HyperPod Resiliency with Nvidia GPUs             | Yes               |

If you install these plugins on your own, make sure that the following configurations are set to work with your HyperPod EKS clusters:

Tolerations (across all plugins):
```
- key: sagemaker.amazonaws.com/node-health-status
  operator: Equal
  value: Unschedulable
  effect: NoSchedule
```

Node Affinities (for neuron and nvidia plugins):
```
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: "node.kubernetes.io/instance-type"
              operator: In
              values:
                - <your HyperPod instance types>
```

Supported Instance Labels (for efa plugin):
Set this in your values.yaml
```
supportedInstanceLabels:
    values:
     - <your HyperPod instance types>
```

## 3. Test the Chart Locally

To ensure that your chart is properly defined, use the helm lint command:

```
helm lint helm_chart/HyperPodHelmChart

```

## 4. Deployment

Notes:
1. To use the resiliency feature in SageMaker HyperPod cluster with Amazon EKS, you need to first install this HelmChart to EKS cluster before creating HyperPod cluster.

2. MLflow, and other optional components are disabled by default. If you wish to enable them, you'll need to manually update the values.yaml file in the main chart by setting the corresponding feature flags to true.

3. Below <dependencies> is the default release name. helm install <dependencies> is the example.

### Step Zero:
* Update kubeconfig file to connect to your EKS cluster.
  ```
  aws eks update-kubeconfig --name <eks_cluster_name>
  ```
* Verify you are connected to your EKS cluster.
  ```
  kubectl config current-context
  ```

### Step One:

* Update helm chart dependencies. It ensures that all the sub-charts required by the main chart are fetched and properly set up before deploying the main chart. It doesn’t actually deploy the chart itself but prepares it by ensuring all dependencies are resolved.

  ```
  helm dependencies update helm_chart/HyperPodHelmChart
  ```

### Step Two:

* Simulate the installation process. Below command shows you what would be installed and the configuration that would be applied. 
  ```
  helm install dependencies helm_chart/HyperPodHelmChart --namespace kube-system --dry-run
  ```

* If the resource already exists, avoid running the install command again, as it may cause conflicts. Instead, use the following command to upgrade the existing release while preserving the current configuration. This ensures that your current settings are maintained without overwriting them.
  - To find all your releases deployed in one namespace (eg. kube-system), run:
    ```
    helm list --namespace kube-system
    ```
  - To upgrade the existing release deployed in one namespace (eg. kube-system), run:
    ```
    helm upgrade <release_name> helm_chart/HyperPodHelmChart --reuse-values --namespace kube-system
    ```

### Step Three:

* Deploy a Helm Chart to Your Kubernetes Cluster. This command deploys the Helm chart to your cluster with custom configurations applied, as specified in the values.yaml file. Please note that only certain versions of dependencies will be deployed based on the configuration specified in the values.yaml.
  ```
  helm install dependencies helm_chart/HyperPodHelmChart --namespace kube-system
  ```


## 5. Create Team Role

* To create role for hyperpod cluster users, please set the value for `computeQuotaTarget.targetId` when installing or upgrade the chart. This value is the same as the `targetId` of quota allocation.
  ```
  helm install dependencies helm_chart/HyperPodHelmChart --namespace kube-system --set computeQuotaTarget.targetId=<target_id>
  ```
### Step Four (whenever you want to upgrade the installation of helm charts):
* This command is required to upgrade the helm chart installation on your cluster, which will also help consume the latest releases of service components like Health Monitoring Agent.
```
helm upgrade dependencies helm_chart/HyperPodHelmChart --namespace kube-system
```

* To install the sub-chart separately that only contains roles and role bindings
  ```
  helm install dependencies helm_chart/HyperPodHelmChart/charts/team-role-and-bindings --set computeQuotaTarget.targetId=<target_id>
  ```

## 6. Notes
- Training job auto resume is expected to work with Kubeflow training operator release v1.7.0, v1.8.0, v1.8.1 https://github.com/kubeflow/training-operator/releases
- If you intend to use the Health Monitoring Agent container image from another region, please see below list to find relevant region's URI.
  ```
  IAD 767398015722.dkr.ecr.us-east-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  PDX 905418368575.dkr.ecr.us-west-2.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  CMH 851725546812.dkr.ecr.us-east-2.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  SFO 011528288828.dkr.ecr.us-west-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  FRA 211125453373.dkr.ecr.eu-central-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  ARN 654654141839.dkr.ecr.eu-north-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  DUB 533267293120.dkr.ecr.eu-west-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  LHR 011528288831.dkr.ecr.eu-west-2.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  NRT 533267052152.dkr.ecr.ap-northeast-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  BOM 011528288864.dkr.ecr.ap-south-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  SIN 905418428165.dkr.ecr.ap-southeast-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  SYD 851725636348.dkr.ecr.ap-southeast-2.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  GRU 025066253954.dkr.ecr.sa-east-1.amazonaws.com/hyperpod-health-monitoring-agent:1.0.643.0_1.0.192.0
  ```

## 7. Troubleshooting

#### ServiceAccount "neuron-device-plugin" in namespace "kube-system" exists and cannot be imported into the current release
- This means dependencies already installed. You can change the name of the dependencies if you want another dependencies. To see dependencies already existed or not
  ```
  kubectl get serviceaccount neuron-device-plugin -n kube-system

  NAME                   SECRETS   AGE
  neuron-device-plugin   0         9m48s
  ```

#### Add new dependencies subchart
- Make sure you run 
  ```
  helm lint HyperPodHelmChart
  ```
- Add chart metadata in the main Chart.yaml. Version should points to subchart major version.
  ```
  name: storage
  version: "0.1.0"
  repository: "file://charts/storage"
  condition: storage.enabled
  ```
