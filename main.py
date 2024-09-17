import os
import sys

import httpx
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend_dateja.analysis import AdvancedVisualizer
from backend_dateja.cleaning import AdvancedDataPipeline

# from backend_dateja.my_agent.main import graph
from backend_dateja.my_agent.WorkflowManager import WorkflowManager


# Data model for the SQL query execution request
class QueryRequest(BaseModel):
    uuid: str
    query: str


class CleaningRequest(BaseModel):
    file_uuid: str
    action: str


class AnalysisRequest(BaseModel):
    file_uuid: str
    action: str


app = FastAPI()

# load credentials
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
ENDPOINT_URL = os.getenv("DB_ENDPOINT_URL")

# for deployment on langgraph cloud
graph = WorkflowManager(api_key=API_KEY, endpoint_url=ENDPOINT_URL).returnGraph()


@app.post("/call-model")
async def call_model(request: QueryRequest):
    uuid = request.uuid
    query = request.query

    # Check if both uuid and query are provided
    if not uuid or not query:
        raise HTTPException(status_code=400, detail="Missing uuid or query")

    try:
        response = graph.invoke({"question": query, "uuid": uuid})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return response


@app.post("/data-cleaning")
async def handle_missing_values(request: CleaningRequest):
    try:
        async with httpx.AsyncClient() as client:
            # from other application in port 8000
            response = await client.get(
                f"http://localhost:8000/get-file-dataframe/{request.file_uuid}"
            )
            df = pd.read_json(response.json())
            print(df)

        pipeline = AdvancedDataPipeline(df)
        response = pipeline.handle_request(request.action)[-1]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return response


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

        visualizer = AdvancedVisualizer(df)
        response = visualizer.handle_request(request.action)
        response = {
            "insights": response,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
