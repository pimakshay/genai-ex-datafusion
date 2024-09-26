import logging
import os
import sys
from io import StringIO
import sqlite3

import httpx
import pandas as pd
from io import BytesIO
import markdown2
from weasyprint import HTML
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


from backend_dateja.analysis import AdvancedVisualizer
from backend_dateja.cleaning import AdvancedDataPipeline

# from backend_dateja.my_agent.main import graph
from backend_dateja.my_agent.WorkflowManager import WorkflowManager
from backend_dateja.receptionist.assistant import VirtualAssistant
from backend_dateja.combined_agents import CombinedAgent

logger = logging.getLogger(__name__)


# Data model for the SQL query execution request
class QueryRequest(BaseModel):
    project_uuid: str
    file_uuid: List[str]
    question: str


class CleaningRequest(BaseModel):
    file_uuid: str
    action: str  # options: handle_inconsistent_formats, handle_missing_values, handle_duplicates, handle_high_dimensionality


class AnalysisRequest(BaseModel):
    file_uuid: str
    action: str  # options: basic_insights, insights,


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# load credentials
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
ENDPOINT_URL = os.getenv("DB_ENDPOINT_URL")
SPEECH2TEXT_CREDS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# for deployment on langgraph cloud
# define csv_agent_graph
csv_agent_graph = WorkflowManager(
    api_key=API_KEY, endpoint_url=ENDPOINT_URL
).returnGraph()

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
async def data_cleaning_pipeline(file_uuid: str):
    try:
        async with httpx.AsyncClient() as client:
            # from other application in port 8000
            response = await client.get(
                f"{ENDPOINT_URL}/get-file-dataframe/{file_uuid}"
            )

            uploads_dir = await client.get(f"{ENDPOINT_URL}/get-uploads-dir")
            uploads_dir = uploads_dir.json()
            df = pd.read_json(response.json())
            print(df)

        pipeline = AdvancedDataPipeline(df)
        cleaned_df = pipeline.run_all()[0]  # .to_csv(string_io, index=False)

        # Connect to SQLite and save the cleaned data
        db_path = os.path.join(uploads_dir, f"{file_uuid}.sqlite")

        conn = sqlite3.connect(db_path)
        try:
            cleaned_df.to_sql("data_cleaned", conn, if_exists="replace", index=False)
            # print("Data saved to 'data_cleaned' table successfully.")
            return {"message": "Finished data cleaning."}
        except Exception as e:
            logger.exception("Error saving data to SQLite.")
            raise HTTPException(
                status_code=500, detail=f"Failed to save cleaned data: {str(e)}"
            )
        finally:
            conn.close()

    except Exception as e:
        logger.exception("Error during the data cleaning pipeline.")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    # return {"message": "Finished data cleaning."}


@app.post("/data-analysis")
async def handle_data_analysis(request: AnalysisRequest):
    try:
        async with httpx.AsyncClient() as client:
            # from other application in port 8000
            response = await client.get(
                f"{ENDPOINT_URL}/get-file-dataframe/{request.file_uuid}"
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


@app.post("/download-data-analysis")
async def download_data_analysis(file_uuid):
    try:
        async with httpx.AsyncClient() as client:
            # from other application in port 8000
            response = await client.get(
                f"{ENDPOINT_URL}/get-file-dataframe/{file_uuid}"
            )
            df = pd.read_json(response.json())
            print(df)

        visualizer = AdvancedVisualizer(df, api_key=API_KEY)
        markdown_response = visualizer.handle_request("generate_report")
        # Convert markdown to HTML
        html_content = markdown2.markdown(markdown_response)

        # Add some basic styling
        styled_html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
                    h1, h2, h3 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
        </html>
        """

        # Convert HTML to PDF
        pdf_buffer = BytesIO()
        HTML(string=styled_html).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)

        # Return PDF as a downloadable file
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={file_uuid}_data_insights.pdf"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
