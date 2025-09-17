import json
import re
import subprocess

def analyze_correlation(API1: str, API2: str, context: list) -> float:
    """
    Analyze the correlation between two APIs
    
    Args:
        API1: First API name
        API2: Second API name  
        context: Context information list containing API definitions and type definitions
        
    Returns:
        float: Average of type relevance and semantic relevance
    """
    
    # Step 1: Extract API information from context
    api_info_1 = None
    api_info_2 = None
    
    # Iterate through context to find API definitions
    for item in context:
        if isinstance(item, dict):
            if API1 in item:
                api_info_1 = item[API1]
            if API2 in item:
                api_info_2 = item[API2]
    
    # Return 0 if either API is not found
    if api_info_1 is None or api_info_2 is None:
        print(f"Warning: Could not find {API1} or {API2} in context")
        return 0.0
    
    # Step 2: Calculate type relevance
    type_relevance = 0
    ret_type_1 = api_info_1.get('ret_type', '')
    param_types_2 = api_info_2.get('param_types', [])
    
    if ret_type_1 in param_types_2:
        type_relevance = 1
    
    # Step 3: Call external script to get semantic relevance
    semantic_relevance = 0.0
    
    # Prepare API info as JSON strings
    api1_info_str = json.dumps(api_info_1)
    api2_info_str = json.dumps(api_info_2)
    
    # Call infer.sh and capture output
    result = subprocess.run(
        ['tools/infer_test.sh', API1, API2, api1_info_str, api2_info_str],
        capture_output=True,
        text=True,
        timeout=120
    )
    if result.returncode != 0:
        print(f"Warning: LLM inference for semantic analysis failed")
    # Analyze the output to find semantic relevance
    output = result.stdout #+ result.stderr
    #print(output)

    # Step 1: Delete everything before </think> (including </think>)
    if '</think>' in output:
        # Get everything after the last occurrence of </think>
        output = output.split('</think>')[-1].strip()
    else:
        # If no </think> found, use the entire output
        output = output.strip()

    # Step 2: Delete the line with only "-" and everything after it
    lines = output.split('\n')
    clean_output = []
    found_dash_line = False

    for line in lines:
        line = line.strip()
        if len(line)>=5 and line[4] == '-':  # Found the line with only "--------"
            found_dash_line = True
            break  # Stop processing further lines
        if not found_dash_line:
            clean_output.append(line)

    # Join the cleaned lines
    cleaned_content = '\n'.join(clean_output).strip()

    # Step 3: Convert the remaining content to float
    semantic_relevance = 0.0
    if cleaned_content:
        try:
            # Try to convert the entire cleaned content to float
            semantic_relevance = float(cleaned_content)
        except ValueError:
            # If not a single number, look for the first numeric value
            numbers = re.findall(r'[-+]?\d*\.?\d+', cleaned_content)
            if numbers:
                try:
                    semantic_relevance = float(numbers[0])
                except ValueError:
                    print(f"Warning: Could not convert extracted number to float: '{numbers[0]}'")
            else:
                print(f"Warning: Could not find any numeric value in cleaned content: '{cleaned_content}'")
        if cleaned_content:
            # Check if the cleaned content is a single number
            try:
                # Try to convert the entire cleaned content to float
                semantic_relevance = float(cleaned_content)
            except ValueError:
                # If not a single number, look for the first line that contains only a number
                for line in cleaned_content.split('\n'):
                    line = line.strip()
                    if line:  # Skip empty lines
                        try:
                            semantic_relevance = float(line)
                            break  # Found a valid number
                        except ValueError:
                            continue  # Not a number, continue to next line
                
                print(f"Warning: Could not extract valid float from cleaned content: '{cleaned_content}'")
        
        # Step 4: Calculate average
        average_relevance = (type_relevance + semantic_relevance) / 2.0
    
    # Print debug information
    print(f"API1: {API1}, Return type: {ret_type_1}")
    print(f"API2: {API2}, Parameter types: {param_types_2}")
    print(f"Type relevance: {type_relevance}")
    print(f"Semantic relevance: {semantic_relevance}")
    print(f"Average relevance: {average_relevance}")
    
    return average_relevance

# Example usage
if __name__ == "__main__":
    # Example context
    example_context = [
        {
            "cJSON_version": {
                "ret_type": "char",
                "param_types": ["void"]
            },
            "cJSON_AddStringToObject": {
                "ret_type": "cJSON", 
                "param_types": ["cJSON", "char", "char"]
            },
            "cJSON_Parse": {
                "ret_type": "cJSON",
                "param_types": ["char"]
            },
            "cJSON_GetObjectItem": {
                "ret_type": "cJSON",
                "param_types": ["cJSON", "char"]
            }
        }
    ]
    
    # Example API sequence
    api_sequence = [
        "cJSON_version",
        "cJSON_AddStringToObject", 
        "cJSON_Parse",
        "cJSON_GetObjectItem"
    ]
    
    # Analyze consecutive pairs and get sum
    total_score = analyze_api_list(api_sequence, example_context)
    
    print(f"Final total correlation sum: {total_score}")