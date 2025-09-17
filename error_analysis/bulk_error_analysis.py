import os
import csv

os.environ['CUDA_VISIBLE_DEVICES'] = '0,1,6'

from swift.llm import PtEngine, RequestConfig, InferRequest

model = '/workspace/models/Qwen3-32B'
model_type = 'qwen3'

# 加载推理引擎
engine = PtEngine(model, max_batch_size=8)  # 你的调用方式
request_config = RequestConfig(max_tokens=4096, temperature=0)

# 读取CSV文件并提取error列
infer_requests = []
errors = []
codes = []

with open('/workspace/comparasion/output/test.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        errors.append(row['error'])
        with open(row['target_file'], 'r') as code_file:
            code_content = code_file.read()
            codes.append(code_content)

# 创建推理请求
for error, code in zip(errors, codes):
    infer_requests.append(
        InferRequest(messages=[
            {
                'role': 'system', 
                'content': 'Analyze error given in the user message for cJSON fuzz drivers; output ONLY a Python list [0 or 1, \'type1\', \'type2\', ...] (multiple types allowed for more than one error); 0 = not cJSON-related, 1 = cJSON-related; allowed types: if 0, then \'non-API misuse error: related to fmemopen\', \'non-API misuse error: others\'; if 1, then \'header file include error: <cjson/cJSON.h> format\', \'header file include error: other include issues\', \'API not exist error\', \'wrong parameter type error\', \'API parameter length mismatch error\', \'library error: others\'; set 1 only if cJSON headers/types/functions/linkage are implicated; fmemopen is non-cJSON.'
            },
            {
                'role': 'user', 
                'content': f"code:\n{code} \nerror: \n{error}"
            }
        ])
    )

# 批量推理
if infer_requests:
    resp_list = engine.infer(infer_requests, request_config)
    
    # 输出所有结果
    for i, resp in enumerate(resp_list):
        print(f'response{i}: {resp.choices[0].message.content}')
else:
    print("No errors found in CSV file")