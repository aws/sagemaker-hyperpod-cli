# Changelog

## v3.7.1 (2026-04-08)

### New Instance Type Support
- Add g7e instance types to HyperPod helm chart values (nvidia/EFA device plugins) (#380)
- Add g7e instance types to Python constants and CLI (#385, #390)
- Add g7e instance types to health-monitoring-agent node affinity (#381)
- Add B300 MIG profiles to GPU operator ConfigMap (#396)
- Add MIG profile support for ml.p6-b300.48xlarge (Blackwell Ultra) (#398)

### Inference Operator
- CRD updates: BYO certificate, RequestLimitsConfig, Custom Kubernetes support (#402)
- Bump hyperpod-inference-operator subchart to v2.1.0 with image tag v3.1 (#402)

### Enhancements
- Support AWS_REGION env var, cluster context fallback, centralize boto3 client creation (#395)
- Handle pagination in cluster stack listing (#394)
- Require --instance-type when specifying accelerator resources (#393)

### Bug Fixes
- Fix EFA field naming in PyTorch job template v1.1: `efa_interfaces` -> `efa`, `efa_interfaces_limit` -> `efa_limit` (#392)
- Fix deep health check nodeSelector label to `sagemaker.amazonaws.com/deep-health-check-status: Passed` (#386)
- Remove non-EFA instance types from EFA device plugin nodeAffinity to prevent CrashLoopBackOff (#389)
- Add missing instance types and fix EFA/memory resource specs (#385)

### Health Monitoring Agent
- Release Health Monitoring Agent 1.0.1434.0_1.0.388.0 (#388)

## v3.7.0 (2026-03-02)

Space CLI
- Added list all functionality and documentation updates
- Disabled traceback for cleaner error output

Inference Operator
- Inference Operator AddOn with NodeAffinity support and version 3.0 update
- Updated hyperpod-inference-operator to version 2.0.0 in HyperPodHelmChart
- Added AddOn migration script and README

#### Enhancements

Monitoring & Observability
- Emit metrics for CLI commands

Testing & Validation
- Added unit tests for inference CRDs
- Added CRD format check for inference

Dependencies & Versions
- Updated GPU operator container toolkit version
- Updated aws-efa-k8s-device-plugin version to 0.5.20

Configuration
- Instance types CRD changes

#### Bug Fixes

- Fixed syntax error in inferenceendpointconfigs by removing tab

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




