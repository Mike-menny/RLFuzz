import os
from tools.generator import APIGenerator
from tools.depot import Depot
from tools.analysis import FuncTypeAnalyzer
import json

project_name = "cjson"
dataset_path = f"/workspace/datasets/prompt004.jsonl"
os.environ['CUDA_VISIBLE_DEVICES'] = '3, 0'
model_path = '/workspace/models/checkpoint-600'

kwargs = {
    'per_device_train_batch_size': 6,
    'per_device_eval_batch_size': 6,
    'learning_rate': 5e-7,
    #'use_vllm': True,
    'eval_steps': 50,
    'save_steps': 100,
    'gradient_accumulation_steps': 1,
    'num_train_epochs': 50,
}

def grpo():
    from swift.llm import rlhf_main, RLHFArguments, infer_main, InferArguments
    Depot.build_project_structure(project_name=project_name)
    path = Depot.find_case_insensitive_path(f"output/build/{project_name}/lib")
    generator = APIGenerator(min_combination=5, max_combination=15)
    APIs = generator._extract_apis_from_lib(path)

    path = Depot.find_case_insensitive_path(f"output/build/{project_name}/include")
    analyzer = FuncTypeAnalyzer(path, APIs)
    context = analyzer.print_result()
    # context = analyzer.extract_all_custom()

    header_name = Depot.find_header_name(path)
    data = {
            "project_name": project_name,
            "dataset_path": dataset_path,
            "APIs":APIs,
            "context":context,
            "header_name":header_name
        }
    if not os.path.exists(f"/workspace/output/projects/{project_name}/data.json"):
        with open(f"/workspace/output/projects/{project_name}/data.json", 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    result = rlhf_main(
        RLHFArguments(
            custom_register_path='tools/dataset_pre.py',
            rlhf_type='grpo',
            model_type='qwen2_5',
            model=model_path,
            train_type='full',
            #lora_rank = 8,
            #lora_alpha = 32,
            #lora_dropout = 0.1,
            external_plugins = 'tools/plugin.py',
            reward_funcs = ['external_countdown'],
            dataset =dataset_path,
            split_dataset_ratio = 0.1,
            max_completion_length=4096,
            num_generations= 6,
            #deepspeed='zero2',
            **kwargs))
    last_model_checkpoint = result['last_model_checkpoint']
    infer_main(InferArguments(model=last_model_checkpoint, load_data_args=True, merge_lora=False))

if __name__ == '__main__':
    grpo()