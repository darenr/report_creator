import logging
from typing import Dict, List, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import pydataset
import yaml
import plotly.express as px

logging.basicConfig(level=logging.INFO)

from report_creator import (
    Base,
    Statistic,
    Blocks,
    Collapse,
    DataTable,
    Group,
    Markdown,
    Plot,
    Python,
    ReportCreator,
    Section,
    Select,
    Text,
    Yaml,
    Image,
)

if __name__ == "__main__":
    df1 = pd.DataFrame(columns=["Name", "Age"])
    df1.Name = ["Lizzie", "Julie", "Andrea"]
    df1.Age = [24, 18, 22]

    fig1 = df1.plot.bar(x="Name", y="Age").get_figure()
    
    df2 = px.data.stocks()
    fig2 = px.line(df2, x='date', y=['GOOG', 'AAPL', 'AMZN', 'FB', 'NFLX', 'MSFT'])

    with open(__file__, "r") as f:
        example_python = f.read()

    with open("example.yaml", "r") as f:
        yaml_data = yaml.safe_load(f.read())

    with open("example.txt", "r") as f:
        example_text = f.read()

    with open("README.md", "r") as f:
        example_md = f.read()

    report = ReportCreator("My Report")

    view = Blocks(
        Collapse(
            "Code (kitchen_sink.py) to create this report",
            Python(example_python, label="kitchen_sink.py"),
        ),
        Group(
            Statistic(
                heading="Chances of rain",
                value="84",
                unit="%",
            ),
            Statistic(heading="Loss", value=0.1),
            Statistic(
                heading="Accuracy",
                value=95,
                label="Number of correct predictions Total number of predictions",
            ),
            label="Grouped Stats",
        ),
        Group(
            Statistic(
                heading="Answer to Life, The Universe, and Everything",
                value="42",
            ),
            Statistic(
                heading="Confidence",
                value=95,
                unit="%",
                label="How likely is this to be correct.",
            ),
            Statistic(
                heading="Author",
                value="Douglas Adams",
            ),
        ),
        Text(
            example_text,
            label="Ready Player One",
        ),
        Yaml(
            yaml_data,
            label="Random Yaml",
        ),
        Section(),
        Markdown(example_md, label="Example Markdown"),
        Plot(fig2, label="Plotly Figure - Stocks"),
        Plot(fig1, label="Matplotlib Figure - People"),
        Select(
            DataTable(pydataset.data("Titanic"), label="Titanic", index=False),
            DataTable(pydataset.data("Journals"), label="Journals", index=False),
            DataTable(pydataset.data("Boston"), label="Boston", index=False),
            DataTable(pydataset.data("Housing"), label="Housing", index=False),
        ),
        Section(label="Images"),
        Group(
            Group(
                Image(
                    "https://media.tate.org.uk/art/images/work/T/T01/T01513_10.jpg",
                ),
                Image(
                    "https://media.tate.org.uk/art/images/work/T/T01/T01513_10.jpg",
                ),
                Image(
                    "https://media.tate.org.uk/art/images/work/T/T01/T01513_10.jpg",
                ),
                label="Yves Klein, IKB 79 1959",
            ),
            Group(
                Image("https://sufipathoflove.files.wordpress.com/2019/02/prim.jpg"),
                label="La Primavera – Botticelli"
            )
        ),
    )

    report.save(view, "index.html")
