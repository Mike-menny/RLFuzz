from tree_sitter import Language, Parser
from pathlib import Path
import os
import subprocess
from typing import List, Dict, Optional, Union
from graphviz import Digraph

# 类型定义
ParameterInfo = Dict[str, Optional[str]]  # {'type': str, 'name': Optional[str]}
FunctionInfo = Dict[str, Union[str, List[ParameterInfo]]]  # {'name': str, 'return_type': str, 'parameters': List[ParameterInfo]}

class HeaderAnalyst:
    def __init__(self):
        """初始化分析器，设置Tree-sitter环境"""
        self.LIB_PATH = "build/my-languages.so"
        self._setup_parser()

    def _setup_parser(self):
        """设置解析器，自动构建语言库"""
        # 如果语言库不存在，则自动构建
        if not os.path.exists(self.LIB_PATH):
            self._build_language_library()

        # 加载C和C++语言
        self.cpp_lang = Language(self.LIB_PATH,'cpp')
        self.c_lang = Language(self.LIB_PATH, 'c')
        self.parser = Parser()

    def _build_language_library(self):
        """构建tree-sitter语言库（修正版本）"""
        os.makedirs('build', exist_ok=True)
        os.makedirs('vendor', exist_ok=True)

        # 克隆特定版本的语言仓库
        if not os.path.exists('vendor/tree-sitter-cpp'):
            subprocess.run([
                'git', 'clone', 
                'https://github.com/tree-sitter/tree-sitter-cpp', 
                'vendor/tree-sitter-cpp',
                '--branch', 'v0.20.2'  # 明确指定兼容版本
            ], check=True)
        
        if not os.path.exists('vendor/tree-sitter-c'):
            subprocess.run([
                'git', 'clone',
                'https://github.com/tree-sitter/tree-sitter-c',
                'vendor/tree-sitter-c',
                '--branch', 'v0.20.4'  # 明确指定兼容版本
            ], check=True)

        # 强制重建
        Language.build_library(
            self.LIB_PATH,
            [
                'vendor/tree-sitter-cpp',
                'vendor/tree-sitter-c'
            ]
        )
    
    def extract_all_types(self, header_content: str, lang: str = 'cpp') -> Dict:
        """
        增强功能：提取所有类型定义（结构体/联合体/枚举/typedef）
        返回结构：
        {
            "structs": {struct_name: {"members": [成员列表], ...}},
            "unions": {...},
            "enums": {...},
            "typedefs": {...}
        }
        """
        self.parser.set_language(self.cpp_lang if lang == 'cpp' else self.c_lang)
        tree = self.parser.parse(bytes(header_content, 'utf8'))
        root_node = tree.root_node
        
        result = {
            "structs": {},
            "unions": {},
            "enums": {},
            "typedefs": {}
        }
        
        # 递归遍历语法树
        cursor = tree.walk()
        stack = [cursor.node]
        
        while stack:
            node = stack.pop()
            print(f"menny! {node}")
            # 处理结构体
            if node.type == 'struct_specifier':
                struct_info = self._parse_struct(node, header_content)
                if struct_info:
                    result["structs"][struct_info["name"]] = struct_info
            
            # 处理联合体
            elif node.type == 'union_specifier':
                union_info = self._parse_union(node, header_content)
                if union_info:
                    result["unions"][union_info["name"]] = union_info
            
            # 处理枚举
            elif node.type == 'enum_specifier':
                enum_info = self._parse_enum(node, header_content)
                if enum_info:
                    result["enums"][enum_info["name"]] = enum_info
            
            # 处理typedef
            elif node.type == 'type_definition':
                typedef_info = self._parse_typedef(node, header_content)
                if typedef_info:
                    result["typedefs"][typedef_info["name"]] = typedef_info
            
            # 继续遍历子节点
            for child in node.children:
                stack.append(child)
        
        return result

    def _parse_struct(self, node, source: str) -> Optional[Dict]:
        """增强版结构体解析"""
        name_node = next((n for n in node.children if n.type == 'type_identifier'), None)
        body_node = next((n for n in node.children if n.type == 'field_declaration_list'), None)
        
        # 处理匿名结构体
        struct_name = source[name_node.start_byte:name_node.end_byte] if name_node else f"anonymous_struct_{node.start_byte}"
        
        members = []
        if body_node:
            for child in body_node.children:
                if child.type == 'field_declaration':
                    # 处理普通成员
                    member = self._parse_member(child, source)
                    if member:
                        members.append(member)
                elif child.type in ('struct_specifier', 'union_specifier'):
                    # 处理嵌套结构体/联合体
                    nested = self._parse_struct(child, source) if child.type == 'struct_specifier' else self._parse_union(child, source)
                    if nested:
                        members.append({
                            "name": "",
                            "type": nested["name"],
                            "is_nested": True,
                            "members": nested["members"]
                        })
        return {
            "name": struct_name,
            "members": members,
            "is_anonymous": not bool(name_node),
            "location": (node.start_byte, node.end_byte)
        }

    def _parse_union(self, node, source: str) -> Optional[Dict]:
        """解析联合体定义（实现类似_parse_struct）"""
        # 实现逻辑与_parse_struct基本相同
        pass

    def _parse_enum(self, node, source: str) -> Optional[Dict]:
        """解析枚举定义"""
        name_node = next((n for n in node.children if n.type == 'type_identifier'), None)
        body_node = next((n for n in node.children if n.type == 'enumerator_list'), None)
        
        if not name_node:
            enum_name = f"anonymous_enum_{node.start_byte}"
        else:
            enum_name = source[name_node.start_byte:name_node.end_byte]
        
        values = []
        if body_node:
            for child in body_node.children:
                if child.type == 'enumerator':
                    name = next((n for n in child.children if n.type == 'identifier'), None)
                    if name:
                        values.append(source[name.start_byte:name.end_byte])
        
        return {
            "name": enum_name,
            "values": values,
            "location": (node.start_byte, node.end_byte)
        }

    def _parse_typedef(self, node, source: str) -> Optional[Dict]:
        """解析typedef定义"""
        type_node = next((n for n in node.children 
                        if n.type in ('struct_specifier', 'union_specifier', 
                                     'enum_specifier', 'type_identifier')), None)
        alias_node = next((n for n in node.children if n.type == 'type_identifier'), None)
        
        if not type_node or not alias_node:
            return None
        
        underlying_type = source[type_node.start_byte:type_node.end_byte]
        alias_name = source[alias_node.start_byte:alias_node.end_byte]
        
        return {
            "name": alias_name,
            "underlying_type": underlying_type,
            "location": (node.start_byte, node.end_byte)
        }

    def _parse_member(self, node, source: str) -> Optional[Dict]:
        """通用成员解析方案 - 支持所有标准C/C++结构体声明"""
        # 跳过预处理指令和注释
        if node.type in ('preproc_if', 'preproc_def', 'comment'):
            return None

        # 类型节点可能出现在不同位置（适应各种编码风格）
        type_nodes = [
            n for n in node.children 
            if n.type in ('type_identifier', 'primitive_type',
                        'struct_specifier', 'union_specifier',
                        'enum_specifier', 'sized_type_specifier')
            and not any(p.type == 'attribute_specifier' for p in node.children)  # 跳过GNU属性
        ]

        # 获取所有可能的声明符（适应各种声明形式）
        declarators = []
        for n in node.children:
            if n.type.endswith('_declarator') or n.type in ('identifier', 'field_identifier'):
                declarators.append(n)
            elif n.type == 'init_declarator':  # 处理带初始化的声明
                declarators.extend(c for c in n.children if c.type.endswith('_declarator'))

        # 基础类型提取（支持GNU/C++扩展）
        base_type = ''
        if type_nodes:
            base_node = type_nodes[0]
            if base_node.type in ('struct_specifier', 'union_specifier', 'enum_specifier'):
                kind = base_node.type.replace('_specifier', '')
                name_node = next((c for c in base_node.children if c.type == 'type_identifier'), None)
                base_type = f"{kind} {name_node.text.decode() if name_node else 'anonymous'}"
            else:
                base_type = source[base_node.start_byte:base_node.end_byte]
                
                # 处理类型限定符 (const/volatile等)
                qualifiers = [
                    source[q.start_byte:q.end_byte] 
                    for q in node.children 
                    if q.type == 'type_qualifier'
                ]
                if qualifiers:
                    base_type = ' '.join(qualifiers + [base_type])
        # 递归解析声明符
        def parse_declarator(decl, current_type):
            """递归处理声明符（指针/数组/函数）"""
            if decl.type == 'pointer_declarator':
                # 处理多级指针 (如 int***)
                ptr_count = sum(1 for c in decl.children if c.type == '*')
                current_type += '*' * ptr_count
                # 继续解析内部声明符
                inner = next((c for c in decl.children if c.type.endswith('_declarator')), None)
                if inner:
                    return parse_declarator(inner, current_type)
                return current_type, None

            elif decl.type == 'array_declarator':
                # 处理多维数组 (如 int[2][3])
                size_node = next((c for c in decl.children if c.type == 'number_literal'), None)
                size = f"[{size_node.text.decode()}]" if size_node else '[]'
                inner = next((c for c in decl.children if c.type.endswith('_declarator')), None)
                if inner:
                    t, name = parse_declarator(inner, current_type)
                    return f"{t}{size}", name
                return f"{current_type}{size}", None

            elif decl.type == 'function_declarator':
                # 处理函数指针 (如 int(*)(int))
                params = self._parse_parameters(decl, source)
                param_str = ', '.join(f"{p['type']} {p['name']}" for p in params)
                return f"{current_type}(*)({param_str})", None

            elif decl.type in ('identifier', 'field_identifier'):
                return current_type, source[decl.start_byte:decl.end_byte]

            return current_type, None

        # 解析成员名称和完整类型
        member_name = ''
        full_type = base_type
        for decl in declarators:
            full_type, name = parse_declarator(decl, full_type)
            if name:
                member_name = name

        # 处理位域
        bit_width = None
        if bitfield_node := next((n for n in node.children if n.type == 'bitfield_clause'), None):
            bit_width = int(bitfield_node.children[1].text) if len(bitfield_node.children) > 1 else 0

        return {
            "name": member_name,
            "type": full_type,
            "bit_width": bit_width,
            "is_func_ptr": '(*)' in full_type
        } if member_name or bit_width is not None else None

    def _parse_parameters(self, node, source: str) -> List[Dict]:
        """通用参数解析（支持C/C++所有参数形式）"""
        params = []
        for child in node.children:
            if child.type == 'parameter_declaration':
                # 处理省略号参数 (C的可变参数)
                if any(c.type == '...' for c in child.children):
                    params.append({"type": "...", "name": ""})
                    continue

                # 提取参数类型和名称
                type_part = []
                name_part = None
                for c in child.children:
                    if c.type in ('type_identifier', 'primitive_type', 
                                'struct_specifier', 'union_specifier'):
                        type_part.append(source[c.start_byte:c.end_byte])
                    elif c.type == 'identifier':
                        name_part = source[c.start_byte:c.end_byte]
                    elif c.type == 'pointer_declarator':
                        type_part.append('*')
                
                params.append({
                    "type": ' '.join(type_part),
                    "name": name_part or ""
                })
        return params

    def extract_apis(self, header_content: str, lang: str = 'cpp') -> List[FunctionInfo]:
        self.parser.set_language(self.cpp_lang if lang == 'cpp' else self.c_lang)
        tree = self.parser.parse(bytes(header_content, 'utf8'))
        
        apis = []
        # 递归遍历所有节点
        cursor = tree.walk()
        stack = [cursor.node]
        
        while stack:
            current_node = stack.pop()
            
            if self._is_function_declaration(current_node):
                api_info = self._extract_function_context(current_node, header_content)
                if api_info:
                    apis.append(api_info)
            
            # 添加子节点到栈中
            for child in current_node.children:
                stack.append(child)
        
        return apis

    def _is_function_declaration(self, node) -> bool:
        """增强版函数声明检测"""
        # 检查直接函数声明
        if node.type in {'function_declarator', 'function_definition'}:
            return True
        
        # 检查声明中的函数
        if node.type == 'declaration':
            return any(child.type == 'function_declarator' for child in node.children)
        
        # 检查带宏的函数声明
        if node.type == 'preproc_def':
            return ')' in node.text.decode()  # 简单启发式判断
        
        return False

    def _extract_function_context(self, node, source_code: str) -> Optional[FunctionInfo]:
        """处理带宏的函数声明"""
        # 处理普通函数声明
        if node.type in {'function_declarator', 'function_definition'}:
            return self._extract_normal_function(node, source_code)
        
        # 处理带宏的声明
        elif node.type == 'preproc_def':
            return self._extract_macro_function(node, source_code)
        
        # 处理标准声明
        elif node.type == 'declaration':
            for child in node.children:
                if child.type == 'function_declarator':
                    return self._extract_normal_function(child, source_code)
        
        return None

    def _extract_normal_function(self, node, source_code):
        """提取普通函数信息"""
        name_node = self._find_child(node, 'identifier')
        if not name_node:
            return None
        
        return {
            'name': source_code[name_node.start_byte:name_node.end_byte],
            'return_type': self._extract_return_type(node, source_code),
            'parameters': self._extract_parameters(node, source_code)
        }

    def _extract_macro_function(self, node, source_code):
        """处理宏定义的函数声明（如CJSON_PUBLIC）"""
        text = source_code[node.start_byte:node.end_byte]
        if '(' not in text or ')' not in text:
            return None
        
        # 简单提取函数名（实际项目可能需要更复杂的解析）
        func_name = text.split('(')[1].split(')')[0].split()[-1]
        return {
            'name': func_name,
            'return_type': 'unknown',  # 宏函数难以自动提取返回类型
            'parameters': []  # 宏函数难以自动提取参数
        }

    def _extract_return_type(self, node, source_code: str) -> str:
        """提取返回类型"""
        type_node = (self._find_child(node, 'primitive_type') or 
                    self._find_child(node, 'type_identifier') or
                    self._find_child(node.parent, 'primitive_type') or
                    self._find_child(node.parent, 'type_identifier'))
        return source_code[type_node.start_byte:type_node.end_byte] if type_node else "void"

    def _extract_parameters(self, node, source_code: str) -> List[ParameterInfo]:
        """更健壮的参数提取"""
        params_node = None
        # 尝试多种可能的参数列表位置
        for possible in ['parameter_list', 'parameters', 'argument_list']:
            params_node = self._find_child(node, possible)
            if params_node:
                break
        
        if not params_node:
            return []

        parameters = []
        for child in params_node.children:
            if child.type in ['parameter_declaration', 'parameter']:
                param_type = self._find_child(child, 'type_identifier') or \
                        self._find_child(child, 'primitive_type') or \
                        self._find_child(child, 'qualified_identifier')
                
                param_name = self._find_child(child, 'identifier') or \
                        self._find_child(child, 'declarator')
                
                parameters.append({
                    'type': source_code[param_type.start_byte:param_type.end_byte] if param_type else 'void',
                    'name': source_code[param_name.start_byte:param_name.end_byte] if param_name else ''
                })
        return parameters

    @staticmethod
    def _find_child(node, child_type: str):
        """递归查找特定类型的子节点"""
        for child in node.children:
            if child.type == child_type:
                return child
            if found := HeaderAnalyst._find_child(child, child_type):
                return found
        return None
    
if __name__ == '__main__':
    analyst = HeaderAnalyst()
    with open('../output/build/cjson/include/cJSON.h', 'r') as f:
        content = f.read()
        type_info = analyst.extract_all_types(content, lang='c')
        
        print("完整结构体信息:")
        for name, struct in type_info["structs"].items():
            print(f"\n{name} (匿名: {struct['is_anonymous']})")
            for i, member in enumerate(struct["members"], 1):
                if member["is_nested"]:
                    print(f"  {i}. 嵌套结构: {member['type']}")
                    for nested_mem in member["members"]:
                        ptr = '*' if nested_mem['is_pointer'] else ''
                        arr = f"[{nested_mem['array_size']}]" if nested_mem['is_array'] else ''
                        bit = f":{nested_mem['bit_width']}" if nested_mem['bit_width'] is not None else ''
                        print(f"      {nested_mem['type']}{ptr} {nested_mem['name']}{arr}{bit}")
                else:
                    ptr = '*' if member['is_pointer'] else ''
                    arr = f"[{member['array_size']}]" if member['is_array'] else ''
                    bit = f":{member['bit_width']}" if member['bit_width'] is not None else ''
                    print(f"  {i}. {member['type']}{ptr} {member['name']}{arr}{bit}")