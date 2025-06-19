import os
import yaml
from utils.helpers import read_file

def run(yaml_path: str) -> dict | None:
    print("--- Running Step 1: Parse Task Configuration ---")

    try:
        config = yaml.safe_load(read_file(yaml_path))
        yaml_dir = os.path.dirname(yaml_path)
        
        # Đổi từ basename directory sang lấy từ YAML
        task_name = config.get("task_description", {}).get("type", "unknown_task")

        relative_data_path = config.get("dataset_description", {}).get("data_path")
        if relative_data_path:
            absolute_data_path = os.path.abspath(os.path.join(yaml_dir, relative_data_path))
        else:
            absolute_data_path = os.path.abspath(os.path.join(yaml_dir, "data"))

        task_info = {
            "task_name": task_name,
            "task_description": config.get("task_description", {}),
            "visualize": config.get("task_description", {}).get("visualize", {}),
            "model_information": config.get("model_information", {}),
            "dataset_description": config.get("dataset_description", {}),
            "data_path": absolute_data_path,
        }
        print(f"✅ YAML parsed successfully. Derived task name: '{task_name}'")
        # print('task_info', task_info)

        model_io = {
            "input_format": task_info["model_information"].get("input_format"),
            "output_format": task_info["model_information"].get("output_format")
        }

        if not model_io["input_format"] or not model_io["output_format"]:
            print("⚠️ Warning: Model I/O not explicitly defined in YAML.")
        
        task_info["model_io"] = model_io
        print("✅ Model I/O format determined.")
        
        return task_info

    except Exception as e:
        print(f"Error processing YAML file at {yaml_path}: {e}")
        return None

    """
    Parses a given task.yaml file and resolves relative paths.
    """
    print("--- Running Step 1: Parse Task Configuration ---")
    
    try:
        config = yaml.safe_load(read_file(yaml_path))
        yaml_dir = os.path.dirname(yaml_path)
        
        # Derive a task name from the parent directory of the YAML file
        task_name = os.path.basename(yaml_dir)
        print('config', config)
        print("--------------------------------")
        print('yaml_dir', yaml_dir)
        print("--------------------------------")
        print('task_name', task_name)

        # Resolve the data_path relative to the YAML file's location
        # This correctly handles paths like "./data".
        relative_data_path = config.get("dataset_description", {}).get("data_path")
        if relative_data_path:
            absolute_data_path = os.path.abspath(os.path.join(yaml_dir, relative_data_path))
        else:
            # Fallback if data_path isn't specified, though it usually is.
            absolute_data_path = os.path.abspath(os.path.join(yaml_dir, "data"))

        # Structure the information for easier access
        task_info = {
            "task_name": task_name,
            "task_description": config.get("task_description", {}),
            "visualize": config.get("task_description", {}).get("visualize", {}),
            "model_information": config.get("model_information", {}),
            "dataset_description": config.get("dataset_description", {}),
            "data_path": absolute_data_path, # Use the resolved, absolute path
        }
        print(f"✅ YAML parsed successfully. Derived task name: '{task_name}'")

        model_io = {
            "input_format": task_info["model_information"].get("input_format"),
            "output_format": task_info["model_information"].get("output_format")
        }
        
        if not model_io["input_format"] or not model_io["output_format"]:
            print("⚠️ Warning: Model I/O not explicitly defined in YAML.")
        
        task_info["model_io"] = model_io
        print("✅ Model I/O format determined.")
        
        return task_info

    except Exception as e:
        print(f"Error processing YAML file at {yaml_path}: {e}")
        return None