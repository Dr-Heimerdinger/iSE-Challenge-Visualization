import os
import json
import requests
from utils.langchain import create_llm_chain
from config import GENERATOR_MODEL

def _make_api_request_with_retry(api_url: str, input_format_desc: str, max_retries: int = 2) -> tuple[dict, dict, list]:

    attempt_history = []
    
    for attempt in range(max_retries + 1): 
        print(f">>> Attempt {attempt + 1}/{max_retries + 1}: Generating test request...")
        
        try:
            # Tạo prompt cơ bản
            prompt_system = "You are a helpful assistant. Given a description of a model's input format, generate a valid JSON payload string with plausible placeholder data. Only output the raw JSON string."
            
            user_prompt = f"Based on this input format description, create a test JSON payload:\n\n{input_format_desc}"
            
            # Thêm thông tin từ các lần thử trước nếu có
            if attempt_history:
                user_prompt += "\n\nPrevious attempts that failed:"
                for i, hist in enumerate(attempt_history):
                    user_prompt += f"\n\nAttempt {i+1}:"
                    user_prompt += f"\nInput sent: {json.dumps(hist['input'], indent=2)}"
                    user_prompt += f"\nError received: {hist['error']}"
                    if hist.get('response_text'):
                        user_prompt += f"\nAPI Response: {hist['response_text']}"
                user_prompt += "\n\nBased on the errors and responses above, please generate a different payload that addresses these issues."
            
            chain = create_llm_chain(prompt_system, model=GENERATOR_MODEL, temperature=0.1)
            payload_str = chain.invoke({"user_prompt": user_prompt})
            payload = json.loads(payload_str)
            
            print(f'Attempt {attempt + 1} payload:', payload)
            
            # Thực hiện API request
            response = requests.post(api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            response_json = response.json()
            print(f"✅ Attempt {attempt + 1} was successful!")
            print('Response:', response_json)
            
            return payload, response_json, attempt_history
            
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            
            # Thu thập thông tin về lần thử này
            attempt_info = {
                'attempt': attempt + 1,
                'input': payload if 'payload' in locals() else None,
                'error': str(e)
            }
            
            # Thu thập response text từ API (quan trọng cho việc retry)
            try:
                if 'response' in locals() and hasattr(response, 'text'):
                    attempt_info['response_text'] = response.text
                elif 'response' in locals() and hasattr(response, 'content'):
                    attempt_info['response_text'] = response.content.decode('utf-8', errors='ignore')
            except:
                attempt_info['response_text'] = "Could not retrieve response text"
                
            attempt_history.append(attempt_info)
            
            # Nếu đã hết số lần thử, raise exception
            if attempt >= max_retries:
                raise Exception(f"All {max_retries + 1} attempts failed. Last error: {e}")
    
    return None, None, attempt_history

def run(task_info: dict) -> dict | None:
    """
    Verifies the model's I/O by making a live API request.
    """
    print("--- Running Step 1b: Verify Model I/O via Live API Call ---")
    api_url = task_info["model_information"].get("api_url")
    input_format_desc = json.dumps(task_info["model_io"]["input_format"], indent=2)

    # --- Primary Attempt with Retry (không dùng sample data) ---
    print(">>> Attempting to generate and send a test request with retry logic...")
    try:
        verified_input, verified_output, primary_history = _make_api_request_with_retry(
            api_url, input_format_desc, max_retries=2
        )
        
        task_info["model_io"]["verified_input"] = verified_input
        task_info["model_io"]["verified_output"] = verified_output
        task_info["model_io"]["attempt_history"] = primary_history
        return task_info

    except Exception as e:
        print(f"❌ All attempts failed: {e}")
        
        # Lưu lại history ngay cả khi thất bại
        if 'primary_history' in locals():
            task_info["model_io"]["failed_attempt_history"] = primary_history
        
        return None