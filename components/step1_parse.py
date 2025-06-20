import os
import yaml
import glob
from utils.helpers import read_file

def run(yaml_path: str) -> dict | None:
    print("--- Running Step 1: Parse Task Configuration ---")
    try:
        config = yaml.safe_load(read_file(yaml_path))
        yaml_dir = os.path.dirname(yaml_path)

        task_name = config.get("task_description", {}).get("type", "unknown_task")

        # Lấy đường dẫn data_path
        relative_data_path = config.get("dataset_description", {}).get("data_path")
        if relative_data_path:
            absolute_data_path = os.path.abspath(os.path.join(yaml_dir, relative_data_path))
        else:
            absolute_data_path = os.path.abspath(os.path.join(yaml_dir, "data"))

        auxiliary_file_paths = {}
   
        for pattern in ("*.json", "*.csv"):
            for file_path in glob.glob(os.path.join(yaml_dir, pattern)):
                filename = os.path.basename(file_path)
                auxiliary_file_paths[filename] = os.path.abspath(file_path)

        task_info = {
            "task_name": task_name,
            "task_description": config.get("task_description", {}),
            "visualize": config.get("task_description", {}).get("visualize", {}),
            "model_information": config.get("model_information", {}),
            "dataset_description": config.get("dataset_description", {}),
            "data_path": absolute_data_path,
            "auxiliary_file_paths": auxiliary_file_paths,
        }
        print(f"✅ YAML parsed successfully. Derived task name: '{task_name}'")
        if auxiliary_file_paths:
            print(f"✅ Found auxiliary files: {list(auxiliary_file_paths.keys())}")

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