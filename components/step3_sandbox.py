import os
import sys
import subprocess
import json
import time
import requests
from utils.helpers import read_file, clean_llm_output
from utils.langchain import create_llm_chain
from config import PROMPTS_DIR, MAX_DEBUG_ATTEMPTS, SANDBOX_TIMEOUT, DEBUGGER_MODEL

def _get_fix_from_llm(bad_code: str, error_message: str, task_info: dict) -> str:
    print(">>> Attempting to fix code with context-aware LLM debugger...")
    
    try:
        system_prompt_path = os.path.join(PROMPTS_DIR, "system_prompt_debug.txt")
        system_prompt = read_file(system_prompt_path)
    except FileNotFoundError:
        print(f"FATAL: Debugger prompt file not found at {system_prompt_path}. Cannot proceed with debugging.")
        # Trả về code cũ để tránh lỗi sâu hơn
        return bad_code

    chain = create_llm_chain(system_prompt, model=DEBUGGER_MODEL, temperature=0.0)
    
    user_prompt_template = """
You are an expert Python and Gradio debugger. A generated script has failed. Your task is to provide a corrected, complete version of the script.

**1. The Error Message:**
{error_message}

**2. The Failed Code:**
```python
{bad_code}
```

**3. Full Task Context (This is crucial for a correct fix):**
This context was used to generate the original script. Use it to understand the script's goal, expected data formats, and file dependencies.
Task Description: {task_description}
Model I/O Format:
{model_io}
Critical Auxiliary File Paths (You MUST use these absolute paths):
{auxiliary_file_paths}

**4. GRADIO VERSION CONTEXT:**
We are using Gradio 3.50.2. Remember these critical changes:
- file_types_allow_multiple is DEPRECATED → Use file_count='multiple'
- Never repeat keyword arguments in components
- Always use absolute paths from auxiliary_file_paths
- **CRITICAL: All event handlers (.click, .submit, etc.) MUST be defined INSIDE the gr.Blocks() context**

**5. SANDBOX EXECUTION CONTEXT:**
- The script will be validated without launching the Gradio server
- Ensure all function definitions are correct
- Make sure there are no infinite loops
- Verify all file paths are absolute
- Confirm all imports are valid

**Your Mission:**
Based on the error and the full task context, rewrite the entire Python script to fix the bug. Pay close attention to:
1. File paths (FileNotFoundError) 
2. Gradio component arguments (TypeError)
3. **Event handler placement - they MUST be inside the gr.Blocks() context**

Return ONLY the complete, corrected Python code without any explanations.
"""

    prompt_variables = {
        "error_message": error_message,
        "bad_code": bad_code,
        "task_description": task_info.get("task_description", {}).get("description", "N/A"),
        "model_io": json.dumps(task_info.get("model_io", {}), indent=2, ensure_ascii=False),
        "auxiliary_file_paths": json.dumps(task_info.get("auxiliary_file_paths", {}), indent=2, ensure_ascii=False)
    }

    user_prompt = user_prompt_template.format(**prompt_variables)

    fixed_code = chain.invoke({"user_prompt": user_prompt})

    return clean_llm_output(fixed_code)

def _create_sandbox_safe_script(script_content: str) -> str:
    """
    Convert the script to a sandbox-safe version for validation
    """
    # Replace .launch() with validation print
    sandbox_safe_script = script_content.replace(
        ".launch()", 
        "# Sandbox-safe execution\n"
        "print('✅ Script structure validated without running server')\n"
        "# .launch()"
    )
    
    # Also handle variations of launch calls
    sandbox_safe_script = sandbox_safe_script.replace(
        ".launch(share=True)", 
        "# Sandbox-safe execution\n"
        "print('✅ Script structure validated without running server')\n"
        "# .launch(share=True)"
    )
    
    sandbox_safe_script = sandbox_safe_script.replace(
        ".launch(server_port=", 
        "# Sandbox-safe execution\n"
        "print('✅ Script structure validated without running server')\n"
        "# .launch(server_port="
    )
    
    return sandbox_safe_script

def run(script_path: str, task_info: dict):
    print("--- Running Step 3: Sandbox Execution & Context-Aware Debugging ---")
    try:
        current_script_content = read_file(script_path)
    except FileNotFoundError:
        print(f"❌ Cannot execute script. File not found at: {script_path}")
        return

    # Create sandbox-safe version for validation
    sandbox_safe_script = _create_sandbox_safe_script(current_script_content)

    for attempt in range(MAX_DEBUG_ATTEMPTS + 1):
        if attempt > 0:
            print(f"\n>>> DEBUG ATTEMPT {attempt}/{MAX_DEBUG_ATTEMPTS} <<<")

        print(f"Validating script: {script_path}")
        try:
            process = subprocess.run(
                [sys.executable, "-c", sandbox_safe_script],
                capture_output=True, 
                text=True, 
                timeout=SANDBOX_TIMEOUT, 
                check=True, 
                encoding='utf-8', 
                env={**os.environ, 'PYTHONUTF8': '1'}  
            )
            
            if "✅ Script structure validated" in process.stdout:
                print("\n✅ Script structure validated successfully!")
                
                # Test with verified input if available
                print("\n--- Testing with verified input ---")
                try:
                    _test_with_verified_input(script_path, task_info)
                except Exception as e:
                    print(f"⚠️ Warning: Could not test with verified input: {e}")
                
                # Launch the production application
                print("\n--- Launching production application ---")
                try:
                    subprocess.Popen(
                        [sys.executable, script_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    print(f"✅ Application is running on http://localhost:8080")
                    print("Press Ctrl+C to stop the application")
                except Exception as e:
                    print(f"⚠️ Warning: Could not launch production app: {e}")
                
                return
            else:
                raise RuntimeError("Validation output not found")

        except subprocess.CalledProcessError as e:
            print(f"❌ Script validation failed with exit code {e.returncode}.")
            print("--- STDOUT ---\n" + e.stdout + "\n---------------------")
            print("--- STDERR ---\n" + e.stderr + "\n---------------------")
            
            if attempt < MAX_DEBUG_ATTEMPTS:
                fixed_code = _get_fix_from_llm(current_script_content, e.stderr, task_info)
                
                if fixed_code and fixed_code != current_script_content:
                    with open(script_path, "w", encoding='utf-8') as f:
                        f.write(fixed_code)
                    current_script_content = fixed_code
                    sandbox_safe_script = _create_sandbox_safe_script(fixed_code)
                    print(f"✅ Debugger provided a fix. Retrying...")
                else:
                    print(f"⚠️ Debugger did not provide a new fix. Aborting.")
                    break
            else:
                print(f"❌ Max debug attempts reached. Could not fix the script.")
                return
        
        except subprocess.TimeoutExpired:
            print("❌ Script validation timed out. Possible infinite loop.")
            break
        except Exception as e:
            print(f"❌ Unexpected error during validation: {e}")
            break

def _test_with_verified_input(script_path: str, task_info: dict):
    """
    Test the application with verified input data
    """
    verified_input = task_info.get("model_io", {}).get("verified_input")
    if not verified_input:
        print("⚠️ No verified input available for testing")
        return
    
    print("Starting temporary server for testing...")
    
    # Start the application in a subprocess
    demo_process = subprocess.Popen(
        [sys.executable, script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    try:
        # Wait for the server to start
        time.sleep(5)
        
        # Test the API endpoint
        api_url = "http://localhost:8080/api/predict"
        print(f"Sending test request to: {api_url}")
        
        response = requests.post(
            api_url,
            json=verified_input,
            timeout=20
        )
        response.raise_for_status()
        
        print(f"✅ API test successful! Response: {response.json()}")
        
    except Exception as e:
        print(f"⚠️ API test failed: {e}")
    
    finally:
        # Clean up: terminate the test server
        demo_process.terminate()
        demo_process.wait(timeout=5)
        print("Test server stopped.")