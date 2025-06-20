import os
import re # Import thư viện regular expression

def read_file(file_path: str) -> str:
    """Reads a file and returns its content."""
    with open(file_path, 'r', encoding='utf-8') as f: # Thêm encoding='utf-8' để đảm bảo
        return f.read()

def clean_llm_output(llm_response: str) -> str:
    cleaned = re.sub(
        r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', 
        '', 
        llm_response
    )
    match = re.search(r"```python\n(.*?)```", llm_response, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    else:
        return cleaned.strip()

def setup_directories():
    """Ensures that the necessary output directory exists."""
    if not os.path.exists(os.path.join(os.getcwd(), 'generated_code')):
        os.makedirs(os.path.join(os.getcwd(), 'generated_code'))