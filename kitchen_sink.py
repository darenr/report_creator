import logging
from typing import Dict, List, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import pydataset
import yaml

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
    df = pd.DataFrame(columns=["name", "age"])
    df.name = ["John", "Peter", "Sarah"]
    df.age = [33, 18, 22]

    fig = df.plot.bar(x="name", y="age").get_figure()

    with open(__file__, "r") as f:
        example_python = f.read()

    with open("example.yaml", "r") as f:
        yaml_data = yaml.safe_load(f.read())

    with open("example.txt", "r") as f:
        example_text = f.read()

    with open("example.md", "r") as f:
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
        Collapse("Example Collapsed Plot", Plot(fig, label="Pies")),
        Select(
            DataTable(pydataset.data("Journals"), label="Journals", index=False),
        ),
        Section(label="Images"),
        Image(
            "https://sufipathoflove.files.wordpress.com/2019/02/prim.jpg",
            label="La Primavera – Botticelli",
        ),
        Group(
            Image(
                "http://placekitten.com/g/400/200",
            ),
            Image(
                "http://placekitten.com/g/300/200",
            ),
            Image(
                "http://placekitten.com/g/500/200",
            ),
        ),
    )

    report.save(view, "aa.html")
