import os
import json
from utils.helpers import read_file, clean_llm_output
from utils.langchain import create_llm_chain
from config import GENERATED_CODE_DIR, PROMPTS_DIR, GENERATOR_MODEL, GRADIO_SERVER_PORT

def run(task_info: dict) -> str | None:
    """
    Generates the Gradio interface source code using an LLM.
    """
    print("--- Running Step 2: Generate Gradio UI Code ---")
    
    system_prompt_path = os.path.join(PROMPTS_DIR, "system_prompt_generate.txt")
    system_prompt = read_file(system_prompt_path)
    
    # Create the chain using our new utility
    chain = create_llm_chain(system_prompt, model=GENERATOR_MODEL, temperature=0.2)
    
    # The user prompt remains as a template string
    user_prompt_template = """
    Generate a complete Python script for a Gradio interface based on the following task.
    The final app must run on port {port}.

    **1. Task Details:**
    - **Type:** {task_type}
    - **Description:** {task_description}

    **2. Visualization Requirements:**
    - **Features:** {visualize_features}
    - **Example Data Path:** {data_path}

    **3. Model Information:**
    - **API URL:** {api_url}
    - **Verified Input Example:** {verified_input}
    - **Verified Output Example:** {verified_output}
    """
    
    prompt_variables = {
        "port": GRADIO_SERVER_PORT,
        "task_type": task_info["task_description"].get("type"), # 
        "task_description": task_info["task_description"].get("description"), # 
        "visualize_features": json.dumps(task_info["visualize"].get("features"), indent=2), # 
        "data_path": task_info.get("data_path"), # 
        "api_url": task_info["model_information"].get("api_url"), # 
        "verified_input": json.dumps(task_info["model_io"].get("verified_input"), indent=2),
        "verified_output": json.dumps(task_info["model_io"].get("verified_output"), indent=2),
    }

    try:
        # We format the user prompt separately as it's more complex
        user_prompt = user_prompt_template.format(**prompt_variables)
        generated_code = chain.invoke({"user_prompt": user_prompt})
        cleaned_code = clean_llm_output(generated_code)
        
        script_path = os.path.join(GENERATED_CODE_DIR, f"{task_info['task_name']}_ui.py")
        with open(script_path, "w") as f:
            f.write(cleaned_code)
            
        print(f"✅ Code generated and saved to {script_path}")
        return script_path
    except Exception as e:
        print(f"❌ Error during code generation: {e}")
        return None