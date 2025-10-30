# Changelog

## v.3.3.1 (2025-10-30)

### Features

  * Describe cluster command
    * User can use hyp describe cluster to learn more info about hp clusters
  * Jinja template handling logic for inference and training
    * User can modify jinja template to add parameters supported by CRD through init experience of inference and training, for further CLI customization
  * Cluster creation template versioning
    * User can choose cloudformation template version through cluster creation expeirence
  * KVCache and intelligent routing for HyperPod Inference
    * InferenceEndpointConfig CRD supported is updated to v1
    * KVCache and Intelligent Routing support is added in template version 1.1


## v.3.3.0 (2025-09-23)

### Features

  * Init Experience
    * Init, Validate, and Create JumpStart endpoint, Custom endpoint, and PyTorch Training Job with local configuration
  * Cluster management 
    * Bug fixes for cluster creation
    

## v.3.2.2 (2025-09-10)

### Features

  * Fix for production canary failures caused by bad training job template.
  * New version for Health Monitoring Agent (1.0.790.0_1.0.266.0) with minor improvements and bug fixes.

## v3.2.1 (2025-08-27)

### Features

 * Cluster management 
   * Bug Fixes with cluster creation
   * Enable cluster template to be installed with hyperpod CLI .

## v3.2.0 (2025-08-25)

### Features

 * Cluster management 
   * Creation of cluster stack 
   * Describing and listing a cluster stack 
   * Updating a cluster 
 * Init Experience 
   * Init, Validate, Create with local configurations
 

## v3.1.0 (2025-08-13)

### Features
 * Task Governance feature for training jobs.


## v3.0.2 (2025-07-31)

### Features

 * Update volume flag to support hostPath and PVC
 * Add an option to disable the deployment of KubeFlow TrainingOperator
 * Enable telemetry for CLI

## v3.0.0 (2025-07-10)

### Features

 * Training Job - Create, List , Get 
 * Inference Jumpstart - Create , List, Get, Invoke
 * Inference Custom - Create , List, Get, Invoke
 * Observability changes

## v2.0.0 (2024-12-04)

### Features

- feature: The HyperPod CLI now support ([Hyperpod recipes](https://github.com/aws/sagemaker-hyperpod-recipes.git)). The HyperPod recipes enable customers to get started training and fine-tuning popular publicly-available foundation models like Llama 3.1 405B in minutes. Learn more ([here](https://github.com/aws/sagemaker-hyperpod-recipes.git)).

## v1.0.0 (2024-09-09)

### Features

- feature: Add support for SageMaker HyperPod CLI



