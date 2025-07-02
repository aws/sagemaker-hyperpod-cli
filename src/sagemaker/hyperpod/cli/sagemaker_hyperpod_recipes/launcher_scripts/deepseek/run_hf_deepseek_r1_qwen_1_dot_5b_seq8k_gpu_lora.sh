#!/bin/bash

# Original Copyright (c), NVIDIA CORPORATION. Modifications © Amazon.com

#Users should setup their cluster type in /recipes_collection/config.yaml

SAGEMAKER_TRAINING_LAUNCHER_DIR=${SAGEMAKER_TRAINING_LAUNCHER_DIR:-"$(pwd)"}

HF_MODEL_NAME_OR_PATH="${HF_MODEL_NAME_OR_PATH}" # HuggingFace pretrained model name or path
HF_ACCESS_TOKEN="${HF_ACCESS_TOKEN}" # Optional HuggingFace access token

TRAIN_DIR="${TRAIN_DIR}" # Location of training dataset
VAL_DIR="${VAL_DIR}" # Location of validation dataset

EXP_DIR="${EXP_DIR}" # Location to save experiment info including logging, checkpoints, ect


HYDRA_FULL_ERROR=1 python3 "${SAGEMAKER_TRAINING_LAUNCHER_DIR}/main.py" \
    recipes=fine-tuning/deepseek/hf_deepseek_r1_distilled_qwen_1_dot_5b_seq8k_gpu_lora \
    base_results_dir="${SAGEMAKER_TRAINING_LAUNCHER_DIR}/results" \
    recipes.run.name="hf-deepseek-r1-distilled-qwen-1-dot-5b-lora" \
    recipes.exp_manager.exp_dir="$EXP_DIR" \
    recipes.trainer.num_nodes=1 \
    recipes.model.train_batch_size=4 \
    recipes.model.data.train_dir="$TRAIN_DIR" \
    recipes.model.data.val_dir="$VAL_DIR" \
    recipes.model.hf_model_name_or_path="$HF_MODEL_NAME_OR_PATH" \
    recipes.model.hf_access_token="$HF_ACCESS_TOKEN" \
