import re
from collections import defaultdict

def count_labels_from_file(filename):
    error_counts = defaultdict(int)
    # 捕获组只保留 0 或 1
    pattern = r'$\s*([01])(?:,\s*(?:\'[^\']*\'|"[^"]*"))*\s*$'

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # 返回的是 '0' 或 '1'
        labels = re.findall(pattern, content, flags=re.DOTALL)
        for lbl in labels:
            error_counts[lbl] += 1

        return dict(error_counts)
    except FileNotFoundError:
        print(f"错误: 文件 {filename} 未找到")
        return {}
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return {}

# 使用示例
if __name__ == "__main__":
    # 从txt文件读取并统计
    filename = "/workspace/error_analysis/output/think.txt"  # 替换为您的实际文件名
    counts = count_labels_from_file(filename)
    
    if counts:
        # 输出结果
        print("错误类型统计:")
        for error_type, count in counts.items():
            print(f"{error_type}: {count}")
        
        # 保存到JSON文件
        import json
        with open('error_analysis/output/error_counts.json', 'w', encoding='utf-8') as f:
            json.dump(counts, f, indent=2, ensure_ascii=False)
        
        print("\n结果已保存到 error_counts.json")
        
    else:
        print("未找到匹配的错误类型或文件为空")