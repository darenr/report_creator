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


    with ReportCreator("Kitchen Sink Report") as report:
        view = Block(
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
            )
        )

        report.save(view, "index.html")
