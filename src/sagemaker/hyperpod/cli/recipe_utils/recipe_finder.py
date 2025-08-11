#!/usr/bin/env python3
"""
HyperPod Recipe Finder
A simple tool to find recipes based on table columns from the README.md
"""

import argparse
import json
import sys
from typing import Dict, List, Any, Optional

class Recipe:
    def __init__(self, source: str, model: str, size: str, seq_length: int, 
                 nodes: int, instance: str, accelerator: str, recipe_path: str, 
                 script_path: str, task: str = "pre-training", method: str = None):
        self.source = source
        self.model = model
        self.size = size
        self.seq_length = seq_length
        self.nodes = nodes
        self.instance = instance
        self.accelerator = accelerator
        self.recipe_path = recipe_path
        self.script_path = script_path
        self.task = task
        self.method = method

# Load recipes from GitHub README tables
def load_recipes():
    # Pre-training recipes
    pre_training = [
        # Llama 3.2 models
        Recipe("Hugging Face", "Llama 3.2", "11b", 8192, 4, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_2_11b_seq8k_gpu_p5x4_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_2_11b_seq8k_gpu_p5x4_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.2", "90b", 8192, 32, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_2_90b_seq8k_gpu_p5x32_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_2_90b_seq8k_gpu_p5x32_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.2", "1b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_2_1b_seq8k_gpu_p5x1_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_2_1b_seq8k_gpu_p5x1_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.2", "3b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_2_3b_seq8k_gpu_p5x1_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_2_3b_seq8k_gpu_p5x1_pretrain.sh"),
        
        # Llama 3.1 models
        Recipe("Hugging Face", "Llama 3.1", "70b", 16384, 32, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_70b_seq16k_gpu_p5x32_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_70b_seq16k_gpu_p5x32_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.1", "70b", 16384, 64, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_70b_seq16k_gpu_p5x64_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_70b_seq16k_gpu_p5x64_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.1", "70b", 16384, 128, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_70b_seq16k_gpu_p5x128_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_70b_seq16k_gpu_p5x128_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.1", "70b", 8192, 32, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_70b_seq8k_gpu_p5x32_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_70b_seq8k_gpu_p5x32_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.1", "70b", 8192, 64, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_70b_seq8k_gpu_p5x64_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_70b_seq8k_gpu_p5x64_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.1", "70b", 8192, 128, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_70b_seq8k_gpu_p5x128_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_70b_seq8k_gpu_p5x128_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.1", "8b", 16384, 16, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_8b_seq16k_gpu_p5x16_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_8b_seq16k_gpu_p5x16_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.1", "8b", 16384, 32, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_8b_seq16k_gpu_p5x32_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_8b_seq16k_gpu_p5x32_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.1", "8b", 8192, 16, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_8b_seq8k_gpu_p5x16_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_8b_seq8k_gpu_p5x16_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3.1", "8b", 8192, 32, "ml.p5.48xlarge", "GPU H100", 
               "llama/hf_llama3_8b_seq8k_gpu_p5x32_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_8b_seq8k_gpu_p5x32_pretrain.sh"),
        
        # Llama 3 models
        Recipe("Hugging Face", "Llama 3", "70b", 8192, 16, "ml.trn1.32xlarge", "TRN", 
               "llama/hf_llama3_70b_seq8k_trn1x16_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_70b_seq8k_trn1x16_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3", "8b", 8192, 4, "ml.trn1.32xlarge", "TRN", 
               "llama/hf_llama3_8b_seq8k_trn1x4_pretrain.yaml",
               "launcher_scripts/llama/run_hf_llama3_8b_seq8k_trn1x4_pretrain.sh"),
        Recipe("Hugging Face", "Llama 3", "70b", 8192, 1, "ml.p4d.24xlarge", "GPU A100", 
               "llama/p4_hf_llama3_70b_seq8k_gpu.yaml",
               "launcher_scripts/llama/p4_run_hf_llama3_70b_seq8k_gpu.sh"),
        
        # Megatron
        Recipe("Megatron", "Llama 3.1", "8b", 8192, 16, "ml.p5.48xlarge", "GPU H100", 
               "llama/megatron_llama3_1_8b_nemo.yaml", "-"),
        
        # Mistral models
        Recipe("Hugging Face", "Mistral", "7b", 16384, 16, "ml.p5.48xlarge", "GPU H100", 
               "mistral/hf_mistral_7b_seq16k_gpu_p5x16_pretrain.yaml",
               "launcher_scripts/mistral/run_hf_mistral_7b_seq16k_gpu_p5x16_pretrain.sh"),
        Recipe("Hugging Face", "Mistral", "7b", 16384, 32, "ml.p5.48xlarge", "GPU H100", 
               "mistral/hf_mistral_7b_seq16k_gpu_p5x32_pretrain.yaml",
               "launcher_scripts/mistral/run_hf_mistral_7b_seq16k_gpu_p5x32_pretrain.sh"),
        Recipe("Hugging Face", "Mistral", "7b", 8192, 16, "ml.p5.48xlarge", "GPU H100", 
               "mistral/hf_mistral_7b_seq8k_gpu_p5x16_pretrain.yaml",
               "launcher_scripts/mistral/run_hf_mistral_7b_seq8k_gpu_p5x16_pretrain.sh"),
        Recipe("Hugging Face", "Mistral", "7b", 8192, 32, "ml.p5.48xlarge", "GPU H100", 
               "mistral/hf_mistral_7b_seq8k_gpu_p5x32_pretrain.yaml",
               "launcher_scripts/mistral/run_hf_mistral_7b_seq8k_gpu_p5x32_pretrain.sh"),
        
        # Mixtral models
        Recipe("Hugging Face", "Mixtral", "22b", 16384, 32, "ml.p5.48xlarge", "GPU H100", 
               "mixtral/hf_mixtral_8x22b_seq16k_gpu_p5x32_pretrain.yaml",
               "launcher_scripts/mixtral/run_hf_mixtral_8x22b_seq16k_gpu_p5x32_pretrain.sh"),
        Recipe("Hugging Face", "Mixtral", "22b", 16384, 64, "ml.p5.48xlarge", "GPU H100", 
               "mixtral/hf_mixtral_8x22b_seq16k_gpu_p5x64_pretrain.yaml",
               "launcher_scripts/mixtral/run_hf_mixtral_8x22b_seq16k_gpu_p5x64_pretrain.sh"),
        Recipe("Hugging Face", "Mixtral", "22b", 16384, 128, "ml.p5.48xlarge", "GPU H100", 
               "mixtral/hf_mixtral_8x22b_seq16k_gpu_p5x128_pretrain.yaml",
               "launcher_scripts/mixtral/run_hf_mixtral_8x22b_seq16k_gpu_p5x128_pretrain.sh"),
        Recipe("Hugging Face", "Mixtral", "22b", 8192, 32, "ml.p5.48xlarge", "GPU H100", 
               "mixtral/hf_mixtral_8x22b_seq8k_gpu_p5x32_pretrain.yaml",
               "launcher_scripts/mixtral/run_hf_mixtral_8x22b_seq8k_gpu_p5x32_pretrain.sh"),
        Recipe("Hugging Face", "Mixtral", "22b", 8192, 64, "ml.p5.48xlarge", "GPU H100", 
               "mixtral/hf_mixtral_8x22b_seq8k_gpu_p5x64_pretrain.yaml",
               "launcher_scripts/mixtral/run_hf_mixtral_8x22b_seq8k_gpu_p5x64_pretrain.sh"),
        Recipe("Hugging Face", "Mixtral", "22b", 8192, 128, "ml.p5.48xlarge", "GPU H100", 
               "mixtral/hf_mixtral_8x22b_seq8k_gpu_p5x128_pretrain.yaml",
               "launcher_scripts/mixtral/run_hf_mixtral_8x22b_seq8k_gpu_p5x128_pretrain.sh"),
        Recipe("Hugging Face", "Mixtral", "7b", 16384, 16, "ml.p5.48xlarge", "GPU H100", 
               "mixtral/hf_mixtral_8x7b_seq16k_gpu_p5x16_pretrain.yaml",
               "launcher_scripts/mixtral/run_hf_mixtral_8x7b_seq16k_gpu_p5x16_pretrain.sh"),
        Recipe("Hugging Face", "Mixtral", "7b", 16384, 32, "ml.p5.48xlarge", "GPU H100", 
               "mixtral/hf_mixtral_8x7b_seq16k_gpu_p5x32_pretrain.yaml",
               "launcher_scripts/mixtral/run_hf_mixtral_8x7b_seq16k_gpu_p5x32_pretrain.sh"),
        Recipe("Hugging Face", "Mixtral", "7b", 8192, 16, "ml.p5.48xlarge", "GPU H100", 
               "mixtral/hf_mixtral_8x7b_seq8k_gpu_p5x16_pretrain.yaml",
               "launcher_scripts/mixtral/run_hf_mixtral_8x7b_seq8k_gpu_p5x16_pretrain.sh"),
        Recipe("Hugging Face", "Mixtral", "7b", 8192, 32, "ml.p5.48xlarge", "GPU H100", 
               "mixtral/hf_mixtral_8x7b_seq8k_gpu_p5x32_pretrain.yaml",
               "launcher_scripts/mixtral/run_hf_mixtral_8x7b_seq8k_gpu_p5x32_pretrain.sh"),
    ]
    
    # Fine-tuning recipes
    fine_tuning = [
        # Llama models
        Recipe("Hugging Face", "Llama 3", "8b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_8b_seq8k_gpu_lora.yaml",
               "launcher_scripts/llama/run_hf_llama3_8b_seq8k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Llama 3", "8b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_8b_seq8k_gpu_fine_tuning.yaml",
               "launcher_scripts/llama/run_hf_llama3_8b_seq8k_gpu_fine_tuning.sh", "fine-tuning", "Full"),
        Recipe("Hugging Face", "Llama 3", "8b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_8b_seq8k_gpu_dpo.yaml",
               "launcher_scripts/llama/run_hf_llama3_8b_seq8k_gpu_dpo.sh", "fine-tuning", "DPO"),
        Recipe("Hugging Face", "Llama 3", "8b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_8b_seq8k_gpu_ppo.yaml",
               "launcher_scripts/llama/run_hf_llama3_8b_seq8k_gpu_ppo.sh", "fine-tuning", "PPO"),
        Recipe("Hugging Face", "Llama 3", "8b", 16384, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_8b_seq16k_gpu_lora.yaml",
               "launcher_scripts/llama/run_hf_llama3_8b_seq16k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Llama 3", "8b", 16384, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_8b_seq16k_gpu_fine_tuning.yaml",
               "launcher_scripts/llama/run_hf_llama3_8b_seq16k_gpu_fine_tuning.sh", "fine-tuning", "Full"),
        Recipe("Hugging Face", "Llama 3", "70b", 8192, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_70b_seq8k_gpu_lora.yaml",
               "launcher_scripts/llama/run_hf_llama3_70b_seq8k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Llama 3", "70b", 8192, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_70b_seq8k_gpu_fine_tuning.yaml",
               "launcher_scripts/llama/run_hf_llama3_70b_seq8k_gpu_fine_tuning.sh", "fine-tuning", "Full"),
        Recipe("Hugging Face", "Llama 3", "70b", 16384, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_70b_seq16k_gpu_lora.yaml",
               "launcher_scripts/llama/run_hf_llama3_70b_seq16k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Llama 3", "70b", 16384, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_70b_seq16k_gpu_fine_tuning.yaml",
               "launcher_scripts/llama/run_hf_llama3_70b_seq16k_gpu_fine_tuning.sh", "fine-tuning", "Full"),
        Recipe("Hugging Face", "Llama 3.3", "70b", 8192, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_3_70b_seq8k_gpu_lora.yaml",
               "launcher_scripts/llama/run_hf_llama3_3_70b_seq8k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Llama 3.3", "70b", 8192, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_3_70b_seq8k_gpu_fine_tuning.yaml",
               "launcher_scripts/llama/run_hf_llama3_3_70b_seq8k_gpu_fine_tuning.sh", "fine-tuning", "Full"),
        Recipe("Hugging Face", "Llama 3.3", "70b", 16384, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_3_70b_seq16k_gpu_lora.yaml",
               "launcher_scripts/llama/run_hf_llama3_3_70b_seq16k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Llama 3.3", "70b", 16384, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama3_3_70b_seq16k_gpu_fine_tuning.yaml",
               "launcher_scripts/llama/run_hf_llama3_3_70b_seq16k_gpu_fine_tuning.sh", "fine-tuning", "Full"),
        Recipe("Hugging Face", "Llama 4", "17b", 8192, 4, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama4_17b_16e_seq8k_gpu_lora_text_to_text.yaml",
               "launcher_scripts/llama/run_hf_llama4_17b_16e_seq8k_gpu_lora_text_to_text.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Llama 4", "17b", 8192, 4, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama4_17b_16e_seq8k_gpu_lora_multimodal_finetuning.yaml",
               "launcher_scripts/llama/run_hf_llama4_17b_16e_seq8k_gpu_lora_multimodal_finetuning.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Llama 4", "17b", 4096, 4, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama4_17b_16e_seq4k_gpu_lora_text_to_text.yaml",
               "launcher_scripts/llama/run_hf_llama4_17b_16e_seq4k_gpu_lora_text_to_text.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Llama 4", "17b", 4096, 4, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/llama/hf_llama4_17b_16e_seq4k_gpu_lora_multimodal_finetuning.yaml",
               "launcher_scripts/llama/run_hf_llama4_17b_16e_seq4k_gpu_lora_multimodal_finetuning.sh", "fine-tuning", "LoRA"),
        
        # DeepSeek models
        Recipe("Hugging Face", "DeepSeek R1", "8b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/deepseek/hf_deepseek_r1_distilled_llama_8b_seq8k_gpu_lora.yaml",
               "launcher_scripts/deepseek/run_hf_deepseek_r1_distilled_llama_8b_seq8k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "DeepSeek R1", "8b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/deepseek/hf_deepseek_r1_distilled_llama_8b_seq8k_gpu_fine_tuning.yaml",
               "launcher_scripts/deepseek/run_hf_deepseek_r1_distilled_llama_8b_seq8k_gpu_fine_tuning.sh", "fine-tuning", "Full"),
        Recipe("Hugging Face", "DeepSeek R1", "8b", 16384, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/deepseek/hf_deepseek_r1_distilled_llama_8b_seq16k_gpu_lora.yaml",
               "launcher_scripts/deepseek/run_hf_deepseek_r1_distilled_llama_8b_seq16k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "DeepSeek R1", "8b", 16384, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/deepseek/hf_deepseek_r1_distilled_llama_8b_seq16k_gpu_fine_tuning.yaml",
               "launcher_scripts/deepseek/run_hf_deepseek_r1_distilled_llama_8b_seq16k_gpu_fine_tuning.sh", "fine-tuning", "Full"),
        Recipe("Hugging Face", "DeepSeek R1", "70b", 8192, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/deepseek/hf_deepseek_r1_distilled_llama_70b_seq8k_gpu_lora.yaml",
               "launcher_scripts/deepseek/run_hf_deepseek_r1_distilled_llama_70b_seq8k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "DeepSeek R1", "70b", 8192, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/deepseek/hf_deepseek_r1_distilled_llama_70b_seq8k_gpu_fine_tuning.yaml",
               "launcher_scripts/deepseek/run_hf_deepseek_r1_distilled_llama_70b_seq8k_gpu_fine_tuning.sh", "fine-tuning", "Full"),
        Recipe("Hugging Face", "DeepSeek R1", "70b", 16384, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/deepseek/hf_deepseek_r1_distilled_llama_70b_seq16k_gpu_lora.yaml",
               "launcher_scripts/deepseek/run_hf_deepseek_r1_distilled_llama_70b_seq16k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "DeepSeek R1", "70b", 16384, 8, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/deepseek/hf_deepseek_r1_distilled_llama_70b_seq16k_gpu_fine_tuning.yaml",
               "launcher_scripts/deepseek/run_hf_deepseek_r1_distilled_llama_70b_seq16k_gpu_fine_tuning.sh", "fine-tuning", "Full"),
        Recipe("Hugging Face", "DeepSeek R1", "671b", 8192, 32, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/deepseek/hf_deepseek_r1_671b_seq8k_gpu_qlora.yaml",
               "launcher_scripts/deepseek/run_hf_deepseek_r1_671b_seq8k_gpu_qlora.sh", "fine-tuning", "QLoRA"),
        Recipe("Hugging Face", "DeepSeek R1", "671b", 8192, 32, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/deepseek/hf_deepseek_r1_671b_seq8k_gpu_lora.yaml",
               "launcher_scripts/deepseek/run_hf_deepseek_r1_671b_seq8k_gpu_lora.sh", "fine-tuning", "LoRA"),
        
        # Nova models
        Recipe("Hugging Face", "Nova Micro", "1.8b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/nova/hf_nova_micro_1_8b_seq8k_gpu_lora.yaml",
               "launcher_scripts/nova/run_hf_nova_micro_1_8b_seq8k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Nova Lite", "7b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/nova/hf_nova_lite_7b_seq8k_gpu_lora.yaml",
               "launcher_scripts/nova/run_hf_nova_lite_7b_seq8k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Nova Pro", "12b", 8192, 2, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/nova/hf_nova_pro_12b_seq8k_gpu_lora.yaml",
               "launcher_scripts/nova/run_hf_nova_pro_12b_seq8k_gpu_lora.sh", "fine-tuning", "LoRA"),
        
        # Mistral models
        Recipe("Hugging Face", "Mistral", "7b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/mistral/hf_mistral_7b_seq8k_gpu_lora.yaml",
               "launcher_scripts/mistral/run_hf_mistral_7b_seq8k_gpu_lora.sh", "fine-tuning", "LoRA"),
        Recipe("Hugging Face", "Mistral", "7b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "fine-tuning/mistral/hf_mistral_7b_seq8k_gpu_fine_tuning.yaml",
               "launcher_scripts/mistral/run_hf_mistral_7b_seq8k_gpu_fine_tuning.sh", "fine-tuning", "Full"),
    ]
    
    # Evaluation recipes
    evaluation = [
        # Llama models
        Recipe("Hugging Face", "Llama 3", "8b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "evaluation/llama/hf_llama3_8b_seq8k_gpu_eval.yaml",
               "launcher_scripts/evaluation/run_hf_llama3_8b_seq8k_gpu_eval.sh", "evaluation"),
        Recipe("Hugging Face", "Llama 3", "70b", 8192, 8, "ml.p5.48xlarge", "GPU H100", 
               "evaluation/llama/hf_llama3_70b_seq8k_gpu_eval.yaml",
               "launcher_scripts/evaluation/run_hf_llama3_70b_seq8k_gpu_eval.sh", "evaluation"),
        Recipe("Hugging Face", "Llama 4", "17b", 8192, 4, "ml.p5.48xlarge", "GPU H100", 
               "evaluation/llama/hf_llama4_17b_seq8k_gpu_eval.yaml",
               "launcher_scripts/evaluation/run_hf_llama4_17b_seq8k_gpu_eval.sh", "evaluation"),
        
        # DeepSeek models
        Recipe("Hugging Face", "DeepSeek R1", "8b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "evaluation/deepseek/hf_deepseek_r1_8b_seq8k_gpu_eval.yaml",
               "launcher_scripts/evaluation/run_hf_deepseek_r1_8b_seq8k_gpu_eval.sh", "evaluation"),
        Recipe("Hugging Face", "DeepSeek R1", "70b", 8192, 8, "ml.p5.48xlarge", "GPU H100", 
               "evaluation/deepseek/hf_deepseek_r1_70b_seq8k_gpu_eval.yaml",
               "launcher_scripts/evaluation/run_hf_deepseek_r1_70b_seq8k_gpu_eval.sh", "evaluation"),
        
        # Mistral models
        Recipe("Hugging Face", "Mistral", "7b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "evaluation/mistral/hf_mistral_7b_seq8k_gpu_eval.yaml",
               "launcher_scripts/evaluation/run_hf_mistral_7b_seq8k_gpu_eval.sh", "evaluation"),
        
        # Nova models
        Recipe("Hugging Face", "Nova Micro", "1.8b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "evaluation/nova/hf_nova_micro_1_8b_seq8k_gpu_eval.yaml",
               "launcher_scripts/evaluation/run_hf_nova_micro_1_8b_seq8k_gpu_eval.sh", "evaluation"),
        Recipe("Hugging Face", "Nova Lite", "7b", 8192, 1, "ml.p5.48xlarge", "GPU H100", 
               "evaluation/nova/hf_nova_lite_7b_seq8k_gpu_eval.yaml",
               "launcher_scripts/evaluation/run_hf_nova_lite_7b_seq8k_gpu_eval.sh", "evaluation"),
        Recipe("Hugging Face", "Nova Pro", "12b", 8192, 2, "ml.p5.48xlarge", "GPU H100", 
               "evaluation/nova/hf_nova_pro_12b_seq8k_gpu_eval.yaml",
               "launcher_scripts/evaluation/run_hf_nova_pro_12b_seq8k_gpu_eval.sh", "evaluation"),
    ]
    
    return pre_training + fine_tuning + evaluation

def get_unique_values(recipes, attribute):
    """Get unique values for a specific attribute across all recipes."""
    values = set()
    for recipe in recipes:
        value = getattr(recipe, attribute, None)
        if value is not None:
            values.add(value)
    return sorted(values)

def filter_recipes(recipes, **filters):
    """Filter recipes based on provided criteria."""
    filtered = recipes
    
    for attr, value in filters.items():
        if value is None:
            continue
        if attr == "min_nodes":
            filtered = [r for r in filtered if r.nodes >= value]
        elif attr == "max_nodes":
            filtered = [r for r in filtered if r.nodes <= value]
        elif attr == "min_seq_length":
            filtered = [r for r in filtered if r.seq_length >= value]
        elif attr == "max_seq_length":
            filtered = [r for r in filtered if r.seq_length <= value]
        else:
            # Use substring matching for string attributes
            filtered = [r for r in filtered if value.lower() in str(getattr(r, attr, "")).lower()]
    
    return filtered

def print_recipe_table(recipes):
    """Print recipes in a formatted table."""
    if not recipes:
        print("No recipes found matching your criteria.")
        return
    
    # Print header
    header = f"{'Source':<15} {'Model':<12} {'Size':<6} {'Seq Len':<8} {'Nodes':<6} {'Instance':<16} {'Accelerator':<12} {'Task':<12}"
    if any(recipe.method for recipe in recipes):
        header += f" {'Method':<8}"
    header += " Recipe Path"
    print(header)
    print("-" * 130)
    
    # Print each recipe
    for recipe in recipes:
        line = f"{recipe.source:<15} {recipe.model:<12} {recipe.size:<6} {recipe.seq_length:<8} {recipe.nodes:<6} {recipe.instance:<16} {recipe.accelerator:<12} {recipe.task:<12}"
        if hasattr(recipe, 'method') and recipe.method:
            line += f" {recipe.method:<8}"
        line += f" {recipe.recipe_path}"
        print(line)

def main():
    recipes = load_recipes()
    
    parser = argparse.ArgumentParser(description="Find HyperPod recipes based on criteria")
    
    # Add filters based on table columns
    parser.add_argument("--source", choices=get_unique_values(recipes, "source"), help="Filter by source")
    parser.add_argument("--model", choices=get_unique_values(recipes, "model"), help="Filter by model")
    parser.add_argument("--size", choices=get_unique_values(recipes, "size"), help="Filter by model size")
    parser.add_argument("--min-seq-length", type=int, help="Minimum sequence length")
    parser.add_argument("--max-seq-length", type=int, help="Maximum sequence length")
    parser.add_argument("--min-nodes", type=int, help="Minimum number of nodes")
    parser.add_argument("--max-nodes", type=int, help="Maximum number of nodes")
    parser.add_argument("--instance", choices=get_unique_values(recipes, "instance"), help="Filter by instance type")
    parser.add_argument("--accelerator", choices=get_unique_values(recipes, "accelerator"), help="Filter by accelerator")
    parser.add_argument("--task", choices=get_unique_values(recipes, "task"), help="Filter by task (pre-training, fine-tuning, evaluation)")
    parser.add_argument("--method", choices=get_unique_values(recipes, "method"), help="Filter by fine-tuning method")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--list-values", choices=["source", "model", "size", "instance", "accelerator", "task", "method"], 
                        help="List all unique values for a specific attribute")
    parser.add_argument("--count", action="store_true", help="Show only the count of matching recipes")
    
    args = parser.parse_args()
    
    # If list-values is specified, print unique values and exit
    if args.list_values:
        values = get_unique_values(recipes, args.list_values)
        print(f"Available {args.list_values} values:")
        for value in values:
            print(f"  - {value}")
        return
    
    # Filter recipes based on provided arguments
    filtered_recipes = filter_recipes(
        recipes,
        source=args.source,
        model=args.model,
        size=args.size,
        min_seq_length=args.min_seq_length,
        max_seq_length=args.max_seq_length,
        min_nodes=args.min_nodes,
        max_nodes=args.max_nodes,
        instance=args.instance,
        accelerator=args.accelerator,
        task=args.task,
        method=args.method
    )
    
    # Output results
    if args.count:
        print(f"Found {len(filtered_recipes)} recipes matching your criteria.")
    elif args.json:
        result = []
        for recipe in filtered_recipes:
            r = {attr: getattr(recipe, attr) for attr in dir(recipe) 
                 if not attr.startswith('_') and not callable(getattr(recipe, attr))}
            result.append(r)
        print(json.dumps(result, indent=2, default=str))
    else:
        print_recipe_table(filtered_recipes)
        print(f"\nFound {len(filtered_recipes)} recipes matching your criteria.")

# if __name__ == "__main__":
#     main()