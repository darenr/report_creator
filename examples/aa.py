import pandas as pd


def df_to_mermaid_graph(df, direction="LR"):
    """Converts a Pandas DataFrame to a Mermaid.js graph."""

    mermaid_str = "graph " + direction + "\n"

    # Add nodes
    for index, row in df.iterrows():
        mermaid_str += f"    {index}({row[0]}) \n"

    # Add edges
    for index, row in df.iterrows():
        for col in df.columns[1:]:
            if pd.notnull(row[col]):
                mermaid_str += f"    {index} --> {row[col]} \n"

    return mermaid_str


# Example DataFrame
df = pd.DataFrame({"Task": ["A", "B", "C", "D"], "Dependency": [None, "A", "A", "B"]})
