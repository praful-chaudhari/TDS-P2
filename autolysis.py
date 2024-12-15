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
import base64

def load_dataset(filename):
    encodings = ["utf-8", "ISO-8859-1", "windows-1252", "utf-16", "utf-32"]
    for encoding in encodings:
        try:
            data = pd.read_csv(filename, encoding=encoding)
            print(f"Dataset '{filename}' loaded successfully with encoding '{encoding}'.")
            return data
        except UnicodeDecodeError:
            continue
    raise ValueError("Error: Could not load file with common encodings.")

def analyze_missing_values(data):
    return data.isnull().sum()

def analyze_correlation(data):
    numeric_data = data.select_dtypes(include=[np.number])
    if numeric_data.shape[1] > 0:
        correlation_matrix = numeric_data.corr()
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", cbar=True)
        plt.title("Correlation Matrix of Numeric Features")
        plt.savefig("correlation_matrix.png")
        plt.close()
        return correlation_matrix
    return None

def generate_histograms(data):
    numeric_data = data.select_dtypes(include=[np.number])
    if not numeric_data.empty:
        column = numeric_data.columns[0]
        plt.figure(figsize=(10, 6))
        sns.histplot(data[column], kde=True)
        plt.title(f'Histogram of {column}')
        plt.savefig("histogram.png")
        plt.close()

def generate_boxplots(data):
    numeric_data = data.select_dtypes(include=[np.number])
    if not numeric_data.empty:
        column = numeric_data.columns[0]
        plt.figure(figsize=(10, 6))
        sns.boxplot(y=data[column])
        plt.title(f'Boxplot of {column}')
        plt.savefig("boxplot.png")
        plt.close()

def encode_image_to_base64(filepath):
    with open(filepath, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    return base64_image

def analyze_outliers(data):
    outliers = {}
    numeric_data = data.select_dtypes(include=[np.number])
    for column in numeric_data.columns:
        Q1 = data[column].quantile(0.25)
        Q3 = data[column].quantile(0.75)
        IQR = Q3 - Q1
        outlier_condition = (data[column] < (Q1 - 1.5 * IQR)) | (data[column] > (Q3 + 1.5 * IQR))
        outliers[column] = data[outlier_condition].shape[0]
    return outliers

def analyze_variance(data):
    numeric_data = data.select_dtypes(include=[np.number])
    variances = numeric_data.var()
    return variances.to_dict()

def analyze_standard_deviation(data):
    numeric_data = data.select_dtypes(include=[np.number])
    std_devs = numeric_data.std()
    return std_devs.to_dict()

def get_example_values(data, num_examples=3):
    return data.head(num_examples).to_dict()

def generate_prompt(data, chart_base64, example_values):
    numeric_data = data.select_dtypes(include=[np.number])
    correlation_matrix = analyze_correlation(data)

    prompt = f"""
    Analyze this dataset and provide insights.

    - Columns: {data.columns.tolist()}
    - Data Types: {data.dtypes.to_dict()}
    - Missing Values: {analyze_missing_values(data).to_dict()}
    - Summary Stats: {numeric_data.describe().to_dict() if not numeric_data.empty else "Not available"}
    - Correlation Matrix: {correlation_matrix.to_dict() if correlation_matrix is not None else "Not available"}
    - Example Values: {example_values}

    Visualizations (base64, detail: low):
    - Histogram: {chart_base64['histogram']}
    - Boxplot: {chart_base64['boxplot']}
    - Correlation Matrix: {chart_base64['correlation_matrix']}

    Provide:
    1. Key findings.
    2. Patterns and trends.
    3. Anomalies or outliers.
    4. Suggestions for further analysis.
    5. Additional observations.
    """
    return prompt

def fetch_llm_response(prompt, api_token, api_url, temperature=0.7):
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        return response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError occurred: {e}")
        error_message = response.json().get("error", {}).get("message", "No error message available")
        error_details = response.json()
        print(f"Error details: {error_message}")
        print(error_details)
        return ""

def generate_narrative(data, insights):
    with open("README.md", "w") as f:
        f.write("# Automated Dataset Analysis\n\n")
        f.write("## Summary\n")
        f.write(f"Columns: {data.columns.tolist()}\n")
        f.write(f"Missing Values: {analyze_missing_values(data).to_dict()}\n")
        f.write("## Correlation Matrix\n")
        correlation_matrix = analyze_correlation(data)
        if correlation_matrix is not None:
            f.write("![Correlation Matrix](correlation_matrix.png)\n")
        f.write("## Histograms\n")
        numeric_data = data.select_dtypes(include=[np.number])
        for i, column in enumerate(numeric_data.columns):
            if i >= 1:
                break
            f.write(f"![Histogram of {column}](./histogram.png)\n")
        f.write("## Boxplots\n")
        for i, column in enumerate(numeric_data.columns):
            if i >= 1:
                break
            f.write(f"![Boxplot of {column}](./boxplot.png)\n")
        f.write("## Insights\n")
        f.write(insights)

def analyze(filename, api_token, api_url):
    data = load_dataset(filename)
    analyze_missing_values(data)
    analyze_correlation(data)
    generate_histograms(data)
    generate_boxplots(data)
    
    chart_base64 = {
        "histogram": encode_image_to_base64("histogram.png"),
        "boxplot": encode_image_to_base64("boxplot.png"),
        "correlation_matrix": encode_image_to_base64("correlation_matrix.png"),
    }

    example_values = get_example_values(data)

    analyze_outliers(data)
    analyze_variance(data)
    analyze_standard_deviation(data)
    prompt = generate_prompt(data, chart_base64, example_values)
    
    insights = fetch_llm_response(prompt, api_token, api_url)
    if insights:
        print("LLM Analysis:")
        print(insights)
        generate_narrative(data, insights)

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

    analyze(filename, AIPROXY_TOKEN, API_URL)
