import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("MODEL")

# Path configurations for automatically generated files
GENERATED_CODE_DIR = "generated_code"
DATA_PREP_MODULE_NAME = "data_preparer_module"
DATA_PREP_MODULE_PATH = os.path.join(GENERATED_CODE_DIR, f"{DATA_PREP_MODULE_NAME}.py")
GENERATED_UI_PATH = os.path.join(GENERATED_CODE_DIR, "generated_ui.py")


MAX_DEBUG_ATTEMPTS = 3 # Maximum number of retry attempts when debugging
EXECUTION_TIMEOUT = 45 # Time (in seconds) to wait to confirm the code runs stably