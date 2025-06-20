import os
import json
import requests
import time
from typing import Optional, Dict
from utils import payload_builder
from utils.langchain import create_llm_chain
from config import GENERATOR_MODEL

def _get_payload_from_llm(input_format_desc: str, attempt_history: list = []) -> Dict:
    print(">>> Builder failed or was skipped. Falling back to LLM to generate payload...")
    prompt_system = """You are an API testing assistant. Your task is to generate VALID JSON payloads for API requests based on the exact input format specification."""
    user_prompt = f"You need to create a test JSON payload based on this input format:\n\n{input_format_desc}"

    if attempt_history:
        user_prompt += "\n\nThe previous attempt with a generated payload failed. Analyze the error and create a new, corrected payload."

    chain = create_llm_chain(prompt_system, model=GENERATOR_MODEL, temperature=0.1)
    payload_str = chain.invoke({"user_prompt": user_prompt})
    return json.loads(payload_str)


def _make_api_request_with_retry(api_url: str, input_format_desc: dict, max_retries: int = 2) -> tuple[dict, dict]:
    """
    Sử dụng phương pháp kết hợp: thử builder trước, nếu thất bại thì dùng LLM.
    Sau đó gửi yêu cầu API với logic retry.
    """
    payload = {}
    
    try:
        # Ưu tiên 1: Thử dùng payload builder (nhanh, rẻ, đáng tin cậy)
        print(">>> Attempting to build payload with deterministic builder...")
        payload = payload_builder.build_payload_from_schema(input_format_desc)
        print("✅ Payload built successfully using the builder.")
    except Exception as e:
        print(f"⚠️ Builder failed: {e}.")
        # Phương án 2: Nếu builder thất bại, chuyển sang dùng LLM
        payload = _get_payload_from_llm(json.dumps(input_format_desc, indent=2))
        print("✅ Payload generated using LLM fallback.")

    print("Final payload to be sent:")
    print(json.dumps(payload, indent=2))

    # Vòng lặp retry giờ đây tập trung vào lỗi mạng hoặc lỗi từ server
    for attempt in range(max_retries + 1):
        try:
            print(f">>> Attempt {attempt + 1}/{max_retries + 1}: Sending API request...")
            response = requests.post(api_url, json=payload, timeout=30)
            response.raise_for_status()
            response_json = response.json()

            if 'error' in response_json and response_json['error']:
                raise ValueError(f"API returned success status but contained an error: {response_json['error']}")

            print("✅ API request and response verification successful!")
            return payload, response_json

        except Exception as e:
            print(f"⚠️ API call attempt {attempt + 1} failed: {e}")
            if attempt >= max_retries:
                print("❌ All API call attempts failed.")
                raise e
            
            if "Builder failed" in locals().get("e", ""): 
                 print(">>> Retrying with LLM, providing error context...")
                 payload = _get_payload_from_llm(
                     json.dumps(input_format_desc, indent=2),
                     attempt_history=[{'error': str(e)}]
                 )

            delay_seconds = 5 * (2 ** attempt)
            print(f"⏳ Waiting {delay_seconds} seconds before next retry...")
            time.sleep(delay_seconds)

    raise ConnectionError("Could not get a valid response from the API after all retries.")


def run(task_info: dict) -> Optional[dict]:
    """
    Verifies the model's I/O using the hybrid (Builder + LLM) approach.
    """
    print("--- Running Step 1b: Verify Model I/O via Live API Call (Hybrid Approach) ---")
    api_url = task_info["model_information"].get("api_url")
    input_format_desc = task_info["model_io"]["input_format"]

    try:
        verified_input, verified_output = _make_api_request_with_retry(
            api_url, input_format_desc, max_retries=2
        )
        
        task_info["model_io"]["verified_input"] = verified_input
        task_info["model_io"]["verified_output"] = verified_output

        task_info["shared_context"] = {
        "input_format": task_info["model_io"]["input_format"],
        "output_format": task_info["model_io"]["output_format"],
    }

        print("✅ Model I/O verification successful.")
        print(f"Verified input: {json.dumps(verified_input, indent=2)}")

        print("✅ Model I/O verification successful.")
        return task_info

    except Exception as e:
        print(f"\n❌ Pipeline failed at Step 1b. Could not verify a working API request. Error: {e}")
        return None