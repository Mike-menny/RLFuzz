import os
os.environ['CUDA_VISIBLE_DEVICES'] = '4,5'
import re
import sys
from contextlib import contextmanager

import torch
os.environ.get('CUDA_VISIBLE_DEVICES')
torch.cuda.device_count()
names = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]

project_name = "cJSON"

@contextmanager
def silence_all_output():
    """Context manager to silence all stdout and stderr output"""
    with open(os.devnull, 'w') as devnull:
        old_out_fd = os.dup(1)
        old_err_fd = os.dup(2)
        old_stdout, old_stderr = sys.stdout, sys.stderr
        try:
            os.dup2(devnull.fileno(), 1)
            os.dup2(devnull.fileno(), 2)
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            os.dup2(old_out_fd, 1)
            os.dup2(old_err_fd, 2)
            os.close(old_out_fd)
            os.close(old_err_fd)

def syntax_categorize(error, code):
    """
    Analyze given error and code using LLM for classification
    
    Args:
        error (str): Error message
        code (str): Related code
        
    Returns:
        list: [extracted response content, full LLM output] or [None, None] if call fails
    """
    with silence_all_output():
        from swift.llm import PtEngine, RequestConfig, InferRequest
        try:
                    # 加载推理引擎
                    model = 'models/Qwen3-8B'
                    engine = PtEngine(model, max_batch_size=1)
                    request_config = RequestConfig(max_tokens=4096, temperature=0)
                    # Create inference request
                    infer_request = InferRequest(messages=[
                        {
                            'role': 'system', 
                            'content': f"Analyze error given in the user message for {project_name} fuzz drivers; output ONLY a Python list [0 or 1, \'type1\', \'type2\', ...] (multiple types allowed for more than one error); 0 = no API-related errors, 1 = at least one API-related error; allowed types: if API-related errors exist (1), then include: \'library header file include error\', \'API not exist error\', \'wrong parameter type error\', \'API parameter length mismatch error\', \'library error: others\'; if no API-related errors (0), then include: \'non-API misuse error: related to fmemopen\', \'non-API misuse error: others\'; set 1 only if {project_name} headers/types/functions/linkage are implicated; fmemopen is non-library; output all error types found in the message."
                        },
                        {
                            'role': 'user', 
                            'content': f"code:\n{code} \nerror: \n{error}"
                        }
                    ])
                    
                    # Execute inference
                    resp_list = engine.infer([infer_request], request_config)
                    
                    if resp_list:
                        # Get complete LLM output
                        full_output = resp_list[0].choices[0].message.content
                        
                        # Extract response content using regex pattern matching
                        pattern = r'\[(0|1),\s*\'([^\']+)\'[^\]]*\]'
                        match = re.search(pattern, full_output)
                        
                        extracted_response = None
                        if match:
                            # Build extracted response format
                            is_cjson_related = match.group(1)
                            error_type = match.group(2)
                            extracted_response = f"[{is_cjson_related}, '{error_type}']"
                        return [extracted_response, full_output]
                    return None
                
        except Exception as e:
                    print(f"Warning: LLM call failed with error: {e}")
                    return None
    

if __name__ == "__main__":
    # 示例用法
    error = "Subprocess error (return code 1): /workspace/output/projects/cjson/harnesses/harness_00568/id_00003.cpp:112:12: error: no matching function for call to 'cJSON_ParseWithOpts';   112 |     return cJSON_ParseWithOpts(json, options, allow_non_const_char_ptr);;       |            ^~~~~~~~~~~~~~~~~~~; /workspace/output/build/cjson/include/cJSON.h:158:23: note: candidate function not viable: no known conversion from 'const char *' to 'const char **' for 2nd argument; take the address of the argument with &;   158 | CJSON_PUBLIC(cJSON *) cJSON_ParseWithOpts(const char *value, const char **return_parse_end, cJSON_bool require_null_terminated);;       |                       ^                                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~; /workspace/output/projects/cjson/harnesses/harness_00568/id_00003.cpp:116:12: error: no matching function for call to 'cJSON_ParseWithLengthOpts';   116 |     return cJSON_ParseWithLengthOpts(json, length, options, allow_non_const_char_ptr);;       |            ^~~~~~~~~~~~~~~~~~~~~~~~~; /workspace/output/build/cjson/include/cJSON.h:159:23: note: candidate function not viable: no known conversion from 'const char *' to 'const char **' for 3rd argument; take the address of the argument with &;   159 | CJSON_PUBLIC(cJSON *) cJSON_ParseWithLengthOpts(const char *value, size_t buffer_length, const char **return_parse_end, cJSON_bool require_null_terminated);;       |                       ^                                                                  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~; 2 errors generated.; clang++ -fsyntax-only -std=c++17 -I/workspace/output/build/cjson/include /workspace/output/projects/cjson/harnesses/harness_00568/id_00003.cpp"
    code = """
    #include <cJSON.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <vector>

// LIFECYCLE PHASE: Factory
cJSON* create_cjson_object(const char* json) {
    return cJSON_Parse(json);
}

cJSON* create_cjson_number(double value) {
    return cJSON_CreateNumber(value);
}

cJSON* create_cjson_true() {
    return cJSON_CreateTrue();
}

cJSON* create_cjson_false() {
    return cJSON_CreateFalse();
}

cJSON* create_cjson_null() {
    return cJSON_CreateNull();
}

cJSON* create_cjson_string(const char* str) {
    return cJSON_CreateString(str);
}

cJSON* create_cjson_array() {
    return cJSON_CreateArray();
}

cJSON* create_cjson_object_reference(cJSON* object) {
    return cJSON_CreateObjectReference(object);
}

cJSON* create_cjson_array_reference(cJSON* array) {
    return cJSON_CreateArrayReference(array);
}

// LIFECYCLE PHASE: Processor
void add_item_to_array(cJSON* array, cJSON* item) {
    cJSON_AddItemToArray(array, item);
}

void add_item_to_object(cJSON* object, const char* key, cJSON* item) {
    cJSON_AddItemToObject(object, key, item);
}

void add_true_to_object(cJSON* object, const char* key) {
    cJSON_AddTrueToObject(object, key);
}

void add_false_to_object(cJSON* object, const char* key) {
    cJSON_AddFalseToObject(object, key);
}

void add_null_to_object(cJSON* object, const char* key) {
    cJSON_AddNullToObject(object, key);
}

void add_number_to_object(cJSON* object, const char* key, double value) {
    cJSON_AddNumberToObject(object, key, value);
}

void add_string_to_object(cJSON* object, const char* key, const char* str) {
    cJSON_AddStringToObject(object, key, str);
}

void add_array_to_object(cJSON* object, const char* key) {
    cJSON_AddArrayToObject(object, key);
}

void add_object_to_object(cJSON* object, const char* key) {
    cJSON_AddObjectToObject(object, key);
}

void insert_item_in_array(cJSON* array, int index, cJSON* item) {
    cJSON_InsertItemInArray(array, index, item);
}

void replace_item_in_object(cJSON* object, const char* key, cJSON* item) {
    cJSON_ReplaceItemInObject(object, key, item);
}

void replace_item_in_array(cJSON* array, int index, cJSON* item) {
    cJSON_ReplaceItemInArray(array, index, item);
}

cJSON* detach_item_from_object(cJSON* object, const char* key) {
    return cJSON_DetachItemFromObject(object, key);
}

cJSON* detach_item_from_array(cJSON* array, int index) {
    return cJSON_DetachItemFromArray(array, index);
}

cJSON* duplicate_cjson(cJSON* object, cJSON_bool with_contents) {
    return cJSON_Duplicate(object, with_contents);
}

cJSON* parse_json_with_length(const char* json, size_t length) {
    return cJSON_ParseWithLength(json, length);
}

cJSON* parse_json_with_opts(const char* json, const char* options, cJSON_bool allow_non_const_char_ptr) {
    return cJSON_ParseWithOpts(json, options, allow_non_const_char_ptr);
}

cJSON* parse_json_with_length_opts(const char* json, size_t length, const char* options, cJSON_bool allow_non_const_char_ptr) {
    return cJSON_ParseWithLengthOpts(json, length, options, allow_non_const_char_ptr);
}

void set_valuestring(cJSON* object, const char* value) {
    cJSON_SetValuestring(object, value);
}

void set_number_value(cJSON* object, double value) {
    object->valuedouble = value;
}

void minify_json(char* json) {
    cJSON_Minify(json);
}

// LIFECYCLE PHASE: Destructor
void delete_cjson(cJSON* object) {
    cJSON_Delete(object);
}

// Invalid enum injection function
void inject_invalid_enum(cJSON* object) {
    object->type = 10; // 10 is not a valid enum value for cJSON
}

// Input mapping via fmemopen()
cJSON* process_input(const uint8_t* data, size_t size) {
    char* json = (char*)malloc(size + 1);
    memcpy(json, data, size);
    json[size] = '\0';

    // Inject invalid enum with 15% probability
    if (rand() % 100 < 15) {
        inject_invalid_enum((cJSON*)json);
    }

    cJSON* result = parse_json_with_length(json, size);
    free(json);
    return result;
}

// Verify memory invariants after transitions
void verify_memory_invariants(cJSON* object) {
    if (object == nullptr) {
        std::cerr << "Error: Object is null" << std::endl;
        exit(EXIT_FAILURE);
    }
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    cJSON* root = process_input(data, size);

    // Verify memory invariants
    verify_memory_invariants(root);

    // Clean up
    delete_cjson(root);

    return 0;
}"""

    result = syntax_categorize(error, code)
    print("Extracted Response:", result[0])
    print("Full LLM Output:", result[1])