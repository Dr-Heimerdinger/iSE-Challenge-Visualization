# visualize/components/step_2_data_preparer.py

import os
import json
import importlib.util
import config
from utils.llm_client import LLMClient
import ast
import pathlib

def prepare_sample_data(task_info, task_dir, llm_client: LLMClient):
    """
    Uses the LLM to generate Python code that prepares a sample data payload,
    then executes that code.
    """
    print("\n--- STEP 2: Automatically Preparing Sample Data ---")

    model_info = task_info.get('model_information', {})
    dataset_info = task_info.get('dataset_description', {})

    if not model_info or not dataset_info:
        print("Error: Missing model_information or dataset_description in task_info")
        return None

    data_dir = os.path.join(task_dir, 'data')
    try:
        data_files = os.listdir(data_dir)
        if not data_files:
            print(f"Error: No files found in data directory '{data_dir}'")
            return None
    except FileNotFoundError:
        print(f"Error: Data directory not found at '{data_dir}'")
        return None

    model_input_format = json.dumps(model_info.get('input_format', {}), indent=2)
    dataset_description = json.dumps(dataset_info, indent=2)
    data_files_json = json.dumps(data_files, indent=2)

    # This is the new, unambiguous prompt that only asks for Python code.
    prompt = f"""
You are an expert Python developer. Your single task is to write a complete Python function `prepare_sample_data(data_dir, task_dir)`. This function will read one sample file and prepare it as a dictionary for an API call.

**FUNCTION REQUIREMENTS:**
1.  The function signature MUST be `def prepare_sample_data(data_dir, task_dir):`.
2.  It MUST read exactly ONE sample file from the `data_dir`. You can pick the first file found in the directory.
3.  It MUST handle different file types. For images (e.g., jpg, png), it must read the file in binary mode and encode it into a UTF-8 base64 string. For text files (e.g., csv, txt), it can read the first line.
4.  The function's return value MUST be a Python dictionary.
5.  The return value must be a dictionary that matches the keys and structure described in `MODEL INPUT FORMAT`. 
    Do NOT include metadata like 'type', 'description', or 'encoding' as values — only real input data should be used. 
    For example, if the schema says {{"data": "base64"}}, your return should be {{"data": "<base64_string>"}}.
6.  The function MUST import all necessary libraries inside itself (e.g., `import os`, `import base64`).
7.  The function must NOT contain any print statements.

**NECESSARY INFORMATION FOR WRITING THE FUNCTION:**

1.  **MODEL INPUT FORMAT (The schema your returned dictionary must follow):**
{model_input_format}

2.  **DATASET DESCRIPTION (Context about the data):**
{dataset_description}

3.  **FILES IN DATA DIRECTORY (Example files your function can read):**
{data_files_json}

Now, write only the complete and correct Python source code for the `prepare_sample_data` function. Do not add any explanations or comments outside the function.
Remember: your returned dictionary must contain actual **input values**, not the field schema itself.
"""

    try:
        print("Sending request to LLM to generate data preparation code...")
        data_prep_code = llm_client.call(prompt)
        if not data_prep_code or "def prepare_sample_data" not in data_prep_code:
            print(f"Error: LLM did not return valid Python code for the function. Response:\n{data_prep_code}")
            return None

        # Validate generated code syntax
        try:
            ast.parse(data_prep_code)
        except SyntaxError as e:
            print(f"Error: Generated code has invalid syntax: {e}")
            return None

        # Write the generated code to a file
        pathlib.Path(config.GENERATED_CODE_DIR).mkdir(parents=True, exist_ok=True)
        with open(config.DATA_PREP_MODULE_PATH, "w", encoding="utf-8") as f:
            f.write(data_prep_code)
        print(f"Successfully generated data preparation code at {config.DATA_PREP_MODULE_PATH}")

        # Load and execute the generated module
        spec = importlib.util.spec_from_file_location(config.DATA_PREP_MODULE_NAME, config.DATA_PREP_MODULE_PATH)
        if spec is None or spec.loader is None:
            print(f"Error: Failed to create module spec for {config.DATA_PREP_MODULE_PATH}")
            return None

        data_preparer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_preparer)

        if not hasattr(data_preparer, 'prepare_sample_data'):
            print("Error: Generated code does not define 'prepare_sample_data' function")
            return None

        # Execute the generated function to get the payload
        payload = data_preparer.prepare_sample_data(data_dir, task_dir)
        
        # Final validation of the payload
        if not isinstance(payload, dict):
            print(f"Error: The generated function returned a {type(payload)}, but a dictionary was expected.")
            return None
            
        print(f"Successfully created sample payload via generated code.")
        return payload

    except Exception as e:
        print(f"An unexpected error occurred during data preparation: {e}")
        return None