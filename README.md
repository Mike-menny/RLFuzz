Open in Docker container

find your ms-swift package path and open the grpo_trainer.py. If you don't know, try:

/usr/local/lib/python3.10/dist-packages/swift/trainers/rlhf_trainer/grpo_trainer.py

then append this to line 1022(after"advantages /= (std_grouped_rewards + 1e-4)"):
```python
nan_mask = torch.isnan(rewards)
advantages[nan_mask] = 0.0
```
and comment out line 925-928:
```python
#row_reward_kwargs = {key: value[nan_row_idx] for key, value in reward_kwargs.items()}
            #row_reward_kwargs['completion'] = completions[nan_row_idx]
            #logger.warning(f'All reward functions returned None for the following kwargs: {row_reward_kwargs}. '
            #               'Please ensure that at least one reward function returns a valid reward.')
```

Build the Project by using:
```Bash
cd data/cJSON
./build.sh
```
download models. You can use modelscope(which is already installed in DockerFile) to download models by:
```Bash
mkdir /workspace/models/
mkdir /workspace/models/Qwen3-8B
modelscope download --model Qwen/Qwen3-8B  --local_dir /workspace/models/Qwen3-8B
```
You can start running RL training. Remember to modeify the configuration in train.py, tools/dataset_pre.py, and tools/plugin.py. The project name, dataset path should be the same across different files.
```Bash
python3 train.py
```
You can refer to the structure.txt to see the detailed explaination about the generated outputs.
Tips: If CUDA out of memory, try setting
```Bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```
To check which GPU is available, use:
```Bash
gpustat -cpu -i 1
```
