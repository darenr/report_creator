import logging
import math
from typing import Dict, List, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import yaml

logging.basicConfig(level=logging.INFO)

import report_creator as rc

if __name__ == "__main__":
    df1 = pd.DataFrame(columns=["Name", "Age"])
    df1.Name = ["Lizzie", "Julie", "Andrea"]
    df1.Age = [24, 18, 22]

    fig1 = df1.plot.bar(x="Name", y="Age").get_figure()

    df2 = px.data.stocks()
    fig2 = px.line(df2, x="date", y=["GOOG", "AAPL", "NFLX", "MSFT"])

    with open(__file__, "r") as f:
        example_python = f.read()

    with open("example.yaml", "r") as f:
        datastructure = yaml.safe_load(f.read())

    with open("example.txt", "r") as f:
        example_text = f.read()

    with open("README.md", "r") as f:
        example_md = f.read()

    with rc.ReportCreator("Kitchen Sink Report") as report:
        view = rc.Block(
            rc.Collapse(
                rc.Python(example_python, label="kitchen_sink.py"),
                label="Code (kitchen_sink.py) to create this report",
            ),
            rc.Group(
                rc.Metric(
                    heading="Chances of rain",
                    value="84",
                    unit="%",
                ),
                rc.Metric(heading="Loss", value=0.1),
                rc.Metric(
                    heading="Accuracy",
                    value=95,
                    label="Number of correct predictions Total number of predictions",
                ),
                label="Grouped Stats",
            ),
            rc.Group(
                rc.Metric(
                    heading="Ultimate Answer",
                    value="42",
                ),
                rc.Metric(
                    heading="Confidence",
                    value=95,
                    unit="%",
                    label="How likely is this to be correct.",
                ),
                rc.Metric(
                    heading="Author",
                    value="Douglas Adams",
                ),
            ),
            rc.Text(
                example_text,
                label="Ready Player One",
            ),
            rc.InfoBox(
                "Warning: Killer Rabbit of Caerbannog",
                is_code=False,
                label="InfoBox",
            ),
            rc.Group(
                rc.Yaml(
                    datastructure,
                    label="Kubernetes Creating a Deployment as YAML",
                ),
                rc.Json(
                    datastructure,
                    label="Kubernetes Creating a Deployment as JSON",
                ),
            ),
            rc.Separator(),
            rc.Markdown(example_md, label="README.md"),
            rc.Plot(fig1, label="Matplotlib Figure - People"),
            rc.Plot(fig2, label="Plotly Figure - Stocks"),
            rc.Separator(),
            rc.Html(
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
            rc.Separator(),
            rc.Select(
                rc.DataTable(px.data.iris(), label="Iris Petals", index=False),
                rc.DataTable(
                    px.data.election(),
                    label="2013 Montreal Election",
                    index=False,
                ),
                rc.DataTable(
                    px.data.medals_long(),
                    label="Olympic Speed Skating",
                    index=False,
                ),
                rc.DataTable(
                    px.data.wind(),
                    label="Wind Intensity",
                    index=False,
                ),
                label="Tab Group of Data Tables",
            ),
            rc.Separator(),
            rc.Group(
                rc.Image(
                    "https://midlibraryassets.b-cdn.net/638266c083c0cd991057c455/655f82d114b7bf12e5f2e5d0_Portrait%20of%20a%20Man%20with%20a%20Medal%20of%20Cosimo%20il%20Vecchio%20de%27%20Medici%20(1475)-p-800.jpg",
                    label="Portrait of a Man with a Medal (1475)",
                    link="https://midlibrary.io/focus/sandro-botticelli",
                ),
                rc.Image(
                    "https://midlibraryassets.b-cdn.net/638266c083c0cd991057c455/655f82d07c2a7e39a7e7424e_Detail%20of%20The%20Spring%20(Flora)%20(late%201470s%20or%20early%201480s).jpg",
                    label="The Spring, Flora (late 1470s or early 1480s)",
                    link="https://midlibrary.io/focus/sandro-botticelli",
                ),
                rc.Image(
                    "https://midlibraryassets.b-cdn.net/638266c083c0cd991057c455/655f82d0703381e47145077a_Idealised%20Portrait%20of%20a%20Lady%20(Portrait%20of%20Simonetta%20Vespucci%20as%20Nymph)%20(1480%E2%80%931485).jpg",
                    label="Portrait of Simonetta Vespucci",
                    link="https://midlibrary.io/focus/sandro-botticelli",
                ),
            ),
        )

        report.save(view, "index.html", mode="light")
