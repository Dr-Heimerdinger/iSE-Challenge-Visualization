import os
import json
from utils.helpers import read_file, clean_llm_output
from utils.langchain import create_llm_chain
from config import GENERATED_CODE_DIR, PROMPTS_DIR, GENERATOR_MODEL

def run(ui_script_path: str, api_handler_code: str, task_info: dict) -> str | None:
    """
    Combine UI layout and API processing logic using an LLM as an integrator.
    """
    print("--- Running Step 2b: Combine UI and API Handler (LLM Integrator) ---")
    
    try:
        # Đọc mã giao diện người dùng đã được tạo
        ui_code = read_file(ui_script_path)
        
        # Đọc prompt dành cho việc tích hợp
        prompt_path = os.path.join(PROMPTS_DIR, "gen_combine_logic_prompt.txt")
        integration_prompt_template = read_file(prompt_path)

        # Định nghĩa system prompt tĩnh cho vai trò của LLM
        system_prompt = "You are an expert Python and Gradio developer, acting as a code integrator."
        
        # Tạo LLM chain
        chain = create_llm_chain(system_prompt, model=GENERATOR_MODEL, temperature=0.1)

        # Chuẩn bị các biến để điền vào prompt
        # Chỉ trích xuất các thông tin cần thiết từ task_info để prompt gọn hơn
        contextual_task_info = {
            "task_description": task_info.get("task_description"),
            "model_io": task_info.get("model_io")
        }

        prompt_variables = {
            "task_info": json.dumps(contextual_task_info, indent=2, ensure_ascii=False),
            "ui_code": ui_code,
            "api_handler_code": api_handler_code
        }
        
        # Tạo user_prompt hoàn chỉnh
        user_prompt = integration_prompt_template.format(**prompt_variables)
        
        print(">>> Sending UI and API code to LLM for integration...")
        # Gọi LLM để thực hiện việc tích hợp
        integrated_code = chain.invoke({"user_prompt": user_prompt})
        cleaned_code = clean_llm_output(integrated_code)
        
        # Lưu script hoàn chỉnh
        safe_task_name = task_info.get('task_name', 'unknown_task').replace(" ", "_")
        combined_script_path = os.path.join(GENERATED_CODE_DIR, f"{safe_task_name}_full_ui.py")
        
        with open(combined_script_path, "w", encoding="utf-8") as f:
            f.write(cleaned_code)
        
        print(f"✅ LLM successfully integrated the code. Combined script saved to {combined_script_path}")
        return combined_script_path

    except FileNotFoundError as e:
        print(f"❌ Error: Prompt file not found. Make sure 'prompts/gen_combine_logic_prompt.txt' exists. Details: {e}")
        return None
    except Exception as e:
        print(f"❌ Error during LLM integration in Step 2b: {e}")
        return None