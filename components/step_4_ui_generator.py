# visualize/components/step_4_ui_generator.py

import json
import config
from utils.llm_client import LLMClient

def generate_ui_code(task_info, api_example_input, api_example_output, llm_client: LLMClient):
    """
    Uses the LLM to generate Gradio UI code.
    """
    print("\n--- STEP 4: Generating Gradio UI Code ---")

    prompt = f"""
You are a professional Python developer. Your task is to create a single Python script that uses the Gradio library to build a user interface for a Machine Learning task.

REQUIREMENTS:
1.  Analyze the information below to create the interface.
2.  The interface must allow users to input new data and call the model's API to get results.
3.  The interface must display illustrative examples from the dataset.
4.  The results must be displayed intuitively and clearly, as described in the `visualize` section.
5.  Use the `requests` library to call the API. Handle network or API errors gracefully.
6.  Launch the Gradio server on port 8080: `demo.launch(server_name="0.0.0.0", server_port=8080)`.

DETAILED TASK INFORMATION:
---
1. TASK DESCRIPTION:
{json.dumps(task_info.get('task_description'), indent=2)}
---
2. MODEL INFORMATION:
{json.dumps(task_info.get('model_information'), indent=2)}
---
3. DATASET DESCRIPTION:
{json.dumps(task_info.get('dataset_description'), indent=2)}
---
4. REAL API CALL EXAMPLE:
- Endpoint: `{task_info.get('model_information', {}).get('api_url')}`
- Input (Payload sent):
    ```json
    {json.dumps(api_example_input, indent=2)}
    ```
- Output (Response received):
    ```json
    {json.dumps(api_example_output, indent=2)}
    ```
---
Now, generate the complete Python script. Return only the source code.
"""

    generated_code = llm_client.call(prompt)
    if generated_code:
        with open(config.GENERATED_UI_PATH, 'w', encoding='utf-8') as f:
            f.write(generated_code)
        print(f"UI source code has been generated and saved to {config.GENERATED_UI_PATH}")
        return generated_code
    else:
        print("Error: The LLM failed to generate UI source code.")
        return None