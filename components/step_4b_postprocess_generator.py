import json
import config
from utils.llm_client import LLMClient

def generate_postprocess_function(task_info: dict, api_example_output: dict, llm_client: LLMClient, task_dir: str) -> str | None:
    """
    Generates a Python function to postprocess the raw API response for display.
    """
    print("\n--- STEP 4b: Generating Postprocess Function ---")

    output_format_guidance = task_info.get('model_information', {}).get('output_format', {}).get('guidance', '')
    visualize_info = task_info.get('task_description', {}).get('visualize', {})

    prompt = f"""
You are a Python expert. Write a single Python function `postprocess(api_response, *original_inputs)` that transforms the raw API response into the final format required by the UI.

**CRITICAL REQUIREMENT:**
The function's return value MUST be a tuple of values. The order and number of elements in the returned tuple MUST EXACTLY MATCH the fields described in the `VISUALIZATION INFO` section. For example, if the UI needs to display `input_image`, then `predicted_label`, your function must `return input_image, predicted_label`.

REQUIREMENTS:
1.  The function signature MUST be `def postprocess(api_response, *original_inputs):`.
2.  The `original_inputs` tuple contains the raw user inputs (e.g., a file path) which you may need for the final output.
3.  The function must rigorously follow the `PROCESSING LOGIC AND GUIDANCE` to transform the `api_response`.
4.  You MUST import necessary libraries (e.g., numpy, json) inside the function.
5.  To access any auxiliary files (like label mappings), use the global `TASK_DIR` variable, which will be available in the execution environment.

---
PROCESSING LOGIC AND GUIDANCE:
{output_format_guidance}
---
VISUALIZATION INFO (This defines the fields your function must return values for, and in what order):
{json.dumps(visualize_info, indent=2)}
---
EXAMPLE of raw `api_response`:
{json.dumps(api_example_output, indent=2)}
---

Now, write only the complete Python source code for the `postprocess` function.
"""

    generated_code = llm_client.call(prompt)
    if generated_code:
        with open(config.POSTPROCESSOR_MODULE_PATH, 'w', encoding='utf-8') as f:
            f.write(generated_code)
        print(f"Postprocessor function saved to {config.POSTPROCESSOR_MODULE_PATH}")
        return generated_code
    else:
        print("Error: The LLM failed to generate the postprocessor function.")
        return None