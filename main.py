import logging
import os
import sys
from io import StringIO
import sqlite3

import httpx
import pandas as pd
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend_dateja.analysis import AdvancedVisualizer
from backend_dateja.cleaning import AdvancedDataPipeline

# from backend_dateja.my_agent.main import graph
from backend_dateja.my_agent.WorkflowManager import WorkflowManager
from backend_dateja.receptionist.assistant import VirtualAssistant
from backend_dateja.combined_agents import CombinedAgent
from backend_dateja.speech2text.audio_recognition import transcribe_streaming
logger = logging.getLogger(__name__)


# Data model for the SQL query execution request
class QueryRequest(BaseModel):
    project_uuid: str
    file_uuid: List[str]
    question: str


class CleaningRequest(BaseModel):
    file_uuid: str
    action: str # options: handle_inconsistent_formats, handle_missing_values, handle_duplicates, handle_high_dimensionality


class AnalysisRequest(BaseModel):
    file_uuid: str
    action: str # options: basic_insights, insights, 


app = FastAPI()

# load credentials
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
ENDPOINT_URL = os.getenv("DB_ENDPOINT_URL")
SPEECH2TEXT_CREDS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# for deployment on langgraph cloud
# define csv_agent_graph
csv_agent_graph = WorkflowManager(api_key=API_KEY, endpoint_url=ENDPOINT_URL).returnGraph()

# define receptionist_agent
assistant = VirtualAssistant(api_key=API_KEY)
receptionist_agent = assistant.get_agent()

# combined agent
combined_agent = CombinedAgent(api_key=API_KEY, endpoint_url=ENDPOINT_URL)

@app.post("/call-model")
async def call_model(request: QueryRequest):
    project_uuid = request.project_uuid
    file_uuid = request.file_uuid
    question = request.question
    # Check if both uuid and query are provided
    if not file_uuid or not question or not project_uuid:
        raise HTTPException(status_code=400, detail="Missing uuid or query")

    try:
        response = csv_agent_graph.invoke(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return response

@app.post("/receptionist-agent/call-model")
async def call_receptionist_agent(query: str):
    # Check if both uuid and query are provided
    if not query:
        raise HTTPException(status_code=400, detail="Missing query")

    try:
        response = receptionist_agent.invoke(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return response


@app.post("/combined-agent/call-model")
async def call_combined_agent(request: QueryRequest):
    project_uuid = request.project_uuid
    file_uuid = request.file_uuid
    query = request.question

    # Check if both uuid and query are provided
    if not file_uuid or not query or project_uuid:
        raise HTTPException(status_code=400, detail="Missing uuid or query")
    try:
        response = combined_agent.invoke(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return response


@app.post("/data-cleaning-actions")
async def data_cleaning_actions(request: CleaningRequest):
    try:
        async with httpx.AsyncClient() as client:
            # from other application in port 8000
            response = await client.get(
                f"{ENDPOINT_URL}/get-file-dataframe/{request.file_uuid}?table_name=data"
            )
            df = pd.read_json(response.json())
            print(df)

        pipeline = AdvancedDataPipeline(df)
        string_io = StringIO()
        response = pipeline.handle_request(request.action)[0].to_csv(
            string_io, index=False
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return StreamingResponse(iter([string_io.getvalue()]), media_type="text/csv")


@app.post("/data-cleaning-pipeline")
async def data_cleaning_pipeline(request: CleaningRequest):
    try:
        async with httpx.AsyncClient() as client:
            # from other application in port 8000
            response = await client.get(
                f"http://localhost:8000/get-file-dataframe/{request.file_uuid}"
            )

            uploads_dir = await client.get(
                f"http://localhost:8000/get-uploads-dir"
            )
            uploads_dir = uploads_dir.json()
            df = pd.read_json(response.json())
            print(df)

        pipeline = AdvancedDataPipeline(df)
        cleaned_df = pipeline.run_all()[0] #.to_csv(string_io, index=False)
       
        # Connect to SQLite and save the cleaned data
        db_path = os.path.join(uploads_dir, f"{request.file_uuid}.sqlite")

        conn = sqlite3.connect(db_path)
        try:
            cleaned_df.to_sql('data_cleaned', conn, if_exists='replace', index=False)
            print("Data saved to 'data_cleaned' table successfully.")
        except Exception as e:
            logger.exception("Error saving data to SQLite.")
            raise HTTPException(status_code=500, detail=f"Failed to save cleaned data: {str(e)}")
        finally:
            conn.close()

    except Exception as e:
        logger.exception("Error during the data cleaning pipeline.")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return {"message": "Data cleaned and saved to 'data_cleaned' table successfully."}


@app.post("/data-analysis")
async def handle_data_analysis(request: AnalysisRequest):
    try:
        async with httpx.AsyncClient() as client:
            # from other application in port 8000
            response = await client.get(
                f"http://localhost:8000/get-file-dataframe/{request.file_uuid}"
            )
            df = pd.read_json(response.json())
            print(df)

        visualizer = AdvancedVisualizer(df, api_key=API_KEY)
        response = visualizer.handle_request(request.action)
        response = {
            "insights": response,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return response

@app.post("/speech2text/{file_path}")
async def recognize_voice(file_path: str):
    return transcribe_streaming(stream_file=file_path, credential_path=SPEECH2TEXT_CREDS)[0]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
