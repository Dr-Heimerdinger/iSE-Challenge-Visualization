import argparse
import os
from utils import helpers
from components import step1_parse, step1b_verify_io, step1c_generate_api_handler, step2_generate, step2b_combine, step3_sandbox
from config import DEFAULT_TASK_YAML_PATH

def main():
    """
    Main pipeline orchestrator. Imports and runs steps from the components directory.
    """
    parser = argparse.ArgumentParser(description="ISE AutoCode Challenge 1: Generic UI Generator.")
    parser.add_argument(
        "--yaml_path",
        type=str,
        default=DEFAULT_TASK_YAML_PATH,
        help="Direct path to the task.yaml file for the unknown ML task."
    )
    args = parser.parse_args()
    
    if not os.path.exists(args.yaml_path):
        print(f"Error: YAML file not found at the specified path: {args.yaml_path}")
        return

    helpers.setup_directories()

    print(f"\n=============================================")
    print(f"STARTING PIPELINE FOR TASK: {args.yaml_path}")
    print(f"=============================================")
    
    # Step 1a: Parse the specified YAML file
    task_info = step1_parse.run(args.yaml_path)
    if not task_info:
        print("Pipeline failed at Step 1a. Aborting.")
        return

    # Step 1b: Verify the Model I/O with a live API call
    verified_task_info = step1b_verify_io.run(task_info)
    if not verified_task_info:
        print("Pipeline failed at Step 1b. Could not verify a working API request. Aborting.")
        return
        
    # Step 1c: Generate API handler logic
    task_info_with_handler = step1c_generate_api_handler.run(verified_task_info)
    if not task_info_with_handler:
        print("Pipeline failed at Step 1c. Aborting.")
        return
    
    # Step 2: Generate UI layout
    ui_script_path = step2_generate.run(task_info_with_handler)
    if not ui_script_path:
        print("Pipeline failed at Step 2. Aborting.")
        return
    
    # Step 2b: Combine UI and API handler
    full_script_path = step2b_combine.run(
        ui_script_path, 
        task_info_with_handler["api_handler_code"],
        task_info_with_handler
    )
    if not full_script_path:
        print("Pipeline failed at Step 2b. Aborting.")
        return
    
    # Step 3: Sandbox testing
    if "verified_input" not in task_info_with_handler.get("model_io", {}):
        print("⚠️ Warning: No verified input available for testing")
        
    step3_sandbox.run(full_script_path, task_info_with_handler)
    
    print(f"\n=============================================")
    print(f"PIPELINE FINISHED FOR TASK: {args.yaml_path}")
    print(f"=============================================")

if __name__ == "__main__":
    main()