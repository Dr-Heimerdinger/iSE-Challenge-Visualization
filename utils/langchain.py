from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import OPENAI_API_KEY

def create_llm_chain(system_prompt: str, model: str, temperature: float):
    """
    Creates a standardized LangChain chain with a specified system prompt, model, and temperature.

    Args:
        system_prompt (str): The system prompt to define the LLM's role.
        model (str): The name of the OpenAI model to use.
        temperature (float): The creativity/randomness of the model's output.

    Returns:
        A LangChain runnable sequence.
    """
    llm = ChatOpenAI(model=model, temperature=temperature, api_key=OPENAI_API_KEY)
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{user_prompt}")
    ])
    
    return prompt_template | llm | StrOutputParser()