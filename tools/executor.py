import os
import subprocess
import time
from pathlib import Path
from typing import Optional, Union
from tools.depot import Depot

class Executor:
    @staticmethod
    def run_fuzzer(
        project_name: str,
        epoch: int,
        completion: int,
        runs: int = 10000,
        max_total_time: int = 60,
    ) -> str:
        """
        Run a compiled fuzzer executable with specified parameters and capture output
        
        Args:
            fuzzer_executable: Path to the fuzzer executable
            runs: Number of test runs to perform (-runs parameter)
            max_total_time: Maximum total time in seconds (-max_total_time parameter)
            seed_dir: Directory containing seed inputs (-seed parameter)
            output_dir: Directory to store fuzzer output
            log_file: Optional path to store the log file (default: output_dir/fuzzer.log)
            
        Returns:
            bool: True if execution completed without errors, False otherwise
        """
        input_dir = "/workspace/output"
        fuzzer_dir = input_dir + f"/projects/{project_name}/work/fuzzer/fuzzer_{str(epoch).zfill(5)}/id_{str(completion).zfill(5)}"
        try:
            fuzzer_executable = str(Depot.find_case_insensitive_path(fuzzer_dir))
        except Exception as e:
            print(f"Error running fuzzer {epoch},{completion}")
            return str(e)
        
        seed_dir = input_dir + f"/build/{project_name}/corpus"
        seed_dir = str(Depot.find_case_insensitive_path(seed_dir))
        Depot.build_project_structure(project_name=project_name.lower())
        output_dir = input_dir + f"/projects/{project_name.lower()}/work/fuzzer_output/fuzzer_output_{str(epoch).zfill(5)}/id_{str(completion).zfill(5)}"
        Depot.create_path(output_dir+"/Dummy") 
        log_file = output_dir+"/log"
        dict_file = input_dir+f"/build/{project_name}/fuzzer.dict"
        dict_file = str(Depot.find_case_insensitive_path(dict_file))
        try:            
            # Prepare the command
            command = [
                fuzzer_executable,
                f"-runs={runs}",
                f"-max_total_time={max_total_time}",
                f"-artifact_prefix={output_dir}/",
                f"-dict={dict_file}",
                f"{seed_dir}",
                # Add memory limits and optimizations
                "-rss_limit_mb=512",       # 可以进一步降低到512MB
                "-max_len=8192",           # 再缩小输入大小到8KB
                "-timeout=2",              # 单样本时间限制再缩短
                "-jobs=1",
                "-workers=1"
            ]
            
            # print(f"Running fuzzer with command: {' '.join(command)}")
            
            # Run the fuzzer and capture output
            with open(log_file, "w") as log:
                start_time = time.time()
                process = subprocess.Popen(
                    command,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                try:
                    return_code = process.wait(timeout=max_total_time + 60)  # Add buffer time
                    end_time = time.time()
                    
                    print(f"Fuzzer {epoch},{completion} completed in {end_time - start_time:.2f} seconds")
                    print(f"Output logged to: {log_file}")
                    
                    # Check if the fuzzer found any crashes
                    crash_files = list(Path(output_dir).glob("crash-*"))
                    if crash_files:
                        print(f"Warning: Fuzzer {epoch},{completion} found {len(crash_files)} crashes!")
                        return f"Warning: Fuzzer {epoch},{completion} found {len(crash_files)} crashes!"
                    
                    if return_code == 0:
                        return None
                    else:
                        return "plz read from log"
                
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"Fuzzer {epoch},{completion} timed out after {max_total_time} seconds")
                    return f"Fuzzer {epoch},{completion} timed out after {max_total_time} seconds"
                
        except Exception as e:
            print(f"Error running fuzzer {epoch},{completion}")
            return str(e)

    @staticmethod
    def run_coverage_fuzzer(
            project_name: str,
            epoch: int,
            completion: int,
            iterations: int = 10000,
            max_time: int = 60,
        ) -> Optional[dict]:
            """
            Run a coverage-instrumented fuzzer executable and collect coverage information
            
            Args:
                project_name: Name of the project
                epoch: Epoch number
                completion: Completion ID
                iterations: Number of test iterations to perform
                max_time: Maximum time in seconds to run the fuzzer
                
            Returns:
                dict: Dictionary containing coverage information, or None if failed
            """
            input_dir = "/workspace/output"
            cov_fuzzer_path = input_dir + f"/projects/{project_name}/work/fuzzer/fuzzer_{str(epoch).zfill(5)}/id_cov_{str(completion).zfill(5)}"
            
            try:
                fuzzer_executable = str(Depot.find_case_insensitive_path(cov_fuzzer_path))
                if not os.path.exists(fuzzer_executable):
                    print(f"Coverage fuzzer executable not found at {cov_fuzzer_path}")
                    return None
            except Exception as e:
                print(f"Error finding coverage fuzzer: {e}")
                return None
            
            # Prepare directories
            seed_dir = input_dir + f"/build/{project_name}/corpus"
            seed_dir = str(Depot.find_case_insensitive_path(seed_dir))
            Depot.build_project_structure(project_name=project_name.lower())
            
            output_dir = input_dir + f"/projects/{project_name.lower()}/work/fuzzer_output/fuzzer_output_{str(epoch).zfill(5)}/id_cov_{str(completion).zfill(5)}"
            Depot.create_path(output_dir+"/Dummy")
            
            log_file = os.path.join(output_dir, "coverage.log")
            dict_file = input_dir + f"/build/{project_name}/fuzzer.dict"
            dict_file = str(Depot.find_case_insensitive_path(dict_file))
            
            # Prepare coverage data file
            coverage_data_file = os.path.join(output_dir, "coverage.dat")
            
            try:
                # Set environment variables for coverage collection
                env = os.environ.copy()
                env["LLVM_PROFILE_FILE"] = coverage_data_file
                
                command = [
                    fuzzer_executable,
                    f"-runs={iterations}",
                    f"-max_total_time={max_time}",
                    f"-artifact_prefix={output_dir}/",
                    f"-dict={dict_file}",
                    seed_dir,
                ]
                
                print(f"Running coverage fuzzer with command: {' '.join(command)}")
                
                # Run the coverage fuzzer
                with open(log_file, "w") as log:
                    start_time = time.time()
                    process = subprocess.Popen(
                        command,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        text=True,
                        env=env
                    )
                    
                    try:
                        return_code = process.wait(timeout=max_time + 60)  # Add buffer time
                        end_time = time.time()
                        
                        print(f"Coverage fuzzer {epoch},{completion} completed in {end_time - start_time:.2f} seconds")
                        print(f"Output logged to: {log_file}")
                        
                        # Check if coverage data was generated
                        if not os.path.exists(coverage_data_file):
                            print(f"No coverage data generated at {coverage_data_file}")
                            return None
                        
                        # Process coverage data (this is a placeholder - you'll need to implement actual coverage analysis)
                        coverage_info = {
                            'execution_time': end_time - start_time,
                            'iterations': iterations,
                            'coverage_data_file': coverage_data_file,
                            'log_file': log_file,
                            'success': return_code == 0
                        }
                        
                        # Here you would add actual coverage metrics by processing the .profraw file
                        # For example using llvm-profdata and llvm-cov
                        
                        return coverage_info
                    
                    except subprocess.TimeoutExpired:
                        process.kill()
                        print(f"Coverage fuzzer {epoch},{completion} timed out after {max_time} seconds")
                        return None
                    
            except Exception as e:
                print(f"Error running coverage fuzzer {epoch},{completion}: {e}")
                return None

# Example usage
if __name__ == "__main__":
    config = {
        "project_name": "cjson",
        "epoch": 8,
        "completion": 1,
    }
    
    # Run the fuzzer
    first = Executor.run_fuzzer(**config)
    if first:
        print("Fuzzer executed successfully!\n")
    else:
        print("Fuzzer encountered errors or found crashes\n")
    success = Executor.run_coverage_fuzzer(**config)
    
    if success:
        print("Cvoerage executed successfully!")
    else:
        print("Coverage encountered errors or found crashes")