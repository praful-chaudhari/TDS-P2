# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "matplotlib",
#     "numpy",
#     "pandas",
#     "requests",
#     "seaborn",
# ]
# ///

import os
import sys
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DataAnalyzer:
    """
    A class used to analyze datasets and generate insights using an LLM.
    """

    def __init__(self, filename: str, api_token: str, api_url: str):
        """
        Initialize the DataAnalyzer with the dataset filename, API token, and API URL.

        :param filename: str, path to the dataset file
        :param api_token: str, API token for the LLM
        :param api_url: str, URL of the LLM API
        """
        self.filename = filename
        self.api_token = api_token
        self.api_url = api_url
        self.data: Optional[pd.DataFrame] = None
        self.numeric_data: Optional[pd.DataFrame] = None
        self.correlation_matrix: Optional[pd.DataFrame] = None

    def load_dataset(self) -> None:
        """
        Load the dataset from a file with different encoding attempts.
        """
        encodings = ["utf-8", "ISO-8859-1", "windows-1252", "utf-16", "utf-32"]
        for encoding in encodings:
            try:
                self.data = pd.read_csv(self.filename, encoding=encoding)
                logging.info(f"Dataset '{self.filename}' loaded successfully with encoding '{encoding}'.")
                return
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logging.error(f"Unexpected error while loading dataset: {e}")
                raise
        raise ValueError("Error: Could not load file with common encodings.")

    def analyze_missing_values(self) -> pd.Series:
        """
        Analyze and return the count of missing values per column.
        """
        if self.data is None:
            raise ValueError("Dataset not loaded.")
        return self.data.isnull().sum()

    def analyze_correlation(self) -> None:
        """
        Compute and save the correlation matrix for numeric columns.
        """
        if self.data is None:
            raise ValueError("Dataset not loaded.")
        self.numeric_data = self.data.select_dtypes(include=[np.number])
        if not self.numeric_data.empty:
            self.correlation_matrix = self.numeric_data.corr()
            sns.heatmap(self.correlation_matrix, annot=True, cmap="coolwarm", cbar=True)
            plt.title("Correlation Matrix of Numeric Features")
            plt.savefig("correlation_matrix.png")
            plt.close()
            logging.info("Correlation matrix saved as 'correlation_matrix.png'.")
        else:
            self.correlation_matrix = None
            logging.warning("No numeric data available for correlation analysis.")

    def generate_histograms(self) -> None:
        """
        Generate and save histograms for numeric columns.
        """
        if self.numeric_data is None or self.numeric_data.empty:
            logging.warning("No numeric data available for histogram generation.")
            return
        for column in self.numeric_data.columns:
            plt.figure(figsize=(10, 6))
            sns.histplot(self.data[column], kde=True)
            plt.title(f'Histogram of {column}')
            plt.savefig(f"{column}_histogram.png")
            plt.close()
            logging.info(f"Histogram for '{column}' saved as '{column}_histogram.png'.")

    def generate_boxplots(self) -> None:
        """
        Generate and save boxplots for numeric columns.
        """
        if self.numeric_data is None or self.numeric_data.empty:
            logging.warning("No numeric data available for boxplot generation.")
            return
        for column in self.numeric_data.columns:
            plt.figure(figsize=(10, 6))
            sns.boxplot(y=self.data[column])
            plt.title(f'Boxplot of {column}')
            plt.savefig(f"{column}_boxplot.png")
            plt.close()
            logging.info(f"Boxplot for '{column}' saved as '{column}_boxplot.png'.")

    def analyze_outliers(self) -> Dict[str, int]:
        """
        Detect outliers in numeric columns using the IQR method.

        :return: dict, count of outliers per column
        """
        if self.numeric_data is None or self.numeric_data.empty:
            logging.warning("No numeric data available for outlier analysis.")
            return {}
        outliers = {}
        for column in self.numeric_data.columns:
            Q1 = self.data[column].quantile(0.25)
            Q3 = self.data[column].quantile(0.75)
            IQR = Q3 - Q1
            outliers[column] = self.data[(self.data[column] < (Q1 - 1.5 * IQR)) | 
                                         (self.data[column] > (Q3 + 1.5 * IQR))].shape[0]
        logging.info("Outlier analysis completed.")
        return outliers

    def analyze_variance(self) -> Dict[str, float]:
        """
        Compute variance for numeric columns.

        :return: dict, variance per column
        """
        if self.numeric_data is None or self.numeric_data.empty:
            logging.warning("No numeric data available for variance analysis.")
            return {}
        return self.numeric_data.var().to_dict()

    def analyze_standard_deviation(self) -> Dict[str, float]:
        """
        Compute standard deviation for numeric columns.

        :return: dict, standard deviation per column
        """
        if self.numeric_data is None or self.numeric_data.empty:
            logging.warning("No numeric data available for standard deviation analysis.")
            return {}
        return self.numeric_data.std().to_dict()

    def generate_prompt(self) -> str:
        """
        Generate a prompt for the LLM based on the dataset analysis.

        :return: str, the generated prompt
        """
        if self.data is None:
            raise ValueError("Dataset not loaded.")
        prompt = f"""
        Please analyze the following dataset and provide comprehensive insights:

        - Columns: {self.data.columns.tolist()}
        - Data Types: {self.data.dtypes.to_dict()}
        - Missing Values per Column: {self.analyze_missing_values().to_dict()}
        - Summary Statistics for Numeric Columns: {self.numeric_data.describe().to_dict() if self.numeric_data is not None else "Not available"}
        - Correlation Matrix (if applicable): {self.correlation_matrix.to_dict() if self.correlation_matrix is not None else "Not available"}
        - Outliers per Column: {self.analyze_outliers()}
        - Variance per Column: {self.analyze_variance()}
        - Standard Deviation per Column: {self.analyze_standard_deviation()}

        Based on the above information, please provide the following:
        1. Key findings and insights from the dataset.
        2. Patterns and trends observed in the data.
        3. Potential anomalies or outliers and their implications.
        4. Suggestions for further analysis or steps to take based on the data.
        5. Any additional observations or recommendations.
        """
        logging.info("Prompt for LLM generated.")
        return prompt

    def fetch_llm_response(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Fetch the response from the LLM based on the generated prompt.

        :param prompt: str, the prompt to be sent to the LLM
        :param temperature: float, the temperature setting for the LLM
        :return: str, the LLM response
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()
            return response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching response from LLM: {e}")
            return ""

    def generate_narrative(self, insights: str) -> None:
        """
        Generate a narrative with the analysis insights and save it to README.md.

        :param insights: str, the insights from the LLM
        """
        if self.data is None:
            raise ValueError("Dataset not loaded.")
        with open("README.md", "w") as f:
            f.write("# Automated Dataset Analysis\n\n")
            f.write("## Summary\n")
            f.write(f"Columns: {self.data.columns.tolist()}\n")
            f.write(f"Missing Values: {self.analyze_missing_values().to_dict()}\n")
            f.write("## Correlation Matrix\n")
            if self.correlation_matrix is not None:
                f.write("![Correlation Matrix](correlation_matrix.png)\n")
            f.write("## Histograms\n")
            for column in self.numeric_data.columns[:1]:
                f.write(f"![Histogram of {column}](./{column}_histogram.png)\n")
            f.write("## Boxplots\n")
            for column in self.numeric_data.columns[:1]:
                f.write(f"![Boxplot of {column}](./{column}_boxplot.png)\n")
            f.write("## Insights\n")
            f.write(insights)
        logging.info("Narrative saved to README.md.")

    def analyze(self) -> None:
        """
        Perform the complete analysis workflow.
        """
        self.load_dataset()
        self.analyze_missing_values()
        self.analyze_correlation()
        self.generate_histograms()
        self.generate_boxplots()
        prompt = self.generate_prompt()
        insights = self.fetch_llm_response(prompt)
        logging.info("LLM Analysis completed.")
        self.generate_narrative(insights)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: python script.py <dataset.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
    API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

    if not AIPROXY_TOKEN:
        logging.error("Error: AIPROXY_TOKEN environment variable not set.")
        sys.exit(1)

    analyzer = DataAnalyzer(filename, AIPROXY_TOKEN, API_URL)
    analyzer.analyze()
