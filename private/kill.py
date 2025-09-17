import subprocess
import re
import time

def get_gpu_processes():
    """使用gpustat获取GPU1上的进程信息"""
    try:
        result = subprocess.run(['gpustat', '--no-color'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout
        else:
            print("gpustat命令执行失败")
            return None
    except subprocess.TimeoutExpired:
        print("gpustat命令超时")
        return None
    except FileNotFoundError:
        print("未找到gpustat命令，请先安装: pip install gpustat")
        return None

def find_user_processes(gpustat_output, target_gpu="1", target_user="zidongliu"):
    """在GPU1上查找指定用户的进程"""
    processes = []
    
    # 解析gpustat输出
    lines = gpustat_output.strip().split('\n')
    
    for line in lines:
        # 查找GPU1的行 - 格式为: [1] NVIDIA H800 | 58°C,  63 % | 66293 / 81559 MB | lyuqingyang(66280M)
        if line.startswith(f'[{target_gpu}]'):
            print(f"找到GPU{target_gpu}行: {line}")
            
            # 查找进程信息部分（最后一个|后面的内容）
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 4:
                    process_part = parts[3].strip()
                    print(f"进程信息部分: {process_part}")
                    
                    # 匹配进程信息格式: username(内存大小M)
                    pattern = r'(\w+?)\((\d+)M\)'
                    matches = re.findall(pattern, process_part)
                    
                    for user, memory in matches:
                        if user == target_user:
                            # 由于gpustat不显示PID，我们需要用其他方法获取PID
                            processes.append({
                                'user': user,
                                'memory': f"{memory}M",
                                'gpu': target_gpu
                            })
    
    return processes

def get_user_pids_on_gpu(target_user, target_gpu="1"):
    """使用nvidia-smi获取指定用户在指定GPU上的进程PID"""
    try:
        # 获取指定GPU上的所有进程
        result = subprocess.run([
            'nvidia-smi', 
            '--query-compute-apps=pid,process_name,used_memory,gpu_index', 
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            pids = []
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 4:
                        pid, process_name, memory, gpu_index = parts[0], parts[1], parts[2], parts[3]
                        
                        # 检查是否在目标GPU上
                        if gpu_index == target_gpu:
                            # 检查进程所有者
                            try:
                                ps_result = subprocess.run(['ps', '-o', 'user=', '-p', pid], 
                                                         capture_output=True, text=True)
                                if ps_result.returncode == 0 and target_user in ps_result.stdout.strip():
                                    pids.append({
                                        'pid': pid,
                                        'user': target_user,
                                        'process_name': process_name,
                                        'memory': f"{memory}MB",
                                        'gpu': gpu_index
                                    })
                            except:
                                continue
            return pids
        return []
    except:
        return []

def kill_process(pid):
    """杀死指定进程"""
    try:
        subprocess.run(['/home/lyuqingyang/bin/kill', pid], check=True)
        print(f"已杀死进程 {pid}")
        return True
    except subprocess.CalledProcessError:
        print(f"杀死进程 {pid} 失败")
        return False

def monitor_and_kill(target_gpu="1", target_user="zidongliu", check_interval=10):
    """监控并杀死指定用户在GPU1上的进程"""
    print(f"开始监控GPU{target_gpu}上的用户'{target_user}'进程...")
    print(f"检查间隔: {check_interval}秒")
    print("按 Ctrl+C 停止监控")
    
    try:
        while True:
            # 获取GPU状态
            gpustat_output = get_gpu_processes()
            if gpustat_output:
                print("当前GPU状态:")
                print(gpustat_output)
                
                # 首先检查目标用户是否在目标GPU上
                user_processes = find_user_processes(gpustat_output, target_gpu, target_user)
                
                if user_processes:
                    print(f"发现用户 '{target_user}' 在GPU{target_gpu}上有进程，正在获取PID...")
                    
                    # 获取该用户在目标GPU上的所有PID
                    pids = get_user_pids_on_gpu(target_user, target_gpu)
                    
                    if pids:
                        print(f"找到 {len(pids)} 个目标进程:")
                        for process in pids:
                            print(f"  PID: {process['pid']}, 进程名: {process['process_name']}, 内存: {process['memory']}")
                        
                        # 杀死所有找到的进程
                        for process in pids:
                            kill_process(process['pid'])
                    else:
                        print("无法获取进程PID，可能权限不足")
                else:
                    print(f"未发现用户 '{target_user}' 在GPU{target_gpu}上的进程")
            
            # 等待下一次检查
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n监控已停止")

if __name__ == "__main__":
    # 配置参数
    TARGET_GPU = "1"          # 要监控的GPU编号
    TARGET_USER = "zidongliu" # 要监控的用户名
    CHECK_INTERVAL = 10       # 检查间隔(秒)
    
    # 启动监控
    monitor_and_kill(TARGET_GPU, TARGET_USER, CHECK_INTERVAL)