from fastapi import FastAPI, HTTPException
import os, sys

from backend_dateja.my_agent.main import graph
from pydantic import BaseModel

# Data model for the SQL query execution request
class QueryRequest(BaseModel):
    uuid: str
    query: str

# load credentials
API_KEY = os.getenv("GOOGLE_API_KEY")

app = FastAPI()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)