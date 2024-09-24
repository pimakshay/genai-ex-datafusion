import os
import shutil
import sqlite3
import uuid

import pandas as pd
from typing import List
from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile, Query
from fastapi.responses import JSONResponse
from metadata_store import query_metadata, store_metadata
from pydantic import BaseModel

# Create FastAPI router
router = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(
    UPLOAD_DIR, exist_ok=True
)  # Create the uploads directory if it doesn't exist


# Data model for the SQL query execution request
class QueryRequest(BaseModel):
    file_uuid: str
    query: str


# Helper function to convert CSV to SQLite
def convert_csv_to_sqlite(csv_file_path: str, sqlite_file_path: str):
    try:
        # Read the CSV into a pandas DataFrame
        df = pd.read_csv(csv_file_path)

        # Write DataFrame to SQLite database
        with sqlite3.connect(sqlite_file_path) as conn:
            df.to_sql("data", conn, if_exists="replace", index=False)
    except Exception as e:
        raise RuntimeError(f"Error converting CSV to SQLite: {str(e)}")


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...), project_uuid: str = None, user_uuid: str = None
):
    try:
        # Check if the file is uploaded
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")

        # Generate a UUID for the file
        file_uuid = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1].lower()
        new_file_path = None

        # Handle .sqlite file
        if file_extension == ".sqlite":
            new_file_path = os.path.join(UPLOAD_DIR, f"{file_uuid}.sqlite")
            # Save the uploaded file to the new path
            with open(new_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        # Handle .csv file
        elif file_extension == ".csv":
            csv_file_path = os.path.join(UPLOAD_DIR, file.filename)
            new_file_path = os.path.join(UPLOAD_DIR, f"{file_uuid}.sqlite")

            # Save the CSV temporarily
            with open(csv_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Convert CSV to SQLite
            try:
                convert_csv_to_sqlite(csv_file_path, new_file_path)
                os.remove(csv_file_path)  # Remove the CSV file after conversion
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error converting CSV to SQLite: {str(e)}"
                )

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only .sqlite and .csv files are supported.",
            )

        # Store metadata in the metadata SQLite database
        store_metadata(file_uuid, project_uuid, user_uuid, UPLOAD_DIR, new_file_path)
        # Return the UUID of the uploaded file
        return JSONResponse(content={"file_uuid": file_uuid})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Endpoint for retrieving the schema of the database
@router.get("/get-uploads-dir")
async def get_uploads_dir():
    
    if os.path.exists(UPLOAD_DIR):
        return os.path.abspath(UPLOAD_DIR)

    return "Uploads directory doesn't exists."

# Endpoint for downloading the cleaned data
@router.get("/download_cleaned_data/{file_uuid}")
async def download_tables_as_csv(file_uuid: str):
    try:
        upload_dir = await get_uploads_dir()
        # Connect to the SQLite database
        conn = sqlite3.connect(os.path.join(upload_dir, f"{uuid}.sqlite"))

        # Define the table names
        tables = ['data', 'data_cleaned']
        
        # Iterate through the table names and export each one to a CSV file
        for table in tables:
            # Query the table data into a pandas dataframe
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            
            # Create the CSV filename using the file_uuid and table name
            csv_file_name = f"{file_uuid}_{table}.csv"
            
            # Write the dataframe to a CSV file
            df.to_csv(csv_file_name, index=False)
            
            print(f"Table '{table}' has been saved as '{csv_file_name}'.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        # Always close the database connection
        conn.close()

# Endpoint for executing SQL queries on uploaded databases
@router.post("/execute-query")
async def execute_query(request: QueryRequest):
    file_uuid = request.file_uuid
    query = request.query

    # Check if both uuid and query are provided
    if not file_uuid or not query:
        raise HTTPException(status_code=400, detail="Missing uuid or query")

    db_path = os.path.join(UPLOAD_DIR, f"{file_uuid}.sqlite")

    # Check if the database file exists
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")

    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the SQL query
        cursor.execute(query)
        results = cursor.fetchall()

        # Convert the results to JSON-friendly format
        result_list = [list(row) for row in results]
        return JSONResponse(content={"results": result_list})
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=f"SQL error: {e}")
    finally:
        cursor.close()
        conn.close()

# Endpoint for retrieving the schema of the database
@router.get("/get-schema/{uuid}")
async def get_schema(uuid: str):
    # Check if uuid is provided
    if not uuid:
        raise HTTPException(status_code=400, detail="Missing uuid")

    db_path = os.path.join(UPLOAD_DIR, f"{uuid}.sqlite")

    # Check if the database file exists
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")

    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get the table schema from sqlite_master
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        schema = []

        # Function to process each table and fetch its schema and example rows
        for table in tables:
            table_name, create_statement = table
            if "data_cleaned" in table_name:
                schema.append(f"Table: {table_name}")
                schema.append(f"CREATE statement: {create_statement}\n")

                # Fetch only 5 rows from the table as this is an example schema for model to generate sql query
                cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 5;")
                rows = cursor.fetchall()
                if rows:
                    schema.append("Example rows:")
                    for row in rows:
                        schema.append(str(row))
                schema.append("")  # Blank line between tables

        # Return the schema as a single response
        return JSONResponse(content={"schema": "\n".join(schema)})

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving schema: {e}")
    finally:
        cursor.close()
        conn.close()

# Endpoint for retrieving the schema of the database
@router.get("/get-schemas")
async def get_schemas(file_uuids:  List[str] = Query(..., description="List of file UUIDs"), project_uuid: str = "test"):
    # Check if uuid is provided
    if not file_uuids:
        raise HTTPException(status_code=400, detail="Missing uuid")

    try:
        await create_multi_file_dataframe(file_uuids=file_uuids, project_uuid=project_uuid)
        return await get_schema(uuid=project_uuid)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



# Basic hello world endpoint
@router.get("/")
async def root():
    return {"message": "Hello World"}


@router.get("/get-file-metadata/{file_uuid}")
async def get_file_metadata(file_uuid: str):
    try:
        # Query metadata from the metadata SQLite database
        result: dict = query_metadata(file_uuid, UPLOAD_DIR)

        if not result:
            raise HTTPException(status_code=404, detail="File metadata not found")

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/get-file-dataframe/{file_uuid}")
async def get_file_dataframe(file_uuid: str, table_name: str = 'data'):
    db_path = os.path.join(UPLOAD_DIR, f"{file_uuid}.sqlite")

    # Check if the database file exists
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")

    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)

        # Read the database into a pandas DataFrame
        df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)

        # Convert the DataFrame to JSON
        df_json = df.to_json(orient="records")

        return JSONResponse(content=df_json)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        conn.close()


@router.get("/create-multi-file-dataframe/{project_uuid}")
async def create_multi_file_dataframe(file_uuids: list[str], project_uuid: str = None):
    """
    This function creates a dataframe for a project from its csv files.
    Arguments:
    :project_uuids: uuid of the selected project
    :file_uuids: list of all uuids belonging to the given project
    """
    # Create a new merged database
    merged_db_name = os.path.join(UPLOAD_DIR, f"{project_uuid}.sqlite")

    # Check if the file already exists, and if so, delete it
    if os.path.exists(merged_db_name):
        os.remove(merged_db_name)

    merged_conn = sqlite3.connect(merged_db_name)

    for i, file_uuid in enumerate(file_uuids):
        source_file = os.path.join(UPLOAD_DIR, f"{file_uuid}.sqlite")
        if os.path.exists(source_file) is False:
            continue
        # Connect to the source database
        source_conn = sqlite3.connect(source_file)
        source_cursor = source_conn.cursor()
        
        # Get all table names from the source database
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = source_cursor.fetchall()
        
        for table in tables:
            source_table_name = table[0]
            if source_table_name=="data_cleaned":
                # Read data from the source table
                source_cursor.execute(f"SELECT * FROM {source_table_name}")
                data = source_cursor.fetchall()
                
                # Get column names
                source_cursor.execute(f"PRAGMA table_info({source_table_name})")
                # columns = [column[1] for column in source_cursor.fetchall()]
                columns_info = source_cursor.fetchall()
                
                # Create the table in the merged database
                # columns_definition = ', '.join([f'"{col}" TEXT' for col in columns])
                columns_definition = ', '.join([f'"{column[1]}" {column[2]}' for column in columns_info])
                merged_conn.execute(f"CREATE TABLE IF NOT EXISTS {source_table_name+str(i)} ({columns_definition})")
                
                # Insert data into the merged database
                placeholders = ', '.join(['?' for _ in columns_info])
                merged_conn.executemany(f"INSERT INTO {source_table_name+str(i)} VALUES ({placeholders})", data)
            
        # Close the source connection
        source_conn.close()

    # Commit changes and close the merged connection
    merged_conn.commit()
    merged_conn.close()
    return f"Project db saved to: {UPLOAD_DIR}"
