import os
import json
import re
from utils.helpers import read_file, clean_llm_output
from utils.langchain import create_llm_chain
from utils.component_parser import extract_ui_components
from utils.context import TaskContext
from config import GENERATED_CODE_DIR, PROMPTS_DIR, GENERATOR_MODEL

def run(task_info: dict) -> str | None:

    print("--- Running Step 2: Generate UI Code ---")

    if not task_info:
        print("❌ Error: Invalid task_info provided to Step 2")
        return None

    # Get shared context or create new
    context = task_info.get("shared_context", TaskContext())
    
    # Read system prompt
    system_prompt_path = os.path.join(PROMPTS_DIR, "system_prompt.txt")
    try:
        system_prompt = read_file(system_prompt_path)
    except Exception as e:
        print(f"❌ Error reading system prompt: {e}")
        return None

    # Read UI generation prompt template
    ui_prompt_path = os.path.join(PROMPTS_DIR, "gen_ui_prompt.txt")
    try:
        user_prompt_template = read_file(ui_prompt_path)
    except Exception as e:
        print(f"❌ Error reading UI generation prompt: {e}")
        return None

    # Prepare prompt variables
    task_description_full = task_info.get("task_description", {})
    task_type = task_description_full.get("type", "unknown")
    visualize = task_description_full.get("visualize", {})
    features = visualize.get("features", [])
    visualize_features = "\n".join([json.dumps(f, indent=2, ensure_ascii=False) for f in features])
    
    # Prepare auxiliary file paths
    auxiliary_file_paths = task_info.get("auxiliary_file_paths", {})
    auxiliary_paths_str = "\n".join([f"{k}: {v}" for k, v in auxiliary_file_paths.items()])
    
    # Prepare post-processing section
    post_processing = task_info.get("model_io", {}).get("output_format", {}).get("post_processing", {})
    post_processing_section = f"Post-processing Steps:\n{json.dumps(post_processing, indent=2)}" if post_processing else ""
    
    # Prepare dataset description
    dataset_description = task_info.get("dataset_description", {})
    dataset_desc_str = json.dumps(dataset_description, indent=2, ensure_ascii=False)
    
    # Prepare verified input/output
    verified_input = task_info.get("model_io", {}).get("verified_input", {})
    verified_output = task_info.get("model_io", {}).get("verified_output", {})
    
    # Prepare port
    port = 8080
    

    # Format user prompt
    prompt_variables = {
        "task_type": task_type,
        "task_description": json.dumps(task_description_full, indent=2, ensure_ascii=False),
        "port": port,
        "visualize_features": visualize_features,
        "api_url": task_info.get("model_information", {}).get("api_url", ""),
        "verified_input": json.dumps(verified_input, indent=2, ensure_ascii=False),
        "verified_output": json.dumps(verified_output, indent=2, ensure_ascii=False),
        "post_processing_section": post_processing_section,
        "data_path": task_info.get("data_path", ""),
        "dataset_description": dataset_desc_str,
        "auxiliary_file_paths": auxiliary_paths_str,
        "context": json.dumps(context.to_dict(), indent=2),
        "api_handler_code": task_info.get("api_handler_code")
    }
    
    user_prompt = user_prompt_template.format(**prompt_variables)

    # Create LLM processing chain
    chain = create_llm_chain(system_prompt, model=GENERATOR_MODEL, temperature=0.2)

    try:
        print("--- Sending UI Generation Prompt to LLM ---")
        generated_code = chain.invoke({"user_prompt": user_prompt})
        cleaned_code = clean_llm_output(generated_code)

        # Generate safe filename
        task_name = task_info.get('task_name', 'unknown_task')
        safe_task_name = re.sub(r'\s+', '_', task_name)
        script_path = os.path.join(GENERATED_CODE_DIR, f"{safe_task_name}_app.py")

        # Save UI code
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(cleaned_code)

        # Extract UI components and update context
        context = task_info.get("shared_context", TaskContext())
        context.ui_components = extract_ui_components(cleaned_code)
        task_info["shared_context"] = context

        print(f"✅ UI layout code generated and saved to {script_path}")
        return script_path
    except KeyError as e:
        print(f"❌ Missing key in task_info: {e}")
        return None
    except Exception as e:
        print(f"❌ Error during UI code generation: {e}")
        return None