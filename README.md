Open in Docker container
Build the Project by using:
cd data/cJSON
./build.sh
download models. You can use modelscope(which is already installed in DockerFile) to download models by:
mkdir /workspace/models/
mkdir /workspace/models/Qwen3-8B
modelscope download --model Qwen/Qwen3-8B  --local_dir /workspace/models/Qwen3-8B
You can start running RL training. Remember to modeify the configuration in train.py, tools/dataset_pre.py, and tools/plugin.py. The project name, dataset path should be the same across different files.
python3 train.py
You can refer to the structure.txt to see the detailed explaination about the generated outputs.
Tips: If CUDA out of memory, try setting

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
To check which GPU is available, use:

gpustat -cpu -i 1

