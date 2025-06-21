import os
import json
import re
import traceback
import zlib
from utils.helpers import read_file, clean_llm_output
from utils.langchain import create_llm_chain
from utils.context import TaskContext
from config import PROMPTS_DIR, GENERATOR_MODEL

def is_base64_image(data):
    """Check recursively if input contains base64-encoded image string"""
    # Xử lý chuỗi
    if isinstance(data, str):
        stripped = data.strip()
        # Kiểm tra header data:image
        if stripped.startswith("data:image") and "base64," in stripped:
            return True
        # Kiểm tra định dạng ảnh không header
        image_prefixes = (
            "iVBOR",  # PNG
            "/9j/",   # JPEG
            "R0lGOD", # GIF
            "UklGR",   # WebP
            "PHN2Zy",  # SVG
            "SUkq"     # TIFF
        )
        if len(stripped) > 200 and stripped.startswith(image_prefixes):
            return True
    
    # Xử lý đệ quy dictionary
    elif isinstance(data, dict):
        for value in data.values():
            if is_base64_image(value):
                return True
    
    # Xử lý đệ quy list
    elif isinstance(data, list):
        for item in data:
            if is_base64_image(item):
                return True
    
    return False

def compress_data(data: dict | list) -> str:
    """Nén dữ liệu lớn để giảm kích thước token"""
    json_str = json.dumps(data)
    if len(json_str) > 5000:  # Chỉ nén khi dữ liệu đủ lớn
        compressed = zlib.compress(json_str.encode())
        return f"<COMPRESSED_DATA:{len(compressed)}>"
    return json_str

def run(task_info: dict) -> dict | None:
    print("--- Running Step 1c: Generate API Handler & Post-processing Logic ---")
    
    try:
        context = TaskContext()
        if "shared_context" in task_info:
            if isinstance(task_info["shared_context"], dict):
                context = TaskContext(task_info["shared_context"])
            elif isinstance(task_info["shared_context"], TaskContext):
                context = task_info["shared_context"]
        
        context.set_value("task_name", task_info.get("task_name", "Unknown Task"))
        context.set_value("api_url", task_info.get("model_information", {}).get("api_url", ""))
        
        model_io = task_info.get("model_io", {})
        context.set_value("input_format", model_io.get("input_format", {}))
        context.set_value("output_format", model_io.get("output_format", {}))
        
        prompt_path = os.path.join(PROMPTS_DIR, "gen_api_handler_prompt.txt")
        user_prompt_template = read_file(prompt_path)
        
        system_prompt = "You are an expert Python developer. Generate ONLY the API handling function and post-processing logic based on the specification."
        chain = create_llm_chain(system_prompt, model=GENERATOR_MODEL, temperature=0.1)
        
        task_description = task_info.get("task_description", {})
        visualize = task_description.get("visualize", {}) if isinstance(task_description, dict) else {}
        features = visualize.get("features", []) if isinstance(visualize, dict) else []

        input_function = ""
        if isinstance(features, list) and features:
            for feature in features:
                if isinstance(feature, dict) and feature.get("input_function"):
                    input_function = feature["input_function"]
                    break
        
        description = ""
        input_format_val = context.get("input_format", {})
        if isinstance(input_format_val, dict):
            structure = input_format_val.get("structure", {})
            if isinstance(structure, dict):
                data = structure.get("data", {})
                if isinstance(data, dict):
                    description = data.get("description", "")

        post_processing = {}
        output_format_val = context.get("output_format", {})
        if isinstance(output_format_val, dict):
            post_processing = output_format_val.get("post_processing", {})

        # Xử lý verified_input: phát hiện base64 và thay thế bằng placeholder
        verified_input_val = model_io.get("verified_input", {})
        if is_base64_image(verified_input_val):
            print("⚠️ Detected base64 image in verified_input - Using minimal placeholder")
            verified_input_str = '"<BASE64_IMAGE>"'
        else:
            # Sử dụng dạng nén nếu dữ liệu quá lớn
            verified_input_str = (
                compress_data(verified_input_val) 
                if isinstance(verified_input_val, (dict, list)) 
                else "{}"
            )
        
        # Xử lý verified_output: kiểm tra base64 trong output
        verified_output_val = model_io.get("verified_output", {})
        if is_base64_image(verified_output_val):
            print("⚠️ Detected base64 image in verified_output - Using minimal placeholder")
            verified_output_str = '"<BASE64_IMAGE>"'
        else:
            # Sử dụng dạng nén nếu dữ liệu quá lớn
            verified_output_str = (
                compress_data(verified_output_val) 
                if isinstance(verified_output_val, (dict, list)) 
                else "{}"
            )

        # Tối ưu context: chỉ giữ lại thông tin cần thiết
        optimized_context = {
            "task_name": context.get("task_name", ""),
            "api_url": context.get("api_url", ""),
            "input_format_summary": str(context.get("input_format", {}).keys()),
            "output_format_summary": str(context.get("output_format", {}).keys())
        }

        prompt_variables = {
            "api_url": context.get("api_url", ""),
            "input_function": input_function,
            "description": description,
            "verified_input": verified_input_str,
            "verified_output": verified_output_str,
            "post_processing": json.dumps(post_processing, indent=2)[:5000] + ("..." if len(json.dumps(post_processing)) > 5000 else ""),
            "context": json.dumps(optimized_context, indent=2)
        }

        print(f"Prompt size before optimization: {sum(len(str(v)) for v in prompt_variables.values())} chars")
        
        # Đảm bảo tất cả giá trị là chuỗi
        for key in prompt_variables:
            if not isinstance(prompt_variables[key], str):
                prompt_variables[key] = str(prompt_variables[key])
                
        print(f"Prompt size after optimization: {sum(len(v) for v in prompt_variables.values())} chars")

        try:
            user_prompt = user_prompt_template.format(**prompt_variables)
        except Exception as e:
            user_prompt = user_prompt_template
            for key, value in prompt_variables.items():
                placeholder = "{" + key + "}"
                user_prompt = user_prompt.replace(placeholder, value)
        
        print(f"Final prompt size: {len(user_prompt)} chars")
        
        generated_code = chain.invoke({"user_prompt": user_prompt})
        cleaned_code = clean_llm_output(generated_code)
        
        signature_match = re.search(r"def\s+(call_model_api|api_handler)\(([^)]+)\)", cleaned_code)
        if signature_match:
            context.api_signature = signature_match.group(0)
        
        task_info["api_handler_code"] = cleaned_code
        task_info["shared_context"] = context

        print("✅ API handler code generated.")
        return task_info
    
    except Exception as e:
        print(f"❌ Error generating API handler: {e}")
        traceback.print_exc()
        return None