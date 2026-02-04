import sys
import os
import argparse
import pandas as pd
import requests
import json
import textwrap
import re
import subprocess

def load_data(filepath):
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    try:
        if ext == '.csv':
            return pd.read_csv(filepath)
        elif ext in ['.xls', '.xlsx']:
            return pd.read_excel(filepath)
        elif ext == '.json':
            return pd.read_json(filepath)
        elif ext == '.parquet':
            return pd.read_parquet(filepath)
        else:
            # Try CSV as default or fallback
            return pd.read_csv(filepath)
    except Exception as e:
        print(f"Error loading data from {filepath}: {e}")
        sys.exit(1)

def get_api_key():
    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not openai_key and not gemini_key:
        print("Error: No API key found. Please set OPENAI_API_KEY or GEMINI_API_KEY environment variable.")
        sys.exit(1)

    return openai_key, gemini_key

def call_openai(prompt, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        if 'response' in locals() and response:
             print(response.text)
        sys.exit(1)

def call_gemini(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        if 'response' in locals() and response:
            print(response.text)
        sys.exit(1)

def extract_python_code(text):
    # Regex to find code blocks
    match = re.search(r'```python(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If no python block, try generic code block
    match = re.search(r'```(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If no blocks, assume the whole text is code if it looks like it
    if "import " in text:
        return text.strip()

    return ""

def main():
    parser = argparse.ArgumentParser(description="Automatically create a report using report_creator and AI.")
    parser.add_argument("datafile", help="Path to the data file (csv, xlsx, etc.)")
    args = parser.parse_args()

    filepath = args.datafile
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    openai_key, gemini_key = get_api_key()

    print(f"Loading data from {filepath}...")
    df = load_data(filepath)

    # Prepare metadata for prompt
    dtypes = df.dtypes.to_string()
    try:
        head = df.head().to_string()
    except Exception:
        head = "Could not convert head to string"

    columns = list(df.columns)

    prompt = f"""
    I have a pandas DataFrame loaded from '{filepath}' with the following columns: {columns}

    Here are the data types:
    {dtypes}

    Here is the head of the data:
    {head}

    Please write a complete, runnable Python script using the `report_creator` library to analyze this data and create an HTML report.

    The script should:
    1. Import `report_creator as rc`, `pandas as pd`, and `plotly.express as px`.
    2. Load the data using the appropriate pandas function (read_csv, read_excel, etc) from '{filepath}'.
    3. Create a `rc.ReportCreator` context.
    4. Profile the data and create interesting visualizations (Bar, Scatter, etc) and metrics using `report_creator` components.
    5. Use `rc.Block`, `rc.Group`, `rc.Widget` (for plots), `rc.Metric`, `rc.Text`, etc.
    6. Save the report to 'report.html'.

    Here is an example of how to use `report_creator`:

    ```python
    import report_creator as rc
    import pandas as pd
    import plotly.express as px

    # Example loading data (you should load the actual file)
    # df = pd.read_csv('{filepath}')

    with rc.ReportCreator(title="My Report") as report:
        view = rc.Block(
            rc.Text("This is an example report."),
            rc.Group(
                rc.Metric(heading="Total Rows", value=len(df)),
                rc.Metric(heading="Columns", value=", ".join(df.columns)),
            ),
            # Example chart
            # rc.Widget(
            #    px.bar(df, x="column_x", y="column_y", title="My Chart"),
            #    label="Bar Chart"
            # )
        )
        report.save(view, "report.html")
    ```

    Generate ONLY the python code.
    """

    print("Querying AI to generate report script...")

    if openai_key:
        response_text = call_openai(prompt, openai_key)
    else:
        response_text = call_gemini(prompt, gemini_key)

    code = extract_python_code(response_text)

    if not code:
        print("Error: Could not extract Python code from AI response.")
        print("Response was:", response_text)
        sys.exit(1)

    output_script = "generate_report.py"
    with open(output_script, "w") as f:
        f.write(code)

    print(f"Generated script saved to {output_script}. Executing...")

    try:
        # Execute the generated script
        subprocess.check_call([sys.executable, output_script])
        print("Report generation complete. Check 'report.html'.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing generated script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
