import os
import json
import re
import traceback
from utils.helpers import read_file, clean_llm_output
from utils.langchain import create_llm_chain
from utils.context import TaskContext
from config import PROMPTS_DIR, GENERATOR_MODEL

def run(task_info: dict) -> dict | None:
    print("--- Running Step 1c: Generate API Handler & Post-processing Logic ---")
    
    try:
        # KHỞI TẠO CONTEXT - XỬ LÝ MỌI TRƯỜNG HỢP
        context = TaskContext()
        if "shared_context" in task_info:
            if isinstance(task_info["shared_context"], dict):
                # Tái tạo đối tượng từ dictionary
                context = TaskContext(task_info["shared_context"])
            elif isinstance(task_info["shared_context"], TaskContext):
                context = task_info["shared_context"]
        
        # Cập nhật giá trị - XỬ LÝ AN TOÀN KHI DỮ LIỆU KHÔNG TỒN TẠI
        context.set_value("task_name", task_info.get("task_name", "Unknown Task"))
        context.set_value("api_url", task_info.get("model_information", {}).get("api_url", ""))
        
        # Xử lý model_io an toàn
        model_io = task_info.get("model_io", {})
        context.set_value("input_format", model_io.get("input_format", {}))
        context.set_value("output_format", model_io.get("output_format", {}))
        
        # Đọc prompt template
        prompt_path = os.path.join(PROMPTS_DIR, "gen_api_handler_prompt.txt")
        user_prompt_template = read_file(prompt_path)
        
        # Tạo LLM chain
        system_prompt = "You are an expert Python developer. Generate ONLY the API handling function and post-processing logic based on the specification."
        chain = create_llm_chain(system_prompt, model=GENERATOR_MODEL, temperature=0.1)
        
        # XỬ LÝ AN TOÀN TẤT CẢ CÁC TRƯỜNG DỮ LIỆU
        task_description = task_info.get("task_description", {})
        visualize = task_description.get("visualize", {}) if isinstance(task_description, dict) else {}
        features = visualize.get("features", []) if isinstance(visualize, dict) else []
        
        # Xử lý input_function an toàn
        input_function = ""
        if isinstance(features, list) and features:
            # Tìm feature có input_function đầu tiên
            for feature in features:
                if isinstance(feature, dict) and feature.get("input_function"):
                    input_function = feature["input_function"]
                    break
        
        # Xử lý description an toàn
        description = ""
        input_format_val = context.get("input_format", {})
        if isinstance(input_format_val, dict):
            structure = input_format_val.get("structure", {})
            if isinstance(structure, dict):
                data = structure.get("data", {})
                if isinstance(data, dict):
                    description = data.get("description", "")
        
        # Xử lý post_processing an toàn
        post_processing = {}
        output_format_val = context.get("output_format", {})
        if isinstance(output_format_val, dict):
            post_processing = output_format_val.get("post_processing", {})
        
        # Chuẩn bị biến cho prompt - XỬ LÝ AN TOÀN TẤT CẢ CÁC TRƯỜNG
        prompt_variables = {
            "api_url": context.get("api_url", ""),
            "input_function": input_function,
            "description": description,
            "verified_input": json.dumps(
                model_io.get("verified_input", {}), 
                indent=2
            ) if isinstance(model_io.get("verified_input"), (dict, list)) else "{}",
            "verified_output": json.dumps(
                model_io.get("verified_output", {}), 
                indent=2
            ) if isinstance(model_io.get("verified_output"), (dict, list)) else "{}",
            "post_processing": json.dumps(post_processing, indent=2),
            "context": json.dumps(context.to_dict(), indent=2)
        }
        
        # ĐẢM BẢO TẤT CẢ GIÁ TRỊ ĐỀU LÀ CHUỖI
        for key in prompt_variables:
            if not isinstance(prompt_variables[key], str):
                prompt_variables[key] = str(prompt_variables[key])
        
        # Format user prompt an toàn
        try:
            user_prompt = user_prompt_template.format(**prompt_variables)
        except Exception as e:
            # print(f"❌ Error formatting prompt: {e}")
            # Thử format thủ công nếu có lỗi
            user_prompt = user_prompt_template
            for key, value in prompt_variables.items():
                placeholder = "{" + key + "}"
                user_prompt = user_prompt.replace(placeholder, value)
        
        generated_code = chain.invoke({"user_prompt": user_prompt})
        cleaned_code = clean_llm_output(generated_code)
        
        # Trích xuất signature API để chia sẻ context
        signature_match = re.search(r"def\s+(call_model_api|api_handler)\(([^)]+)\)", cleaned_code)
        if signature_match:
            context.api_signature = signature_match.group(0)
        
        # LƯU CONTEXT VÀ TASK_INFO
        task_info["api_handler_code"] = cleaned_code
        task_info["shared_context"] = context
        
        print("✅ API handler code generated.", task_info["api_handler_code"])
        return task_info
        
    except Exception as e:
        print(f"❌ Error generating API handler: {e}")
        traceback.print_exc()
        return None