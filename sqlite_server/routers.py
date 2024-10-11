import os
import shutil
import sqlite3
import uuid
from io import BytesIO
import markdown2
from weasyprint import HTML

import pandas as pd
import zipfile
import tabula
from typing import List
from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile, Query
from fastapi.responses import JSONResponse
# from metadata_store import query_metadata, store_metadata
from pydantic import BaseModel
from io import StringIO
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI router
router = FastAPI()

router.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
CLEANED_TABLE_NAME = "data_cleaned"
ANALYSED_TABLE_NAME = "data_analysed"
os.makedirs(
    UPLOAD_DIR, exist_ok=True
)  # Create the uploads directory if it doesn't exist


# Data model for the SQL query execution request
class QueryRequest(BaseModel):
    file_uuid: str
    query: str

# Helper function to store DataFrame(s) to SQLite
def convert_dataframe_to_sqlite(df, sqlite_file_path: str):
    try:
        # Open a connection to the SQLite database
        with sqlite3.connect(sqlite_file_path) as conn:
            # Check if df is a list of DataFrames
            if isinstance(df, list):
                for idx, dataframe in enumerate(df):
                    table_name = f"data_{idx+1}"  # Create unique table names for each DataFrame
                    dataframe.to_sql(table_name, conn, if_exists="replace", index=False)
            else:
                # If df is a single DataFrame, store it with a default table name
                df.to_sql("data", conn, if_exists="replace", index=False)
    except Exception as e:
        raise RuntimeError(f"Error converting DataFrame(s) to SQLite: {str(e)}")

def table_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    has_cleaned_table = False
    for table in tables:
        table_name, create_statement = table
        if table_name in table_name:
            has_cleaned_table = True

    if has_cleaned_table is False:
        raise HTTPException(status_code=404, detail=f"Cleaned Table does not exist in the database")
    
    return True

@router.post("/upload-file", description="Allowed file formats: csv, xls, xlsx, sqlite, pdf ")
async def upload_file(
    file: UploadFile = File(...),
):
    # Check if both uuid and query are provided
    if not file:
        raise HTTPException(status_code=400, detail="Missing uuids or file")
    allowed_formats = ["csv", "xls", "xlsx", "sqlite", "pdf"]
    file_extension = os.path.splitext(file.filename)[1][1:].lower()

    if file_extension not in allowed_formats:
        raise HTTPException(status_code=400, detail=f"Invalid file format. Allowed formats are: {', '.join(allowed_formats)}")
    
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
                df = pd.read_csv(csv_file_path)
                convert_dataframe_to_sqlite(df, new_file_path)
                os.remove(csv_file_path)  # Remove the CSV file after conversion
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error converting CSV to SQLite: {str(e)}"
                )
        # Handle .xls and .xlsx files
        elif file_extension in [".xls", ".xlsx"]:
            excel_file_path = os.path.join(UPLOAD_DIR, file.filename)
            new_file_path = os.path.join(UPLOAD_DIR, f"{file_uuid}.sqlite")

            # Save the Excel file temporarily
            with open(excel_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Convert Excel to SQLite
            try:
                df = pd.read_excel(excel_file_path)
                convert_dataframe_to_sqlite(df, new_file_path)
                os.remove(excel_file_path)  # Remove the Excel file after conversion
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error converting Excel to SQLite: {str(e)}"
                )
        # Handle .pdf files
        elif file_extension in [".pdf"]:
            pdf_file_path = os.path.join(UPLOAD_DIR, file.filename)
            new_file_path = os.path.join(UPLOAD_DIR, f"{file_uuid}.sqlite")

            # Save the pdf file temporarily
            with open(pdf_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Convert pdf to SQLite
            try:
                df = tabula.read_pdf(pdf_file_path, 
                                     pages='all', 
                                     multiple_tables=True, 
                                     stream=True,)
                                    #  pandas_options={'header': None})
                # df = pd.concat(df, ignore_index=True)
                # df.columns = column_names
                convert_dataframe_to_sqlite(df, new_file_path)
                os.remove(pdf_file_path)  # Remove the pdf file after conversion
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error converting PDF to SQLite: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only .sqlite, .csv, .xls, .xlsx, or .pdf files are supported.",
            )
        return JSONResponse(content={"file_uuid": file_uuid})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Endpoint for retrieving the schema of the database
@router.get("/get-uploads-dir")
async def get_uploads_dir():
    
    if os.path.exists(UPLOAD_DIR):
        return os.path.abspath(UPLOAD_DIR)

    return "Uploads directory doesn't exists."

async def get_table_as_csv(file_uuid: str, table_prefix: str):
    # Get the uploads directory (assuming it's a sync function now)
    upload_dir = await get_uploads_dir()  # Adjust if you use await or any async operation
    db_file_path = os.path.join(upload_dir, f"{file_uuid}.sqlite")

    # Connect to the SQLite database
    conn = sqlite3.connect(db_file_path)

    try:
        # retrieve all table names
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql_query(query, conn)

        # Check if any tables exist
        if tables.empty:
            raise HTTPException(status_code=404, detail="No tables found in the database")

        # Dictionary to hold CSV data for each table
        csv_buffers = {}

        # Process each table, convert to CSV, and store in a StringIO buffer
        for table in tables['name']:
            if table_prefix in table:
                df = pd.read_sql_query(f"SELECT * FROM {table};", conn)
                csv_buffer = StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)
                csv_buffers[table] = csv_buffer.getvalue()  # Store CSV content as a string

        if bool(csv_buffers):
            return csv_buffers  # Return the dictionary with table names and CSV data
        else:
            raise HTTPException(status_code=404, detail="Data is not cleaned")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting table {table_prefix}: {str(e)}")
    
    finally:
        # Always close the database connection
        conn.close()

# Updated download route to handle multiple tables as CSVs
@router.get("/download_cleaned_data/{file_uuid}")
async def download_tables_as_csv(file_uuid: str):
    try:
        # Get the CSV data for all tables (or just the specified one)
        csv_data = await get_table_as_csv(file_uuid=file_uuid, table_prefix=CLEANED_TABLE_NAME)

        # If multiple tables, zip them
        if isinstance(csv_data, dict) and len(csv_data) > 1:
            # Create an in-memory ZIP file
            zip_buffer = BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for table_name, csv_content in csv_data.items():
                    # Write each table's CSV content to a separate file in the ZIP
                    zip_file.writestr(f"{file_uuid}_{table_name}.csv", csv_content)

            # Reset the buffer position to the beginning
            zip_buffer.seek(0)

            # Return the ZIP file as a streaming response
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={file_uuid}_tables.zip"}
            )

        # If only a single table was returned, send it as CSV directly
        else:
            table_name = list(csv_data.keys())[0]
            csv_content = csv_data[table_name]

            # Stream the single CSV file
            csv_buffer = StringIO(csv_content)
            csv_buffer.seek(0)

            return StreamingResponse(
                csv_buffer,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={file_uuid}_{table_name}.csv"}
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download CSV: {str(e)}")

# Updated route to handle multiple analyzed tables and return as PDF files
@router.get("/download_data_analysis/{file_uuid}")
async def download_data_insights_as_pdf(file_uuid: str):
    try:
        upload_dir = await get_uploads_dir()
        # Connect to the SQLite database
        db_file_path = os.path.join(upload_dir, f"{file_uuid}.sqlite")
        conn = sqlite3.connect(db_file_path)

        # Query to get all analyzed tables (those with names like "data_analyzed_{i}")
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '{ANALYSED_TABLE_NAME}_%';"
        analyzed_tables = pd.read_sql_query(query, conn)

        # Check if any analyzed tables are found
        if analyzed_tables.empty:
            raise HTTPException(status_code=404, detail="No analyzed tables found in the database")

        # Prepare to collect all PDFs in a ZIP file
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for table_name in analyzed_tables['name']:
                # Read the analyzed table data into a DataFrame
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

                # Assuming the table has a markdown column named "markdown_content"
                if "markdown_content" not in df.columns or df.empty:
                    continue  # Skip this table if there's no content or markdown column

                # Convert markdown to HTML
                html_content = markdown2.markdown(df["markdown_content"].iloc[0])

                # Add some basic styling for the PDF
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

                # Convert the styled HTML to a PDF
                pdf_buffer = BytesIO()
                HTML(string=styled_html).write_pdf(pdf_buffer)
                pdf_buffer.seek(0)

                # Add the PDF to the ZIP file with the table's name
                zip_file.writestr(f"{file_uuid}_{table_name}.pdf", pdf_buffer.getvalue())

        # Reset the buffer position to the beginning
        zip_buffer.seek(0)

        # Return the ZIP file as a streaming response
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={file_uuid}_analyzed_tables.zip"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    finally:
        # Always close the database connection
        conn.close()

##

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
        table_exists(conn=conn, table_name=CLEANED_TABLE_NAME)
        cursor = conn.cursor()

        # Get the table schema from sqlite_master
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        schema = []

        # Function to process each table and fetch its schema and example rows
        for table in tables:
            table_name, create_statement = table
            if CLEANED_TABLE_NAME in table_name:
                schema.append(f"Table: {table_name}")
                schema.append(f"CREATE statement: {create_statement}\n")

                # Fetch only 5 rows from the table as this is an example schema for model to generate sql query
                cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 10;")
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
    return {"message": "This is a sqlite-server"}


@router.get("/get-file-dataframe/{file_uuid}")
async def get_file_dataframe(file_uuid: str, table_prefix: str = ""):
    db_path = os.path.join(UPLOAD_DIR, f"{file_uuid}.sqlite")

    # Check if the database file exists
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")

    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)

        # If no specific table_name is provided, retrieve all table names
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql_query(query, conn)

        # Check if any tables are found
        if tables.empty:
            raise HTTPException(status_code=404, detail="No tables found in the database")

        # Read all tables into DataFrames
        dataframes = []
        for table in tables['name']:
            if table_prefix in table:
                df = pd.read_sql_query(f"SELECT * FROM {table};", conn)
                df_json = df.to_json(orient="records")
                dataframes.append(df_json)

        return JSONResponse(content=dataframes)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        conn.close()


# @router.get("/create-multi-file-dataframe/{project_uuid}")
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
            if CLEANED_TABLE_NAME in source_table_name:
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
