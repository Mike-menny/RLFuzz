import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser, Query, QueryCursor
import os
import json
from tools.depot import Depot

class FuncTypeAnalyzer:
    def __init__(self, header_dir, func_names):
        import tree_sitter_c as tsc
        import tree_sitter_cpp as tscpp
        from tree_sitter import Language, Parser, Query, QueryCursor
        import os
        self.tsc = tsc
        self.tscpp = tscpp
        self.Language = Language
        self.Parser = Parser
        self.QueryCursor = QueryCursor
        self.header_dir = header_dir
        self.header_paths = self._get_header_files()  # 修改为自动获取目录下头文件
        self.func_names = set(func_names)
        self.LANG = None
        self.parser = None
        self.initialize_parser()
        self.primitive_types = set([
            'void', 'char', 'short', 'int', 'long', 'float', 'double', 'signed', 'unsigned', 
            'bool', '_Bool', 'size_t', 'ssize_t', 'wchar_t', 'ptrdiff_t', 
            'int8_t', 'int16_t', 'int32_t', 'int64_t', 'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t'
        ])
        self.collected_types = set()
        self.type_defs = {}

    def _get_header_files(self):
        """获取目录下所有头文件路径"""
        header_exts = ('.h', '.hpp', '.hh', '.hxx')
        header_files = []
        for root, _, files in os.walk(self.header_dir):
            for file in files:
                if file.lower().endswith(header_exts):
                    header_files.append(os.path.join(root, file))
        return header_files

    def initialize_parser(self):
        # Determine language based on first file's extension
        first_path = self.header_paths[0]
        _, ext = os.path.splitext(first_path)
        ext = ext.lower()
        if ext in ['.h', '.cheader']:
            self.LANG = self.Language(self.tsc.language())
        elif ext in ['.hpp', '.cpp']:
            self.LANG = self.Language(self.tscpp.language())
        else:
            self.LANG = self.Language(self.tsc.language())
        self.parser = self.Parser(self.LANG)

    def read_files(self):
        content = ""
        for path in self.header_paths:
            with open(path, 'r', encoding='utf-8') as file:
                content += file.read() + "\n"
        return content

    def parse(self):
        content = self.read_files()
        return self.parser.parse(bytes(content, "utf8"))

    def query_functions(self, tree):
        query = Query(self.LANG, """
    (declaration) @func_decl
    """)
        cursor = self.QueryCursor(query)
        matches = cursor.captures(tree.root_node)
        return matches

    def query_types(self, tree):
        # Query for struct/union/enum/class/typedef definitions
        if self.LANG == self.Language(self.tscpp.language()):
            query = Query(self.LANG, """
(type_definition) @typedef
(struct_specifier) @struct
(union_specifier) @union
(enum_specifier) @enum
(class_specifier) @class
        """)
        else:
            query = Query(self.LANG, """
(type_definition)@typedef
(preproc_def)@macro
        """)
        cursor = self.QueryCursor(query)
        matches = cursor.captures(tree.root_node)
        return matches

    def extract_type_name(self, node):
        # 递归提取类型名，适配各种声明
        if node.type in ('type_identifier', 'primitive_type', 'struct_specifier', 'union_specifier', 'enum_specifier'):
            return node.text.decode('utf8')
        if node.type in ('pointer_declarator', 'abstract_pointer_declarator'):
            # 指针类型
            for child in node.children:
                t = self.extract_type_name(child)
                if t:
                    return t + ' *'
        if node.type == 'type_qualifier':
            # const/volatile等修饰符
            for child in node.children:
                t = self.extract_type_name(child)
                if t:
                    return 'const ' + t
        if node.type == 'macro_type_specifier':
            # 宏包裹的返回类型
            for child in node.children:
                t = self.extract_type_name(child)
                if t:
                    return t
        if node.type == 'type_descriptor':
            for child in node.children:
                t = self.extract_type_name(child)
                if t:
                    return t
        # 递归所有子节点
        for child in node.children:
            t = self.extract_type_name(child)
            if t:
                return t
        return None

    def extract_func_signature(self, decl_node):
        # decl_node: declaration
        func_name = None
        ret_type = None
        param_types = []
        func_decl = None
        # 找 function_declarator
        for child in decl_node.children:
            if child.type == 'function_declarator':
                func_decl = child
                break
        if not func_decl:
            return None
        # 函数名
        for c in func_decl.children:
            if c.type == 'identifier':
                func_name = c.text.decode('utf8')
                break
        # 返回类型
        for child in decl_node.children:
            if child.type not in ('function_declarator', 'init_declarator', 'identifier'):
                t = self.extract_type_name(child)
                if t:
                    ret_type = t
                    break
        # 参数类型
        for c in func_decl.children:
            if c.type == 'parameter_list':
                for param in c.children:
                    if param.type == 'parameter_declaration':
                        t = self.extract_type_name(param)
                        if t:
                            param_types.append(t)
        return func_name, ret_type, param_types

    def extract_func_types(self, tree):
        matches = self.query_functions(tree)
        func_types = {}
        for node in matches.get('func_decl', []):
            sig = self.extract_func_signature(node)
            if not sig:
                continue
            func_name, ret_type, param_types = sig
            if func_name and func_name in self.func_names:
                func_types[func_name] = {
                    'ret_type': ret_type,
                    'param_types': param_types
                }
        return func_types

    def collect_custom_types(self, func_types, tree):
        # Recursively collect all custom types used in func_types
        to_check = set()
        for f in func_types.values():
            if f['ret_type'] and f['ret_type'] not in self.primitive_types:
                to_check.add(f['ret_type'])
            for t in f['param_types']:
                if t and t not in self.primitive_types:
                    to_check.add(t)
        # Query all type definitions
        type_matches = self.query_types(tree)
        type_map = {}
        for cap, nodes in type_matches.items():
            for node in nodes:
                # Try to get the name of the type
                name = None
                for child in node.children:
                    if child.type in ('type_identifier', 'identifier'):
                        name = child.text.decode('utf8')
                        break
                if name:
                    type_map[name] = (node, cap)
        # Recursively collect
        def collect(name):
            if name in self.collected_types or name not in type_map:
                return
            self.collected_types.add(name)
            node, cap = type_map[name]
            self.type_defs[name] = node.text.decode('utf8')
            # For struct/union/class, check member types recursively
            for child in node.children:
                if child.type == 'field_declaration_list':
                    for field in child.children:
                        if field.type == 'field_declaration':
                            for cc in field.children:
                                if cc.type == 'type_identifier':
                                    tname = cc.text.decode('utf8')
                                    if tname not in self.primitive_types:
                                        collect(tname)
        for name in to_check:
            collect(name)

    def analyze(self):
        tree = self.parse()
        func_types = self.extract_func_types(tree)
        self.collect_custom_types(func_types, tree)
        return func_types, self.type_defs

    def extract_all_custom(self):
        """Extract all custom types (struct/union/enum/class/typedef) from all header files"""
        tree = self.parse()
        type_matches = self.query_types(tree)
        custom_types = {}

        for cap, nodes in type_matches.items():
            for node in nodes:
                # Try to get the name of the type
                name = None
                for child in node.children:
                    if child.type in ('type_identifier', 'identifier'):
                        name = child.text.decode('utf8')
                        break
                if name and name not in self.primitive_types:
                    custom_types[name] = node.text.decode('utf8')
        
        # Also collect types from field declarations in structs/unions/classes
        if self.LANG == self.Language(self.tscpp.language()):
            query = Query(self.LANG, """
    (struct_specifier) @struct
    (union_specifier) @union
    (class_specifier) @class
            """)
        else:
            query = Query(self.LANG, """
    (struct_specifier) @struct
    (union_specifier) @union
            """)
        
        cursor = self.QueryCursor(query)
        matches = cursor.captures(tree.root_node)
        
        for cap, nodes in matches.items():
            for node in nodes:
                # Get the name of the struct/union/class
                name_node = None
                for child in node.children:
                    if child.type == 'type_identifier':
                        name_node = child
                        break
                
                if name_node:
                    name = name_node.text.decode('utf8')
                    if name not in custom_types:
                        custom_types[name] = node.text.decode('utf8')
                    
                    # Get all field declarations
                    for child in node.children:
                        if child.type == 'field_declaration_list':
                            for field in child.children:
                                if field.type == 'field_declaration':
                                    for cc in field.children:
                                        if cc.type == 'type_identifier':
                                            tname = cc.text.decode('utf8')
                                            if tname not in self.primitive_types and tname not in custom_types:
                                                # Try to find the definition of this type
                                                def_query = Query(self.LANG, f"""
    (type_definition declarator: (type_identifier) @type[text="{tname}"])
    (struct_specifier name: (type_identifier) @type[text="{tname}"])
    (union_specifier name: (type_identifier) @type[text="{tname}"])
    (enum_specifier name: (type_identifier) @type[text="{tname}"])
                                                """)
                                                def_cursor = self.QueryCursor(def_query)
                                                def_matches = def_cursor.captures(tree.root_node)
                                                for _, def_nodes in def_matches.items():
                                                    for def_node in def_nodes:
                                                        custom_types[tname] = def_node.text.decode('utf8')
        
        return custom_types

    def print_result(self, bool = False):
        func_types, type_defs = self.analyze()
        if bool == True:
            print("Function Types:")
            print(json.dumps(func_types, indent=2, ensure_ascii=False))
            print("\nCollected Custom Types:")
            print(json.dumps(type_defs, indent=2, ensure_ascii=False))
        return [func_types, type_defs]

if __name__ == "__main__":
    project = "cJSON"
    path = Depot.find_case_insensitive_path(f"/workspace/output/build/{project}/include")
    combination=['cJSON_DetachItemViaPointer', 'cJSON_CreateObject', 'cJSON_ReplaceItemInObject', 'cJSON_GetObjectItem', 'cJSON_CreateBool', 'cJSON_GetArraySize', 'cJSON_IsString', 'cJSON_ReplaceItemInObjectCaseSensitive', 'cJSON_CreateObjectReference']
    analyzer = FuncTypeAnalyzer(path, combination)
    #analyzer.print_result()
    #context = analyzer.print_result()
    allcus = analyzer.extract_all_custom()
    print(allcus)