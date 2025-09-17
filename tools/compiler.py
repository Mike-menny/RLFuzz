import subprocess
import sys
import os
sys.path.insert(0, '/workspace')
from tools.depot import Depot
from typing import List, Optional
import glob
from pathlib import Path

class Compiler:
    @staticmethod
    def compile_syntax(project_name:str, epoch:int, completion:int, std: str = "c++17") -> str:
        include_dir = f"output/build/{project_name}/include"
        include_dir = str(Depot.find_case_insensitive_path(include_dir))
        include_flags = [f"-I{include_dir}"]
        try:
            cpp_file = f"output/projects/{project_name}/harnesses/harness_{str(epoch).zfill(5)}"
            tem = str(Depot.find_case_insensitive_path(cpp_file))
            # 优先检查.cpp是否存在
            cpp_file = f"{tem}/id_{str(completion).zfill(5)}.cpp"
            if not (Path(cpp_file).exists()):
                    # 其次检查.c是否存在
                    cpp_file = f"{tem}/id_{str(completion).zfill(5)}.c"
                    if not Path(cpp_file).exists():
                        print(f"Error: harness file for {project_name},{epoch},{completion} not found.")
                        return f"Error: harness file for {project_name},{epoch},{completion} not found."
        except Exception as e:
            #print(e)
            print(f"harness {epoch},{completion} Syntax check failed")
            return str(e)
        command = ["clang++", "-fsyntax-only", f"-std={std}", *include_flags, cpp_file]
        
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            print(f"harness {epoch},{completion} Syntax check passed!")
            return None
        except subprocess.CalledProcessError as e:
            print(f"harness {epoch},{completion} Syntax check failed")
            #print(e.stderr)
            return str(e.stderr)
        except Exception as e:
            print(f"harness {epoch},{completion} Syntax check failed")
            return str(e)

    @staticmethod
    def compile_fuzzer(
        project_name: str,
        epoch:int,
        completion:int,
        std: str = "c++17",
        additional_flags: Optional[List[str]] = None,
        sanitizers: List[str] = ["address", "undefined", "fuzzer"],
        debug: bool = False
    ) -> str:
        project_path = f"output/build/{project_name}"
        project_path = str(Depot.find_case_insensitive_path(project_path))
        include_dir = project_path+"/include"
        include_flags = [f"-I{include_dir}"]
        lib_build = project_path+"/lib"
        lib_flags = [f"-L{lib_build}", *[lib for lib in glob.glob(f"{lib_build}/*.a")]]

        Depot.build_project_structure(project_name=project_name.lower())
        project_path = f"output/projects/{project_name.lower()}"
        project_path = str(Depot.find_case_insensitive_path(project_path))
        try:
            cpp_file = f"output/projects/{project_name}/harnesses/harness_{str(epoch).zfill(5)}"
            tem = str(Depot.find_case_insensitive_path(cpp_file))
            # 优先检查.cpp是否存在
            cpp_file = f"{tem}/id_{str(completion).zfill(5)}.cpp"
            if not (Path(cpp_file).exists()):
                    # 其次检查.c是否存在
                    cpp_file = f"{tem}/id_{str(completion).zfill(5)}.c"
                    if not Path(cpp_file).exists():
                        print(f"Error: harness file for {project_name},{epoch},{completion} not found.")
                        return f"Error: harness file for {project_name},{epoch},{completion} not found."
        except Exception as e:
            print(f"Fuzzer {epoch},{completion} compilation failed")
            return str(e)
        output_file = project_path+f"/work/fuzzer/fuzzer_{str(epoch).zfill(5)}/id_{str(completion).zfill(5)}"
        Depot.delete_file(output_file)
        Depot.create_path(output_file)

        sanitizer_flags = [
            f"-fsanitize={','.join(sanitizers)}",
            "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer",
        ]
        
        if "fuzzer" in sanitizers:
            # libFuzzer需要链接标志
            sanitizer_flags.append("-fsanitize-link-c++-runtime")
        
        debug_flags = ["-g"] if debug else []
        
        command = [
            "clang++",
            f"-std={std}",
            *include_flags,
            cpp_file,
            *lib_flags,
            *sanitizer_flags,
            *debug_flags,
            "-o", output_file,
        ]
        
        if additional_flags:
            command.extend(additional_flags)
        
        try:
            #print("Compiling with command:")
            #print(" ".join(command))
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            print(f"Fuzzer {epoch},{completion} compilation successful! Output: {output_file}")
            return None
        except subprocess.CalledProcessError as e:
            print(f"Fuzzer {epoch},{completion} compilation failed")
            return str(e)
        except Exception as e:
            print(f"Fuzzer {epoch},{completion} compilation failed")
            return str(e)

    @staticmethod
    def compile_cov(
        project_name: str,
        epoch: int,
        completion: int,
        std: str = "c++17",
        additional_flags: Optional[List[str]] = None,
        debug: bool = False
    ) -> str:
        project_path = f"output/build/{project_name}"
        project_path = str(Depot.find_case_insensitive_path(project_path))
        include_dir = project_path+"/include"
        include_flags = [f"-I{include_dir}"]
        lib_build = project_path+"/lib"
        lib_flags = [f"-L{lib_build}", *[lib for lib in glob.glob(f"{lib_build}/*.a")]]
        source = project_path+f"/src/{project_name}"
        source = str(Depot.find_case_insensitive_path(source))

        Depot.build_project_structure(project_name=project_name.lower())
        project_path = f"output/projects/{project_name.lower()}"
        project_path = str(Depot.find_case_insensitive_path(project_path))

        try:
            cpp_file = f"output/projects/{project_name}/harnesses/harness_{str(epoch).zfill(5)}"
            tem = str(Depot.find_case_insensitive_path(cpp_file))
            # Check for .cpp first, then .c
            cpp_file = f"{tem}/id_{str(completion).zfill(5)}.cpp"
            if not (Path(cpp_file).exists()):
                cpp_file = f"{tem}/id_{str(completion).zfill(5)}.c"
                if not Path(cpp_file).exists():
                    print(f"Error: harness file for {project_name},{epoch},{completion} not found.")
                    return f"Error: harness file for {project_name},{epoch},{completion} not found."
        except Exception as e:
            print(e)
            return str(e)
            
        output_file = project_path+f"/work/fuzzer/fuzzer_{str(epoch).zfill(5)}/id_cov_{str(completion).zfill(5)}"
        Depot.delete_file(output_file)
        Depot.create_path(output_file)

        coverage_flags = [
            "-fno-sanitize=all",
            # 修改为标准的覆盖率标志（不要路径限定）
            "-fprofile-instr-generate",
            "-fcoverage-mapping",
        ]
        
        linker_flags = [
            "-fsanitize=fuzzer"
        ]
        
        debug_flags = ["-g"] if debug else []
        
        command = [
            "clang++",
            f"-std={std}",
            *include_flags,
            f"-I{source}",
            *coverage_flags,
            cpp_file,
            *lib_flags,
            *linker_flags,
            *debug_flags,
            "-o", output_file,
        ]
        
        if additional_flags:
            command.extend(additional_flags)
        
        try:
            print("Compiling with command:", " ".join(command))
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            print(f"Coverage fuzzer {epoch},{completion} compilation successful! Output: {output_file}")
            return None
        except subprocess.CalledProcessError as e:
            print(f"Coverage fuzzer {epoch},{completion} compilation failed")
            return str(e)
        except Exception as e:
            print(f"Coverage fuzzer {epoch},{completion} compilation failed")
            return str(e)

# 使用示例
if __name__ == "__main__":
    syntax_error = Compiler.compile_syntax(project_name="cjson",epoch=1,completion=0, std="c++17")
    print(syntax_error)
    Compiler.compile_cov(project_name="cjson",epoch=0,completion=0,
                            additional_flags=["-O2"],
                            debug=True)
