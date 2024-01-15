import logging
from typing import Dict, List, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import yaml
import math

logging.basicConfig(level=logging.INFO)

from report_creator import (
    Base,
    Block,
    Collapse,
    DataTable,
    Group,
    Html,
    Image,
    Json,
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
                    heading="Ultimate Answer",
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
            Separator(),
            Html(
                "<span>"
                + "".join(
                    [
                        f"""
                <svg height="100" width="100">
                    <circle cx="50" cy="50" r="40" stroke="lightgrey" stroke-width="0.5" fill="{color}" />
                </svg>
                """
                        for color in (
                            "red",
                            "orange",
                            "yellow",
                            "green",
                            "indigo",
                            "violet",
                            "blue",
                        )
                    ]
                )
                + "</span>",
                label="HTML Showing SVG Circles with black border",
            ),
            Separator(),
            Select(
                DataTable(px.data.iris(), label="Iris Petals", index=False),
                DataTable(
                    px.data.election(),
                    label="2013 Montreal Election",
                    index=False,
                ),
                DataTable(
                    px.data.medals_long(),
                    label="Olympic Speed Skating",
                    index=False,
                ),
                DataTable(
                    px.data.wind(),
                    label="Wind Intensity",
                    index=False,
                ),
                label="Tab Group of Data Tables",
            ),
            Separator(),
            Group(
                Image(
                    "https://midlibraryassets.b-cdn.net/638266c083c0cd991057c455/655f82d114b7bf12e5f2e5d0_Portrait%20of%20a%20Man%20with%20a%20Medal%20of%20Cosimo%20il%20Vecchio%20de%27%20Medici%20(1475)-p-800.jpg",
                    label="Portrait of a Man with a Medal (1475)",
                    link="https://midlibrary.io/focus/sandro-botticelli",
                ),
                Image(
                    "https://midlibraryassets.b-cdn.net/638266c083c0cd991057c455/655f82d07c2a7e39a7e7424e_Detail%20of%20The%20Spring%20(Flora)%20(late%201470s%20or%20early%201480s).jpg",
                    label="The Spring, Flora (late 1470s or early 1480s)",
                    link="https://midlibrary.io/focus/sandro-botticelli",
                ),
                Image(
                    "https://midlibraryassets.b-cdn.net/638266c083c0cd991057c455/655f82d0703381e47145077a_Idealised%20Portrait%20of%20a%20Lady%20(Portrait%20of%20Simonetta%20Vespucci%20as%20Nymph)%20(1480%E2%80%931485).jpg",
                    label="Portrait of Simonetta Vespucci",
                    link="https://midlibrary.io/focus/sandro-botticelli",
                ),
            ),
        )

        report.save(view, "index.html", mode="light")
