from typing import Dict, Any
from swift.llm import DatasetMeta, MessagesPreprocessor, load_dataset, register_dataset
from tools.generator import APIGenerator
from tools.depot import Depot
from tools.analysis import FuncTypeAnalyzer
import os
import time

project_name = "cjson"
dataset_path = f"/workspace/datasets/prompt004.jsonl"

class CustomPreprocessor(MessagesPreprocessor):
    def preprocess(self, row: Dict[str, Any]):
        start_time = time.time()
        generator = APIGenerator(min_combination=5, max_combination=15)
        prompt = row
        project = project_name
        path = Depot.find_case_insensitive_path(f"output/build/{project}/lib")
        APIs = generator._extract_apis_from_lib(path)
        
        # combination = generator.generate_combination(path)
        combination = ""

        path = Depot.find_case_insensitive_path(f"output/build/{project}/include")
        analyzer = FuncTypeAnalyzer(path, APIs)
        context = analyzer.print_result()
        # context = analyzer.extract_all_custom()

        header_name = Depot.find_header_name(path)

        # generate prompt
        system = row["messages"][0]["content"]
        user = row["messages"][1]["content"]
        system_prompt = generator.generate_prompt(
            system, project, APIs, combination, context, path, header_name)
        user_prompt = generator.generate_prompt(
            user, project, APIs, combination, context, path, header_name)
        prompt['messages'][0]["content"] = system_prompt
        prompt['messages'][1]["content"] = user_prompt
        # print("\nGenerated prompt:")
        # print(prompt)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        print("Dataset processing took {:.2f} seconds".format(elapsed_time))
        return prompt


register_dataset(
    DatasetMeta(
        dataset_path = dataset_path,
        preprocess_func=CustomPreprocessor(),
    ))

if __name__ == '__main__':
    print("good")
    dataset = load_dataset([dataset_path])[0]
    print(f'{dataset}')