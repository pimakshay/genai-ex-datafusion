import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI

load_dotenv(dotenv_path="../../.env")

API_KEY = os.getenv("GOOGLE_API_KEY")

class LLMManager:
    def __init__(self):
        model_name = "gemini-1.5-flash"
        api_key = API_KEY
        temperature = 0.0
        verbose = True

        # Create an OpenAI object.
        self.llm = ChatGoogleGenerativeAI(model=model_name, 
                                google_api_key=api_key, 
                                temperature=temperature, 
                                verbose=verbose)

    def invoke(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        messages = prompt.format_messages(**kwargs)
        response = self.llm.invoke(messages)
        return response.content