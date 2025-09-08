import json
import os
from pathlib import Path
from tools.depot import Depot
from tools.compiler import Compiler
from tools.executor import Executor

class Reward:
    @staticmethod
    def save_log(project_name="cjson", epoch=None, completion=None, reward=-1, error=None, API_Called = [], kwargs=None):
        output_dir = f"/workspace/output/projects/{project_name}/harnesses/harness_{str(epoch).zfill(5)}/log_id_{str(completion).zfill(5)}.txt"
        Depot.create_path(output_dir) 
        with open(output_dir, "w") as f:
                f.write(f"reward: {reward}\nerror:\n{error}\nAPIs: {API_Called}\nprompt:\n{kwargs['messages'][completion]}")

    @staticmethod
    def syntax_error(project_name="cjson", epoch=None, completion=None, rewards=None):
        """
        Check for syntax errors in the generated code.
        Returns error
        """
        if rewards is None:
            rewards = []
        
        syntax_error = Compiler.compile_syntax(project_name, epoch, completion, std="c++17")
        if syntax_error is not None:
            rewards.append(-1.0)
            return syntax_error
        return None
    
    @staticmethod
    def compilation_error(project_name="cjson", epoch=None, completion=None, rewards=None, additional_flags=None, debug=True):
        """
        Check for compilation errors in the generated code.
        Returns True if compilation error found, False otherwise.
        """
        if rewards is None:
            rewards = []
        if additional_flags is None:
            additional_flags = ["-O2"]
        
        compilation_error = Compiler.compile_fuzzer(
            project_name=project_name,
            epoch=epoch,
            completion=completion,
            additional_flags=additional_flags,
            debug=debug
        )
        
        if compilation_error is not None:
            rewards.append(-0.04)
            return compilation_error
        return None
    
    @staticmethod
    def fuzz_error(project_name="cjson", epoch=None, completion=None, rewards=None):
        """
        Check for fuzzing errors when running the generated code.
        Returns True if fuzzing error found, False otherwise.
        """
        if rewards is None:
            rewards = []
        
        fuzz_error = Executor.run_fuzzer(project_name=project_name, epoch=epoch, completion=completion)
        
        if fuzz_error is not None:
            rewards.append(-0.008)
            return fuzz_error
        return None
    
    @staticmethod
    def API_coverage(project_name="cjson", epoch=None, completion=None, rewards=None):
        """
        Check for API coverage in the generated code.
        """
        if rewards is None:
            rewards = []

        data_path = f"/workspace/output/projects/{project_name}/data.json"
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        api_list = data.get("APIs", [])
        if not api_list:
            return []
        
        used_apis = set()
        harness_dir = f"/workspace/output/projects/{project_name}/harnesses/harness_{str(epoch).zfill(5)}/id_{str(completion).zfill(5)}.cpp"
        
        if not os.path.exists(harness_dir):
            return []
        
                
        with open(harness_dir, 'r') as f:
            content = f.read()
            for api in api_list:
                if api in content:
                    used_apis.add(api)
        
        coverage = len(used_apis) / len(api_list) if api_list else 0
        rewards.append(coverage*10)
        return list(used_apis)



    