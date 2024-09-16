import logging

import google.generativeai as genai
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class AdvancedVisualizer:

    def __init__(self, df):
        self.df = df
        self.original_df = df.copy()
        self.metadata = None
        self.numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        self.categorical_cols = self.df.select_dtypes(
            include=["object", "category"]
        ).columns
        self.datetime_cols = self.df.select_dtypes(include=["datetime64"]).columns

    def generate_basic_insights(self):
        if self.df is None:
            return "No data available. Please upload data first."

        try:
            insights = []

            # Basic dataset information
            insights.append(f"Dataset shape: {self.df.shape}")
            insights.append(f"Columns: {', '.join(self.df.columns)}")

            # Missing values
            missing_data = self.df.isnull().sum()
            insights.append("\nMissing values:")
            for column, count in missing_data[missing_data > 0].items():
                insights.append(f"  {column}: {count} ({count/len(self.df):.2%})")

            # Numeric column statistics
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            insights.append("\nNumeric column statistics:")
            for col in numeric_cols:
                insights.append(f"  {col}:")
                insights.append(f"    Mean: {self.df[col].mean():.2f}")
                insights.append(f"    Median: {self.df[col].median():.2f}")
                insights.append(f"    Std Dev: {self.df[col].std():.2f}")
                insights.append(f"    Min: {self.df[col].min():.2f}")
                insights.append(f"    Max: {self.df[col].max():.2f}")

            # Categorical column information
            cat_cols = self.df.select_dtypes(include=["object"]).columns
            insights.append("\nCategorical column information:")
            for col in cat_cols:
                insights.append(f"  {col}:")
                insights.append(f"    Unique values: {self.df[col].nunique()}")
                insights.append(
                    f"    Top 3 values: {', '.join(self.df[col].value_counts().nlargest(3).index.astype(str))}"
                )

            # Correlation insights
            if len(numeric_cols) > 1:
                corr_matrix = self.df[numeric_cols].corr()
                high_corr = corr_matrix[abs(corr_matrix) > 0.7].stack().reset_index()
                high_corr = high_corr[high_corr["level_0"] != high_corr["level_1"]]
                if not high_corr.empty:
                    insights.append("\nHigh correlations:")
                    for _, row in high_corr.iterrows():
                        insights.append(
                            f"  {row['level_0']} and {row['level_1']}: {row[0]:.2f}"
                        )

            # Data types
            insights.append("\nColumn data types:")
            for col, dtype in self.df.dtypes.items():
                insights.append(f"  {col}: {dtype}")

            # Sample data
            insights.append("\nSample data (first 5 rows):")
            insights.append(self.df.head().to_string())

            return "\n".join(insights)
        except Exception as e:
            logger.error(f"Error in generate_basic_insights: {str(e)}")
            logger.exception(e)

            return f"Error in generate_basic_insights: {str(e)}"

    def generate_ai_insights(self, basic_insights):
        if self.df is None:
            return "No data available. Please upload data first."

        try:
            model = genai.GenerativeModel("gemini-pro")
            prompt = f"""Analyze the following dataset summary and provide key insights, patterns, and recommendations:

                Dataset Summary:
                {basic_insights}

                Please provide:
                1. Key insights about the data
                2. Potential patterns or trends
                3. Recommendations for further analysis or actions
                4. Any potential issues or areas of concern in the data
                5. Suggestions for feature engineering or model selection based on the data characteristics
                """
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error generating AI insights: {str(e)}")
            return f"Error generating AI insights: {str(e)}"

    def generate_insights(self):
        basic_insights = self.generate_basic_insights()
        ai_insights = self.generate_ai_insights(basic_insights)
        return basic_insights + "\n\n" + ai_insights

    def create_numeric_summaries(self, columns):
        fig = make_subplots(
            rows=len(columns),
            cols=2,
            subplot_titles=[f"{col} Distribution" for col in columns for _ in range(2)],
        )
        for i, col in enumerate(columns, 1):
            fig.add_trace(
                go.Histogram(x=self.df[col], name=f"{col} Histogram", nbinsx=30),
                row=i,
                col=1,
            )
            fig.add_trace(go.Box(y=self.df[col], name=f"{col} Box Plot"), row=i, col=2)
        fig.update_layout(
            height=300 * len(columns),
            title_text="Numeric Column Distributions",
            showlegend=False,
            margin=dict(l=60, r=60, t=60, b=60),
            autosize=True,
        )
        fig.update_xaxes(title_text="Value")
        fig.update_yaxes(title_text="Frequency", col=1)
        fig.update_yaxes(title_text="Value Distribution", col=2)
        return fig

    def create_correlation_heatmap(self, columns):
        corr_matrix = self.df[columns].corr()
        fig = go.Figure(
            data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale="RdBu",
                zmin=-1,
                zmax=1,
                colorbar=dict(title="Correlation"),
            )
        )
        fig.update_layout(
            title="Correlation Between Numeric Variables",
            height=600,
            width=800,
            xaxis_title="Variables",
            yaxis_title="Variables",
            margin=dict(l=60, r=60, t=60, b=60),
            autosize=True,
        )
        return fig

    def create_categorical_summaries(self, columns, top_n=15):
        fig = make_subplots(
            rows=len(columns),
            cols=1,
            vertical_spacing=0.2,  # Increase vertical spacing between subplots
        )
        for i, col in enumerate(columns, 1):
            value_counts = self.df[col].value_counts()
            top_n_counts = value_counts.nlargest(top_n)
            other_count = value_counts.sum() - top_n_counts.sum()
            if other_count > 0:
                top_n_counts["Other"] = other_count
            fig.add_trace(
                go.Bar(x=top_n_counts.index, y=top_n_counts.values, name=col),
                row=i,
                col=1,
            )

            # Update x-axis for each subplot individually
            fig.update_xaxes(
                tickangle=-45, title_text=col, automargin=True, row=i, col=1
            )

        fig.update_layout(
            height=500 * len(columns),  # Adjust height per subplot
            title_text="Top 15 Categories for Each Categorical Variable",
            showlegend=False,
            margin=dict(l=80, r=20, t=100, b=50, pad=4),
        )

        fig.update_yaxes(title_text="Count", title_standoff=15)

        # Adjust layout for better spacing
        fig.update_layout(
            uniformtext_minsize=8, uniformtext_mode="hide", bargap=0.15, bargroupgap=0.1
        )

        return fig
