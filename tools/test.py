import re
from typing import List
from swift.plugin import ORM, orms
from tools.depot import Depot
from swift.utils import get_logger
import time
from tools.rewards_test import Reward
from error_analysis.syntax_categorizer import syntax_categorize

text = """#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cJSON.h>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < 1) {
        return 0;
    }
    for (size_t i = 0; i < size; i++) {
        if (data[i] < 32 || data[i] > 126) {
            return 0;
        }
    }
    // Create memory streams for file operations
    char buffer[1024];
    FILE *mem_file = fmemopen(buffer, sizeof(buffer), "w+");
    if (!mem_file) {
        return 0;
    }
    while (setvbuf(mem_file, NULL, _IONBF, 0) != 0) {
        // Retry until successful
    }

    // Parse the input data into a cJSON object
    const char *json_data = reinterpret_cast<const char*>(data);
    cJSON *root = cJSON_ParseWithLength(json_data, size);
    if (!root) {
        const char *error_ptr = cJSON_GetErrorPtr();
        if (error_ptr) {
            fprintf(stderr, "Error before: %s\n", error_ptr);
        }
        fclose(mem_file);
        return 0;
    }

    // Add a new item to the JSON object
    cJSON *new_item = cJSON_CreateString("fuzzed_value");
    if (cJSON_AddItemToObject(root, "new_key", new_item) != 1) {
        fprintf(stderr, "Failed to add item to JSON object\n");
        cJSON_Delete(root);
        fclose(mem_file);
        return 0;
    }

    // Duplicate the JSON object
    cJSON *duplicated = cJSON_Duplicate(root, 1);
    if (!duplicated) {
        fprintf(stderr, "Failed to duplicate JSON object\n");
        cJSON_Delete(root);
        fclose(mem_file);
        return 0;
    }

    // Compare the original and duplicated JSON objects
    cJSON_bool are_equal = cJSON_Compare(root, duplicated, cJSON_CompareFull);
    if (!are_equal) {
        fprintf(stderr, "JSON objects are not equal\n");
    }

    // Print the duplicated JSON object to the memory stream
    if (cJSON_PrintPreallocated(duplicated, buffer, sizeof(buffer), 1) == 0) {
        fprintf(stderr, "Failed to print JSON object to memory stream\n");
    } else {
        fclose(mem_file);
        // Write the content of the memory stream to a file
        char output_path[] = "/workspace/output/projects/cjson/work/tem/fuzzed_output.txt";
        FILE *output_file = fopen(output_path, "w");
        if (output_file) {
            fprintf(output_file, "%s", buffer);
            fclose(output_file);
        } else {
            fprintf(stderr, "Failed to open output file\n");
        }
    }

    // Clean up resources
    cJSON_Delete(root);
    cJSON_Delete(duplicated);

    return 0;
}"""

epoch = 1
project_name = "cjson"
rewards=[]
error = None
            # Check for syntax errors
error = Reward.syntax_error(project_name=project_name,  epoch=epoch,  completion=1,  code=text)
if error:
                if error[1] is None or error[1][0]=="0":
                    rewards.append(0)
                    Reward.save_log(project_name, epoch, 1, 0, error, [])
                else:
                    rewards.append(-1.0)
                    Reward.save_log(project_name, epoch, 1, -1, error, [])
                exit()
            
            # Check for compilation errors
error = Reward.compilation_error(project_name=project_name, epoch=epoch, completion=1, additional_flags=["-O2"], debug=True)
if error:
                rewards.append(0.008)
                Reward.save_log(project_name, epoch, 1, 0.008, error,[])
                exit()
            
            # Check for fuzzing errors
error = Reward.fuzz_error(project_name=project_name, epoch=epoch, completion=1)
if error:
                rewards.append(0.04)
                Reward.save_log(project_name, epoch, 1, 0.04, error, [])
                exit()

            # If no errors
API_Called = Reward.API_coverage(project_name=project_name, epoch=epoch, completion=i)
rewards.append(0.04+API_Called[0])  
Reward.save_log(project_name, epoch, 1, rewards[-1], error, API_Called)

end_time = time.time()
elapsed_time = end_time - start_time
print("Reward computation took {:.2f} seconds".format(elapsed_time))

