import re
import matplotlib.pyplot as plt

def extract_loss_values(file_path):
    loss_values = []
    pattern = re.compile(r"'loss':\s*([0-9.e+-]+)")
    
    with open(file_path, 'r') as file:
        for line in file:
            match = pattern.search(line)
            if match:
                try:
                    loss_value = float(match.group(1))
                    loss_values.append(loss_value)
                except ValueError:
                    print(f"无法转换loss值: {match.group(1)}")
    
    return loss_values

def plot_loss_values(loss_values, save_path='loss_trend.png'):
    plt.figure(figsize=(10, 6))
    plt.plot(range(len(loss_values)), loss_values, marker='o', linestyle='-', color='b')
    plt.title('Loss Value Trend')
    plt.xlabel('Index')
    plt.ylabel('Loss Value')
    plt.grid(True)
    
    # 保存图像到文件
    plt.savefig(save_path, dpi=300, bbox_inches='tight')  # 高分辨率保存
    print(f"Loss趋势图已保存至: {save_path}")
    
    plt.tight_layout()
    plt.show()  # 仍然显示图像（可选）

if __name__ == "__main__":
    file_path = 'nohup.out'
    
    try:
        loss_values = extract_loss_values(file_path)
        
        if not loss_values:
            print("没有找到任何loss值。")
        else:
            print("提取到的loss值:")
            for i, loss in enumerate(loss_values):
                print(f"{i}: {loss}")
            
            plot_loss_values(loss_values)
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 未找到。")