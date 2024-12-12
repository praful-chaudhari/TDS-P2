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


class DataAnalyzer:
    """
    A class used to analyze datasets and generate insights using an LLM.
    """
    def __init__(self, filename, api_token, api_url):
        """
        Initialize the DataAnalyzer with the dataset filename, API token, and API URL.

        :param filename: str, path to the dataset file
        :param api_token: str, API token for the LLM
        :param api_url: str, URL of the LLM API
        """
        self.filename = filename
        self.api_token = api_token
        self.api_url = api_url
        self.data = None
        self.numeric_data = None
        self.correlation_matrix = None

    def load_dataset(self):
        """
        Load the dataset from a file with different encoding attempts.
        """
        encodings = ["utf-8", "ISO-8859-1", "windows-1252", "utf-16", "utf-32"]
        for encoding in encodings:
            try:
                self.data = pd.read_csv(self.filename, encoding=encoding)
                print(f"Dataset '{self.filename}' loaded successfully with encoding '{encoding}'.")
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Error: Could not load file with common encodings.")

    def analyze_missing_values(self):
        """
        Analyze and return the count of missing values per column.
        """
        return self.data.isnull().sum()

    def analyze_correlation(self):
        """
        Compute and save the correlation matrix for numeric columns.
        """
        self.numeric_data = self.data.select_dtypes(include=[np.number])
        if self.numeric_data.shape[1] > 0:
            self.correlation_matrix = self.numeric_data.corr()
            sns.heatmap(self.correlation_matrix, annot=True, cmap="coolwarm", cbar=True)
            plt.title("Correlation Matrix of Numeric Features")
            plt.savefig("correlation_matrix.png")
            plt.close()
        else:
            self.correlation_matrix = None

    def generate_histograms(self):
        """
        Generate and save histograms for the first numeric column.
        """
        if not self.numeric_data.empty:
            column = self.numeric_data.columns[0]
            plt.figure(figsize=(10, 6))
            sns.histplot(self.data[column], kde=True)
            plt.title(f'Histogram of {column}')
            plt.savefig(f"{column}_histogram.png")
            plt.close()

    def generate_boxplots(self):
        """
        Generate and save boxplots for the first numeric column.
        """
        if not self.numeric_data.empty:
            column = self.numeric_data.columns[0]
            plt.figure(figsize=(10, 6))
            sns.boxplot(y=self.data[column])
            plt.title(f'Boxplot of {column}')
            plt.savefig(f"{column}_boxplot.png")
            plt.close()

    def analyze_outliers(self):
        """
        Detect outliers in numeric columns using the IQR method.

        :return: dict, count of outliers per column
        """
        outliers = {}
        for column in self.numeric_data.columns:
            Q1 = self.data[column].quantile(0.25)
            Q3 = self.data[column].quantile(0.75)
            IQR = Q3 - Q1
            outliers[column] = self.data[
                (self.data[column] < (Q1 - 1.5 * IQR)) | (self.data[column] > (Q3 + 1.5 * IQR))
            ].shape[0]
        return outliers

    def analyze_variance(self):
        """
        Compute variance for numeric columns.

        :return: dict, variance per column
        """
        variances = self.numeric_data.var()
        return variances.to_dict()

    def analyze_standard_deviation(self):
        """
        Compute standard deviation for numeric columns.

        :return: dict, standard deviation per column
        """
        std_devs = self.numeric_data.std()
        return std_devs.to_dict()

    def generate_prompt(self):
        """
        Generate a prompt for the LLM based on the dataset analysis.

        :return: str, the generated prompt
        """
        prompt = f"""
        Please analyze the following dataset and provide comprehensive insights:

        - Columns: {self.data.columns.tolist()}
        - Data Types: {self.data.dtypes.to_dict()}
        - Missing Values per Column: {self.analyze_missing_values().to_dict()}
        - Summary Statistics for Numeric Columns: {self.numeric_data.describe().to_dict() if not self.numeric_data.empty else "Not available"}
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
        return prompt

    def fetch_llm_response(self, prompt, temperature=0.7):
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
        response = requests.post(self.api_url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            raise ValueError(f"Error: {response.status_code} - {response.text}")

    def generate_narrative(self, insights):
        """
        Generate a narrative with the analysis insights and save it to README.md.

        :param insights: str, the insights from the LLM
        """
        with open("README.md", "w") as f:
            f.write("# Automated Dataset Analysis\n\n")
            f.write("## Summary\n")
            f.write(f"Columns: {self.data.columns.tolist()}\n")
            f.write(f"Missing Values: {self.analyze_missing_values().to_dict()}\n")
            f.write("## Correlation Matrix\n")
            if self.correlation_matrix is not None:
                f.write("![Correlation Matrix](correlation_matrix.png)\n")
            f.write("## Histograms\n")
            for i, column in enumerate(self.numeric_data.columns):
                if i >= 1:
                    break
                f.write(f"![Histogram of {column}](./{column}_histogram.png)\n")
            f.write("## Boxplots\n")
            for i, column in enumerate(self.numeric_data.columns):
                if i >= 1:
                    break
                f.write(f"![Boxplot of {column}](./{column}_boxplot.png)\n")
            f.write("## Insights\n")
            f.write(insights)

    def analyze(self):
        """
        Perform the complete analysis workflow.
        """
        self.load_dataset()
        self.analyze_missing_values()
        self.analyze_correlation()
        self.generate_histograms()
        self.generate_boxplots()
        self.analyze_outliers()
        self.analyze_variance()
        self.analyze_standard_deviation()
        prompt = self.generate_prompt()
        insights = self.fetch_llm_response(prompt)
        print("LLM Analysis:")
        print(insights)
        self.generate_narrative(insights)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <dataset.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
    API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

    if not AIPROXY_TOKEN:
        print("Error: AIPROXY_TOKEN environment variable not set.")
        sys.exit(1)

    analyzer = DataAnalyzer(filename, AIPROXY_TOKEN, API_URL)
    analyzer.analyze()
