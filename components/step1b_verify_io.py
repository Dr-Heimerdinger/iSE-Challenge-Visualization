import os
import json
import requests
import time
from typing import Optional, Dict
from utils import payload_builder
from utils.langchain import create_llm_chain
from config import GENERATOR_MODEL

def _get_payload_from_llm(input_format_desc: str, error_info: str = "") -> Dict:
    print(">>> Using LLM to generate payload...")
    prompt_system = """You are an API testing assistant. Your task is to generate VALID JSON payloads for API requests based on the exact input format specification."""
    
    user_prompt = f"""Generate a test JSON payload based on this input format specification:
    
    {input_format_desc}
    
    Follow these guidelines:
    1. Use realistic sample values
    2. Match the exact structure and data types
    3. Keep the payload minimal but complete"""
    
    if error_info:
        user_prompt += f"\n\nPrevious attempt failed with error: {error_info}\nPlease analyze and create a corrected payload."
    
    chain = create_llm_chain(prompt_system, model=GENERATOR_MODEL, temperature=0.1)
    payload_str = chain.invoke({"user_prompt": user_prompt})
    
    try:
        return json.loads(payload_str)
    except json.JSONDecodeError:
        print("⚠️ LLM returned invalid JSON, trying to fix...")
        # Try to extract JSON from markdown or code block
        if "```json" in payload_str:
            payload_str = payload_str.split("```json")[1].split("```")[0].strip()
        elif "```" in payload_str:
            payload_str = payload_str.split("```")[1].split("```")[0].strip()
        return json.loads(payload_str)


def _make_api_request_with_retry(api_url: str, input_format_desc: dict, max_retries: int = 3) -> tuple[dict, dict]:
    """
    Sử dụng phương pháp kết hợp: thử builder trước, nếu thất bại thì dùng LLM.
    Sau đó gửi yêu cầu API với logic retry.
    """
    payload = {}
    used_llm = False
    error_history = []
    
    try:
        # Ưu tiên 1: Thử dùng payload builder (nhanh, rẻ, đáng tin cậy)
        print(">>> Attempting to build payload with deterministic builder...")
        payload = payload_builder.build_payload_from_schema(input_format_desc)
        print("✅ Payload built successfully using the builder.")
    except Exception as e:
        print(f"⚠️ Builder failed: {e}.")
        used_llm = True
        # Phương án 2: Nếu builder thất bại, chuyển sang dùng LLM
        payload = _get_payload_from_llm(json.dumps(input_format_desc, indent=2))
        print("✅ Payload generated using LLM fallback.")

    print("Final payload to be sent:")
    print(json.dumps(payload, indent=2))

    # Vòng lặp retry
    for attempt in range(max_retries + 1):
        try:
            print(f">>> Attempt {attempt + 1}/{max_retries + 1}: Sending API request...")
            response = requests.post(api_url, json=payload, timeout=30)
            response.raise_for_status()  # Sẽ ném exception cho mã lỗi 4xx/5xx
            
            # Kiểm tra response có phải JSON hợp lệ không
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                raise ValueError(f"API returned invalid JSON: {response.text[:200]}...")
                
            # Kiểm tra lỗi trong response JSON
            if 'error' in response_json and response_json['error']:
                error_msg = f"API returned success status but contained an error: {response_json['error']}"
                raise ValueError(error_msg)

            print("✅ API request and response verification successful!")
            return payload, response_json

        except Exception as e:
            error_info = str(e)
            print(f"⚠️ API call attempt {attempt + 1} failed: {error_info}")
            error_history.append(error_info)
            
            if attempt >= max_retries:
                print("❌ All API call attempts failed.")
                raise e
            
            # LUÔN sử dụng LLM để tạo payload mới khi gặp lỗi
            print(">>> Generating new payload with LLM using error context...")
            payload = _get_payload_from_llm(
                json.dumps(input_format_desc, indent=2),
                error_info="\n".join(error_history)
            )
            used_llm = True
            
            print("New payload generated:")
            print(json.dumps(payload, indent=2))
            
            delay_seconds = 3 * (attempt + 1)
            print(f"⏳ Waiting {delay_seconds} seconds before next retry...")
            time.sleep(delay_seconds)

    raise ConnectionError("Could not get a valid response from the API after all retries.")


def run(task_info: dict) -> Optional[dict]:
    """
    Verifies the model's I/O using the hybrid (Builder + LLM) approach.
    """
    print("--- Running Step 1b: Verify Model I/O via Live API Call (Hybrid Approach) ---")
    api_url = task_info["model_information"].get("api_url")
    
    # Xử lý input format
    input_format_desc = task_info["model_io"]["input_format"]
    
    # Tự động sửa lỗi chính tả phổ biến
    if "strucutre" in input_format_desc:
        print("⚠️ Warning: Found typo 'strucutre' in input_format, correcting to 'structure'")
        input_format_desc["structure"] = input_format_desc.pop("strucutre")
    
    # Đảm bảo cấu trúc hợp lệ
    if "structure" not in input_format_desc:
        print("⚠️ Warning: Input format missing 'structure' key, using LLM-only approach")
        # Tạo payload mẫu bằng LLM nếu cấu trúc không hợp lệ
        task_info["model_io"]["input_format"] = {
            "type": "json",
            "structure": input_format_desc
        }
        input_format_desc = task_info["model_io"]["input_format"]

    try:
        verified_input, verified_output = _make_api_request_with_retry(
            api_url, input_format_desc, max_retries=3
        )
        
        # CẬP NHẬT TASK_INFO
        task_info["model_io"]["verified_input"] = verified_input
        task_info["model_io"]["verified_output"] = verified_output

        print("✅ Model I/O verification successful.")
        print(f"Verified input: {json.dumps(verified_input, indent=2)}")
        return task_info

    except Exception as e:
        print(f"\n❌ Pipeline failed at Step 1b. Could not verify a working API request. Error: {e}")
        return None