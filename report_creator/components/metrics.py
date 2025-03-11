import logging
import textwrap
from datetime import datetime
from typing import Optional, Union

import dateutil.parser
import humanize
import pandas as pd
import plotly.express as px

from ..utilities import (
    _gfm_markdown_to_html,
    _random_light_color_generator,
    _strip_whitespace,
)
from .base import Base
from .charts import PxBase
from .layout import Group

# Configure logging
logger = logging.getLogger("report_creator")


class Metric(Base):
    """
    Displays a single, key metric with a heading, value, and optional supporting information.

    The `Metric` component is designed to highlight important quantitative or qualitative
    data points within a report. It allows for a concise presentation of key performance
    indicators (KPIs), summary statistics, or any other crucial piece of information.

    Args:
        heading (str): The primary label or title for the metric. This concisely describes
            what the metric represents (e.g., "Total Revenue", "Conversion Rate",
            "Average Order Value").
        value (Union[str, int, float, datetime]): The actual value of the metric. This can be
            a numerical value, a string, or a datetime object.
        unit (Optional[str], optional): An optional unit of measurement for the metric.
            If provided, it will be displayed directly after the value (e.g., "%",
            "USD", "ms", "items"). Defaults to None.
        float_precision (Optional[int], optional): The number of decimal places to display
            for float values. Defaults to 3.
        label (Optional[str], optional): An optional description or additional context for
            the metric. This label can be formatted using Markdown syntax and will be
            displayed below the metric's value. Defaults to None.
        color (Optional[bool], optional): If True, the metric will be displayed with a
            subtle background color. Consecutive metrics with `color=True` will have
            different background colors, aiding in visual distinction. Defaults to False.
    """

    def __init__(
        self,
        heading: str,
        value: Union[str, int, float, datetime],
        *,
        unit: Optional[str] = None,
        float_precision: Optional[int] = 3,
        label: Optional[str] = None,
        color: Optional[bool] = False,
    ):
        super().__init__(label=textwrap.dedent(label) if label else None)
        self.heading = heading
        self.float_precision = float_precision
        self.value = value
        self.unit = unit or ""
        self.color = color

        if isinstance(self.value, (str)):
            self.value = self.value.strip()

        logger.info(f"Metric: {self.heading} {self.value}")

    def __str__(self) -> str:
        return f"Metric {self.heading=} {self.value=} {self.unit=} {self.label=}"

    @_strip_whitespace
    def to_html(self) -> str:
        if isinstance(self.value, (int)):
            value_str = humanize.intword(self.value)
        elif isinstance(self.value, (float)):
            value_str = round(self.value, self.float_precision)
        elif isinstance(self.value, datetime):
            value_str = self.value.strftime("%Y-%m-%d")
        else:
            value_str = str(self.value)

        description = (
            f"<div class='metric-description'>{_gfm_markdown_to_html(self.label)}</div>"
            if self.label
            else ""
        )

        if self.color:
            bk_color, _ = _random_light_color_generator(f"{self.heading}")
            style = f'style="background-color: {bk_color};"'
        else:
            style = ""

        return f"""
            <div class="metric" {style}>
                <p>{self.heading}:</p>
                <h1>{value_str}{self.unit}</h1>
                <p>{description}</p>
            </div>
        """


class MetricGroup(Base):
    """
    A container for displaying multiple metrics in a structured group.

    The `MetricGroup` component is designed to efficiently present
    a collection of metrics derived from a Pandas DataFrame. Each
    row in the DataFrame is transformed into a separate `Metric`
    component, and these `Metric`s are then arranged horizontally
    within a `Group`.
    """

    def __init__(
        self, df: pd.DataFrame, heading: str, value: str, *, label: Optional[str] = None
    ):
        super().__init__(label=label)
        assert heading in df.columns, f"heading {heading} not in df"
        assert value in df.columns, f"value {value} not in df"

        self.g = Group(
            *[Metric(row[heading], row[value]) for _, row in df.iterrows()], label=label
        )

        logger.info(f"MetricGroup: {len(df)} metrics")

    @_strip_whitespace
    def to_html(self) -> str:
        return self.g.to_html()


class EventMetric(Base):
    """
    A specialized metric component for tracking event frequency over time.

    The `EventMetric` component is specifically designed for visualizing
    the occurrence of events that satisfy a given condition within a
    time series. It's particularly useful for telemetry, event tracking,
    or monitoring the frequency of specific occurrences within a dataset.

    The component analyzes a Pandas DataFrame, applies a boolean condition
    to each row, and aggregates the results over a specified time
    frequency (e.g., daily, weekly). The output includes a line chart
    depicting the event frequency over time and the total count of events.

    Args:
        df (pd.DataFrame): The DataFrame containing the event data.
            This DataFrame should include a date-like column and any
            columns necessary to evaluate the `condition`.
        condition (str): A boolean expression to evaluate for each row
            in the DataFrame. This expression should return `True` if
            the event occurred and `False` otherwise (e.g.,
            "status == 200", "error_code != 0").
        date (str): The name of the date-like column in the DataFrame.
            This column will be used to group the data by the specified
            `frequency`.
        frequency (str, optional): The time frequency to group the data
            by. Common options include "D" for daily, "W" for weekly,
            "M" for monthly, etc. Defaults to "D".
        color (str, optional): The color to use for the line chart.
            Defaults to "red".
        heading (Optional[str], optional): An optional heading for the
            metric. If not provided, the `condition` will be used as
            the heading. Defaults to None.
        label (Optional[str], optional): An optional description for
            the metric. This description is displayed below the event
            count. Defaults to None.

    Raises:
        AssertionError: If the specified `date` column is not found in the DataFrame.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        condition: str,
        date: str,
        frequency: str = "D",
        color: str = "red",
        heading: Optional[str] = None,
        *,
        label: Optional[str] = None,
    ):
        super().__init__(label=label)

        assert date in df.columns, f"index column {date} not in df"
        self.df = df
        self.date = date

        self.freq = frequency

        from pandas.api.types import is_datetime64_any_dtype as is_datetime

        if not is_datetime(self.df[date]):
            logger.info(f"EventMetric converting {date} to datetime")
            self.df[date] = self.df[date].apply(dateutil.parser.parse)

        self.condition = condition
        self.color = color
        self.heading = heading or f"{condition}"
        self.yhat = "_Y_"

        logger.info(f"EventMetric: {len(df)} rows, fn: ({condition})")

    @_strip_whitespace
    def to_html(self) -> str:
        # Create a copy of the dataframe to avoid modifying the original
        dfx = self.df.eval(f"{self.yhat} = {self.condition}")[[self.date, self.yhat]].copy()
        dfx[self.yhat] = dfx[self.yhat].astype(int)
        dfx = dfx.groupby(pd.Grouper(key=self.date, freq=self.freq)).sum().reset_index()

        # For an empty dataframe summing a series doesn't return 0
        agg_value = dfx["_Y_"].sum() if not dfx.empty else 0

        fig = px.line(
            dfx,
            x=self.date,
            y=self.yhat,
            line_shape="spline",
            height=135,
            template="simple_white",
        )
        PxBase.apply_common_fig_options(fig)

        # fill area under curve
        fig.update_traces(
            fill="tonexty",
            fillcolor=self.color,
            line_color=self.color,
            hovertemplate=None,
        )
        fig.update_layout(margin={"t": 0, "l": 0, "b": 0, "r": 0})
        fig.update_xaxes(
            visible=True,
            showticklabels=True,
            title=None,
            tickformat="%m/%d",
        )
        fig.update_yaxes(
            visible=True,
            showticklabels=True,
            title=None,
        )

        fig_html = fig.to_html(
            include_plotlyjs=False,
            full_html=False,
            config={"responsive": True, "displayModeBar": False},
        )

        description = (
            f"<div class='metric-description'><p>{self.label}</p></div>" if self.label else ""
        )

        return f"""
            <div class="metric">
                <p>{self.heading}:</p>
                <div><h1>{agg_value:d}</h1></div>
                <div>{fig_html}</div>
                {description}
            </div>
        """
