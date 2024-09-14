from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent, create_csv_agent
from langchain.agents import AgentType
import pandas as pd

def create_agent(filename: str, llm: ChatGoogleGenerativeAI, agent_type: AgentType):
    """
    Create an agent that can access and use a large language model (LLM).

    Args:
        filename: The path to the CSV file that contains the data.

    Returns:
        An agent that can access and use the LLM.
    """

    # Read the CSV file into a Pandas DataFrame.
    df = pd.read_csv(filename)

    # Create a Pandas DataFrame agent.
    return create_pandas_dataframe_agent(llm, df, verbose=True, 
                                         allow_dangerous_code=True, 
                                         agent_type=agent_type,)
