import json
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
        ['/workspace/tools/infer.sh', API1, API2, api1_info_str, api2_info_str],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    # Analyze the output to find semantic relevance
    output = result.stdout + result.stderr
    
    # Look for lines starting with <<< and extract the content after it
    for line in output.split('\n'):
        if line.strip().startswith('<<<'):
            # Extract the content after <<<
            content = line.split('<<<', 1)[1].strip()
            
            # Try to convert to float (this should be the semantic relevance score)
            try:
                semantic_relevance = float(content)
                break  # Found the score, break out of loop
            except ValueError:
                print(f"Warning: Could not convert '{content}' to float")
                continue
    
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
    example_context = [
        {
            "cJSON_version": {
                "ret_type": "char",
                "param_types": ["void"]
            },
            "cJSON_AddStringToObject": {
                "ret_type": "cJSON", 
                "param_types": ["cJSON", "char", "char"]
            }
        }
    ]
    
    result = analyze_correlation(
        "cJSON_version", 
        "cJSON_AddStringToObject", 
        example_context
    )
    print(f"Final result: {result}")