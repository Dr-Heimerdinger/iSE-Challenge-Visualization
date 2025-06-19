import os
import json
import importlib.util
import config
from utils.llm_client import LLMClient
import ast
import pathlib

def prepare_sample_data(task_info, task_dir, llm_client: LLMClient):
    """
    Uses the LLM to generate and execute code for preparing sample data.
    """
    print("\n--- STEP 2: Automatically Preparing Sample Data ---")
    
    # Validate inputs
    if not isinstance(llm_client, LLMClient) or not hasattr(llm_client, 'call'):
        print("Error: Invalid LLMClient provided")
        return None

    model_info = task_info.get('model_information', {})
    dataset_info = task_info.get('dataset_description', {})
    
    # Validate model_info and dataset_info
    if not model_info or not dataset_info:
        print("Error: Missing model_information or dataset_description in task_info")
        return None

    data_dir = os.path.join(task_dir, 'data')
    
    # Check if data_dir exists and contains files
    try:
        data_files = os.listdir(data_dir)
        if not data_files:
            print(f"Error: No files found in data directory '{data_dir}'")
            return None
    except FileNotFoundError:
        print(f"Error: Data directory not found at '{data_dir}'")
        return None

    # Precompute JSON strings for the prompt
    try:
        model_input_format = json.dumps(model_info.get('input_format', {}), indent=2)
        dataset_description = json.dumps(dataset_info, indent=2)
        data_files_json = json.dumps(data_files, indent=2)
    except (TypeError, ValueError) as e:
        print(f"Error: Failed to serialize model_info or dataset_info: {e}")
        return None

    # Construct the prompt
    prompt = f"""
You are a Python data processing expert. Write a single Python function named `prepare_sample_data(data_dir, task_dir)` to prepare an input sample for an ML model.

REQUIREMENTS:
1. The function takes `data_dir` (path to the directory containing data) and `task_dir` (path to the task directory) as input.
2. The function must read ONE data sample from `data_dir`.
3. The function must return a dictionary (payload) with the exact structure described in the `MODEL INPUT FORMAT` below.
4. Use standard Python libraries (e.g., os, pandas, json, csv) for data processing.
5. Do not include external dependencies or print statements in the function.

**EXAMPLE OF A CORRECT RETURN VALUE:**
If the model's input format is `{{ "texts": "a string" }}`, your function should return something like `{{ "texts": "I am feeling happy today." }}`.
If the model's input format is `{{ "image_path": "path to image" }}`, your function should return `{{ "image_path": "task_example/image_classification/data/cat.jpg" }}`.

NECESSARY INFORMATION:
1. MODEL INPUT FORMAT:
{model_input_format}
2. DATASET DESCRIPTION:
{dataset_description}
3. FILES IN DATA DIRECTORY:
{data_files_json}

Now, write the Python source code for the prepare_sample_data function. Return only the source code.
"""

    try:
        # Call LLM to generate code
        data_prep_code = llm_client.call(prompt)
        if not data_prep_code:
            print("Error: LLM did not return any code for data preparation")
            return None

        # Validate generated code syntax
        try:
            ast.parse(data_prep_code)
        except SyntaxError as e:
            print(f"Error: Generated code has invalid syntax: {e}")
            return None

        # Ensure the output directory exists
        pathlib.Path(os.path.dirname(config.DATA_PREP_MODULE_PATH)).mkdir(parents=True, exist_ok=True)

        # Write the generated code to a file
        with open(config.DATA_PREP_MODULE_PATH, "w", encoding="utf-8") as f:
            f.write(data_prep_code)
        print(f"Successfully generated data preparation code at {config.DATA_PREP_MODULE_PATH}")

        # Load and execute the generated module
        spec = importlib.util.spec_from_file_location(config.DATA_PREP_MODULE_NAME, config.DATA_PREP_MODULE_PATH)
        if spec is None:
            print(f"Error: Failed to create module spec for {config.DATA_PREP_MODULE_PATH}")
            return None

        data_preparer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_preparer)

        # Check if the required function exists
        if not hasattr(data_preparer, 'prepare_sample_data'):
            print("Error: Generated code does not define 'prepare_sample_data' function")
            return None

        # Execute the generated function
        payload = data_preparer.prepare_sample_data(data_dir, task_dir)
        print(f"Successfully created sample payload: {payload}")
        return payload

    except FileNotFoundError as e:
        print(f"Error: File operation failed: {e}")
        return None
    except AttributeError as e:
        print(f"Error: Invalid generated code structure: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during data preparation: {e}")
        return None