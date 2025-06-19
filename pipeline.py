import os
import config
from utils.llm_client import LLMClient
from components.step_1_yaml_parser import parse_yaml
from components.step_2_data_preparer import prepare_sample_data
from components.step_3_api_caller import get_api_example
from components.step_4a_preprocess_generator import generate_preprocess_function
from components.step_4b_postprocess_generator import generate_postprocess_function
from components.step_4c_ui_assembler import assemble_ui
from components.step_5_executor import execute_and_debug
from dotenv import load_dotenv

load_dotenv()

def main():
    task_dir = os.getenv("FOLDER_DIR")
    task_yaml_path = os.path.join(task_dir, 'task.yaml')
    os.makedirs(config.GENERATED_CODE_DIR, exist_ok=True)

    llm_client = LLMClient()
    if not llm_client.client:
        print("Cannot initialize pipeline due to LLM Client error.")
        return

    # Step 1: Parse YAML
    task_info = parse_yaml(task_yaml_path)
    if not task_info:
        print("Failed to parse YAML. Exiting.")
        return

    # Step 2: Prepare sample data
    sample_payload = prepare_sample_data(task_info, task_dir, llm_client)
    if not sample_payload:
        print("Failed to prepare sample data. Exiting.")
        return

    # Step 3: Call API to get example output
    api_url = task_info.get('model_information', {}).get('api_url')
    api_example_output = get_api_example(api_url, sample_payload)
    if not api_example_output:
        print("Failed to call API. Exiting.")
        return

    # Step 4a: Generate preprocess function
    preprocess_code = generate_preprocess_function(task_info, llm_client)
    if not preprocess_code:
        print("Failed to generate preprocess function. Exiting.")
        return

    # Step 4b: Generate postprocess function
    postprocess_code = generate_postprocess_function(task_info, api_example_output, llm_client, task_dir)
    if not postprocess_code:
        print("Failed to generate postprocess function. Exiting.")
        return

    # Step 4c: Assemble final UI
    ui_code = assemble_ui(task_info, preprocess_code, postprocess_code, llm_client, task_dir)
    if not ui_code:
        print("Failed to assemble UI. Exiting.")
        return

    # Step 5 & 6: Execute and debug
    execute_and_debug(llm_client)

if __name__ == '__main__':
    main()
