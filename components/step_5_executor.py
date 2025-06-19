import subprocess
import time
import config
from utils.llm_client import LLMClient

def execute_and_debug(llm_client: LLMClient):
    """
    Executes the generated UI code in a subprocess.
    If an error occurs, sends the error to the LLM for fixing and retries.
    """
    print("\n--- STEPS 5 & 6: Executing and Debugging the Code ---")
    
    for attempt in range(config.MAX_DEBUG_ATTEMPTS):
        print(f"\n>> Attempt {attempt + 1}/{config.MAX_DEBUG_ATTEMPTS} to run the generated UI...")
        process = None
        try:
            # Start the Gradio app as a subprocess
            process = subprocess.Popen(
                ['python', config.GENERATED_UI_PATH],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # Wait for a few seconds to see if it crashes immediately
            time.sleep(config.EXECUTION_TIMEOUT)
            
            # Check if the process has terminated
            return_code = process.poll()
            if return_code is not None:
                # Process crashed, get the error message
                _, stderr = process.communicate()
                raise RuntimeError(f"Code execution failed with return code {return_code}:\n{stderr}")

            # If the process is still running, assume it's stable
            print("="*60)
            print(">> EXECUTION SUCCESSFUL! <<")
            print(f">> Gradio interface is likely running. Access it at http://localhost:8080")
            print(">> Press Ctrl+C in this terminal window to stop the pipeline.")
            print("="*60)
            process.wait()  # Keep the main script alive while the subprocess runs
            return True

        except Exception as e:
            error_message = str(e)
            print(f"Error on attempt {attempt + 1}: \n{error_message}")
            
            if attempt + 1 == config.MAX_DEBUG_ATTEMPTS:
                print("Maximum debug attempts reached. Stopping.")
                return False

            print(">> Sending the error to the LLM to fix the code...")
            try:
                with open(config.GENERATED_UI_PATH, 'r', encoding='utf-8') as f:
                    faulty_code = f.read()
            except FileNotFoundError:
                print("Could not read the generated UI file to send for debugging. Stopping.")
                return False

            fix_prompt = f"""
The following Python Gradio script produced an error during execution.
Please analyze the error and fix the script. Only return the complete, corrected Python source code, with no additional explanations or comments.

ERROR:
---
{error_message}
---

FAULTY SOURCE CODE:
---
{faulty_code}
---
"""
            fixed_code = llm_client.call(fix_prompt)
            if fixed_code and "import gradio" in fixed_code:
                print(">> Received fixed code from LLM. Overwriting the file and retrying...")
                with open(config.GENERATED_UI_PATH, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)
            else:
                print("LLM could not provide a valid fix. Stopping.")
                return False
        finally:
            # Clean up the subprocess if it's still alive
            if process and process.poll() is None:
                process.terminate()
                process.wait()