import json
import config
from utils.llm_client import LLMClient

def generate_preprocess_function(task_info: dict, llm_client: LLMClient) -> str | None:
    """
    Generates a Python function to preprocess raw user input into an API-ready payload.
    """
    print("\n--- STEP 4a: Generating Preprocess Function ---")

    model_info = task_info.get('model_information', {})
    input_format = model_info.get('input_format', {})
    input_description = task_info.get('task_description', {}).get('input', '')

    prompt = f"""
You are a Python expert. Your task is to write a single Python function `preprocess(*args)` that takes raw user input from Gradio components and converts it into a dictionary payload for an API.

**CRITICAL INSTRUCTIONS:**
1. The function signature MUST be `def preprocess(*args):`. The user input will be passed as arguments in the order they appear in the UI.
2. The returned dictionary's structure **MUST MATCH** the API INPUT FORMAT schema provided below.
3. **DO NOT** wrap the result in additional nested structures. Return the payload dictionary directly.
4. Handle different input types appropriately (text, files, numbers, etc.).
5. Include proper error handling for missing or invalid inputs.
6. Add necessary imports at the top of the file if needed (e.g., base64, json, os, etc.).

**INPUT PROCESSING GUIDELINES:**
- **Text inputs**: Use as-is or apply necessary transformations
- **File inputs**: Handle file paths - read, encode, or process as needed
- **Image files**: May need base64 encoding or binary reading
- **JSON/CSV files**: May need parsing or content extraction
- **Numeric inputs**: Convert to appropriate data types
- **Multiple inputs**: Map to corresponding API fields in order

**ERROR HANDLING:**
- Return None or appropriate default values for missing inputs
- Handle file reading errors gracefully
- Validate input types when necessary

---
**CONTEXT:**
- USER INPUT DESCRIPTION: "{input_description}"
- The function will receive inputs from Gradio components in the order they appear in the UI
- Each input will be passed as a separate argument in args

**API INPUT FORMAT** (This is the exact structure your returned dictionary must match):
```json
{json.dumps(input_format, indent=2)}
```

**EXAMPLES:**

Example 1 - Text input to API expecting "text" field:
```python
def preprocess(*args):
    user_text = args[0] if args else ""
    return {{"text": user_text}}
```

Example 2 - Image file to API expecting base64 "data" field:
```python
import base64

def preprocess(*args):
    image_path = args[0] if args else None
    if not image_path:
        return None
    
    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        return {{"data": encoded}}
    except Exception:
        return None
```

Example 3 - Multiple inputs to API expecting multiple fields:
```python
def preprocess(*args):
    text = args[0] if len(args) > 0 else ""
    number = args[1] if len(args) > 1 else 0
    return {{"input_text": text, "threshold": number}}
```

Now, analyze the API INPUT FORMAT and USER INPUT DESCRIPTION, then write the complete Python source code for the preprocess function that correctly maps the Gradio inputs to the API payload structure.
"""

    generated_code = llm_client.call(prompt)
    if generated_code:
        # Add a basic check to ensure it's generating a function
        if "def preprocess" not in generated_code:
            print("Error: LLM failed to generate a valid preprocess function.")
            return None
        with open(config.PREPROCESSOR_MODULE_PATH, 'w', encoding='utf-8') as f:
            f.write(generated_code)
        print(f"Preprocessor function saved to {config.PREPROCESSOR_MODULE_PATH}")
        return generated_code
    else:
        print("Error: The LLM failed to generate the preprocessor function.")
        return None