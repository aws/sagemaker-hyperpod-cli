# End-to-End Walkthrough - Amazon SageMaker HyperPod CLI and SDK
This folder contains a full, end-to-end walkthrough of the HyperPod CLI and SDK functionalities for cluster management, training job submission, inference deployments, task governance as well as spaces (IDE) deployment.

- [**Getting Started**](./00-getting-started/)
    - [00-setup.md](./00-getting-started/00-setup.md) - Instructions on how to install the CLI and setting up prerequisites you should have in your AWS account for running the examples.
    - [01-(optional)-cluster-creation.md](./00-getting-started/01-(optional)-cluster-creation.md) - Optional instructions on how to create a new HyperPod cluster using the CLI. Alternatively an existing cluster can be used for the examples, or one can be created using the console UI.
- [**Training Job Submission**](./01-training-job-submission/)
    - [00-pytorch-training-job.md](./01-training-job-submission/00-pytorch-training-job.md) - Instructions on how to create and submit a Qwen3 4B Lora fine-tuning job to the HyperPod cluster through the HyperPod CLI. Additionally, an example for instance failure recovery.
    - [01-pytorch-training-job-sdk.ipynb](./01-training-job-submission/01-pytorch-training-job-sdk.ipynb) - Instructions on how to to utilize the HyperPod Python SDK to create and submit the equivalent job to the HyperPod cluster.
- [**Inference Deployment**](./02-inference-deployment/)
    - [00-jumpstart-endpoint.md](./02-inference-deployment/00-jumpstart-endpoint.md) - Instructions on how to deploy models available on SageMaker JumpStart to the HyperPod cluster.
    - [01-custom-model-endpoint.md](./02-inference-deployment/01-custom-model-endpoint.md) - Instructions on how to deploy a custom model from an S3 bucket (TinyLlama) to the HyperPod cluster and how to utilize the autoscaling functionality.
- [**Task Governance**](./03-task-governance/)
    - [00-task-governance.md](./03-task-governance/00-task-governance.md) - Instructions on multiple scenarios for task governance, including borrowing idle compute, reclaiming guaranteed compute as well as preempting lower priority tasks.
- [**Spaces**](./04-spaces/)
    - [00-create-space.md](./04-spaces/00-create-space.md) - Instructions on how to set up the SageMaker Spaces functionality for hosting IDEs and notebooks on the HyperPod cluster.  
