import json
import os
import config
from utils.llm_client import LLMClient

def assemble_ui(task_info: dict, preprocess_code: str, postprocess_code: str, llm_client: LLMClient, task_dir: str) -> str | None:
    """
    Assembles the final Gradio UI script by filling in a robust template.
    """
    print("\n--- STEP 4c: Assembling the Final Gradio UI using a Template ---")

    api_url = task_info.get('model_information', {}).get('api_url')
    task_description_str = json.dumps(task_info.get('task_description', {}), indent=2)

    prompt = f"""
You are an expert Python developer specializing in creating dynamic Gradio applications from a schema. Your task is to complete a Python script by filling in the `# TODO` sections of a template.

**PRIMARY INSTRUCTION:**
You must dynamically generate the Gradio input and output components by interpreting the `visualize.features` list within the `TASK DESCRIPTION` schema. For each object in the `fields` list of a feature, create one Gradio component.

**COMPONENT MAPPING LOGIC:**
- Use the dictionary key (e.g., `input_image`, `predicted_label`) as the Python variable name for the component.
- Infer the component type from the key and its description in the schema:
  - If a field is named or described as an 'image', 'picture', or 'photo', use `gr.Image()`.
  - If a field is named or described as 'label', 'text', 'sentence', or 'description', use `gr.Label()` for output or `gr.Textbox()` for input.
  - If a field is named or described as 'probability', 'confidence', 'score', or 'number', use `gr.Number()`.
  - For complex data like bounding boxes, classifications, or other dictionaries/lists, use `gr.JSON()`.
- **CRITICAL RULE: The `gr.JSON`, `gr.Label`, `gr.Dataframe`, and `gr.Image` output components DO NOT accept an `interactive` argument. You MUST NOT include `interactive=...` when creating these specific components.**
- The feature describing `input_function` defines the INPUT components.
- The feature describing `list_display` (or similar) defines the OUTPUT components.

**TEMPLATE TO COMPLETE:**
```python
import gradio as gr
import requests
import os
import json
import numpy as np
from {config.PREPROCESSOR_MODULE_NAME} import preprocess
from {config.POSTPROCESSOR_MODULE_NAME} import postprocess

# Define the task directory as a global constant
TASK_DIR = r"{os.path.normpath(task_dir)}"

# --- Interface Logic ---
def predict(*inputs):
    # The last input is always the API URL
    api_url = inputs[-1]
    raw_user_inputs = inputs[:-1]

    # Preprocess all raw inputs.
    payload = preprocess(*raw_user_inputs)
    
    # Runtime type check for the preprocessor output
    if not isinstance(payload, dict):
        raise gr.Error(f"Preprocessing failed! Expected a dictionary payload but got {{type(payload)}}.")
    
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        # Pass both API response and original inputs to postprocessor
        results = postprocess(response.json(), *raw_user_inputs)
        return results
    except requests.exceptions.RequestException as e:
        raise gr.Error(f"API Call Failed: {{str(e)}}")
    except Exception as e:
        raise gr.Error(f"An unexpected error occurred: {{str(e)}}")

# --- Gradio Interface Definition ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Auto-Generated UI for: {task_info.get('task_description', {}).get('type', 'ML Task')}")
    gr.Markdown("{task_info.get('task_description', {}).get('description', '')}")

    with gr.Row():
        with gr.Column(scale=1):
            # TODO: Define the Gradio INPUT components here by reflecting on the 'input_function' in the TASK DESCRIPTION.
            # Example: input_image = gr.Image(type="filepath", label="Upload Image")
            pass

            api_url_textbox = gr.Textbox(value="{api_url}", label="API URL", interactive=True)
            predict_button = gr.Button("Predict", variant="primary")

        with gr.Column(scale=1):
            # TODO: Define the Gradio OUTPUT components here by reflecting on the 'list_display' in the TASK DESCRIPTION.
            # The variable names must match the keys in the schema.
            # Example: output_image = gr.Image(label="Input Image")
            # Example: output_label = gr.Label(label="Predicted Label")
            pass

    # TODO: Define the list of all input components for the click event.
    # The order must match the `preprocess` function's expectation.
    inputs_list = [] 

    # TODO: Define the list of all output components for the click event.
    # The order must match the `postprocess` function's return tuple.
    outputs_list = [] 

    predict_button.click(
        fn=predict,
        inputs=inputs_list,
        outputs=outputs_list
    )

demo.launch(server_name="localhost", server_port=8080)
CONTEXT FOR COMPLETION:

TASK DESCRIPTION (Schema to be used for UI generation): {task_description_str}
Now, generate the complete Python script by filling in the # TODO sections based on the schema reflection instructions.
"""
    generated_code = llm_client.call(prompt)
    if generated_code:
        if "import gradio" not in generated_code:
            print("Error: The LLM failed to return a valid Gradio script.")
            return None
        with open(config.GENERATED_UI_PATH, 'w', encoding='utf-8') as f:
            f.write(generated_code)
        print(f"Final UI script assembled and saved to {config.GENERATED_UI_PATH}")
        return generated_code
    else:
        print("Error: The LLM failed to assemble the final UI script.")
        return None