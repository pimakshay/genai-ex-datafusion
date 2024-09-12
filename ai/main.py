from fastapi import FastAPI
import os, sys
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

# set system path
CURR_DIR = os.path.dirname('__file__')
ROOT_DIR=os.path.join(os.getcwd() ,'../')
sys.path.append(ROOT_DIR)

from ai.api import csv_interactor

# load credentials
API_KEY = os.getenv("GOOGLE_API_KEY")

app = FastAPI()

app.include_router(csv_interactor.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)