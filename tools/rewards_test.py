import json
import ast
import os
import re
from pathlib import Path
from tools.depot import Depot
from tools.compiler import Compiler
from tools.executor import Executor
from error_analysis.syntax_categorizer import syntax_categorize

class Reward:
    @staticmethod
    def save_log(project_name="cjson", epoch=None, completion=None, reward=-1, error=None, API_Called = [], kwargs=None):
        output_dir = f"output/projects/{project_name}/harnesses/harness_{str(epoch).zfill(5)}/log_id_{str(completion).zfill(5)}.txt"
        Depot.create_path(output_dir) 
        with open(output_dir, "w") as f:
                f.write(f"reward: {reward}\nerror:\n{error}\nAPIs: {API_Called}\n")

    @staticmethod
    def syntax_error(project_name="cjson", epoch=None, completion=None, code = None):
        """
        Check for syntax errors in the generated code.
        Returns error
        """
        
        syntax_error = Compiler.compile_syntax(project_name, epoch, completion, std="c++17")
        if syntax_error is not None:
            result = syntax_categorize(syntax_error, code)
            if result is None:
                return [syntax_error, None, "LLM call failed"]
            result[0] = ast.literal_eval(result[0])  # 将字符串转换为实际的列表
            if int(result[0][0]) == 1:
                return [syntax_error, results[0], results[1]]
            else:
                return [syntax_error, result[0], result[1]]
        return None
    
    @staticmethod
    def compilation_error(project_name="cjson", epoch=None, completion=None, additional_flags=None, debug=True):
        """
        Check for compilation errors in the generated code.
        Returns True if compilation error found, False otherwise.
        """
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
            return compilation_error
        return None
    
    @staticmethod
    def fuzz_error(project_name="cjson", epoch=None, completion=None):
        """
        Check for fuzzing errors when running the generated code.
        Returns True if fuzzing error found, False otherwise.
        """
        
        fuzz_error = Executor.run_fuzzer(project_name=project_name, epoch=epoch, completion=completion)
        
        if fuzz_error is not None:
            return fuzz_error
        return None
    
    @staticmethod
    def utility_check(project_name="cjson", epoch=None, completion=None):
        """
        Check if used minimum API amount.
        """

        data_path = f"output/projects/{project_name}/data.json"
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        api_list = data.get("APIs", [])
        if not api_list:
            return [False, []]
        
        used_apis = []
        harness_dir = f"output/projects/{project_name}/harnesses/harness_{str(epoch).zfill(5)}/id_{str(completion).zfill(5)}.cpp"
        
        if not os.path.exists(harness_dir):
            return [False,[]]
        
        with open(harness_dir, 'r') as f:
            content = f.read()
            
        # Find all API occurrences in the order they appear in the file
        for api in api_list:
            if api in content:
                used_apis.append(api)
        
        if used_apis and len(used_apis) > 3:
            return [True,used_apis]
        return [False,used_apis]

    @staticmethod
    def API_coverage(project_name="cjson", epoch=None, completion=None):
        """
        Check for API coverage in the generated code.
        """

        data_path = f"output/projects/{project_name}/data.json"
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        api_list = data.get("APIs", [])
        if not api_list:
            return []
        
        used_apis = []
        harness_dir = f"output/projects/{project_name}/harnesses/harness_{str(epoch).zfill(5)}/id_{str(completion).zfill(5)}.cpp"
        
        if not os.path.exists(harness_dir):
            return []
        
        with open(harness_dir, 'r') as f:
            content = f.read()
            
        # Find all API occurrences in the order they appear in the file
        for api in api_list:
            # Find all positions where this API appears
            positions = [m.start() for m in re.finditer(re.escape(api), content)]
            for pos in positions:
                used_apis.append((pos, api))
        
        # Sort by position and extract only the API names in order of appearance
        used_apis.sort(key=lambda x: x[0])
        ordered_apis = [api for pos, api in used_apis]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ordered_apis = []
        for api in ordered_apis:
            if api not in seen:
                seen.add(api)
                unique_ordered_apis.append(api)
        
        coverage = 10* max((len(unique_ordered_apis) / len(api_list) - 0.05), 0) if api_list else 0
        return [coverage, unique_ordered_apis]

    @staticmethod
    def count_loops(project_name="cjson", epoch=None, completion=None, code=None):
        """
        Count the number of loops in the provided C++ code and return count * 0.5.
        
        Args:
            project_name: Project name (unused in this function but kept for consistency)
            epoch: Epoch number (unused)
            completion: Completion number (unused)
            code: C++ source code string to analyze
            
        Returns:
            float: Number of loops multiplied by 0.5, or 0 if no code provided
        """
        if code is None:
            return 0.0
        
        # Simple and broad loop detection
        loop_patterns = [
            r'\bfor\s*\(',          # for loops - any for followed by (
            r'\bwhile\s*\(',        # while loops - any while followed by (
            r'\bdo\s*\{',           # do-while loops - do followed by {
            r'\bdo\s+',             # do-while loops - do followed by whitespace
        ]
        
        loop_count = 0
        
        # Count each type of loop with simple matching
        for pattern in loop_patterns:
            matches = re.findall(pattern, code)
            loop_count += len(matches)
        
        return loop_count * 0.5

if __name__ == "__main__":
    print(Reward.API_coverage(project_name="cjson", epoch=1, completion=1))
    print(Reward.utility_check(project_name="cjson", epoch=1, completion=1))



    