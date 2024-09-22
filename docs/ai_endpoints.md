# AI Endpoints
This updated documentation provides more detailed information about the request structures and available options for the AI model calls, data cleaning and analysis endpoints.

## 1. Call Model: SQL Agent
- **POST** `/call-model`
- Request Body: `QueryRequest`
  ```python
  {
    "project_uuid": str,
    "file_uuid": list(str), # list of selected file uuids
    "question": str
  }
- Returns a JSON response
    ```python
    {
    "parsed_question": {
        "is_relevant": bool,
        "relevant_tables": [
            {
                "table_name": str,
                "columns": list(str),
                "noun_columns": list(str)
            },
            {
                "table_name": str,
                "columns": list(str),
                "noun_columns": list(str)
            },
        ]
    },
    "unique_nouns": list(str)
    "project_uuid": str,
    "sql_query": str,
    "sql_valid": bool, 
    "sql_issues": str,
    "results": list(list(str)),
    "answer": str,
    "visualization": str, # type of vis
    "visualization_reason": str, # reason for choosing that vis
    "formatted_data_for_visualization": {
        "labels": list(str),
        "values": list({"data": float, "label": str})
    }
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

## 3. Data cleaning
- **POST** `/data-cleaning`
- Request Body: `CleaningRequest`
    ```python 
    {
        "file_uuid": str, 
        "action": str
    }
- Available `action`: `handle_inconsistent_formats`, `handle_missing_values`, `handle_duplicates`,`handle_high_dimensionality`
- Returns a cleaned schema

## 4. Data analysis
- **POST** `/data-analysis`
- Request Body: `AnalysisRequest`
    ```python 
    {
        "file_uuid": str, 
        "action": str
    }
- Available `action`: `basic_insights`, `insights`