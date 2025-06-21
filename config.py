import os
from dotenv import load_dotenv

load_dotenv()

# --- PATHS ---
GENERATED_CODE_DIR = "generated_code"
TASK_EXAMPLES_DIR = "private_test"
PROMPTS_DIR = "prompts"
# Thêm thư mục cho React
REACT_APP_DIR = "generated_react_app"
REACT_COMPONENTS_DIR = os.path.join(REACT_APP_DIR, "src", "components")

DEFAULT_TASK_YAML_PATH = os.getenv("YAML_FILE_DIR")

# --- LLM & API ---
# API Key for OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Models for generation and debugging
GENERATOR_MODEL = os.getenv("MODEL")
DEBUGGER_MODEL = os.getenv("MODEL")

SHARED_CONTEXT = {
    "task_name": "",
    "api_url": "",
    "input_format": {},
    "output_format": {},
    "auxiliary_files": {},
}

# --- EXECUTION ---
# Max attempts for the debugging loop
MAX_DEBUG_ATTEMPTS = 3
# Timeout for sandbox execution in seconds
SANDBOX_TIMEOUT = 120

# Add Streamlit-specific config
STREAMLIT_PORT = 8501
STREAMLIT_CONFIG_FILE = os.path.expanduser("~/.streamlit/config.toml")