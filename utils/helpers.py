import os

def read_file(file_path: str) -> str:
    """Reads a file and returns its content."""
    with open(file_path, 'r') as f:
        return f.read()

def clean_llm_output(code: str) -> str:
    """Removes markdown formatting from LLM code output."""
    if code.startswith("```python"):
        code = code[len("```python\n"):]
    if code.endswith("```"):
        code = code[:-len("```")]
    return code.strip()

def setup_directories():
    """Ensures that the necessary output directory exists."""
    if not os.path.exists(os.path.join(os.getcwd(), 'generated_code')):
        os.makedirs(os.path.join(os.getcwd(), 'generated_code'))