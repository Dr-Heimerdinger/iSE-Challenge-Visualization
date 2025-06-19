import yaml

def parse_yaml(file_path):
    """Parses the task.yaml file and returns the configuration."""
    with open(file_path, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return None