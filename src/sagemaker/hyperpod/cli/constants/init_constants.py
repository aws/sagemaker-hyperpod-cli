from hyperpod_jumpstart_inference_template.registry import SCHEMA_REGISTRY as JS_EP_REG, TEMPLATE_REGISTRY as JS_EP_TEMPLATE_REG
from hyperpod_custom_inference_template.registry import SCHEMA_REGISTRY as CUSTOM_EP_REG, TEMPLATE_REGISTRY as CUSTOM_EP_TEMPLATE_REG
from hyperpod_pytorch_job_template.registry import SCHEMA_REGISTRY as PYTORCH_JOB_REG, TEMPLATE_REGISTRY as PYTORCH_JOB_TEMPLATE_REG
from hyperpod_cluster_stack_template.registry import SCHEMA_REGISTRY as CLUSTER_REG, TEMPLATE_REGISTRY as CLUSTER_TEMPLATE_REG

import sys

# Here is the list of existing templates supported
# You can onboard new template by adding the mapping here

CRD = "crd"
CFN = "cfn"
TEMPLATES = {
    "hyp-jumpstart-endpoint": {
        "registry": JS_EP_REG,
        "template_registry": JS_EP_TEMPLATE_REG,
        "schema_pkg": "hyperpod_jumpstart_inference_template",
        "schema_type": CRD,
        'type': "jinja"
    },
    "hyp-custom-endpoint": {
        "registry": CUSTOM_EP_REG,
        "template_registry": CUSTOM_EP_TEMPLATE_REG,
        "schema_pkg": "hyperpod_custom_inference_template",
        "schema_type": CRD,
        'type': "jinja"
    },
    "hyp-pytorch-job": {
        "registry": PYTORCH_JOB_REG,
        "template_registry": PYTORCH_JOB_TEMPLATE_REG,
        "schema_pkg": "hyperpod_pytorch_job_template",
        "schema_type": CRD,
        'type': "jinja"
    },
    "cluster-stack": {
        "registry": CLUSTER_REG,
        "template_registry": CLUSTER_TEMPLATE_REG,
        "schema_pkg": "hyperpod_cluster_stack_template",
        "schema_type": CFN,
        'type': "jinja"
    }
}

# K8s Kind to class mapping for create_from_k8s_yaml
K8S_KIND_MAPPING = {
    "InferenceEndpointConfig": {
        "class_path": "sagemaker.hyperpod.inference.hp_endpoint.HPEndpoint",
        "metadata_handling": "separate"  # metadata handled separately
    },
    "JumpStartModel": {
        "class_path": "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.HPJumpStartEndpoint", 
        "metadata_handling": "separate"
    },
    "HyperPodPyTorchJob": {
        "class_path": "sagemaker.hyperpod.training.hyperpod_pytorch_job.HyperPodPytorchJob",
        "metadata_handling": "combined"  # metadata combined with spec
    }
}


def _get_handler_from_template_version(template_name, version, handler_name):
    """Dynamically import handler from a specific version of a template"""
    try:
        template_info = TEMPLATES[template_name]
        registry = template_info["registry"]
        
        if version not in registry:
            return None
            
        model_class = registry[version]
        module = sys.modules[model_class.__module__]
        return getattr(module, handler_name)
    except (ImportError, AttributeError):
        return None


# Template.field to handler mapping - avoids conflicts and works reliably
SPECIAL_FIELD_HANDLERS = {
    'hyp-pytorch-job.1.0.volume': _get_handler_from_template_version("hyp-pytorch-job", "1.0", "VOLUME_TYPE_HANDLER"),
    'hyp-pytorch-job.1.1.volume': _get_handler_from_template_version("hyp-pytorch-job", "1.1", "VOLUME_TYPE_HANDLER"),
}

USAGE_GUIDE_TEXT_CFN = """# SageMaker HyperPod CLI - Initialization Workflow

This document explains the initialization workflow and related commands for the SageMaker HyperPod CLI.

## Table of Contents
- [Init Command](#init-command)
- [Configure Command](#configure-command)
- [Reset Command](#reset-command)
- [Validate Command](#validate-command)
- [Create Command](#create-command)

## Init Command

The `init` command creates a scaffold for your HyperPod cluster stack configuration. It generates a `config.yaml` file, a CFN template (`cfn_params.jinja`), and a README with usage instructions.

### Basic Usage

```bash
hyp init <template-type>
```

Example:
```bash
hyp init cluster-stack
```

This creates the following files in your current directory:
```
├── config.yaml      # Configuration file with default values
├── cfn_params.jinja        # Cloudformation template with placeholders
└── README.md        # Usage instructions
```

### Specifying a Directory

You can specify a target directory for initialization:

```bash
hyp init cluster-stack <directory>
cd <directory>
```

### Edge Cases

**Re-initializing the same template:**
```
hyp init cluster-stack
⚠️ config.yaml already initialized as 'cluster-stack'.
Overwrite? [y/N]:
```

**Initializing with a different template:**
```
hyp init hyp-custom-endpoint
⚠️ Directory already initialized as 'cluster-stack'.
⚠️ It is highly unrecommended to initiate this directory with a different template.
⚠️ Recommended path is create a new folder and then init with 'hyp-custom-endpoint'.
If you insist, re-init as 'hyp-custom-endpoint' instead? [y/N]:
```

## Configure Command

The `configure` command updates specific fields in your `config.yaml` file without modifying other values.

```bash
hyp configure \
    --stack-name my-stack \
    --create-fsx-stack: False
```

## Reset Command

The `reset` command resets your `config.yaml` to default values while preserving the template type and namespace.

```bash
hyp reset
```

## Validate Command

The `validate` command checks your `config.yaml` against the JSON schema to ensure all required fields are present and valid.

```bash
hyp validate
```

## Create Command

The `create` command processes your configuration and creates the cluster stack. It injects values from `config.yaml` into the `cfn_params.jinja` template and creates a timestamped record in the `runs` directory.

```bash
hyp create
```

After submission, your directory structure will look like:
```
├── config.yaml
├── cfn_params.jinja
├── README.md
└── runs/
    └── 2025-07-16T15-22-03Z/
        ├── config.yaml  # Copy of the config used for this run
        └── cfn_params.yaml     # Generated Cloudformation template
```

## Workflow Example

A typical workflow might look like:

1. Initialize a new endpoint configuration:
   ```bash
   hyp init cluster-stack
   ```

2. Configure required parameters:
   ```bash
   hyp configure \
       --stack-name my-stack \
       --create-fsx-stack: False
   ```

3. Validate the configuration:
   ```bash
   hyp validate
   ```

4. Create the cluster stack request:
   ```bash
   hyp create
   ```

5. Check the status of your cluster stack:
   ```bash
   hyp list cluster-stack
   ```
"""

USAGE_GUIDE_TEXT_CRD = """# SageMaker HyperPod CLI - Initialization Workflow

This document explains the initialization workflow and related commands for the SageMaker HyperPod CLI.

## Table of Contents
- [Init Command](#init-command)
- [Configure Command](#configure-command)
- [Reset Command](#reset-command)
- [Validate Command](#validate-command)
- [Create Command](#create-command)

## Init Command

The `init` command creates a scaffold for your HyperPod endpoint configuration. It generates a `config.yaml` file, a Kubernetes template (`k8s.jinja`), and a README with usage instructions.

### Basic Usage

```bash
hyp init <template-type>
```

Example:
```bash
hyp init hyp-jumpstart-endpoint
```

This creates the following files in your current directory:
```
├── config.yaml      # Configuration file with default values
├── k8s.jinja        # Kubernetes template with placeholders
└── README.md        # Usage instructions
```

### Specifying a Directory

You can specify a target directory for initialization:

```bash
hyp init hyp-jumpstart-endpoint <directory>
cd <directory>
```

### Edge Cases

**Re-initializing the same template:**
```
hyp init hyp-jumpstart-endpoint
⚠️ config.yaml already initialized as 'hyp-jumpstart-endpoint'.
Overwrite? [y/N]:
```

**Initializing with a different template:**
```
hyp init hyp-custom-endpoint
⚠️ Directory already initialized as 'hyp-jumpstart-endpoint'.
⚠️ It is highly unrecommended to initiate this directory with a different template.
⚠️ Recommended path is create a new folder and then init with 'hyp-custom-endpoint'.
If you insist, re-init as 'hyp-custom-endpoint' instead? [y/N]:
```

## Configure Command

The `configure` command updates specific fields in your `config.yaml` file without modifying other values.

```bash
hyp configure \
    --instance-type ml.g5.12xlarge \
    --model-version 2.0.4
```

## Reset Command

The `reset` command resets your `config.yaml` to default values while preserving the template type and namespace.

```bash
hyp reset
```

## Validate Command

The `validate` command checks your `config.yaml` against the JSON schema to ensure all required fields are present and valid.

```bash
hyp validate
```

## Create Command

The `create` command processes your configuration and creates the endpoint. It injects values from `config.yaml` into the `k8s.jinja` template and creates a timestamped record in the `runs` directory.

```bash
hyp create
```

After submission, your directory structure will look like:
```
├── config.yaml
├── k8s.jinja
├── README.md
└── runs/
    └── 2025-07-16T15-22-03Z/
        ├── config.yaml  # Copy of the config used for this run
        └── k8s.yaml     # Generated Kubernetes manifest
```

## Workflow Example

A typical workflow might look like:

1. Initialize a new endpoint configuration:
   ```bash
   hyp init hyp-jumpstart-endpoint
   ```

2. Configure required parameters:
   ```bash
   hyp configure \
       --model-id meta-textgeneration-llama-3-70b \
       --instance-type ml.g5.8xlarge \
       --endpoint-name my-llama-endpoint
   ```

3. Validate the configuration:
   ```bash
   hyp validate
   ```

4. Create the endpoint creation request:
   ```bash
   hyp create
   ```

5. Check the status of your endpoint:
   ```bash
   hyp list hyp-jumpstart-endpoint
   ```
"""
