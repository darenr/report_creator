import logging
from typing import Dict, List, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import yaml

logging.basicConfig(level=logging.INFO)

from report_creator import (
    Base,
    Block,
    Collapse,
    DataTable,
    Group,
    Image,
    Json,
    Html,
    Markdown,
    Plot,
    Python,
    ReportCreator,
    Select,
    Separator,
    Statistic,
    Text,
    Yaml,
)

if __name__ == "__main__":
    df1 = pd.DataFrame(columns=["Name", "Age"])
    df1.Name = ["Lizzie", "Julie", "Andrea"]
    df1.Age = [24, 18, 22]

    fig1 = df1.plot.bar(x="Name", y="Age").get_figure()

    df2 = px.data.stocks()
    fig2 = px.line(df2, x="date", y=["GOOG", "AAPL", "AMZN", "FB", "NFLX", "MSFT"])

    with open(__file__, "r") as f:
        example_python = f.read()

    with open("example.yaml", "r") as f:
        datastructure = yaml.safe_load(f.read())

    with open("example.txt", "r") as f:
        example_text = f.read()

    with open("README.md", "r") as f:
        example_md = f.read()

    with ReportCreator("Kitchen Sink Report") as report:
        view = Block(
            Collapse(
                Python(example_python, label="kitchen_sink.py"),
                label="Code (kitchen_sink.py) to create this report",
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
            Group(
                Yaml(
                    datastructure,
                    label="Kubernetes Creating a Deployment as YAML",
                ),
                Json(
                    datastructure,
                    label="Kubernetes Creating a Deployment as JSON",
                ),
            ),
            Separator(),
            Markdown(example_md, label="README.md"),
            Plot(fig1, label="Matplotlib Figure - People"),
            Plot(fig2, label="Plotly Figure - Stocks"),
            Html("""
                <svg height="100" width="100">
                    <circle cx="50" cy="50" r="40" stroke="black" stroke-width="3" fill="blue" />
                </svg>
                """, label="HTML Showing blue SVG Circle with black border"),
            Select(
                DataTable(px.data.iris(), label="Iris", index=False),
                DataTable(
                    px.data.election(),
                    label="2013 Montreal election",
                    index=False,
                ),
                DataTable(
                    px.data.medals_long(),
                    label="Olympic speed Skating",
                    index=False,
                ),
                DataTable(
                    px.data.wind(),
                    label="Wind intensity",
                    index=False,
                ),
            ),
            Separator(label="Images"),
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
                    Image(
                        "https://sufipathoflove.files.wordpress.com/2019/02/prim.jpg"
                    ),
                    label="La Primavera – Botticelli",
                ),
            ),
        )

        report.save(view, "index.html")
