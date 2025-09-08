import os
import re
import glob
from typing import Optional, List, Tuple,Union
from pathlib import Path
from heapq import nlargest

class Depot:
    @staticmethod
    def find_header_name(
        directory: Union[str, Path],
        recursive: bool = False,
        header_extensions: Optional[List[str]] = None
    ) -> List[str]:
        """
        Find all header files in the specified directory.
        
        Args:
            directory: Directory to search in
            recursive: Whether to search recursively (default False)
            header_extensions: List of header file extensions to look for 
                            (default: [".h", ".hpp", ".hxx", ".hh"])
        
        Returns:
            List of header file names (without paths)
        
        Raises:
            ValueError: If directory doesn't exist
        """
        if header_extensions is None:
            header_extensions = [".h", ".hpp", ".hxx", ".hh"]
        
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        # Build search pattern
        search_pattern = "**/*" if recursive else "*"
        
        header_files = []
        for ext in header_extensions:
            for file_path in dir_path.glob(search_pattern):
                if file_path.is_file() and file_path.suffix.lower() == ext.lower():
                    header_files.append(file_path.name)
        
        return sorted(header_files)

    @staticmethod
    def build_project_structure(
        workspace_dir: str = "output",  # 新增参数指定workspace路径
        project_name: str = "cjson"
    ) -> str:
        """        
        目录结构 (绝对路径):
        {workspace_dir}/projects/
            |-{project_name}
                |-harnesses       (保留已有内容)
                |-work
                    |-fuzzer      (保留已有内容)
                    |-fuzzer_output (保留已有内容)
                |-tem
        
        Args:
            workspace_dir: workspace目录路径 (默认: "workspace/output")
            project_name: 项目名称 (默认: "cjson")
        
        Returns:
            str: 项目根目录绝对路径
        
        Raises:
            OSError: 如果目录创建失败（但不会因目录已存在而报错）
        """
        # 转换为绝对路径
        workspace_path = Path(workspace_dir).absolute()
        project_root = workspace_path / "projects" / project_name
        
        try:
            # 安全创建目录（保留已有内容）
            os.makedirs(project_root / "harnesses", exist_ok=True)
            os.makedirs(project_root / "tem", exist_ok=True)
            os.makedirs(project_root / "work/fuzzer", exist_ok=True)
            os.makedirs(project_root / "work/fuzzer_output", exist_ok=True)
            
            abs_path = str(project_root.resolve())
            print(f"Project structure created at: {abs_path}")
            return abs_path
            
        except Exception as e:
            raise OSError(f"Failed to create project structure: {e}")

    @staticmethod
    def find_newest_files(
        directory: Union[str, Path],
        n: int = 1,
        pattern: str = "*",
        recursive: bool = False
        ) -> List[Path]:
            """
            Find the n files with highest numerical index in their names
        
            Args:
                directory: Directory to search in
                n:        Number of highest-index files to return (default 1)
                pattern:  File pattern to match (default "*" for all files)
                recursive: Whether to search recursively (default False)
            
            Returns:
                List of Path objects of the highest-index files (descending order)
                Empty list if no matching files found
            
            Raises:
                ValueError: If directory doesn't exist or n is invalid
            """
            if n < 1:
                raise ValueError("n must be at least 1")
            
            dir_path = Path(directory)
            if not dir_path.exists():
                raise ValueError(f"Directory does not exist: {directory}")
            if not dir_path.is_dir():
                raise ValueError(f"Path is not a directory: {directory}")

            # Build search pattern
            search_pattern = dir_path / "**" / pattern if recursive else dir_path / pattern
        
            # Find all matching files with their indices
            files_with_index = []
            for file_path in glob.glob(str(search_pattern), recursive=recursive):
                path = Path(file_path)
                if path.is_file():
                    index_str = Depot.find_index(path.name)
                    if index_str is not None:
                        # 关键修改：直接使用字符串索引排序（保留前导零的字典序）
                        files_with_index.append((index_str, path))
        
            if not files_with_index:
                return []
            
            # 按索引字符串的字典序降序排列（"00099" > "00098"）
            files_with_index.sort(key=lambda x: x[0], reverse=True)
        
            # 返回前n个文件的Path对象
            return [file for (index, file) in files_with_index[:n]]

    @staticmethod
    def delete_file(path: Union[str, Path]) -> bool:
        """
        Delete a file or directory if it exists
        
        Args:
            path: Path to the file or directory to be deleted
            
        Returns:
            bool: True if deletion was successful or path didn't exist,
                  False if deletion failed
                  
        Examples:
            >>> Depot.delete_file("/path/to/file.txt")
            True  # if deleted successfully or file didn't exist
            >>> Depot.delete_file("/path/to/directory")
            True  # if deleted successfully or dir didn't exist
        """
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return True  # Consider non-existent paths as "success"
                
            if path_obj.is_file() or path_obj.is_symlink():
                path_obj.unlink()  # Delete file or symlink
            elif path_obj.is_dir():
                shutil.rmtree(path_obj)  # Recursively delete directory
            return True
        except Exception as e:
            print(f"Error deleting {path}: {e}")
            return False

    @staticmethod
    def find_index(filename: Union[str, Path]) -> Optional[str]:
        """
        从文件名中提取数字索引部分（保留前导零）
        
        Args:
            filename: 文件名或路径 (如 "$%^&(^$_00024.cpp" 或 "/path/to/file_0042.txt")
            
        Returns:
            str: 提取到的数字索引字符串 (如 "00024")，保留前导零
            None: 如果文件名中不包含数字索引
            
        Examples:
            >>> Depot.find_index("$%^&(^$_00024.cpp")
            "00024"
            >>> Depot.find_index("file0042.txt")
            "0042"
            >>> Depot.find_index("no_index_here.txt")
            None
        """
        # 转换为字符串并获取纯文件名(不带路径)
        filename_str = str(Path(filename).name)
        
        # 匹配文件名末尾的数字部分(至少1位数字)
        match = re.search(r'(\d+)(?:\..+)?$', filename_str)
        if match:
            return match.group(1)  # 直接返回匹配到的数字字符串
        return None

    @staticmethod
    def create_new_name(
        directory: Union[str, Path], 
        prefix: str = "file",
        is_dir: bool = False
    ) -> str:
        """
        查找最新的编号文件/目录并创建新名称

        Args:
            directory: 要搜索的目录路径
            prefix: 编号文件/目录的前缀 (默认 "file")
            is_dir: 是否创建目录 (默认False，即创建文件)
        
        Returns:
            str: 新文件/目录的完整路径 (格式 "{prefix}{index:05d}")
        
        Raises:
            ValueError: 如果目录不存在或路径不是目录
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        # 匹配模式 {prefix}\d+
        pattern = re.compile(rf"^{prefix}(\d+)(.*)$")
        max_index = -1
        suffix = ""  # 默认无后缀
    
        for item in dir_path.iterdir():
            # 根据是否是目录来筛选
            if (is_dir and item.is_dir()) or (not is_dir and item.is_file()):
                match = pattern.match(item.stem)
                if match:
                    current_index = int(match.group(1))
                    if current_index > max_index:
                        max_index = current_index
                        suffix = item.suffix if not is_dir else ""  # 目录忽略后缀

        if max_index == -1:
            # 没有找到编号文件/目录，从00000开始
            new_index = 0
        else:
            new_index = max_index + 1

        # 格式化新名称，5位数字补零
        new_name = f"{prefix}{new_index:05d}{suffix}"
        new_path = dir_path / new_name
    
        # 如果需要创建目录，则创建它
        if is_dir:
            new_path.mkdir(parents=True, exist_ok=True)
    
        return str(new_path)

    @staticmethod
    def find_case_insensitive_path(input_path: str) -> str:
        """
        不区分大小写查找路径，返回真实大小写的绝对路径
        
        Args:
            input_path: 输入路径（相对/绝对均可，如 "output/BUILD/lib"）
        
        Returns:
            str: 匹配到的真实绝对路径（如 "/workspace/output/build/lib"）
        
        Raises:
            ValueError: 如果找不到匹配的路径
        """
        # 转换为绝对路径（基于当前工作目录）
        abs_path = Path(input_path).absolute()
        
        # 递归检查路径是否存在（不区分大小写）
        def find_real_path(path: Path) -> Path:
            if path.exists():
                return path
            
            # 如果当前路径不存在，尝试在父目录中查找小写匹配
            parent = path.parent
            if not parent.exists():
                parent = find_real_path(parent)
            
            # 在父目录中查找匹配的子项（不区分大小写）
            target_name = path.name.lower()
            for child in parent.iterdir():
                if child.name.lower() == target_name:
                    return child
            
            raise FileNotFoundError
        
        try:
            real_path = find_real_path(abs_path)
            return str(real_path.resolve())
        except FileNotFoundError:
            raise ValueError(f"No match found for: {input_path}")

    @staticmethod
    def create_path(path: Union[str, List[str]]) -> bool:
        path = os.path.dirname(path)
        if isinstance(path, str):
            paths = [path]
        else:
            paths = path
            
        all_success = True
        
        for p in paths:
            try:
                if not (os.path.exists(p)):
                    os.makedirs(p)
                    print(f"Path created: {p}")
            except Exception as e:
                print(f"Failed to create path {p}: {e}")
                all_success = False
                
        return all_success

if __name__ == "__main__":
    path = Depot.find_header_name("/workspace/output/build/cjson/include")
    print(path)
        
    