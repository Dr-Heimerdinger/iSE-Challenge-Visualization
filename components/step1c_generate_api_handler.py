import os
import json
from utils.helpers import read_file, clean_llm_output
from utils.langchain import create_llm_chain
from config import PROMPTS_DIR, GENERATOR_MODEL

def run(task_info: dict) -> dict | None:
    """
    Generate the API handling and post-processing logic using LLM
    """
    print("--- Running Step 1c: Generate API Handler & Post-processing Logic ---")
    
    # Đọc prompt template cho user
    prompt_path = os.path.join(PROMPTS_DIR, "gen_api_handler_prompt.txt")
    try:
        # File này chứa template cho 'user_prompt', không phải 'system_prompt'
        user_prompt_template = read_file(prompt_path)
    except Exception as e:
        print(f"❌ Error reading API handler prompt: {e}")
        return None
    
    # Định nghĩa system_prompt một cách tĩnh, chứa chỉ dẫn chung cho LLM
    # Nội dung này có thể lấy từ dòng đầu của file prompt hoặc định nghĩa trực tiếp
    system_prompt = "You are an expert Python developer. Generate ONLY the API handling function and post-processing logic based on the specification."

    # Tạo LLM chain với system prompt tĩnh
    chain = create_llm_chain(system_prompt, model=GENERATOR_MODEL, temperature=0.1)
    
    try:
        # Chuẩn bị các biến để điền vào user_prompt_template
        prompt_variables = {
            "api_url": task_info["model_information"].get("api_url", ""),
            "input_function": task_info["task_description"]["visualize"]["features"][1]["input_function"],
            "description": task_info["model_io"]["input_format"]["structure"]["data"]["description"],
            "verified_input": json.dumps(
                task_info["model_io"].get("verified_input", {}), 
                indent=2
            ),
            "verified_output": json.dumps(
                task_info["model_io"].get("verified_output", {}), 
                indent=2
            ),
            "post_processing": json.dumps(
                task_info["model_information"].get("output_format", {}).get("post_processing", {}), 
                indent=2
            )
        }
        
        user_prompt = user_prompt_template.format(**prompt_variables)
        generated_code = chain.invoke({"user_prompt": user_prompt})
        cleaned_code = clean_llm_output(generated_code)
        
        task_info["api_handler_code"] = cleaned_code
        print("✅ API handler code generated.", task_info["api_handler_code"])
        return task_info
    except KeyError as e:
        print(f"❌ Missing key while preparing prompt variables: {e}")
        print("Ensure task_info contains: model_information, model_io with input_format/output_format")
        return None
    except Exception as e:
        print(f"❌ Error generating API handler: {e}")
        return None