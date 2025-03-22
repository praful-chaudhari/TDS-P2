# TDS-P2

This repository contains a Python script that analyzes a given CSV file using the OpenAI API. The script is designed to provide insights and analysis based on the data provided in the CSV file. It is part of a RAG (Retrieval-Augmented Generation) application.

## How to Use

Run the script using the following command:

```bash
uv run autolysis.py filename.csv
```

Replace `filename.csv` with the path to your CSV file.

## Script Overview

The `autolysis.py` script performs the following tasks:

-   Reads the input CSV file provided as a command-line argument.
-   Processes the data to extract relevant information.
-   Uses the OpenAI API to analyze the data and generate insights.
-   Outputs the results of the analysis to the console or a specified output file.

## Prerequisites

-   An OpenAI API key is required to run the script. Ensure you have set up your API key as an environment variable:
    ```bash
    export OPENAI_API_KEY=your_api_key
    ```

## Features

-   **Data Analysis**: The script processes and analyzes the data in the CSV file.
-   **OpenAI Integration**: Leverages the OpenAI API to generate meaningful insights.
-   **Command-Line Interface**: Easy-to-use CLI for running the analysis.

## Example

To analyze a file named `data.csv`, run:

```bash
uv run autolysis.py data.csv
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This script requires an active OpenAI API key and may incur costs based on API usage. Please refer to OpenAI's pricing for more details.
