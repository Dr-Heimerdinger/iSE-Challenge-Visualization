import os
import json
import re
from utils.helpers import read_file, clean_llm_output  # [cite: 4]
from utils.langchain import create_llm_chain          # [cite: 4]
from config import GENERATED_CODE_DIR, PROMPTS_DIR, GENERATOR_MODEL  # [cite: 4]

def run(task_info: dict) -> str | None:
    """
    Step 2: Generate Gradio UI code based solely on the task description.
    """
    print("--- Running Step 2: Generate Gradio UI 3.30.0 Code (Based on Description Only) ---")

    if not task_info:
        print("❌ Error: Invalid task_info provided to Step 2")
        return None

    # Read the shared system prompt
    system_prompt_path = os.path.join(PROMPTS_DIR, "system_prompt.txt")  # [cite: 4]
    try:
        system_prompt = read_file(system_prompt_path)  # [cite: 4]
    except Exception as e:
        print(f"❌ Error reading system prompt: {e}")
        return None

    # Prompt template focused exclusively on task description
    user_prompt_template = """
Generate ONLY the Gradio UI 3.30.0 layout and component definitions based on the following task description.

**Task Description (JSON Format):**
{task_description_json}

**Important Rules:**
- From the description, infer the necessary input components (e.g., `gr.Image` for an image, `gr.Textbox` for text) and output components (e.g., `gr.Label`, `gr.Dataframe`).
- Your generated code should ONLY contain the UI component definitions inside a `gr.Blocks()` context.
- DO NOT include any event handlers (like `.click()`) or data processing logic.
- The main function must be named `create_ui()`.
- The function must return the final Blocks object.
- Make sure to import the `gradio` library as `gr`.
"""

    # Create LLM processing chain
    chain = create_llm_chain(system_prompt, model=GENERATOR_MODEL, temperature=0.2)  # [cite: 4]

    try:
        # Use only the 'task_description' part from task_info
        task_description_full = task_info.get("task_description", {})

        # Convert the task description dictionary into a JSON-formatted string
        task_description_json = json.dumps(task_description_full, indent=2, ensure_ascii=False)

        # Prepare variables for the simplified prompt
        prompt_variables = {
            "task_description_json": task_description_json
        }

        user_prompt = user_prompt_template.format(**prompt_variables)

        print("--- Sending Simplified UI Generation Prompt to LLM ---")
        generated_code = chain.invoke({"user_prompt": user_prompt})  # [cite: 4]
        cleaned_code = clean_llm_output(generated_code)  # [cite: 4]

        # Generate a safe filename from the task name
        task_name = task_info.get('task_name', 'unknown_task')  # [cite: 4]
        safe_task_name = re.sub(r'\s+', '_', task_name)  # [cite: 4]
        script_path = os.path.join(GENERATED_CODE_DIR, f"{safe_task_name}_ui.py")  # [cite: 4]

        # Save the generated UI code to a file
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(cleaned_code)

        print(f"✅ UI layout code generated and saved to {script_path}")
        return script_path
    except KeyError as e:
        print(f"❌ Missing 'task_description' key in task_info: {e}")
        return None
    except Exception as e:
        print(f"❌ Error during UI code generation: {e}")
        return None
