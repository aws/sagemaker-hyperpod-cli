
# SageMaker HyperPod command-line interface

The Amazon SageMaker HyperPod command-line interface (HyperPod CLI) is a tool that helps manage training jobs on the SageMaker HyperPod clusters orchestrated by Amazon EKS.

This documentation serves as a reference for the available HyperPod CLI commands. For a comprehensive user guide, see [Orchestrating SageMaker HyperPod clusters with Amazon EKS](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks.html) in the *Amazon SageMaker Developer Guide*.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Platform Support](#platform-support)
- [ML Framework Support](#ml-framework-support)
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

## Overview

The SageMaker HyperPod CLI is a tool that helps submit training jobs to the Amazon SageMaker HyperPod clusters orchestrated by Amazon EKS. It provides a set of commands for managing the full lifecycle of training jobs, including submitting, describing, listing, patching and canceling jobs, as well as accessing logs and executing commands within the job's containers. The CLI is designed to abstract away the complexity of working directly with Kubernetes for these core actions of managing jobs on SageMaker HyperPod clusters orchestrated by Amazon EKS.

## Prerequisites

- HyperPod CLI currently only supports starting kubeflow/PyTorchJob. To start a job, you need to install Kubeflow Training Operator first. 
  - You can either follow [kubeflow public doc](https://www.kubeflow.org/docs/components/training/installation/) to install it.
  - Or you can follow the [Readme under helm_chart folder](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/helm_chart/readme.md) to install Kubeflow Training Operator.
- Configure [aws cli](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) to point to the correct region where your HyperPod clusters are located. 

## Platform Support

SageMaker HyperPod CLI currently supports Linux and MacOS platforms. Windows platform is not supported now.

## ML Framework Support

SageMaker HyperPod CLI currently supports start training job with:
- PyTorch ML Framework. Version requirements: PyTorch >= 1.10

## Installation

1. Make sure that your local python version is 3.8, 3.9, 3.10 or 3.11.

1. Install ```helm```.

    The SageMaker Hyperpod CLI uses Helm to start training jobs. See also the [Helm installation guide](https://helm.sh/docs/intro/install/).

    ```
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    chmod 700 get_helm.sh
    ./get_helm.sh
    rm -f ./get_helm.sh  
    ```

1. Clone and install the sagemaker-hyperpod-cli package.

    ```
    git clone git@github.com:aws/sagemaker-hyperpod-cli.git
    cd sagemaker-hyperpod-cli
    pip install .
    ```

1. Verify if the installation succeeded by running the following command.

    ```
    hyperpod --help
    ```

1. If you have a running HyperPod cluster, you can try to run a training job using the sample configuration file provided at ```/examples/basic-job-example-config.yaml```.
    - Get your HyperPod clusters to show their capacities.
      ```
      hyperpod get-clusters
      ```
    - Get your HyperPod clusters to show their capacities and quota allocation info for a team.
      ```
      hyperpod get-clusters -n hyperpod-ns-<team-name>
      ```
    - Connect to one HyperPod cluster and specify a namespace you have access to.
      ```
      hyperpod connect-cluster --cluster-name <cluster-name>
      ```
    - Start a job in your cluster. Change the `instance_type` in the yaml file to be same as the one in your HyperPod cluster. Also change the `namespace` you want to submit a job to, the example uses kubeflow namespace. You need to have installed PyTorch in your cluster.
      ```
      hyperpod start-job --config-file ./examples/basic-job-example-config.yaml
      ```

## Usage

The HyperPod CLI provides the following commands:

- [Getting Clusters](#getting-cluster-information)
- [Connecting to a Cluster](#connecting-to-a-cluster)
- [Submitting a Job](#submitting-a-job)
- [Getting Job Details](#getting-job-details)
- [Listing Jobs](#listing-jobs)
- [Canceling a Job](#canceling-a-job)
- [Listing Pods](#listing-pods)
- [Accessing Logs](#accessing-logs)
- [Executing Commands](#executing-commands)

### Getting Cluster information

This command lists the available SageMaker HyperPod clusters and their capacity information.

```
hyperpod get-clusters [--region <region>] [--clusters <cluster1,cluster2>] [--namespace <namespace>] [--orchestrator <eks>] [--output <json|table>]
```

* `region` (string) - Optional. The region that the SageMaker HyperPod and EKS clusters are located. If not specified, it will be set to the region from the current AWS account credentials.
* `clusters` (list[string]) - Optional. A list of SageMaker HyperPod cluster names that users want to check the capacity for. This is useful for users who know some of their most commonly used clusters and want to check the capacity status of the clusters in the AWS account.
* `namespace` (string) - Optional. The namespace that users want to check the quota with. Only the SageMaker managed namespaces are supported.
* `orchestrator` (enum) - Optional. The orchestrator type for the cluster. Currently, `'eks'` is the only available option.
* `output` (enum) - Optional. The output format. Available values are `table` and `json`. The default value is `json`.

### Connecting to a Cluster

This command configures the local Kubectl environment to interact with the specified SageMaker HyperPod cluster and namespace.

```
hyperpod connect-cluster --cluster-name <cluster-name> [--region <region>] [--namespace <namespace>]
```

* `cluster-name` (string) - Required. The SageMaker HyperPod cluster name to configure with.
* `region` (string) - Optional. The region that the SageMaker HyperPod and EKS clusters are located. If not specified, it will be set to the region from the current AWS account credentials.
* `namespace` (string) - Optional. The namespace that you want to connect to. If not specified, Hyperpod cli commands will auto discover the accessible namespace.

### Submitting a Job

This command submits a new training job to the connected SageMaker HyperPod cluster.

```
hyperpod start-job --job-name <job-name> [--namespace <namespace>] [--job-kind <kubeflow/PyTorchJob>] [--image <image>] [--command <command>] [--entry-script <script>] [--script-args <arg1 arg2>] [--environment <key=value>] [--pull-policy <Always|IfNotPresent|Never>] [--instance-type <instance-type>] [--node-count <count>] [--tasks-per-node <count>] [--label-selector <key=value>] [--deep-health-check-passed-nodes-only] [--scheduler-type <Kueue SageMaker None>] [--queue-name <queue-name>] [--priority <priority>] [--auto-resume] [--max-retry <count>] [--restart-policy <Always|OnFailure|Never|ExitCode>] [--volumes <volume1,volume2>] [--persistent-volume-claims <claim1:/mount/path,claim2:/mount/path>] [--results-dir <dir>] [--service-account-name <account>]
```

* `job-name` (string) - Required. The base name of the job. A unique identifier (UUID) will automatically be appended to the name like `<job-name>-<UUID>`.
* `job-kind` (string) - Optional. The training job kind. The job type currently supported is `kubeflow/PyTorchJob`.
* `namespace` (string) - Optional. The namespace to use. If not specified, this command will first use the namespace when connecting the cluster. Otherwise if namespace is not configured when connecting to the cluster, a namespace that is managed by SageMaker will be auto discovered.
* `image` (string) - Required. The image used when creating the training job.
* `pull-policy` (enum) - Optional. The policy to pull the container image. Valid values are `Always`, `IfNotPresent`, and `Never`, as available from the PyTorchJob. The default is `Always`.
* `command` (string) - Optional. The command to run the entrypoint script. Currently, only `torchrun` is supported.
* `entry-script` (string) - Required. The path to the training script.
* `script-args` (list[string]) - Optional. The list of arguments for entry scripts.
* `environment` (dict[string, string]) - Optional. The environment variables (key-value pairs) to set in the containers.
* `node-count` (int) - Required. The number of nodes (instances) to launch the jobs on.
* `instance-type` (string) - Required. The instance type to launch the job on. Note that the instance types you can use are the available instances within your SageMaker quotas for instances prefixed with `ml`. If `node.kubernetes.io/instance-type` is provided via the `label-selector` it will take precedence for node selection.
* `tasks-per-node` (int) - Optional. The number of devices to use per instance.
* `label-selector` (dict[string, list[string]]) - Optional. A dictionary of labels and their values that will override the predefined node selection rules based on the SageMaker HyperPod `node-health-status` label and values. If users provide this field, the CLI will launch the job with this customized label selection.
* `deep-health-check-passed-nodes-only` (bool) - Optional. If set to `true`, the job will be launched only on nodes that have the `deep-health-check-status` label with the value `passed`.
* `scheduler-type` (enum) - Optional. The scheduler type to use which can be `SageMaker`, `Kueue` or `None`. Default value is `SageMaker`.
* `queue-name` (string) - Optional. The name of the queue to submit the job to, which is created by the cluster admin users in your AWS account.
* `priority` (string) - Optional. The priority for the job, which needs to be created by the cluster admin users and match the name in the cluster.
* `auto-resume` (bool) - Optional. The flag to enable HyperPod resilience job auto resume. If set to `true`, the job will automatically resume after pod or node failure. To enable `auto-resume`, you also should set `restart-policy` to `OnFailure`.
* `max-retry` (int) - Optional. The maximum number of retries for HyperPod resilience job auto resume. If `auto-resume` is set to true and `max-retry` is not specified, the default value is 1.
* `restart-policy` (enum) - Optional. The PyTorchJob restart policy, which can be `Always`, `OnFailure`, `Never`, or `ExitCode`. The default is `OnFailure`. To enable `auto-resume`, `restart-policy` should be set to `OnFailure`.
* `volumes` (list[string]) - Optional. Add a temp directory for containers to store data in the hosts.
* `persistent-volume-claims` (list[string]) - Optional. The pre-created persistent volume claims (PVCs) that the data scientist can choose to mount to the containers. The cluster admin users should create PVCs and provide it to the data scientist users.
* `results-dir` (string) - Optional. The location to store the results, checkpoints, and logs. The cluster admin users should set this up and provide it to the data scientist users. The default value is `./results`.
* `service-account-name` - Optional. The Kubernetes service account that allows Pods to access resources based on the permissions granted to that service account. The cluster admin users should create the Kubernetes service account.
* `recipe` (string) - Optional. The recipe to use for the job. The recipe is a predefined set of parameters for the job.
* `override-parameters` (string) - Optional. The parameters to override for the job. The parameters are in JSON format.
Example:
```
hyperpod start-job --recipe <recipe-name>
```

Below is an example of how to use the `override-parameters` option and deepseek recipe.

```
hyperpod start-job --recipe fine-tuning/deepseek/hf_deepseek_r1_distilled_llama_8b_seq8k_gpu_fine_tuning --override-parameters \
'{
    "cluster":"k8s",
    "cluster_type":"k8s",
    "container":"658645717510.dkr.ecr.us-west-2.amazonaws.com/smdistributed-modelparallel:2.4.1-gpu-py311-cu121",
    "+cluster.persistent_volume_claims.0.claimName":"fsx-claim-large",
    "+cluster.persistent_volume_claims.0.mountPath":"data",
    "cluster.service_account_name":"",
    "recipes.run.name":"deepseek",
    "recipes.model.train_batch_size":"1",
    "instance_type":"p4d.24xlarge",
    "recipes.model.data.use_synthetic_data":"True",
    "recipes.model.fp8":"False",
    "recipes.exp_manager.auto_checkpoint.enabled":"False",
    "recipes.exp_manager.export_full_model.save_last":"False",
    "recipes.exp_manager.checkpoint_callback_params.save_last":"False",
    "recipes.model.hf_model_name_or_path":"deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    "recipes.model.hf_access_token":"<your-access-token>",
    "recipes.exp_manager.exp_dir":""   
}'\
```


### Getting Job Details

This command displays detailed information about a specific training job.

```
hyperpod get-job --job-name <job-name> [--namespace <namespace>] [--verbose]
```

* `job-name` (string) - Required. The name of the job.
* `namespace` (string) - Optional. The namespace to use. If not specified, this command will first use the namespace when connecting the cluster. Otherwise if namespace is not configured when connecting to the cluster, a namespace that is managed by SageMaker will be auto discovered.
* `verbose` (flag) - Optional. If set to `True`, the command enables verbose mode and prints out more detailed output with additional fields.

### Listing Jobs

This command lists all the training jobs in the connected SageMaker HyperPod cluster or namespace.

```
hyperpod list-jobs [--namespace <namespace>] [--all-namespaces] [--selector <key=value>]
```

* `namespace` (string) - Optional. The namespace to use. If not specified, this command will first use the namespace when connecting the cluster. Otherwise if namespace is not configured when connecting to the cluster, a namespace that is managed by SageMaker will be auto discovered.
* `all-namespaces` (flag) - Optional. If set, this command lists jobs from all namespaces the data scientist users have access to. The namespace in the current AWS account credentials will be ignored, even if specified with the `--namespace` option.
* `selector` (string) - Optional. A label selector to filter the listed jobs. The selector supports the '=', '==', and '!=' operators (e.g., `-l key1=value1,key2=value2`).

### Canceling a Job

This command cancels and deletes a running training job.

```
hyperpod cancel-job --job-name <job-name> [--namespace <namespace>]
```

* `job-name` (string) - Required. The name of the job to cancel.
* `namespace` (string) - Optional. The namespace to use. If not specified, this command will first use the namespace when connecting the cluster. Otherwise if namespace is not configured when connecting to the cluster, a namespace that is managed by SageMaker will be auto discovered.

### Listing Pods

This command lists all the pods associated with a specific training job.

```
hyperpod list-pods --job-name <job-name> [--namespace <namespace>]
```

* `job-name` (string) - Required. The name of the job to list pods for.
* `namespace` (string) - Optional. The namespace to use. If not specified, this command will first use the namespace when connecting the cluster. Otherwise if namespace is not configured when connecting to the cluster, a namespace that is managed by SageMaker will be auto discovered.

### Accessing Logs

This command retrieves the logs for a specific pod within a training job.

```
hyperpod get-log --job-name <job-name> --pod <pod-name> [--namespace <namespace>]
```

* `job-name` (string) - Required. The name of the job to get the log for.
* `pod` (string) - Required. The name of the pod to get the log from.
* `namespace` (string) - Optional. The namespace to use. If not specified, this command will first use the namespace when connecting the cluster. Otherwise if namespace is not configured when connecting to the cluster, a namespace that is managed by SageMaker will be auto discovered.

### Executing Commands

This command executes a specified command within the container of a pod associated with a training job.

```
hyperpod exec --job-name <job-name> [-p <pod-name>] [--all-pods] -- <command>
```

* `job-name` (string) - Required. The name of the job to execute the command within the container of a pod associated with a training job.
* `bash-command` (string) - Required. The bash command(s) to run.
* `namespace` (string) - Optional. The namespace to use. If not specified, this command will first use the namespace when connecting the cluster. Otherwise if namespace is not configured when connecting to the cluster, a namespace that is managed by SageMaker will be auto discovered.
* `pod` (string) - Optional. The name of the pod to execute the command in. You must provide either `--pod` or `--all-pods`.
* `all-pods` (flag) - Optional. If set, the command will be executed in all pods associated with the job.

### Patch Jobs

This command patches a job with certain operation. Currently only `suspend` and `unsuspend` are supported.

```
hyperpod patch-job suspend --job-name <job-name> [--namespace <namespace>]
```

```
hyperpod patch-job unsuspend --job-name <job-name> [--namespace <namespace>]
```

* `job-name` (string) - Required. The name of the job to be patched.
* `namespace` (string) - Optional. The namespace to use. If not specified, this command will first use the namespace when connecting the cluster. Otherwise if namespace is not configured when connecting to the cluster, a namespace that is managed by SageMaker will be auto discovered.