import re
import subprocess
import csv
import ast
import os
from typing import Optional, List
from pathlib import Path

def get_error_message(exception: Exception) -> str:
    """
    通用函数，从各种异常类型中提取有用的错误信息
    """
    if isinstance(exception, subprocess.CalledProcessError):
        error_output = exception.stderr or exception.stdout or str(exception)
        return f"Subprocess error (return code {exception.returncode}): {error_output}"
    
    elif isinstance(exception, (FileNotFoundError, PermissionError)):
        return f"File error: {str(exception)}"
    
    elif isinstance(exception, ValueError):
        return f"Value error: {str(exception)}"
    
    elif isinstance(exception, TypeError):
        return f"Type error: {str(exception)}"
    
    elif isinstance(exception, AttributeError):
        return f"Attribute error: {str(exception)}"
    
    elif isinstance(exception, OSError):
        return f"OS error: {str(exception)}"
    
    else:
        return f"Unexpected error: {type(exception).__name__}: {str(exception)}"

def extract_command_from_text(text: str) -> Optional[List[str]]:
    """
    从文本中提取 command 列表
    正确的正则表达式匹配 Command '[...]' 格式
    """
    # 匹配 Command '[...]' 格式
    pattern = r"Command\s*'(\[.*?\])'"
    match = re.search(pattern, text)
    
    if match:
        command_str = match.group(1)
        try:
            # 使用 ast.literal_eval 安全地解析列表
            command_list = ast.literal_eval(command_str)
            if isinstance(command_list, list) and all(isinstance(item, str) for item in command_list):
                return command_list
        except (ValueError, SyntaxError) as e:
            print(f"Failed to parse command string: {command_str}")
            print(f"Parse error: {e}")
    
    return None

def process_single_file(file_path: str) -> Optional[dict]:
    """
    处理单个文件，返回结果字典或None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查 reward 是否为 -1
        if 'reward: -1' not in content:
            return None
        
        # 提取命令
        command = extract_command_from_text(content)
        if not command:
            print(f"No command found in file: {file_path}")
            return None
        
        print(f"Processing file: {file_path}")
        print(f"Extracted command: {command}")
        
        # 获取文件路径（通常是命令的最后一个参数）
        target_file_path = command[-1] if command else "unknown"
        
        # 重新运行命令
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=30
            )
            error_type = "UnexpectedSuccess"
            error_output = "Command unexpectedly succeeded"
            
        except subprocess.CalledProcessError as e:
            error_type = "SubprocessError"
            error_output = get_error_message(e)
            
        except subprocess.TimeoutExpired as e:
            error_type = "TimeoutError"
            error_output = get_error_message(e)
            
        except FileNotFoundError as e:
            error_type = "FileNotFoundError"
            error_output = get_error_message(e)
            
        except Exception as e:
            error_type = type(e).__name__
            error_output = get_error_message(e)
        
        # 返回结果字典
        return {
            'source_file': file_path,
            'target_file': target_file_path,
            'error_type': error_type,
            'error': error_output.replace('\n', '; ').replace('\r', ''),
            'command': ' '.join(command)
        }
        
    except Exception as e:
        print(f"Error processing file {file_path}: {get_error_message(e)}")
        return None

def find_txt_files(directory: str) -> List[str]:
    """
    递归查找目录中的所有txt文件
    """
    txt_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                txt_files.append(os.path.join(root, file))
    return txt_files

def process_directory(input_directory: str, output_csv: str):
    """
    处理目录中的所有txt文件
    """
    results = []
    
    # 查找所有txt文件
    txt_files = find_txt_files(input_directory)
    print(f"Found {len(txt_files)} txt files in directory: {input_directory}")
    
    # 处理每个文件
    for i, file_path in enumerate(txt_files, 1):
        print(f"Processing file {i}/{len(txt_files)}: {file_path}")
        result = process_single_file(file_path)
        if result:
            results.append(result)
    
    # 写入CSV文件
    if results:
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['source_file', 'target_file', 'error_type', 'error', 'command'])
            writer.writeheader()
            for result in results:
                writer.writerow(result)
        
        print(f"Results written to {output_csv}")
        print(f"Processed {len(results)} files with reward: -1")
    else:
        print("No files with reward: -1 found in the directory")

# 使用示例
if __name__ == "__main__":
    input_directory = "/workspace/history/cjson009/projects2/cjson/harnesses/"  # 替换为你的输入目录
    output_csv = "syntax_error.csv"  # 输出CSV文件
    
    process_directory(input_directory, output_csv)