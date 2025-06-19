import yaml

def parse_yaml(yaml_path):
    """
    Parses a YAML file and returns its content as a dictionary.
    """
    print(f"--- STEP 1: Reading and parsing the {yaml_path} file ---")
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        print("YAML parsed successfully.")
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {yaml_path}")
        return None
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return None