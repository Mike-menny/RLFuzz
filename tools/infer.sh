#!/bin/bash

# 检查参数数量
if [ $# -ne 4 ]; then
    echo "Usage: $0 <api1> <api2> <api1_info> <api2_info>"
    echo "Example: $0 'create_file' 'write_file' 'Creates a new file' 'Writes content to an existing file'"
    exit 1
fi

API1="$1"
API2="$2"
API1_INFO="$3"
API2_INFO="$4"

# 构建单行prompt
PROMPT="Please analyze if these two given APIs have semantic relationship, such as create-append or append-remove logic chains. API1: ${API1} - ${API1_INFO}. API2: ${API2} - ${API2_INFO}. If there is a semantic relationship, output only '1'. If not, output only '0'. Do not include any other text or explanation in your response."

# 一次性输入整个prompt
echo "$PROMPT" | CUDA_VISIBLE_DEVICES=4 swift infer \
    --model_type qwen2_5 \
    --model /workspace/models/QwenQwen2.5-Coder-7B-Instruct \
    --stream true \
    --infer_backend pt \
    --max_new_tokens 2048