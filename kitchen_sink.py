import logging
from typing import Dict, List, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from pydataset import data

logging.basicConfig(level=logging.INFO)

from report_creator import (
    Base,
    BigNumber,
    Blocks,
    Collapse,
    DataTable,
    Group,
    Markdown,
    Plot,
    Python,
    ReportCreator,
    Section,
    Text,
    Yaml,
)

if __name__ == "__main__":
    df = pd.DataFrame(columns=["name", "age"])
    df.name = ["John", "Peter", "Sarah"]
    df.age = [33, 18, 22]

    fig = df.plot.bar(x="name", y="age").get_figure()

    with open(__file__, "r") as f:
        example_python = f.read()

    with open("example.yaml", "r") as f:
        yaml_data = f.read()

    with open("example.txt", "r") as f:
        example_text = f.read()

    with open("example.md", "r") as f:
        example_md = f.read()

    report = ReportCreator("My Report")

    view = Blocks(
        Group(
            BigNumber(
                heading="Chances of rain",
                value="84%",
            ),
            BigNumber(heading="Loss", value=0.1),
            BigNumber(
                heading="Accuracy",
                value=95,
                label="Number of correct predictions Total number of predictions",
            ),
        ),
        Text(
            example_text,
            label="Alice in Wonderland",
        ),
        Yaml(
            yaml_data,
            label="Random Yaml",
        ),
        Python(example_python, label="Report Creator Code"),
        Markdown(example_md, label="Example Markdown"),
        Collapse("Example Collapsed Plot", Plot(fig, label="Pies")),
        DataTable(df, label="People", index=False),
        Section(),
        DataTable(data("Journals"), label="Journals", index=False),
    )

    report.save(view, "aa.html")
