# PyTorch Training Job - HyperPod CLI End-to-End Walkthrough

This folder contains the following files:
- [00-pytorch-training-job.md](00-pytorch-training-job.md) - Instructions on how to create and submit a **Qwen3 4B Lora** fine-tuning job to the HyperPod cluster through the HyperPod CLI. Additionally, an example for instance failure recovery.
- [01-pytorch-training-job-sdk.ipynb](01-pytorch-training-job-sdk.ipynb) - Instructions on how to to utilize the HyperPod Python SDK to create and submit the equivalent job to the HyperPod cluster.
- [02-recipe-job-cli.ipynb](02-recipe-job-cli.ipynb) - Instructions on how to submit a fine-tuning job using the HyperPod CLI recipe job experience (`hyp-recipe-job`). Recipes are pre-built fine-tuning configurations fetched from SageMaker JumpStart Hub — no YAML authoring required.