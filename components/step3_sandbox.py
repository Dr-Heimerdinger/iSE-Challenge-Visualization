import os
import sys
import subprocess
from utils.helpers import read_file, clean_llm_output
from utils.langchain import create_llm_chain
from config import PROMPTS_DIR, MAX_DEBUG_ATTEMPTS, SANDBOX_TIMEOUT, DEBUGGER_MODEL

def _get_fix_from_llm(bad_code: str, error_message: str) -> str:
    """Uses a centralized LLM chain to debug the failed script."""
    print(">>> Attempting to fix code with LLM debugger...")
    
    system_prompt_path = os.path.join(PROMPTS_DIR, "system_prompt_debug.txt")
    system_prompt = read_file(system_prompt_path)
    
    # Create the chain using our new utility
    chain = create_llm_chain(system_prompt, model=DEBUGGER_MODEL, temperature=0.0)
    
    user_prompt = f"The script below failed with an error. Please fix it.\n\n**FAILED CODE:**\n```{bad_code}```\n\n**ERROR MESSAGE:**\n```{error_message}```"
    fixed_code = chain.invoke({"user_prompt": user_prompt})
    
    return clean_llm_output(fixed_code)

def run(script_path: str):
    """
    Runs the generated code in a sandbox and attempts to debug it on failure. 
    """
    print("--- Running Step 3: Sandbox Execution & Debugging ---")
    
    for attempt in range(MAX_DEBUG_ATTEMPTS + 1):
        # ... (The rest of the run function remains unchanged) ...
        if attempt > 0:
            print(f"\n>>> DEBUG ATTEMPT {attempt}/{MAX_DEBUG_ATTEMPTS} <<<")

        print(f"Executing script: {script_path}")
        try:
            subprocess.run(
                [sys.executable, script_path],
                capture_output=True, text=True, timeout=SANDBOX_TIMEOUT, check=True
            )
            print("\n✅ Script executed successfully without errors!")
            print("The pipeline has successfully generated a functional UI script.")
            # According to the rules, the presentation is tomorrow afternoon, 21/06/2025. 
            print(f"To run the interface for the presentation, execute:\npython {script_path}")
            return

        except subprocess.CalledProcessError as e:
            print(f"❌ Script failed with exit code {e.returncode}.")
            print("--- ERROR MESSAGE ---\n" + e.stderr + "\n---------------------")
            if attempt < MAX_DEBUG_ATTEMPTS:
                bad_code = read_file(script_path)
                fixed_code = _get_fix_from_llm(bad_code, e.stderr)
                with open(script_path, "w") as f: f.write(fixed_code)
                print(f"✅ Debugger provided a fix. Retrying...")
            else:
                print(f"❌ Max debug attempts reached. Could not fix the script.")
        
        except subprocess.TimeoutExpired:
            print("❌ Script execution timed out. Aborting.")
            break