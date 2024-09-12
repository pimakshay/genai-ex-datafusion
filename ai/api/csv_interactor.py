import os
import sys
import json
from fastapi import APIRouter, HTTPException
from langchain.agents import AgentType

# Set system path for project directories
CURR_DIR = os.path.dirname('__file__')
ROOT_DIR = os.path.join(os.getcwd(), '../../')
sys.path.append(ROOT_DIR)

from ai.model.csv_agent import create_agent
from ai.model.query_csv_agent import query_agent
from ai.configs.llm_config import get_csv_llm_config
from ai.utils.helper_functions import fix_json
from fastapi import UploadFile, File

# Create FastAPI router
router = APIRouter()

# Define a global dictionary to hold agents by filename
csv_agents = {}

@router.post("/upload-csv")
async def upload_csv(filename: str):
    try:
        llm_model = get_csv_llm_config()

        # Create an agent with the uploaded CSV
        agent = create_agent(filename=filename,llm=llm_model, agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION)

        # Store the agent for future queries, using the filename as key
        csv_agents[filename] = agent

        return {"message": f"CSV file {filename} loaded and agent created successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading CSV: {str(e)}")



# Route to get matched courses based on keywords
@router.post("/csv-interactor")
async def csv_interactor(user_query: str, filename:str):
    try:
        agent = csv_agents[filename]
        if not agent:
            raise HTTPException(status_code=404, detail=f"CSV file {filename} not loaded or agent not created.")
                
        response = query_agent(agent=agent, query=user_query)
        
        try:
            response = json.loads(response)
        except json.JSONDecodeError as e:
            print(f"Original error in {filename}: {e}")
            print(f"Error in {filename} at line {e.lineno}, column {e.colno}")
            
            # If parsing fails, try to fix the JSON
            fixed_response = fix_json(response)
            response = json.loads(fixed_response, strict=False)

        return response

    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")