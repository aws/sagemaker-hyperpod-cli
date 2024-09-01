
# HyperPod CLI

The HyperPod CLI is a command-line interface for managing training jobs on the HyperPod Kubernetes cluster.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
  - [Listing Clusters](#listing-clusters)
  - [Connecting to a Cluster](#connecting-to-a-cluster)
  - [Submitting a Job](#submitting-a-job)
  - [Getting Job Details](#getting-job-details)
  - [Listing Jobs](#listing-jobs)
  - [Canceling a Job](#canceling-a-job)
  - [Listing Pods](#listing-pods)
  - [Accessing Logs](#accessing-logs)
  - [Executing Commands](#executing-commands)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Overview

The SageMaker HyperPod CLI is a tool that helps data scientists submit training jobs to the SageMaker HyperPod clusters orchestrated by Amazon EKS. It provides a set of commands for managing the full lifecycle of training jobs, including submitting, describing, listing, and canceling jobs, as well as accessing logs and executing commands within the job's containers. The CLI is designed to abstract away the complexity of working directly with Kubernetes for these core actions of managing jobs on SageMaker HyperPod clusters orchestrated by Amazon EKS.

## Installation

1. Make sure that your local python version is 3.8 or later. Supported python versions are 3.8, 3.9, 3.10, 3.11

1. Install ```helm```.

    The SageMaker Hyperpod CLI uses Helm to start training jobs. See also the [Helm installation guide](https://helm.sh/docs/intro/install/).

    ```
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    chmod 700 get_helm.sh
    ./get_helm.sh
    rm -f ./get_helm.sh  
    ```

1. Clone and install the [SageMaker HyperPod CLI](https://github.com/aws/sagemaker-hyperpod-cli) package.

    ```
    git clone https://github.com/aws/sagemaker-hyperpod-cli
    cd sagemaker-hyperpod-cli
    pip install .
    ```

1. Verify if the installation succeeded by running the following command.

    ```
    hyperpod --help
    ```

1. Try to run a training job using the sample configuration file provided at ```/examples/basic-job-example-config.yaml```.

    ```
    hyperpod start-job --config-file ./examples/basic-job-example-config.yaml
    ```

## Usage

The HyperPod CLI provides the following commands:

- [Listing Clusters](#listing-clusters)
- [Connecting to a Cluster](#connecting-to-a-cluster)
- [Submitting a Job](#submitting-a-job)
- [Getting Job Details](#getting-job-details)
- [Listing Jobs](#listing-jobs)
- [Canceling a Job](#canceling-a-job)
- [Listing Pods](#listing-pods)
- [Accessing Logs](#accessing-logs)
- [Executing Commands](#executing-commands)

### Listing Clusters

This command lists the available HyperPod clusters and their capacity information.

```
hyperpod list-clusters [--region <region>] [--clusters <cluster1,cluster2>] [--orchestrator <eks>] [--output <json|table>]
```

* `region` (string) - Optional. The region that the Cluster resides. Default will be the region from the current context.
* `clusters` (list[string]) - Optional. A list of HyperPod cluster names that users want to check the capacity for. This is useful for users who know some of their most commonly used clusters and want to check the capacity status for an admin account with many HyperPod clusters.
* `orchestrator` (enum) - Optional. The orchestrator type for the cluster. Currently, only `'eks'` is the only available option for supporting SageMaker HyperPod clusters orchestrated by Amazon EKS.
* `output` (enum) - Optional. The output format. Available values are `TABLE` and `JSON`. The default value is `JSON`.

### Connecting to a Cluster

This command configures the local Kubectl environment to interact with the specified HyperPod cluster and namespace.

```
hyperpod connect-cluster --cluster-name <cluster-name> [--region <region>] [--namespace <namespace>]
```

* `cluster-name` (string) - Required. The cluster name to connect to.
* `region` (string) - Optional. The region that the cluster resides.  If not provided, the default will be set to the region from the current context.
* `namespace` (string) - Optional. The namespace that users want to connect to. If not provided, the default namespace will be used.

### Submitting a Job

This command submits a new training job to the connected HyperPod cluster.

```
hyperpod start-job --job-name <job-name> [--namespace <namespace>] [--job-kind <kubeflow/PyTorchJob>] [--image <image>] [--command <command>] [--entry-script <script>] [--script-args <arg1 arg2>] [--environment <key=value>] [--pull-policy <Always|IfNotPresent|Never>] [--instance-type <instance-type>] [--node-count <count>] [--tasks-per-node <count>] [--label-selector <key=value>] [--deep-health-check-passed-nodes-only] [--scheduler-type <Kueue>] [--queue-name <queue-name>] [--priority <priority>] [--auto-resume] [--max-retry <count>] [--restart-policy <Always|OnFailure|Never|ExitCode>] [--volumes <volume1,volume2>] [--persistent-volume-claims <claim1:/mount/path,claim2:/mount/path>] [--results-dir <dir>] [--service-account-name <account>]
```

* `job-name` (string) - Required. The name of the job.
* `job-kind` (string) - Optional. The training job kind. Currently, only `kubeflow/PyTorchJob` is supported.
* `namespace` (string) - Optional. The namespace to use. Default is `kubeflow`.
* `image` (string) - Required. The image used when creating the training job.
* `pull-policy` (enum) - Optional. The policy to pull the container image. Valid values are `Always`, `IfNotPresent`, and `Never`, as available from the PyTorchJob. The default is `Always`.
* `command` (string) - Optional. The command to run the entrypoint script. Currently, only `torchrun` is supported in Kandinsky, and the CLI will restrict it to only `torchrun`.
* `entry-script` (string) - Required. The path to the training script. Default is `./train.py`.
* `script-args` (list[string]) - Optional. The list of script arguments.
* `environment` (dict[string, string]) - Optional. The environment variables (key-value pairs) to set in the containers.
* `node-count` (int) - Required. The number of nodes to launch the jobs on.
* `instance-type` (string) - Required. The instance type used by Kandinsky to determine the GPU/CPU/TRN launcher.
* `tasks-per-node` (int) - Optional. The number of devices to use per instance. Similar to the Kandinsky field. Kandinsky has added default value support for GPU devices. The default value for CPU devices on Kandinsky has been pushed back, but we can provide a default value in the CLI to make this field completely optional.
* `label-selector` (dict[string, list[string]]) - Optional. A dictionary of labels and their values that will override the predefined node selection rules based on the HyperPod `node-health-status` label and values. If users provide this field, the CLI will launch the job with this customized label selection. See examples of use cases in "Using custom labels" and "Node Selector Behavior".
* `deep-health-check-passed-nodes-only` (bool) - Optional. If set to `true`, the job will be launched only on nodes that have the `deep-health-check-status` label with the value `passed`.
* `scheduler-type` (enum) - Optional. The scheduler type to use. Currently, only `Kueue` is supported.
* `queue-name` (string) - Optional. The queue to submit the job to, which is created by an admin.
* `priority` (string) - Optional. The priority for the job, which needs to be created by an admin and match the name in the cluster.
* `auto-resume` (bool) - Optional. If set to `true`, the job will automatically resume after a failure.
* `max-retry` (int) - Optional. The maximum number of retries if `auto-resume` is `true`. The default value is 1 if not specified.
* `restart-policy` (enum) - Optional. The PyTorchJob restart policy, which can be `Always`, `OnFailure`, `Never`, or `ExitCode`. The default is `OnFailure`.
* `persistent-volume-claims` (list[string]) - Optional. The pre-created persistent volume claims (PVCs) that the data scientist can choose to mount to the containers (admin responsibility).
* `results-dir` (string) - Optional. The location to store the results, checkpoints, and logs. The default is `./results`.


### Getting Job Details

This command displays detailed information about a specific training job.

```
hyperpod get-job --job-name <job-name> [--namespace <namespace>] [--verbose]
```

* `name` (string) - Required. The name of the job.
* `namespace` (string) - Optional. The namespace to describe the job in. If not provided, the CLI will try to describe the job in the namespace set by the customer while connecting to the cluster. If provided, and the customer has access to the namespace, the CLI will describe the job from the specified namespace.
* `verbose` (flag) - Optional. If set, the CLI will enable verbose mode and print out more detailed output with additional fields.

### Listing Jobs

This command lists all the training jobs in the connected HyperPod cluster or namespace.

```
hyperpod list-jobs [--namespace <namespace>] [--all-namespaces] [--selector <key=value>]
```

* `namespace` (string) - Optional. The namespace to list the jobs in. If not provided, the CLI will try to list the jobs in the namespace set by the customer while connecting to the cluster. If provided, and the customer has access to the namespace, the CLI will list the jobs from the specified namespace.
* `all-namespaces` (flag) - Optional. If set, the CLI will list jobs from all namespaces the user has access to. The namespace in the current context will be ignored, even if specified with the `--namespace` option.
* `selector` (string) - Optional. A label selector to filter the listed jobs. The selector supports the '=', '==', and '!=' operators (e.g., `-l key1=value1,key2=value2`). The listed jobs must satisfy all of the specified label constraints.

### Canceling a Job

This command cancels and deletes a running training job.

```
hyperpod cancel-job --job-name <job-name> [--namespace <namespace>]
```

* `name` (string) - Required. The name of the job to cancel.
* `namespace` (string) - Optional. The namespace to cancel the job in. If not provided, the CLI will try to cancel the job in the namespace set by the customer while connecting to the cluster. If provided, and the customer has access to the namespace, the CLI will cancel the job from the specified namespace.

### Listing Pods

This command lists all the pods associated with a specific training job.

```
hyperpod list-pods --job-name <job-name> [--namespace <namespace>]
```

* `name` (string) - Required. The name of the job to list pods for.
* `namespace` (string) - Optional. The namespace to list the pods in. If not provided, the CLI will list the pods in the namespace set by the customer while connecting to the cluster. If provided, and the customer has access to the namespace, the CLI will list the pods from the specified namespace.

### Accessing Logs

This command retrieves the logs for a specific pod within a training job.

```
hyperpod get-log --job-name <job-name> --pod <pod-name> [--namespace <namespace>]
```

* `name` (string) - Required. The name of the job to get the log for.
* `pod` (string) - Required. The name of the pod to get the log from.
* `namespace` (string) - Optional. The namespace to get the log from. If not provided, the CLI will get the log from the pod in the namespace set by the customer while connecting to the cluster. If provided, and the customer has access to the namespace, the CLI will get the log from the pod in the specified namespace.

### Executing Commands

This command executes a specified command within the container of a pod associated with a training job.

```
hyperpod exec --job-name <job-name> [-p <pod-name>] [--all-pods] -- <command>
```

* `name` (string) - Required. The name of the job to execute the command on.
* `bash-command` (string) - Required. The command(s) to run.
* `namespace` (string) - Optional. The namespace to execute the command in. If not provided, the CLI will try to execute the command in the pod in the namespace set by the customer while connecting to the cluster. If provided, and the customer has access to the namespace, the CLI will execute the command in the pod from the specified namespace.
* `pod` (string) - Optional. The name of the pod to execute the command in. You must provide either `--pod` or `--all-pods`.
* `all-pods` (flag) - Optional. If set, the command will be executed in all pods associated with the job.