# SQLITE Endpoints
This summary provides a quick overview of the available endpoints, their HTTP methods, paths, and expected input formats.

## 1. Upload File
- **POST** `/upload-file`
- Parameters:
  - `project_uuid` (optional)
  - `user_uuid` (optional)
- Returns 
    ```python 
    {"file_uuid": str}

## 2. Execute Query
- **POST** `/execute-query`
- Request Body:
  ```python
  {
    "file_uuid": str, # uuid of the file
    "query": str # SQL query to execute
  }

## 2. Call Receptionist Agent
- **POST** `/receptionist-agent/call-model`
- Request Body: `QueryRequest`
  ```python
  {
    "project_uuid": str,
    "file_uuid": list(str),
    "question": str
  }
- Returns a text response

## 3. Get Schema

- **GET** `/get-schema/{uuid}`
- Path Parameter: `uuid` of file

## 4. Get Schemas
- Used for retrieving schema of multiple files; calls `/create-multi-file-dataframe/{project_uuid}` internally.
- **GET** `/get-schemas`
- Query Parameters:
    ```python
    {
        "file_uuids": list(str), # List of file UUIDs
        "project_uuid": str # merged sqlite file is stored with project_uuid
    }

## 5. Get File Metadata
- **GET** `/get-file-metadata/{file_uuid}`
- Path Parameter: `file_uuid`
- Response body:
    ```python
    {
    "file_uuid": str,
    "project_uuid": str,
    "user_uuid": str,
    "file_name": str, # sqlite filename
    "file_size": 8192, # in bytes
    "row_count": 7, # number of rows
    "columns": [
        "order_id",
        "customer_id",
        "product_id",
        "quantity",
    ]
    }

## 6. Create Multi-File Dataframe
- Creates a dataframe from multiple input file uuids
- **GET** `/create-multi-file-dataframe/{project_uuid}`
- Path Parameter: `project_uuid`
- Query Parameters:
    ```python
    {
        "file_uuids": list(str),
        "project_uuid": str
    }