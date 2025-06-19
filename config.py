import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- PATHS ---
# Main project directories
GENERATED_CODE_DIR = "generated_code"
TASK_EXAMPLES_DIR = "task_example"
PROMPTS_DIR = "prompts"

DEFAULT_TASK_YAML_PATH = os.getenv("YAML_FILE_DIR")

# --- LLM & API ---
# API Key for OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Models for generation and debugging
GENERATOR_MODEL = os.getenv("MODEL")
DEBUGGER_MODEL = os.getenv("MODEL")

# --- EXECUTION ---
# Max attempts for the debugging loop
MAX_DEBUG_ATTEMPTS = 2
# Timeout for sandbox execution in seconds
SANDBOX_TIMEOUT = 60
# Port for Gradio to run on
GRADIO_SERVER_PORT = 8080