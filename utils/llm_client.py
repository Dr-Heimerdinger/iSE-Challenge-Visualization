from openai import OpenAI
import config
import os 

class LLMClient:
    def __init__(self):
        """
        Initializes the client and loads the system prompt from a file.
        """
        try:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'system_prompt.txt')
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.system_prompt = f.read()
            print("LLM Client initialized successfully and system prompt loaded.")
        except FileNotFoundError:
            print("Error: prompts/system_prompt.txt not found. Using default system prompt.")
            self.system_prompt = "You are a helpful Python programmer."
        except Exception as e:
            print(f"Error initializing LLM Client: {e}")
            self.client = None
            self.system_prompt = ""

    def call(self, prompt, model_name=config.LLM_MODEL):
        """
        Sends a prompt to the model and receives a response.
        """
        if not self.client:
            print("LLM Client is not initialized. Cannot send request.")
            return "print('LLM Client is not configured.')"

        print(f"\n===== Sending request to LLM ({model_name}) =====")
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    # Sử dụng system prompt đã được load từ file
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            
            # Xử lý code block markdown
            if content.strip().startswith("```python"):
                content = content.strip()[9:-3].strip()
            elif content.strip().startswith("```"):
                 content = content.strip()[3:-3].strip()
            
            print("===== Received response from LLM successfully =====\n")
            return content
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return None