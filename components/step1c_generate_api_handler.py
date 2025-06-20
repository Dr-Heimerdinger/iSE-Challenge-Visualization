import os
import json
import re
from utils.helpers import read_file, clean_llm_output
from utils.langchain import create_llm_chain
from utils.context import TaskContext
from config import PROMPTS_DIR, GENERATOR_MODEL

def run(task_info: dict) -> dict | None:
    print("--- Running Step 1c: Generate API Handler & Post-processing Logic ---")
    
    # Khởi tạo hoặc cập nhật context
    context = task_info.get("shared_context", TaskContext())
    
    # SỬA: Sử dụng set_value thay vì update
    context.set_value("task_name", task_info.get("task_name", "Unknown Task"))
    context.set_value("api_url", task_info["model_information"].get("api_url", ""))
    context.set_value("input_format", task_info["model_io"]["input_format"])
    context.set_value("output_format", task_info["model_io"]["output_format"])
    
    # Đọc prompt template
    prompt_path = os.path.join(PROMPTS_DIR, "gen_api_handler_prompt.txt")
    try:
        user_prompt_template = read_file(prompt_path)
    except Exception as e:
        print(f"❌ Error reading API handler prompt: {e}")
        return None
    
    # Tạo LLM chain
    system_prompt = "You are an expert Python developer. Generate ONLY the API handling function and post-processing logic based on the specification."
    chain = create_llm_chain(system_prompt, model=GENERATOR_MODEL, temperature=0.1)
    
    try:
        # Chuẩn bị biến cho prompt
        prompt_variables = {
            "api_url": context.get("api_url", ""),
            "input_function": task_info["task_description"]["visualize"]["features"][1]["input_function"],
            "description": context.get("input_format", {}).get("structure", {}).get("data", {}).get("description", ""),
            "verified_input": json.dumps(
                task_info["model_io"].get("verified_input", {}), 
                indent=2
            ),
            "verified_output": json.dumps(
                task_info["model_io"].get("verified_output", {}), 
                indent=2
            ),
            "post_processing": json.dumps(
                context.get("output_format", {}).get("post_processing", {}), 
                indent=2
            ),
            "context": json.dumps(context.to_dict(), indent=2)
        }
        
        user_prompt = user_prompt_template.format(**prompt_variables)
        generated_code = chain.invoke({"user_prompt": user_prompt})
        cleaned_code = clean_llm_output(generated_code)
        
        # Trích xuất signature API để chia sẻ context
        signature_match = re.search(r"def\s+(call_model_api|api_handler)\(([^)]+)\)", cleaned_code)
        if signature_match:
            context.api_signature = signature_match.group(0)
        
        task_info["api_handler_code"] = cleaned_code
        task_info["shared_context"] = context
        
        print("✅ API handler code generated.")
        return task_info
        
    except KeyError as e:
        print(f"❌ Missing key while preparing prompt variables: {e}")
        return None
    except Exception as e:
        print(f"❌ Error generating API handler: {e}")
        return None