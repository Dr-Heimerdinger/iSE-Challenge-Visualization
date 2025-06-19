from openai import OpenAI
import config

class LLMClient:
    def __init__(self):
        """
        Initializes the client to communicate with the OpenAI API.
        """
        try:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            print("LLM Client initialized successfully.")
        except Exception as e:
            print(f"Error initializing LLM Client: {e}")
            self.client = None

    def call(self, prompt, model_name=config.LLM_MODEL):
        """
        Sends a prompt to the model and receives a response.
        """
        if not self.client:
            print("LLM Client is not initialized. Cannot send request.")
            # Return a mock response so the pipeline doesn't crash completely
            return "print('LLM Client is not configured.')"

        print(f"\n===== Sending request to LLM ({model_name}) =====")
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful and professional Python programmer and machine learning engineer as well as data scientist."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            
            # The LLM often wraps code in ```python ... ```, which needs to be removed
            if content.strip().startswith("```python"):
                content = content.strip()[9:-3].strip()
            
            print("===== Received response from LLM successfully =====\n")
            return content
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return None # Return None if there's an error