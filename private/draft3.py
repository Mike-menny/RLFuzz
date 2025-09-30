import os
import re
import matplotlib.pyplot as plt
import numpy as np

def extract_reward_from_file(file_path):
    """
    Extract the reward value from the first line starting with "reward: " in a file.
    Returns None if no reward line is found.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('reward: '):
                    # Extract number after "reward: "
                    match = re.search(r'reward:\s*(-?\d+\.?\d*)', line)
                    if match:
                        return float(match.group(1))
                    else:
                        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None
    return None

def get_sorted_txt_files(directory):
    """
    Recursively get all txt files in directory and sort them by name.
    """
    txt_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                txt_files.append(os.path.join(root, file))
    
    # Sort files by name
    txt_files.sort()
    return txt_files

def extract_rewards_from_directory(directory):
    """
    Extract reward values from all txt files in directory.
    Returns list of reward values and corresponding file names.
    """
    txt_files = get_sorted_txt_files(directory)
    rewards = []
    valid_files = []
    
    for file_path in txt_files:
        reward = extract_reward_from_file(file_path)
        if reward is not None:
            rewards.append(reward)
            valid_files.append(os.path.basename(file_path))
            print(f"File: {os.path.basename(file_path)} - Reward: {reward}")
        else:
            print(f"File: {os.path.basename(file_path)} - No valid reward found")
    
    return rewards, valid_files

def plot_reward_values(reward_values, file_names=None, save_path='reward_trend.png'):
    """
    Plot reward values trend.
    """
    plt.figure(figsize=(12, 6))
    
    # Create x-axis labels (file indices or names)
    x_indices = range(len(reward_values))
    
    plt.plot(x_indices, reward_values, marker='o', linestyle='-', color='b', linewidth=2, markersize=4)
    plt.title('Reward Value Trend', fontsize=14)
    plt.xlabel('File Index', fontsize=12)
    plt.ylabel('Reward Value', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add file names as x-tick labels if provided and not too many
    if file_names and len(reward_values) <= 50:
        plt.xticks(x_indices, file_names, rotation=45, ha='right')
    
    # Add some statistics to the plot
    if reward_values:
        avg_reward = np.mean(reward_values)
        max_reward = np.max(reward_values)
        min_reward = np.min(reward_values)
        
        plt.axhline(y=avg_reward, color='r', linestyle='--', alpha=0.7, 
                   label=f'Average: {avg_reward:.2f}')
        plt.legend()
        
        print(f"\nStatistics:")
        print(f"Total files with rewards: {len(reward_values)}")
        print(f"Average reward: {avg_reward:.2f}")
        print(f"Max reward: {max_reward:.2f}")
        print(f"Min reward: {min_reward:.2f}")
    
    plt.tight_layout()
    
    # Save image
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nReward趋势图已保存至: {save_path}")
    
    plt.show()

def main():
    # Set the directory to search (current directory by default)
    search_directory = "/workspace/output/projects/cjson/harnesses"
    if not search_directory:
        search_directory = '.'
    
    if not os.path.exists(search_directory):
        print(f"Directory '{search_directory}' does not exist!")
        return
    
    print(f"Searching for txt files in: {os.path.abspath(search_directory)}")
    print("-" * 50)
    
    # Extract rewards from all txt files
    rewards, file_names = extract_rewards_from_directory(search_directory)
    
    if not rewards:
        print("No reward values found in any txt files!")
        return
    
    print("-" * 50)
    print(f"Found {len(rewards)} files with valid reward values")
    
    # Plot the reward trend
    plot_reward_values(rewards, file_names)

if __name__ == "__main__":
    main()