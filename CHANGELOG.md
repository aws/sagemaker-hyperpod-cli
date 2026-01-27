# Changelog

## v3.6.0 (2026-01-27)

### Features
* Add EFA support in manifest for training jobs (#345)
* Add end-to-end example documentation (#350)
* Add 4 new HyperPod GA regions (ca-central-1, ap-southeast-3, ap-southeast-4, eu-south-2) (#360)

### Enhancements
* Update documentation for elastic training arguments (#343)
* Upgrade Inference Operator helm chart (#346)
* Update MIG config for GPU operator (#358)
* Release Health Monitoring Agent 1.0.1249.0_1.0.359.0 with enhanced Nvidia timeout analysis and bug fixes (#361)

### Bug Fixes
* Fix canary test failures for GPU quota allocation integration tests (#356)
* Fix region fallback logic for health-monitoring-agent image URIs (#360)
* Remove command flag from init pytorch job integration test (#351)
* Skip expensive integration tests to improve CI performance (#355)


## v.3.5.0 (2025-12-03)

### Features
  * Elastic training support for HyperPodTrainingOperator that is released in Reinvent 2025 keynote 3. This is a method that dynamically scales distributed machine learning operations.


## v.3.4.0 (2025-11-20)

### Features

  * HyperPod Dev Spaces template for data scientists to create, manage, and access interactive ML development environments with configurable resource allocation and namespace isolation
  * Support for KVCaching, intelligent routing, tiered storage, MIG
  * Support for fractional gpu
  * Support KVCache and Intelligent Routing support in template version 1.1
  * User can modify jinja template to add parameters supported by CRD through init experience, for further CLI customization
  * MIG support for model deployment on SageMaker Hyperpod Inference


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



