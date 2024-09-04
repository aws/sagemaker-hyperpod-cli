
# SageMaker HyperPod command-line interface

The Amazon SageMaker HyperPod command-line interface (HyperPod CLI) is a tool that helps manage training jobs on the SageMaker HyperPod clusters orchestrated by Amazon EKS.

This documentation serves as a reference for the available HyperPod CLI commands. For a comprehensive user guide, see [Orchestrating HyperPod clusters with Amazon EKS](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks.html) in the *Amazon SageMaker Developer Guide*.

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

The SageMaker HyperPod CLI is a tool that helps submit training jobs to the Amazon SageMaker HyperPod clusters orchestrated by Amazon EKS. It provides a set of commands for managing the full lifecycle of training jobs, including submitting, describing, listing, and canceling jobs, as well as accessing logs and executing commands within the job's containers. The CLI is designed to abstract away the complexity of working directly with Kubernetes for these core actions of managing jobs on SageMaker HyperPod clusters orchestrated by Amazon EKS.

## Installation

1. Make sure that your local python version is 3.8 or later.

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

* `region` (string) - Optional. The region that the HyperPod and EKS clusters are located. If not specified, it will be set to the region from the current AWS account credentials.
* `clusters` (list[string]) - Optional. A list of HyperPod cluster names that users want to check the capacity for. This is useful for users who know some of their most commonly used clusters and want to check the capacity status of the clusters in the AWS account.
* `orchestrator` (enum) - Optional. The orchestrator type for the cluster. Currently, `'eks'` is the only available option.
* `output` (enum) - Optional. The output format. Available values are `TABLE` and `JSON`. The default value is `JSON`.

### Connecting to a Cluster

This command configures the local Kubectl environment to interact with the specified HyperPod cluster and namespace.

```
hyperpod connect-cluster --cluster-name <cluster-name> [--region <region>] [--namespace <namespace>]
```

* `cluster-name` (string) - Required. The HyperPod cluster name to configure with.
* `region` (string) - Optional. The region that the HyperPod and EKS clusters are located. If not specified, it will be set to the region from the current AWS account credentials.
* `namespace` (string) - Optional. The namespace that you want to connect to. If not specified, this command uses the [Kubernetes namespace](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) of the Amazon EKS cluster associated with the SageMaker HyperPod cluster in your AWS account.

### Submitting a Job

This command submits a new training job to the connected HyperPod cluster.

```
hyperpod start-job --job-name <job-name> [--namespace <namespace>] [--job-kind <kubeflow/PyTorchJob>] [--image <image>] [--command <command>] [--entry-script <script>] [--script-args <arg1 arg2>] [--environment <key=value>] [--pull-policy <Always|IfNotPresent|Never>] [--instance-type <instance-type>] [--node-count <count>] [--tasks-per-node <count>] [--label-selector <key=value>] [--deep-health-check-passed-nodes-only] [--scheduler-type <Kueue>] [--queue-name <queue-name>] [--priority <priority>] [--auto-resume] [--max-retry <count>] [--restart-policy <Always|OnFailure|Never|ExitCode>] [--volumes <volume1,volume2>] [--persistent-volume-claims <claim1:/mount/path,claim2:/mount/path>] [--results-dir <dir>] [--service-account-name <account>]
```

* `job-name` (string) - Required. The name of the job.
* `job-kind` (string) - Optional. The training job kind. The job types currently supported are `kubeflow` and `PyTorchJob`.
* `namespace` (string) - Optional. The namespace to use. If not specified, this command uses the [Kubernetes namespace](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) of the Amazon EKS cluster associated with the SageMaker HyperPod cluster in your AWS account.
* `image` (string) - Required. The image used when creating the training job.
* `pull-policy` (enum) - Optional. The policy to pull the container image. Valid values are `Always`, `IfNotPresent`, and `Never`, as available from the PyTorchJob. The default is `Always`.
* `command` (string) - Optional. The command to run the entrypoint script. Currently, only `torchrun` is supported.
* `entry-script` (string) - Required. The path to the training script.
* `script-args` (list[string]) - Optional. The list of arguments for entryscripts.
* `environment` (dict[string, string]) - Optional. The environment variables (key-value pairs) to set in the containers.
* `node-count` (int) - Required. The number of nodes (instances) to launch the jobs on.
* `instance-type` (string) - Required. The instance type to launch the job on. Note that the instance types you can use are the available instances within your SageMaker quotas for instances prefixed with `ml`.
* `tasks-per-node` (int) - Optional. The number of devices to use per instance.
* `label-selector` (dict[string, list[string]]) - Optional. A dictionary of labels and their values that will override the predefined node selection rules based on the HyperPod `node-health-status` label and values. If users provide this field, the CLI will launch the job with this customized label selection.
* `deep-health-check-passed-nodes-only` (bool) - Optional. If set to `true`, the job will be launched only on nodes that have the `deep-health-check-status` label with the value `passed`.
* `scheduler-type` (enum) - Optional. The scheduler type to use. Currently, only `Kueue` is supported.
* `queue-name` (string) - Optional. The name of the queue to submit the job to, which is created by the cluster admin users in your AWS account.
* `priority` (string) - Optional. The priority for the job, which needs to be created by the cluster admin users and match the name in the cluster.
* `auto-resume` (bool) - Optional. If set to `true`, the job will automatically resume after a failure. Note that `auto-resume` currently only works in the `kubeflow` namespace or the namespace prefixed with `aws-hyperpod`. To enable `auto-resume`, you also should set `restart-policy` to `OnFailure`.
* `max-retry` (int) - Optional. The maximum number of retries if `auto-resume` is `true`. If `auto-resume` is set to true and `max-retry` is not specified, the default value is 1.
* `restart-policy` (enum) - Optional. The PyTorchJob restart policy, which can be `Always`, `OnFailure`, `Never`, or `ExitCode`. The default is `OnFailure`. To enable `auto-resume`, `restart-policy` should be set to `OnFailure`.
* `volumes` (list[string]) - Optional. Add a temp directory for containers to store data in the hosts.
* `persistent-volume-claims` (list[string]) - Optional. The pre-created persistent volume claims (PVCs) that the data scientist can choose to mount to the containers. The cluster admin users should create PVCs and provide it to the data scientist users.
* `results-dir` (string) - Optional. The location to store the results, checkpoints, and logs. The cluster admin users should set this up and provide it to the data scientist users. The default value is `./results`.
* `service-account-name` - Optional. The Kubernetes service account that allows Pods to access resources based on the permissions granted to that service account. The cluster admin users should create the Kubernetes service account.


### Getting Job Details

This command displays detailed information about a specific training job.

```
hyperpod get-job --job-name <job-name> [--namespace <namespace>] [--verbose]
```

* `job-name` (string) - Required. The name of the job.
* `namespace` (string) - Optional. The namespace to describe the job in. If not provided, the CLI will try to describe the job in the namespace set by the user while connecting to the cluster. If provided, and the user has access to the namespace, the CLI will describe the job from the specified namespace.
* `verbose` (flag) - Optional. If set to `True`, the command enables verbose mode and prints out more detailed output with additional fields.

### Listing Jobs

This command lists all the training jobs in the connected HyperPod cluster or namespace.

```
hyperpod list-jobs [--namespace <namespace>] [--all-namespaces] [--selector <key=value>]
```

* `namespace` (string) - Optional. The namespace to list the jobs in. If not provided, this command lists the jobs in the namespace specified during connecting to the cluster. If the namespace is provided and if the user has access to the namespace, this command lists the jobs from the specified namespace.
* `all-namespaces` (flag) - Optional. If set, this command lists jobs from all namespaces the data scientist users have access to. The namespace in the current AWS account credentials will be ignored, even if specified with the `--namespace` option.
* `selector` (string) - Optional. A label selector to filter the listed jobs. The selector supports the '=', '==', and '!=' operators (e.g., `-l key1=value1,key2=value2`).

### Canceling a Job

This command cancels and deletes a running training job.

```
hyperpod cancel-job --job-name <job-name> [--namespace <namespace>]
```

* `job-name` (string) - Required. The name of the job to cancel.
* `namespace` (string) - Optional. The namespace to cancel the job in. If not provided, the CLI will try to cancel the job in the namespace set by the user while connecting to the cluster. If provided, and the user has access to the namespace, the CLI will cancel the job from the specified namespace.

### Listing Pods

This command lists all the pods associated with a specific training job.

```
hyperpod list-pods --job-name <job-name> [--namespace <namespace>]
```

* `job-name` (string) - Required. The name of the job to list pods for.
* `namespace` (string) - Optional. The namespace to list the pods in. If not provided, the CLI will list the pods in the namespace set by the user while connecting to the cluster. If provided, and the user has access to the namespace, the CLI will list the pods from the specified namespace.

### Accessing Logs

This command retrieves the logs for a specific pod within a training job.

```
hyperpod get-log --job-name <job-name> --pod <pod-name> [--namespace <namespace>]
```

* `job-name` (string) - Required. The name of the job to get the log for.
* `pod` (string) - Required. The name of the pod to get the log from.
* `namespace` (string) - Optional. The namespace to get the log from. If not provided, the CLI will get the log from the pod in the namespace set by the user while connecting to the cluster. If provided, and the user has access to the namespace, the CLI will get the log from the pod in the specified namespace.

### Executing Commands

This command executes a specified command within the container of a pod associated with a training job.

```
hyperpod exec --job-name <job-name> [-p <pod-name>] [--all-pods] -- <command>
```

* `job-name` (string) - Required. The name of the job to execute the command within the container of a pod associated with a training job.
* `bash-command` (string) - Required. The bash command(s) to run.
* `namespace` (string) - Optional. The namespace to execute the command in. If not provided, the CLI will try to execute the command in the pod in the namespace set by the user while connecting to the cluster. If provided, and the user has access to the namespace, the CLI will execute the command in the pod from the specified namespace.
* `pod` (string) - Optional. The name of the pod to execute the command in. You must provide either `--pod` or `--all-pods`.
* `all-pods` (flag) - Optional. If set, the command will be executed in all pods associated with the job.