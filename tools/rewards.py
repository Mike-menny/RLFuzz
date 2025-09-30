import json
import ast
import os
import re
from pathlib import Path
from tools.depot import Depot
from tools.compiler import Compiler
from tools.executor import Executor
from tools.correlation import analyze_correlation
from error_analysis.syntax_categorizer import syntax_categorize

class Reward:
    @staticmethod
    def save_log(project_name="cjson", epoch=None, completion=None, reward=-1, error=None, API_Called = [], kwargs=None):
        output_dir = f"/workspace/output/projects/{project_name}/harnesses/harness_{str(epoch).zfill(5)}/log_id_{str(completion).zfill(5)}.txt"
        Depot.create_path(output_dir) 
        with open(output_dir, "w") as f:
                f.write(f"reward: {reward}\nerror:\n{error}\nAPIs: {API_Called}\nprompt:\n{kwargs['messages'][completion]}")

    @staticmethod
    def syntax_error(project_name="cjson", epoch=None, completion=None, code = None):
        """
        Check for syntax errors in the generated code.
        Returns error
        """
        syntax_error = Compiler.compile_syntax(project_name, epoch, completion, std="c++17")
        if syntax_error is not None:
            return syntax_error
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

        data_path = f"/workspace/output/projects/{project_name}/data.json"
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        api_list = data.get("APIs", [])
        if not api_list:
            return [False, [f"cannot find API list in {data_path}"]]
        
        used_apis = []
        harness_dir = f"/workspace/output/projects/{project_name}/harnesses/harness_{str(epoch).zfill(5)}/id_{str(completion).zfill(5)}.cpp"
        
        if not os.path.exists(harness_dir):
            return [False,[f"{harness_dir} not exist"]]
        
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

        data_path = f"/workspace/output/projects/{project_name}/data.json"
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        api_list = data.get("APIs", [])
        if not api_list:
            return []
        
        used_apis = []
        harness_dir = f"/workspace/output/projects/{project_name}/harnesses/harness_{str(epoch).zfill(5)}/id_{str(completion).zfill(5)}.cpp"
        
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
        
        # Remove comments to avoid false positives
        # Remove single-line comments
        code_no_comments = re.sub(r'//.*', '', code)
        # Remove multi-line comments
        code_no_comments = re.sub(r'/\*.*?\*/', '', code_no_comments, flags=re.DOTALL)
        
        # Define loop patterns for C++ with more specific matching
        loop_patterns = [
            r'\bfor\s*\([^{};]*\)\s*\{',      # for loops with braces
            r'\bfor\s*\([^{};]*\)\s*[^{}]',   # for loops without braces (single statement)
            r'\bwhile\s*\([^{};]*\)\s*\{',    # while loops with braces
            r'\bwhile\s*\([^{};]*\)\s*[^{}]', # while loops without braces
            r'\bdo\s*\{',                     # do-while loops start
            r'\bdo\s*\n',                     # do-while loops with newline
        ]
        
        loop_count = 0
        
        # Count each type of loop
        for pattern in loop_patterns:
            matches = re.finditer(pattern, code_no_comments)
            loop_count += len(list(matches))
        
        # Also count range-based for loops (C++11)
        range_based_for = re.findall(r'\bfor\s*\([^{}]*:[^{}]*\)\s*\{', code_no_comments)
        loop_count += len(range_based_for)
        
        return loop_count * 0.5
    
    @staticmethod
    def dependency_check(api_list: list, context: list) -> float:
        """
        Analyze correlation between all consecutive APIs in a list and return the sum.
        
        Args:
            api_list: List of API names in the order they appear
            context: Context information list containing API definitions and type definitions
            
        Returns:
            float: Sum of correlation scores for all consecutive API pairs
        """
        if not api_list or len(api_list) < 2:
            print("Warning: API list must contain at least 2 APIs")
            return 0.0
        
        total_correlation = 0.0
        
        # Iterate through consecutive pairs
        for i in range(len(api_list) - 1):
            api1 = api_list[i]
            api2 = api_list[i + 1]
            
            print(f"\nAnalyzing pair {i+1}: {api1} -> {api2}")
            
            # Analyze correlation for this consecutive pair
            score = analyze_correlation(api1, api2, context)
            total_correlation += score
            
            print(f"Correlation score for {api1} -> {api2}: {score}")
        
        print(f"\nTotal correlation sum: {total_correlation}")
        return total_correlation

    

if __name__ == "__main__":
    print(Reward.API_coverage(project_name="cjson", epoch=1, completion=1))
    print(Reward.utility_check(project_name="cjson", epoch=1, completion=1))



    