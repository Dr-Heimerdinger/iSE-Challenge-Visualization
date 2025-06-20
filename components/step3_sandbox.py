import os
import subprocess
import sys
import time
from config import MAX_DEBUG_ATTEMPTS, SANDBOX_TIMEOUT

def run(script_path: str, task_info: dict):
    print("--- Running Step 3: Streamlit Sandbox Execution ---")
    
    for attempt in range(MAX_DEBUG_ATTEMPTS + 1):
        try:
            # Launch Streamlit app
            process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print("✅ Streamlit app launched successfully")
            print(f"Application is running on http://localhost:8501")
            
            # Monitor process
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                print("\nStopping application...")
                process.terminate()
                break
                
        except Exception as e:
            print(f"❌ Error launching Streamlit app: {e}")
            if attempt < MAX_DEBUG_ATTEMPTS:
                # Debugging logic here
                pass
            else:
                print("❌ Max debug attempts reached")
                return