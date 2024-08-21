# Building, Packaging, and Testing Helm Charts

This guide walks you through the process of creating, packaging, and testing HyperPod Helm chart.

## 1. Set Up Your Helm Environment

Before starting, make sure Helm is installed on your machine. You can install Helm using the following commands:

```bash
chmod 700 get_helm.sh
./get_helm.sh
```
## 2. Package structure

```
HyperpodHelmChart/
├── charts/                        # External Helm chart dependencies
│   ├── kueue/                     # Kueue related sub-chart
│   │   ├── Chart.yaml             # Metadata and dependencies for Kueue
│   │   ├── values.yaml            # Default configuration values for Kueue
│   │   ├── templates/
│   │       ├── queue.yaml         # YAML template to create Kueue queues
│   │       ├── priority-class.yaml# YAML template for Kueue priority class
│   │       └── resource-quota.yaml# YAML template for Kueue resource quota
│   ├── storage/                   # Storage related sub-chart
│   │   ├── Chart.yaml             # Metadata and dependencies for Storage
│   │   ├── values.yaml            # Default configuration values for Storage
│   │   ├── templates/
│   │       ├── csi-driver.yaml    # YAML template for CSI driver
│   │       └── storageclass.yaml  # YAML template for StorageClass
│   ├── mlflow/                    # MLflow related sub-chart
│   │   ├── Chart.yaml             # Metadata and dependencies for MLflow
│   │   ├── values.yaml            # Default configuration values for MLflow
│   │   ├── templates/
│   │       ├── service-account.yaml # YAML template for MLflow service account
│   │       ├── deployment.yaml    # YAML template for MLflow deployment
│   │       └── service.yaml       # YAML template for MLflow service
│   ├── auth/                      # Auth related sub-chart
│   │   ├── Chart.yaml             # Metadata and dependencies for Auth
│   │   ├── values.yaml            # Default configuration values for Auth
│   │   ├── templates/
│   │       ├── auth-deployment.yaml # YAML template for authentication service 
│   │       ├── auth-service.yaml  # YAML template for authentication service
│   │       └── auth-config.yaml   # YAML template for authentication configuration
│   ├── training-operators/        # Kubeflow Training Operators related sub-chart
│       ├── Chart.yaml             # Metadata and dependencies for Training Operators
│       ├── values.yaml            # Default configuration values for Training Operators
│       ├── templates/
│           └── pytorchjob.yaml    # YAML template for PyTorchJob resources
├── Chart.yaml                     # Helm chart metadata and dependencies for HyperpodHelmChart
├── values.yaml                    # Default configuration values for the HyperpodHelmChart
└── README.md                      # Documentation for the Helm chart
```

## 3. Test the Chart Locally

To ensure that your chart is properly defined, use the helm lint command:

```
helm lint HyperPodHelmChart

```

## 4. Deployment

Prerequisites:

make sure you have a running Kubernetes cluster and are connected to it using HyperpodCLI connect cluster.

### Step Zero:

* install kubeflow training operators through install_dependencies.sh
* update helm chart dependencies. 

Command: 

```
helm dependencies update HyperPodHelmChart
```
* It ensures that all the sub-charts required by the main chart are fetched and properly set up before deploying the main chart. It doesn’t actually deploy the chart itself but prepares it by ensuring all dependencies are resolved.

### Step One:

* Install the Helm chart that includes all the dependencies. 
    * command: 
```
helm install dependencies HyperPodHelmChart --dry-run
```
helm will output template which will apply to k8s cluster.



### Step Two:

* Install a Helm chart and deploy it to your Kubernetes cluster. 
    * command: 
```
helm install dependencies HyperPodHelmChart --namespace kube-system
```
* This command deploys the chart to the Kubernetes cluster with the custom configurations applied. values.yaml specified Notes on only deploying certain version of dependencies in Values.yaml

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

