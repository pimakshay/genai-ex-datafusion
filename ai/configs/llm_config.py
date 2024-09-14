import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
load_dotenv(dotenv_path="../../.env")

# load credentials
API_KEY = os.getenv("GOOGLE_API_KEY")

def get_csv_llm_config():
    """
    Returns an instance of the LLM (e.g., OpenAI) initialized with the necessary API key.
    You can extend this to switch models based on config or environment variables.
    """
    model_name = "gemini-1.5-flash"
    api_key = API_KEY
    temperature = 0.0
    verbose = True

    # Create an OpenAI object.
    llm = ChatGoogleGenerativeAI(model=model_name, 
                             google_api_key=api_key, 
                             temperature=temperature, 
                             verbose=verbose)

    return llm
