import json
from logging import getLogger

import numpy as np
import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from ..my_agent.DatabaseManager import DatabaseManager
from .utils import parse_json_output

logger = getLogger(__name__)


class GenerativeAIDataPipeline:
    def __init__(
        self,
        df,
        database_manager_endpoint: str,
    ):
        self.df = df
        self.database_manager = DatabaseManager(endpoint_url=database_manager_endpoint)
        self.base_llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
        )
        self.metadata = None
        self.numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        self.categorical_cols = self.df.select_dtypes(
            include=["object", "category"]
        ).columns
        self.datetime_cols = self.df.select_dtypes(include=["datetime64"]).columns
        self.agent_executor = create_pandas_dataframe_agent(
            self.base_llm,
            df,
            agent_type="zero-shot-react-description",
            verbose=True,
            allow_dangerous_code=True,
            return_intermediate_steps=True,
        )

    def extract_column_names_with_possible_subfeatures(self, df):
        """Extract column names that may contain subfeatures."""

        message = SystemMessage(
            content="""Extract the column names that may contain subfeatures from the dataframe.
Examples could be address, datetime column, phone number, etc. You can ignore numerical columns.
Return nothing but the result.
The output format should be:
{
    "columns": {
        "column_name": "subfeature1, subfeature2, subfeature3"
    }

}"""
        )

        try:
            res = self.agent_executor.invoke(message)
            res = parse_json_output(res["output"])
            return res
        except Exception as e:
            logger.exception(e)
            return {"columns": []}

    def extract_subcolumns(self, df, sub_column_info):
        """Extract subcolumns from the given columns."""
        for column in sub_column_info["columns"]:

            sub_columns_example_dict = {
                k.strip(): "some_value"
                for k in sub_column_info["columns"][column].split(",")
            }
            sys_message = SystemMessage(
                content=f"""Extract the subcolumns from the following column: {column}.
The column contains the following subfeatures: {sub_column_info["columns"][column]}.
The response should be in the following format:
{json.dumps(sub_columns_example_dict, indent=2)}
"""
            )

            def extract_str_subfeatures(info):
                try:
                    human_msg = HumanMessage(content=info)
                    response = self.base_llm.invoke([sys_message, human_msg])
                    response = parse_json_output(response.content)
                    return response
                except Exception as e:
                    logger.exception(e)
                    return {k.strip(): "" for k in sub_column_info[column].split(",")}

            df[column] = df[column].astype(str)
            df_sub_features = df[column].apply(extract_str_subfeatures).apply(pd.Series)

            df = pd.concat([df, df_sub_features], axis=1)

        return df

    def handle_request(self, action):
        if action == "extract_subcolumns":
            sub_column_info = self.extract_column_names_with_possible_subfeatures(
                self.df
            )
            res = self.extract_subcolumns(self.df, sub_column_info)
            return res
        else:
            raise ValueError(f"Invalid action: {action}")
