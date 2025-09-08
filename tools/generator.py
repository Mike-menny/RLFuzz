import os
import subprocess
import random
from typing import List
from tools.depot import Depot  
from tools.analysis import FuncTypeAnalyzer

class APIGenerator:
    def __init__(self, min_combination=3, max_combination=10):
        """
        初始化API生成器
        
        Args:
            min_combination (int): 随机组合的最小API数量
            max_combination (int): 随机组合的最大API数量
        """
        self.min_combination = min_combination
        self.max_combination = max_combination
    
    def _extract_apis_from_lib(self, lib_path: str) -> List[str]:
        """从库文件中提取API符号"""
        so_files = [f for f in os.listdir(lib_path) if f.endswith('.so')]
        if not so_files:
            raise ValueError(f"No .so files found in directory: {lib_path}")
        for so_file in so_files:
            lib_path = os.path.join(lib_path, so_file)
            try:
                # 运行nm命令并demangle符号
                cmd = f"nm -gC --defined-only {lib_path} | c++filt"
                result = subprocess.run(cmd, shell=True, check=True, 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    text=True)
                
                # 解析输出，提取API名称
                apis = []
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 3 and parts[1] in ('T', 'W'):  # T=代码段, W=弱符号
                        api = parts[2]
                        # 过滤掉编译器生成的符号
                        if not api.startswith(('_', '__', '.')) and not api.endswith(']'):
                            apis.append(api)
                return apis
            except subprocess.CalledProcessError as e:
                print(f"Error processing {lib_path}: {e.stderr}")
                return []
    
    def generate_combination(self, path: str) -> List[str]:
        """
        从指定目录下的.so文件中提取API并生成随机组合
        
        Args:
            path (str): 包含.so文件的目录路径
            
        Returns:
            List[str]: 随机API组合列表
        """
        
        # 提取所有API并去重
        all_apis = set()
        apis = self._extract_apis_from_lib(path)
        all_apis.update(apis)
        
        if not all_apis:
            raise ValueError("No APIs found in the library files")
        
        # 转换为列表并排序
        unique_apis = sorted(all_apis)
        
        # 生成随机组合
        combination_size = random.randint(
            min(self.min_combination, len(unique_apis)),
            min(self.max_combination, len(unique_apis)))
        
        return random.sample(unique_apis, combination_size)
    
    def generate_prompt(self, prompt: str, project: str, APIs: str, combination: str, context: str, 
                   header_dir: str = None, header_name: List[str] = None) -> str:
        """
        生成替换后的提示文本
        
        Args:
            prompt (str): 包含占位符的原始提示文本
            project (str): 要替换{project}的文本
            APIs (str): 要替换{APIs}的文本
            combination (str): 要替换{combination}的文本
            context (str): 要替换{context}的文本
            header_dir (str): 包含头文件的目录路径，用于替换{headers}
            header_name (List[str]): 头文件名称列表，用于替换{header_name}
            
        Returns:
            str: 替换后的提示文本
        """
        # 基础替换项
        replacements = {
            "{APIs}": APIs,
            "{combinations}": combination,
            "{context}": context,
            "{project}": project
        }

        # 处理头文件目录内容替换{headers}
        if "{headers}" in prompt and header_dir:
            header_dir = Depot.find_case_insensitive_path(header_dir)
            header_content = []
            for root, _, files in os.walk(header_dir):
                for file in files:
                    if file.endswith(('.h', '.hpp')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                header_content.append(f"/* {file} */\n{f.read()}")
                        except Exception as e:
                            print(f"Error reading {file_path}: {str(e)}")
            replacements["{headers}"] = "\n\n".join(header_content) if header_content else "/* No header files found */"
        
        # 处理头文件名称列表替换{header_name}
        if "{header_name}" in prompt and header_name:
            # 将列表转换为字符串，每个元素占一行
            header_names_str = "\n".join(header_name) if header_name else "No header files specified"
            replacements["{header_name}"] = header_names_str
        
        # 执行所有替换 - 循环直到没有更多占位符
        changed = True
        while changed:
            changed = False
            for placeholder, value in replacements.items():
                if placeholder in prompt:
                    if not isinstance(value, str):
                        value = str(value)
                    prompt = prompt.replace(placeholder, value)
                    changed = True
        
        return prompt


# 使用示例
if __name__ == "__main__":
    generator = APIGenerator(min_combination=5, max_combination=15)
    project = "cjSON"
    path = Depot.find_case_insensitive_path(f"output/build/{project}/lib")
    # 示例1: 生成API组合
    APIs = generator._extract_apis_from_lib(path)
    combination = generator.generate_combination(path)
    print("Generated API combination:")
    print(combination)
    # 示例2: 生成提示
    template = """
    Based on the following APIs: {APIs}
    And this specific combination: {combination}
    Considering the context: {context}
    and header file: {header_name}
    Please analyze the potential interactions.
    """
    path = Depot.find_case_insensitive_path(f"output/build/{project}/include")
    analyzer = FuncTypeAnalyzer(path, combination)
    context = analyzer.print_result()

    header_name = Depot.find_header_name(path)
    
    final_prompt = generator.generate_prompt(
        template, project, APIs, combination, context, path, header_name)
    print(final_prompt)
    