import os
import json
import re 
from utils.helpers import read_file, clean_llm_output
from utils.langchain import create_llm_chain
from config import GENERATED_CODE_DIR, PROMPTS_DIR, GENERATOR_MODEL, GRADIO_SERVER_PORT

def run(task_info: dict) -> str | None:

    print("--- Running Step 2: Generate Gradio UI Code ---")

    system_prompt_path = os.path.join(PROMPTS_DIR, "system_prompt.txt")
    system_prompt = read_file(system_prompt_path)

    user_prompt_path = os.path.join(PROMPTS_DIR, "gen_ui_prompt.txt")
    user_prompt_template = read_file(user_prompt_path)

    chain = create_llm_chain(system_prompt, model=GENERATOR_MODEL, temperature=0.2)

    output_format_info = task_info.get("model_information", {}).get("output_format", {})

    post_processing_info = output_format_info.get("post_processing")
    post_processing_section = ""

    gradio_warnings = """
# --- GRADIO VERSION WARNINGS ---
# IMPORTANT: Avoid these deprecated patterns in Gradio 5.34.0
# - gr.File(file_types_allow_multiple=...): Use file_count='multiple' instead
# - gr.File(file_types=...): Use file_types=[...] without allow_multiple
# - gr.Image(type=..., type=...): Never repeat keyword arguments
    """
 
    if post_processing_info:
        print('post_processing_info', post_processing_info)
        post_processing_section = f"""- **Output Post-Processing:** The raw API output needs to be processed. Follow these steps:\n```json\n{json.dumps(post_processing_info, indent=2)}\n```"""


    guidance_info = output_format_info.get("guidance")
    guidance_section = ""

    if guidance_info:
        print('guidance_info', guidance_info)
        guidance_section = f"""- **API Guidance:** Additional instructions for handling the API output:\n{guidance_info}"""

    prompt_variables = {
        "port": GRADIO_SERVER_PORT,
        "task_type": task_info["task_description"].get("type"),
        "task_description": task_info["task_description"].get("description"),
        "visualize_features": json.dumps(task_info["visualize"].get("features"), indent=2, ensure_ascii=False),
        "data_path": task_info.get("data_path"),
        "api_url": task_info["model_information"].get("api_url"),
        "verified_input": json.dumps(task_info["model_io"].get("verified_input"), indent=2, ensure_ascii=False),
        "verified_output": json.dumps(task_info["model_io"].get("verified_output"), indent=2, ensure_ascii=False),
        "post_processing_section": post_processing_section,
        "guidance_section": guidance_section,
        "dataset_description": json.dumps(task_info.get("dataset_description", {}), indent=2, ensure_ascii=False),
        "auxiliary_file_paths": json.dumps(task_info.get("auxiliary_file_paths", {}), indent=2, ensure_ascii=False),
        "gradio_warnings": gradio_warnings
    }

    try:
        user_prompt = user_prompt_template.format(**prompt_variables)

        print("--- Sending Enhanced Prompt to LLM ---")

        generated_code = chain.invoke({"user_prompt": user_prompt})
        cleaned_code = clean_llm_output(generated_code)

        safe_task_name = re.sub(r'\s+', '_', task_info['task_name'])
        script_path = os.path.join(GENERATED_CODE_DIR, f"{safe_task_name}_ui.py")
        
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(cleaned_code)

        print(f"✅ Code generated and saved to {script_path}")
        return script_path
    except Exception as e:
        print(f"❌ Error during code generation: {e}")
        return None