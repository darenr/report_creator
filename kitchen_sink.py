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
    # set up of example text, plots and dataframes
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

    # begin the use of the report_creator package

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
                label="Grouped Stats",
            ),
            rc.Text(
                example_text,
                label="Ready Player One",
            ),
            rc.InfoBox(
                "**Warning** *You’ve performed this action too many times, please try again later.*",
                format="markdown",
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
                    "https://images.metmuseum.org/CRDImages/ma/mobile-large/DT1438.jpg",
                    label="The Italian Woman - Modigliani (1916)",
                    link="https://www.metmuseum.org/art/collection/search/489102",
                ),
                rc.Image(
                    "https://images.metmuseum.org/CRDImages/ma/mobile-large/DT2180.jpg",
                    label="Jeanne Hébuterne - Modigliani (1919)",
                    link="https://www.metmuseum.org/art/collection/search/489102",
                ),
                rc.Image(
                    "https://images.metmuseum.org/CRDImages/ma/mobile-large/CT_2860.jpg",
                    label="Girl in a Sailor's Blouse - Modigliani (1918)",
                    link="https://www.metmuseum.org/art/collection/search/489102",
                ),
            ),
        )

        # save the report, light, dark, or auto mode (follow browser settings)
        report.save(view, "index.html", mode="light")
