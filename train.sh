#!/bin/bash

export CUDA_VISIBLE_DEVICES=0,1

swift rlhf \
    --rlhf_type grpo \
    --model_type qwen2_5 \
    --model models/QwenQwen2.5-Coder-7B-Instruct \
    --train_type lora \
    --lora_rank 8 \
    --lora_alpha 32 \
    --lora_dropout 0.1 \
    --lora_bias none \
    --custom_register_path tools/dataset_pre.py \
    --external_plugins tools/plugin.py \
    --reward_funcs external_countdown \
    --dataset datasets/prompt003.jsonl \
    --split_dataset_ratio 0.1 \
    --max_completion_length 4096 \
    --num_generations 4 \
    --device_map 'auto' \
    --per_device_train_batch_size 4 \
    --per_device_eval_batch_size 4 \
    --learning_rate 5e-7 \
    --torch_dtype bfloat16 \
    --eval_steps 50 \
    --save_steps 100 \
    --save_total_limit 2 \
    --gradient_accumulation_steps 1 \
    --num_train_epochs 20