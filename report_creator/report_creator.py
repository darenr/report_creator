# Standard library imports
import base64
import html
import io
import json
import os
import re
import textwrap
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union
from uuid import uuid4

# Third-party imports - organized by category
# Data handling
# Visualization
import humanize
import matplotlib
import matplotlib as mpl
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import plotly.io as pio
import yaml
from cycler import cycler

# Templating & formatting
from jinja2 import Environment, FileSystemLoader

# Loguru for logging
from loguru import logger
from pandas.api.types import is_datetime64_any_dtype as is_datetime

# Internal imports
from .base import Base  # Import Base from base.py
from .charts import PxBase  # Import charts
from .theming import get_rc_theme, preferred_fonts, report_creator_colors
from .utilities import (
    _check_html_tags_are_closed,
    _convert_filepath_to_datauri,
    _convert_imgurl_to_datauri,
    _generate_anchor_id,
    _gfm_markdown_to_html,
    _random_color_generator,
    _random_light_color_generator,
    _strip_whitespace,
    _time_it,
)

# Silence noisy loggers from dependencies
logger.disable("urllib3")  # Often too verbose with connection pool messages
logger.disable("matplotlib")
logger.disable("matplotlib.font_manager")


class Block(Base):
    """
    A container for vertically stacking report components.

    The `Block` component is a fundamental layout tool for structuring reports.
    It arranges its child components vertically, rendering them one after another
    in a single column from top to bottom. This is useful for creating distinct
    sections or stacking elements within a report.

    Each child component is wrapped in `<block-component>` tags, and the entire
    set of components is wrapped in `<block>` tags. These custom tags might be
    used for specific CSS styling or JavaScript interactions if defined in the
    report's template.

    Args:
        *components (Base): A variable number of report components (instances of
            classes derived from `Base`, e.g., `Widget`, `Markdown`, `PlotlyChart`)
            to be stacked vertically within this block.
        label (Optional[str], optional): An optional label for the block. This label
            is inherited from the `Base` class but is not explicitly rendered by the
            `Block` component's `to_html` method itself. It can be used for
            identification or other purposes if accessed directly. Defaults to None.
    """

    def __init__(self, *components: Base, label: Optional[str] = None):
        super().__init__(label=label)
        self.components = components  # Store the child components
        logger.info(
            f"Block component initialized with {len(self.components)} child components. Label: '{label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Block component and all its child components to an HTML string.

        The child components are rendered sequentially and wrapped in
        `<block-component>` tags, which are themselves contained within a
        `<block>` tag.

        Returns:
            str: The HTML representation of the block and its contents.
        """
        # Using a list to join parts is generally more efficient for many concatenations
        html_parts = ["<block>"]

        for component in self.components:
            html_parts.append("<block-component>")
            # Each component is responsible for its own HTML representation
            html_parts.append(component.to_html())
            html_parts.append("</block-component>")

        html_parts.append("</block>")

        return "".join(html_parts)


##############################


class Group(Base):
    """
    A container for horizontally arranging report components.

    The `Group` component arranges multiple report components horizontally,
    side-by-side, effectively creating columns or rows of elements.
    Each child component is wrapped in a `div` with class 'group-content',
    and the entire set of components is wrapped in a `div` with class 'group'.

    If a `label` is provided, it's displayed as a caption above the group,
    HTML-escaped, and linked with an anchor ID generated from the label text.

    Args:
        *components (Base): A variable number of report components (instances of
            classes derived from `Base`) to be arranged horizontally.
        label (Optional[str], optional): An optional label for the group. If provided,
            it is displayed above the components as a caption. The label text will be
            HTML-escaped. Inherits from `Base`. Defaults to None.
    """

    def __init__(self, *components: Base, label: Optional[str] = None):
        super().__init__(label=label)
        self.components = components  # Store the child components
        logger.info(
            f"Group component initialized with {len(self.components)} child components. Label: '{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Group component and its child components to an HTML string.

        Child components are placed within `div` elements with class 'group-content',
        and these are contained within a main `div` with class 'group'.
        An optional, HTML-escaped label is rendered as a caption above the group.

        Returns:
            str: The HTML representation of the group and its contents.
        """
        html_parts = ["<div>"]  # Outer container for label + group

        if self.label:
            # Ensure the label is HTML-escaped before rendering
            escaped_label = html.escape(self.label)
            # Generate anchor ID from the original (unescaped) label for consistency
            anchor_id = _generate_anchor_id(self.label)
            html_parts.append(
                f"<report-caption><a href='#{anchor_id}'>{escaped_label}</a></report-caption>"
            )

        html_parts.append('<div class="group">')  # Start of the group content area

        for component in self.components:
            html_parts.append('<div class="group-content">')
            html_parts.append(component.to_html())  # Each component renders itself
            html_parts.append("</div>")

        html_parts.append("</div>")  # End of group
        html_parts.append("</div>")  # End of outer container

        return "".join(html_parts)


##############################


class Collapse(Base):
    """
    A container for creating collapsible sections in a report.

    The `Collapse` component creates a collapsible section, often called an
    "accordion" or "details/summary" element in HTML. It groups a set of
    report components under a clickable header (defined by the `label`).
    When the header is clicked, the content within the `Collapse` section
    is shown or hidden.

    The `label` is crucial as it forms the visible summary text. This label
    will be HTML-escaped before being rendered in the `<summary>` tag.

    Args:
        *components (Base): A variable number of report components to be placed
                            within the collapsible section.
        label (Optional[str], optional): The text displayed as the clickable header
            (summary) for the collapsible section. This text will be HTML-escaped.
            A `label` is typically required for `Collapse` to be meaningful.
            Inherits from `Base`. Defaults to None, in which case "Details" is used.
    """

    def __init__(self, *components: Base, label: Optional[str] = None):
        super().__init__(label=label)
        self.components = components  # Store child components
        if not label:
            logger.warning(
                "Collapse component initialized without a label. The summary will default to 'Details'."
            )
        logger.info(
            f"Collapse component initialized with {len(self.components)} child components. Label: '{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Collapse component to an HTML string.

        It uses the HTML `<details>` and `<summary>` elements to create
        the collapsible behavior. The `label` (HTML-escaped) is used as the
        summary text. Child components are rendered within the `<details>` tag.

        Returns:
            str: The HTML representation of the collapsible section.
        """
        # HTML-escape the label for safe rendering within <summary>.
        # Provide a default if label is None or empty.
        summary_text = (
            html.escape(self.label) if self.label and self.label.strip() else "Details"
        )

        html_parts = [f'<details class="collapse"><summary>{summary_text}</summary>']

        for component in self.components:
            html_parts.append(component.to_html())  # Components render themselves

        html_parts.append("</details>")
        return "".join(html_parts)


##############################


class Widget(Base):
    """
    A container for embedding and rendering external content or interactive widgets.

    The `Widget` component serves as a versatile container for displaying various
    Python objects that can render themselves as HTML. This is particularly useful
    for embedding common data science outputs like Pandas DataFrames, Matplotlib
    figures, and Plotly figures directly into the report.

    The component intelligently attempts to find the best HTML representation:
    - For Plotly `go.Figure` objects, common styling options are applied.
    - For objects with a `get_figure()` method (common in libraries like Seaborn),
    that method is called to retrieve the figure.
    - For Pandas DataFrames, `style._repr_html_()` is used.
    - For Matplotlib figures, they are saved as PNG images, base64-encoded,
    and embedded in an `<img>` tag with styling for responsiveness.
    - For other objects, it checks for a `_repr_html_()` method.
    - As a fallback, it uses the object's standard `__repr__` or `__str__`
    representation wrapped in `<pre>` tags after HTML escaping.

    An optional `label` (HTML-escaped) can be displayed as a caption above the widget.

    Args:
        widget (Any): The Python object to be embedded. Supported types include:
            - Plotly `go.Figure`
            - Objects with a `get_figure()` method (e.g., some Seaborn plot objects)
            - Pandas `DataFrame`
            - Matplotlib `figure.Figure`
            - Any object with a `_repr_html_()` method
            - Any object with `__repr__` or `__str__` methods (as a fallback)
        label (Optional[str], optional): An optional label or caption for the widget.
            If provided, it will be HTML-escaped and displayed above the widget,
            linked with an anchor ID. Inherits from `Base`. Defaults to None.
    """

    def __init__(self, widget: Any, *, label: Optional[str] = None):
        super().__init__(label=label)

        # Pre-process certain widget types
        processed_widget = widget
        if isinstance(widget, go.Figure):
            PxBase.apply_common_fig_options(processed_widget)  # Apply consistent styling
        elif hasattr(widget, "get_figure") and callable(widget.get_figure):
            # For objects like Seaborn's FacetGrid or JointGrid
            try:
                fig = widget.get_figure()
                if isinstance(fig, matplotlib.figure.Figure):
                    processed_widget = fig
                else:
                    logger.warning(
                        f"get_figure() on {type(widget)} did not return a Matplotlib Figure. Using original widget."
                    )
            except Exception as e:
                logger.warning(
                    f"Error calling get_figure() on {type(widget)}: {e}. Using original widget."
                )

        self.widget = processed_widget
        logger.info(
            f"Widget component initialized with widget of type: {type(self.widget)}. Label: '{self.label}'"
        )

    def _render_widget_to_html(self) -> str:
        """Determines the best HTML representation for the widget."""
        if isinstance(self.widget, pd.DataFrame):
            # Use Pandas' built-in HTML styling, ensuring cell content is escaped
            return self.widget.style.format(escape="html").to_html()
        elif isinstance(self.widget, matplotlib.figure.Figure):
            # Convert Matplotlib figure to an embedded base64 PNG image
            img_buffer = io.BytesIO()
            # Configure figure properties for better appearance in reports
            self.widget.set_dpi(150)  # Standard DPI for web display
            # Consider making figwidth/figheight configurable if needed
            # self.widget.set_figwidth(10)
            self.widget.tight_layout()  # Adjust layout to prevent overlapping elements
            self.widget.savefig(img_buffer, format="png", bbox_inches="tight")
            img_buffer.seek(0)
            b64_image = (
                base64.b64encode(img_buffer.getvalue()).decode("utf-8").replace("\n", "")
            )
            alt_text = html.escape(self.label or "Matplotlib Figure")
            # Style for responsiveness: max-width ensures it scales down, height:auto maintains aspect ratio.
            return f'<img src="data:image/png;base64,{b64_image}" alt="{alt_text}" style="max-width:100%; height:auto; border: 1px solid #ddd;">'
        elif hasattr(self.widget, "_repr_html_"):
            # Use the object's own HTML representation method if available
            return self.widget._repr_html_()
        elif hasattr(self.widget, "__repr__") or hasattr(self.widget, "__str__"):
            # Fallback: convert the object to string, HTML-escape it, and wrap in <pre> for preformatted text
            return f"<pre>{html.escape(str(self.widget))}</pre>"
        else:
            logger.warning(
                f"Widget of type {type(self.widget)} has no known HTML representation."
            )
            return "<p><i>Widget content could not be rendered.</i></p>"

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Widget component to an HTML string.

        It includes an optional HTML-escaped label (caption) and the HTML
        representation of the embedded widget.

        Returns:
            str: The HTML representation of the widget.
        """
        html_parts = ["<div class='report-widget'>"]

        if self.label:
            escaped_label = html.escape(self.label)
            anchor_id = _generate_anchor_id(self.label)  # Use original label for ID
            html_parts.append(
                f"<report-caption><a href='#{anchor_id}'>{escaped_label}</a></report-caption>"
            )

        html_parts.append(self._render_widget_to_html())
        html_parts.append("</div>")
        return "".join(html_parts)


##############################


class MetricGroup(Base):
    """
    A container for displaying multiple metrics in a structured group.

    The `MetricGroup` component facilitates the display of multiple `Metric`
    instances derived from the rows of a Pandas DataFrame. It effectively
    creates a `Metric` for each row, using specified DataFrame columns for the
    metric's `heading` and `value`. These `Metric` components are then
    arranged horizontally by an internally managed `Group` component.

    This component is a convenient way to present a collection of related
    key performance indicators (KPIs) or summary statistics side-by-side.

    Args:
        df (pd.DataFrame): The DataFrame containing the data for the metrics.
            Each row will typically result in one `Metric` component.
        heading (str): The name of the column in `df` whose values will be used
            as the `heading` for each generated `Metric` component.
        value (str): The name of the column in `df` whose values will be used
            as the `value` for each generated `Metric` component.
        label (Optional[str], optional): An optional label for the entire metric group.
            This label is passed to the internal `Group` component, which will
            render it as an HTML-escaped caption above the group of metrics.
            Inherits from `Base`. Defaults to None.

    Raises:
        ValueError: If the specified `heading` or `value` columns are not
            found in the input `df`, or if `df` is not a Pandas DataFrame.
    """

    def __init__(
        self, df: pd.DataFrame, heading: str, value: str, *, label: Optional[str] = None
    ):
        super().__init__(label=label)  # The label is primarily for the Group

        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input 'df' must be a Pandas DataFrame.")
        if heading not in df.columns:
            raise ValueError(
                f"Heading column '{heading}' not found in DataFrame columns: {df.columns.tolist()}"
            )
        if value not in df.columns:
            raise ValueError(
                f"Value column '{value}' not found in DataFrame columns: {df.columns.tolist()}"
            )

        # Create a list of Metric components from the DataFrame rows
        metrics = [
            Metric(heading=str(row[heading]), value=row[value]) for _, row in df.iterrows()
        ]

        # Use an internal Group component to arrange these metrics.
        # The label provided to MetricGroup is passed to this Group.
        self.group_component = Group(*metrics, label=self.label)

        logger.info(
            f"MetricGroup component generated {len(metrics)} metrics. Label for the group: '{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the MetricGroup to HTML by delegating to its internal `Group` component.

        Returns:
            str: The HTML representation of the grouped metrics.
        """
        return self.group_component.to_html()


##############################


class EventMetric(Base):
    """
    A specialized metric component for tracking event frequency over time.

    The `EventMetric` component is designed for visualizing the occurrence of
    events that satisfy a given condition within a time series. It's useful for
    telemetry, event tracking, or monitoring specific occurrences.

    It analyzes a Pandas DataFrame, applies a boolean condition to each row, and
    aggregates results over a specified time frequency (e.g., daily, weekly).
    The output includes a compact line chart (event frequency over time) and
    the total event count.

    Args:
        df (pd.DataFrame): DataFrame with event data. Must include a date-like
            column and columns for evaluating the `condition`.
        condition (str): A boolean expression string (e.g., `"status == 200"`,
            `"error_code != 0"`) evaluated for each row. Rows where the
            condition is True are counted as events.
        date (str): Name of the date-like column in `df`. This column is used
            for time-based grouping and will be parsed into datetime objects.
        frequency (str, optional): Time frequency for grouping (Pandas offset alias,
            e.g., "D" for daily, "W" for weekly). Defaults to "D".
        color (str, optional): Color for the line chart fill and line (CSS color string).
            Defaults to "red".
        heading (Optional[str], optional): Heading for the metric. If None, the
            `condition` string is used. Defaults to None.
        label (Optional[str], optional): Description for the metric, displayed below
            the event count. Inherits from `Base`. Defaults to None.

    Raises:
        ValueError: If `date` column is not in `df`, or if its values cannot be
            parsed as dates.
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

        if date not in df.columns:
            raise ValueError(f"Date column '{date}' not found in DataFrame.")

        self.df = df.copy()  # Work on a copy
        self.date_col_name = date
        self.frequency = frequency

        # Ensure the date column is in datetime format

        if not is_datetime(self.df[self.date_col_name]):
            logger.info(
                f"EventMetric attempting to convert column '{self.date_col_name}' to datetime."
            )
            try:
                self.df[self.date_col_name] = pd.to_datetime(self.df[self.date_col_name])
            except Exception as e:
                logger.error(f"Error converting column '{self.date_col_name}' to datetime: {e}")
                raise ValueError(
                    f"Could not parse dates in column '{self.date_col_name}'. "
                    "Ensure it contains valid date representations."
                ) from e

        self.condition = condition
        self.color = color
        self.heading = heading if heading is not None else self.condition
        # Internal column name for the result of the condition evaluation (0 or 1)
        self.y_col_name = f"_Y_EVENT_METRIC_{uuid4().hex[:8]}"  # Unique internal name

        logger.info(
            f"EventMetric initialized: {len(self.df)} rows, "
            f"condition: '{self.condition}', date column: '{self.date_col_name}', "
            f"frequency: '{self.frequency}'."
        )

    def _prepare_data(self) -> tuple[pd.DataFrame, int]:
        """
        Prepares data for plotting and calculates the aggregate event count.
        Evaluates the condition, groups by frequency, and sums events.

        Returns:
            tuple[pd.DataFrame, int]: (grouped_df, total_event_count)
        """
        # Evaluate the condition to create the target column (1 if true, 0 if false)
        try:
            self.df[self.y_col_name] = self.df.eval(self.condition).astype(int)
        except Exception as e:
            logger.error(f"Error evaluating condition '{self.condition}': {e}")
            raise ValueError(
                f"Failed to evaluate condition: {self.condition}. Error: {e}"
            ) from e

        # Group by the specified frequency and sum the event indicator column
        df_grouped = (
            self.df[[self.date_col_name, self.y_col_name]]
            .groupby(pd.Grouper(key=self.date_col_name, freq=self.frequency))
            .sum()
            .reset_index()
        )

        agg_value = int(df_grouped[self.y_col_name].sum(skipna=True))
        return df_grouped, agg_value

    def _create_figure(self, df_plot: pd.DataFrame) -> go.Figure:
        """
        Creates and configures the Plotly line chart for the event metric.

        Args:
            df_plot (pd.DataFrame): Data prepared by `_prepare_data`.

        Returns:
            go.Figure: The configured Plotly figure object.
        """
        fig = px.line(
            df_plot,
            x=self.date_col_name,
            y=self.y_col_name,
            line_shape="spline",
            height=135,  # Compact height
            template="simple_white",
        )
        PxBase.apply_common_fig_options(fig)

        fig.update_traces(
            fill="tonexty",
            fillcolor=self.color,
            line_color=self.color,
            hovertemplate=None,  # Use Plotly's default hover
        )
        fig.update_layout(margin={"t": 0, "l": 0, "b": 0, "r": 0})
        fig.update_xaxes(visible=True, showticklabels=True, title=None, tickformat="%m/%d")
        fig.update_yaxes(visible=True, showticklabels=True, title=None)
        return fig

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Generates the HTML representation of the EventMetric.

        Returns:
            str: The HTML string for the EventMetric component.
        """
        try:
            df_plot, agg_value = self._prepare_data()
            fig = self._create_figure(df_plot)
            fig_html = fig.to_html(
                include_plotlyjs=False,
                full_html=False,
                config={"responsive": True, "displayModeBar": False},
            )
        except Exception as e:
            logger.error(f"Failed to generate EventMetric plot: {e}\n{traceback.format_exc()}")
            fig_html = "<p><i>Error generating event metric chart.</i></p>"
            agg_value = "Error"

        description_html = (
            f"<div class='metric-description'><p>{html.escape(self.label)}</p></div>"
            if self.label
            else ""
        )

        return f"""
            <div class="metric">
                <p>{html.escape(self.heading)}:</p>
                <div><h1>{agg_value}</h1></div>
                <div>{fig_html}</div>
                {description_html}
            </div>
        """


##############################


class Metric(Base):
    """
    Displays a single, key metric with a heading, value, and optional supporting information.

    The `Metric` component is designed to highlight important quantitative or qualitative
    data points within a report. It allows for a concise presentation of key performance
    indicators (KPIs), summary statistics, or any other crucial piece of information.

    Args:
        heading (str): The primary label or title for the metric. This concisely describes
            what the metric represents (e.g., "Total Revenue", "Conversion Rate").
            The `heading` is also used as a seed for the random background color
            if `color` is set to True.
        value (Union[str, int, float, datetime]): The actual value of the metric.
            - `int` values may be humanized (e.g., 1,000,000 becomes "1.0 Million").
            - `datetime` objects are formatted as "YYYY-MM-DD".
            - `str` values are displayed as is (after stripping whitespace).
        unit (Optional[str], optional): An optional unit of measurement for the metric,
            displayed directly after the value (e.g., "%", "USD", "ms"). Defaults to an empty string.
        float_precision (Optional[int], optional): The number of decimal places to display
            for float values when humanization is not applied or does not significantly
            alter the number. Defaults to 3.
        label (Optional[str], optional): An optional description or additional context
            for the metric, displayed below the value. Supports GitHub Flavored Markdown.
            Inherits from `Base`. Defaults to None.
        color (Optional[bool], optional): If True, the metric will be rendered with a
            subtly colored background. The background color is deterministically generated
            based on the `heading` string, ensuring that the same heading will consistently
            produce the same background color. This helps in visually distinguishing
            metrics. Defaults to False, resulting in a standard background.
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
        self.heading = str(heading)  # Ensure heading is a string
        self.float_precision = (
            float_precision or 3
        )  # Default to 3 decimal places if not specified
        self.value = value
        self.unit = unit or ""  # Ensure unit is a string, defaults to empty
        self.color = color

        if isinstance(self.value, str):
            self.value = self.value.strip()

        logger.info(
            f"Metric component: heading='{self.heading}', value='{self.value}', label='{self.label}', unit='{self.unit}', color={self.color}', float_precision={self.float_precision}"
        )

    def __str__(self) -> str:
        return f"Metric component: heading='{self.heading}', value='{self.value}', label='{self.label}', unit='{self.unit}', color={self.color}', float_precision={self.float_precision}"

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Metric component to an HTML string.
        Formats the value based on its type (int, float, datetime, str) and applies
        humanization or precision formatting. An optional label is rendered as Markdown.
        If `color` is True, a deterministic background color based on the heading is applied.

        Returns:
            str: The HTML representation of the metric.
        """
        value_str: str
        if isinstance(self.value, int):
            value_str = humanize.intword(self.value) if self.value > 1000 else str(self.value)
        elif isinstance(self.value, float):
            value_str = f"{self.value:.{self.float_precision}f}".rstrip("0").rstrip(".")
        elif isinstance(self.value, datetime):
            value_str = self.value.strftime("%Y-%m-%d")
        else:
            value_str = html.escape(str(self.value))  # Escape string values

        description_html = (
            f"<div class='metric-description'>{_gfm_markdown_to_html(self.label)}</div>"
            if self.label
            else ""
        )

        style_attribute = ""
        if self.color:
            bk_color, text_color = _random_light_color_generator(self.heading)
            style_attribute = f'style="background-color: {bk_color}; color: {text_color};"'

        escaped_heading = html.escape(self.heading)

        return f"""
            <div class="metric" {style_attribute}>
                <p>{escaped_heading}:</p>
                <h1>{value_str}{html.escape(self.unit)}</h1>
                {description_html}
            </div>
        """


##############################


class Table(Widget):
    """
    Displays a Pandas DataFrame or a list of dictionaries as a formatted HTML table.

    The `Table` component displays a Pandas DataFrame or a list of dictionaries
    as a static HTML table. It leverages Pandas' Styler API for formatting.
    This component is a subclass of `Widget`, using the Styler object as its widget.

    Content within the table cells is HTML-escaped by default by the
    Pandas Styler's `to_html()` method (which is invoked via `format(escape="html")`).

    Args:
        data (Union[pd.DataFrame, list[dict]]): The data for the table.
            Can be a Pandas DataFrame or a list of dictionaries (where each
            dictionary represents a row and keys are column names).
        label (Optional[str], optional): An optional label or caption for the table,
            HTML-escaped and displayed above it by the parent Widget's rendering logic.
            Inherits from `Widget` and `Base`. Defaults to None.
        index (bool, optional): If True, the DataFrame's index will be displayed
            in the table. If False (default), the index is hidden.
        float_precision (int, optional): The number of decimal places for
            floating-point numbers in the table. Defaults to 2.

    Raises:
        ValueError: If `data` is not a Pandas DataFrame or a list of dictionaries.
    """

    def __init__(
        self,
        data: Union[pd.DataFrame, list[dict]],
        *,
        label: Optional[str] = None,
        index: Optional[bool] = False,  # Default to False for cleaner tables
        float_precision: Optional[int] = 2,
    ):
        if isinstance(data, list):
            try:
                df = pd.DataFrame(data)
            except Exception as e:
                raise ValueError(
                    f"Could not convert list of dictionaries to DataFrame: {e}"
                ) from e
        elif isinstance(data, pd.DataFrame):
            df = data.copy()  # Use a copy to avoid modifying the original DataFrame
        else:
            raise ValueError(
                f"Expected data to be a list of dictionaries or pd.DataFrame, got {type(data).__name__}"
            )

        # Apply Pandas Styler for formatting
        styler = df.style
        if not index:
            styler = styler.hide(axis="index")  # Hide index if requested

        # Format with specified precision and ensure HTML escaping for cell content.
        # The 'escape="html"' argument to Styler.format handles escaping cell content.
        # If the Styler object itself needs to be passed to Widget, this formatting might
        # happen there, or Widget needs to be aware it's a Styler object.
        # For now, assuming Widget can handle a Styler object or we pass HTML directly.
        # If Widget expects raw HTML, then formatted_styler.to_html() would be passed.
        # Based on Widget's _render_widget_to_html, it expects the Styler object.
        formatted_styler = styler.format(precision=float_precision, escape="html")

        logger.info(
            f"Table component initialized with {len(df)} rows, {len(df.columns)} columns. "
            f"Label: '{label}', Index shown: {index}, Float precision: {float_precision}"
        )

        # Initialize the parent Widget class with the formatted Styler object
        # The label will be handled by the Widget's to_html method (including escaping).
        super().__init__(widget=formatted_styler, label=label)


##############################


class DataTable(Base):
    """
    Displays a sortable and searchable table from a Pandas DataFrame or a list of dictionaries.

    The `DataTable` component displays tabular data (from Pandas DataFrames or
    lists of dictionaries) as an interactive HTML table. This table includes
    features like client-side searching, sorting by columns, and pagination,
    powered by the DataTables JavaScript library.

    The component uses Pandas' Styler API to format the table structure and data
    before embedding it. Cell content is HTML-escaped by default.

    Args:
        data (Union[pd.DataFrame, list[dict]]): The data for the table. Can be a
            Pandas DataFrame or a list of dictionaries (each dict is a row).
        label (Optional[str], optional): An optional caption for the table. If provided,
            it's set as the table's caption using Pandas Styler and will be
            HTML-escaped by the Styler. Inherits from `Base`. Defaults to None.
        wrap_text (bool, optional): If True (default), text within table cells can wrap.
            If False, a 'nowrap' class is added, which typically prevents wrapping
            (CSS dependent).
        index (bool, optional): If True, the DataFrame's index is included as a column.
            If False (default), the index is hidden.
        max_rows (int, optional): Maximum number of rows from the DataFrame to display.
            If -1 (default), all rows are included. This affects the data passed to
            DataTables, not just initial display.
        float_precision (int, optional): Number of decimal places for float values.
            Defaults to 2.

    Raises:
        ValueError: If `data` is not a Pandas DataFrame or list of dictionaries.
    """

    def __init__(
        self,
        data: Union[pd.DataFrame, list[dict]],
        *,
        label: Optional[str] = None,  # Label for table caption
        wrap_text: bool = True,
        index: Optional[bool] = False,  # Default to False
        max_rows: Optional[int] = -1,  # Default to all rows
        float_precision: Optional[int] = 2,
    ):
        # The 'label' for Base is used here as the table's caption.
        # Styler handles HTML escaping for the caption if 'label' is passed to it.
        super().__init__(label=label)

        if isinstance(data, list):
            try:
                df = pd.DataFrame(data)
            except Exception as e:
                raise ValueError(
                    f"Could not convert list of dictionaries to DataFrame: {e}"
                ) from e
        elif isinstance(data, pd.DataFrame):
            df = data.copy()  # Use a copy
        else:
            raise ValueError(
                f"Expected data to be a list of dictionaries or pd.DataFrame, got {type(data).__name__}"
            )

        # Apply row limit if specified
        processed_df = df.head(max_rows) if max_rows > 0 else df
        styler = processed_df.style

        if self.label:  # Use the label passed to __init__ (and stored in Base)
            # Pandas Styler's set_caption should handle HTML escaping of the caption text.
            styler = styler.set_caption(self.label)

        table_classes = ["fancy-table", "display", "row-border", "hover", "responsive"]
        if not wrap_text:
            table_classes.append("nowrap")

        if not index:
            styler = styler.hide(axis="index")

        # Set table attributes for DataTables styling and functionality
        styler = styler.set_table_attributes(
            f'class="{" ".join(table_classes)} cellspacing="0" style="width: 100%;"'
        )

        # Format the Styler object to HTML, ensuring cell content is escaped.
        # The 'escape="html"' argument to format() handles this.
        self.table_html = styler.format(precision=float_precision, escape="html").to_html()

        logger.info(
            f"DataTable component initialized: {len(processed_df)} rows, {len(processed_df.columns)} columns. "
            f"Label: '{self.label}', Index: {index}, Wrap: {wrap_text}, Max Rows: {max_rows}"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the DataTable to an HTML string.

        The table HTML generated by Pandas Styler is wrapped in a `div` with class
        'dataTables-wrapper include_datatable'. The 'include_datatable' class
        signals the JavaScript in the main template to initialize DataTables on this table.
        A `<br/>` is added before the table for spacing.

        Returns:
            str: The HTML representation of the interactive DataTable.
        """
        # self.table_html is already generated and formatted in __init__
        return f'<div class="dataTables-wrapper include_datatable"><br/>{self.table_html}</div>'


##############################


class Html(Base):
    """
    Embeds raw HTML content, optionally with inline CSS styling, into the report.

    The `Html` component provides a way to include arbitrary HTML markup directly
    within a report. This is useful for embedding custom web elements, adding
    specialized formatting, or integrating content from external sources that
    provide HTML snippets.

    Args:
        html (str): The raw HTML content to be embedded. This can include any
            valid HTML tags and content.
            **Important:** The provided HTML is validated to ensure all tags are properly
            closed using an internal utility (`_check_html_tags_are_closed`). If unclosed
            tags are detected, a `ValueError` will be raised to prevent malformed
            report layouts. Content should be properly escaped if generated from untrusted
            sources to prevent XSS vulnerabilities, as it is rendered directly.
        css (Optional[str], optional): Optional inline CSS styles to be applied specifically
            to this HTML content. These styles will be wrapped in `<style>` tags if provided.
            Defaults to None.
        label (Optional[str], optional): An optional label for the HTML component, displayed
            above the content if provided. Inherits from `Base`. If a label is provided,
            it will be HTML-escaped before rendering. Defaults to None.
        bordered (Optional[bool], optional): If True, the HTML content will be rendered
            within a container styled with a border. Defaults to False.

    Raises:
        ValueError: If the provided `html` string contains unclosed HTML tags.
    """

    def __init__(
        self,
        html: str,
        *,
        css: Optional[str] = None,
        label: Optional[str] = None,
        bordered: Optional[bool] = False,
    ):
        super().__init__(label=label)
        self.html_str = str(html)  # Ensure it's a string
        self.css = css
        self.bordered = bordered
        status, errors = _check_html_tags_are_closed(self.html_str)
        if not status:
            # Raise ValueError for invalid HTML structure
            error_message = f"HTML component (label: '{self.label}') contains unclosed tags: {', '.join(errors)}"
            logger.error(error_message)
            raise ValueError(error_message)
        logger.info(f"Html component: {len(self.html_str)} HTML characters, label='{label}'")

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Html component to an HTML string.
        Includes the raw HTML, optional CSS, and an optional HTML-escaped label.
        A border class is applied if `bordered` is True.

        Returns:
            str: The HTML string for the component.
        """
        border_class = "round-bordered" if self.bordered else ""

        html_output_parts = []

        if self.css:
            # CSS is typically not HTML-escaped when placed in <style> tags.
            # However, ensure no malicious content if CSS comes from untrusted source.
            # For now, assuming CSS is safe.
            html_output_parts.append(f"<style>{self.css}</style>")

        if self.label:
            escaped_label = html.escape(self.label)
            anchor_id = _generate_anchor_id(self.label)  # Use original label for ID
            html_output_parts.append(
                f"<report-caption><a href='#{anchor_id}'>{escaped_label}</a></report-caption>"
            )

        # self.html_str is already validated for closed tags in __init__.
        # It is rendered as-is.
        html_output_parts.append(f'<div class="{border_class}">{self.html_str}</div>')

        return "".join(html_output_parts)


##############################


class Diagram(Base):
    """
    Renders a diagram using Mermaid.js syntax within the report.

    The `Diagram` component allows you to create and embed diagrams
    directly within your report using the Mermaid.js library. Mermaid
    allows you to define diagrams using a simple text-based syntax,
    which is then rendered visually by the library.

    This component enables embedding various diagrams (flowcharts, sequence diagrams,
    Gantt charts, etc.) using Mermaid.js syntax. The Mermaid source code is
    rendered by the Mermaid.js library in the browser.

    Refer to the Mermaid.js documentation (https://mermaid.js.org/syntax/examples.html)
    for syntax examples. AI tools like ChatGPT can also help generate Mermaid syntax.

    The `src` (Mermaid code) is not HTML-escaped by this component as it's processed
    by JavaScript. Ensure the `src` is from a trusted source or properly sanitized if
    dynamically generated from user input outside of typical Mermaid syntax.

    Args:
        src (str): The Mermaid.js source code string defining the diagram.
            This string is placed directly within `<pre class='mermaid'>` tags.
        pan_and_zoom (Optional[bool], optional): If True (default), enables panning
            (mouse drag) and zooming (Shift + mouse wheel) for the rendered diagram,
            if supported by the 'mermaid-pan-zoom' class and associated JavaScript.
        extra_css (Optional[str], optional): Additional inline CSS styles to be applied
            to the `<pre>` element containing the Mermaid source. Be cautious with
            user-provided CSS. Defaults to an empty string.
        label (Optional[str], optional): An optional label or caption for the diagram,
            HTML-escaped and displayed above it within a `<figcaption>`.
            Inherits from `Base`. Defaults to None.
    """

    def __init__(
        self,
        src: str,
        *,
        pan_and_zoom: Optional[bool] = True,
        extra_css: Optional[str] = None,
        label: Optional[str] = None,
    ):
        super().__init__(label=label)

        self.src = src  # Mermaid source code
        self.extra_css = extra_css or ""  # Ensure it's a string
        self.pan_and_zoom = pan_and_zoom
        logger.info(
            f"Diagram component initialized with {len(self.src)} characters of Mermaid source. "
            f"Label: '{self.label}', Pan & Zoom: {self.pan_and_zoom}"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Diagram component to an HTML string.

        The Mermaid source (`src`) is embedded in a `<pre>` tag with class 'mermaid'.
        An optional, HTML-escaped label is rendered as a caption.
        Pan and zoom functionality is enabled by adding the 'mermaid-pan-zoom' class
        and associated UI elements if `pan_and_zoom` is True.

        Returns:
            str: The HTML representation of the diagram placeholder.
        """
        html_parts = ['<div class="diagram-block"><figure>']

        if self.label:
            escaped_label = html.escape(self.label)
            anchor_id = _generate_anchor_id(self.label)  # Use original label for ID
            html_parts.append(
                f"<figcaption><report-caption><a href='#{anchor_id}'>{escaped_label}</a></report-caption></figcaption>"
            )

        # Add 'include_mermaid' class to signal JS to process this.
        # Add 'mermaid-pan-zoom' class if pan_and_zoom is enabled.
        mermaid_classes = "mermaid include_mermaid"
        if self.pan_and_zoom:
            mermaid_classes += " mermaid-pan-zoom"

        # extra_css should be used carefully; ensure it's safe if from user input.
        # self.src is not escaped here as Mermaid.js processes it.
        # Strip leading/trailing whitespace from src for cleaner rendering in <pre>
        html_parts.append(
            f'<pre class="{mermaid_classes}" style="{html.escape(self.extra_css, quote=True)}">{self.src.strip()}</pre>'
        )

        if self.pan_and_zoom:
            html_parts.append(
                "<small>pan (mouse drag) and zoom (shift + mouse wheel)"
                '&nbsp;<a href="#" onclick="event.preventDefault();" class="panzoom-reset">(reset)</a>'
                "</small>"
            )

        html_parts.append("</figure></div>")
        return "".join(html_parts)


##############################


class Image(Base):
    """
    Embeds an image within the report, optionally linking it to an external URL.

    The `Image` component allows you to include images in your report,
    either by referencing an external URL or by embedding a base64-encoded
    image directly within the HTML. You can also make the image clickable,
    linking it to another webpage.

    Args:
        src (str): The source of the image. The component handles `src` as follows:
            - **Base64 Data URI:** If `src` starts with "data:image", it's used directly.
            - **Local File Path:** If `src` is a valid local file path (checked using `os.path.exists`),
            the image is read, converted to a base64 data URI, and embedded.
            - **URL (Remote Image):** If `src` is a URL (e.g., "http://", "https://"):
            if `convert_to_base64` is `True`, the image is downloaded, converted to base64, and embedded.
            if `convert_to_base64` is `False` (default), the `src` URL is used directly.
            The `alt` attribute for the image is generated from the `label` if provided,
            otherwise from the `src` (first 50 chars if long).
        link_to (Optional[str], optional): An optional URL. If provided, the image will be
            wrapped in an anchor (`<a>`) tag, making it a clickable link that opens
            the URL in a new tab (`target="_blank"`). Defaults to None.
        label (Optional[str], optional): An optional label or caption for the image,
            displayed below it within a `<figcaption>`. If provided, it will be
            HTML-escaped. This label is also used as the `alt` text for the image.
            Inherits from `Base`. Defaults to None.
        extra_css (Optional[str], optional): Additional inline CSS styles to be applied
            directly to the `<img>` element (e.g., "width: 100px; height: auto;").
            Defaults to an empty string.
        rounded (bool, optional): If True (default), applies CSS for rounded corners.
        convert_to_base64 (bool, optional): If `True` and `src` is a URL, the image is
            fetched, converted to base64, and embedded. Defaults to False.
            Has no effect if `src` is already a data URI or a local file path.
    Raises:
            ValueError: If the `src` is not a valid image source or if conversion fails.
            The component logs errors and falls back to using the original `src` if conversion fails.
            This allows the browser to attempt rendering the image if it's a valid URL.

    """

    def __init__(
        self,
        src: str,
        *,
        link_to: Optional[str] = None,
        label: Optional[str] = None,
        extra_css: Optional[str] = None,
        rounded: Optional[bool] = True,
        convert_to_base64: Optional[bool] = False,
    ):
        super().__init__(label=label)
        self.original_src = src  # Keep original src for alt text or logging
        self.link_to = link_to
        self.extra_css = extra_css or ""
        self.rounded_css = "border-radius: 0.75rem;" if rounded else ""

        processed_src = src
        try:
            if src.startswith("data:image"):
                # Already a Base64 image
                pass
            elif os.path.exists(src):
                # Local file, always convert to base64
                processed_src = _convert_filepath_to_datauri(src)
            elif src.startswith(("http://", "https://")) and convert_to_base64:
                # URL to be fetched and converted to base64
                processed_src = _convert_imgurl_to_datauri(src)
            # If it's a URL and convert_to_base64 is False, src remains as is.
        except ValueError as e:  # Catch errors from conversion utilities
            logger.error(
                f"Error processing image source '{src}': {e}. Will use original src if possible."
            )
            # Fallback to using original src if conversion failed, browser might still render it if it's a valid URL
            processed_src = src

        self.src = processed_src
        logger.info(
            f"Image component: processed_src='{self.src[:70]}...', label='{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Image component to an HTML string.
        Includes the image (either linked or embedded), an optional link,
        and an optional HTML-escaped caption.

        Returns:
            str: The HTML representation of the image component.
        """
        html_output_parts = ['<div class="image-block"><figure>']

        # Determine alt text: use label if available, otherwise use the original src.
        # Escape alt text for safety.
        alt_text_source = self.label if self.label else self.original_src
        alt_text = html.escape(
            alt_text_source[:100] if alt_text_source else "Image"
        )  # Limit alt text length

        # Ensure self.src (image source) and self.extra_css are properly escaped for HTML attributes
        escaped_img_src = html.escape(self.src, quote=True)
        escaped_extra_css = html.escape(self.extra_css.strip(), quote=True)

        image_style = f"{self.rounded_css} {escaped_extra_css}".strip()
        image_markup = f'<img src="{escaped_img_src}" style="{image_style}" alt="{alt_text}">'

        if self.link_to:
            escaped_link_to = html.escape(self.link_to, quote=True)
            html_output_parts.append(
                f'<a href="{escaped_link_to}" target="_blank">{image_markup}</a>'
            )
        else:
            html_output_parts.append(image_markup)

        if self.label:
            escaped_label_for_caption = html.escape(self.label)
            anchor_id = _generate_anchor_id(self.label)  # Use original label for ID
            html_output_parts.append(
                f"<figcaption><report-caption><a href='#{anchor_id}'>{escaped_label_for_caption}</a></report-caption></figcaption>"
            )

        html_output_parts.append("</figure></div>")
        return "".join(html_output_parts)


##############################


class Markdown(Base):
    """
    Embeds Markdown-formatted text within the report, with optional styling and borders.

    The `Markdown` component allows you to include rich text content in your report
    using Markdown syntax. It supports Github Falvored Markdown formatting and provides
    options for adding custom CSS styles and borders.

    Args:
        text (str): The Markdown-formatted text to be rendered. This string will be
            processed by `textwrap.dedent` to remove common leading whitespace,
            then converted from GitHub Flavored Markdown to HTML using an internal utility
            (`_gfm_markdown_to_html`). The resulting HTML is then rendered.
            Code blocks within the Markdown can be syntax highlighted if Highlight.js
            is active (signaled by `include_hljs` class).
        label (Optional[str], optional): An optional label or heading for the Markdown section.
            If provided, it's HTML-escaped and displayed above the content, linked
            with an anchor ID. Inherits from `Base`. Defaults to None.
        extra_css (Optional[str], optional): Additional inline CSS styles to be applied
            to the inner `div` that wraps the Markdown content. Be cautious with
            user-provided CSS. Defaults to an empty string.
        bordered (bool, optional): If True, the Markdown content will be rendered
            within a container that has a 'round-bordered' class, typically applying
            a border and rounded corners via CSS. Defaults to False.
    """

    def __init__(
        self,
        text: str,
        *,
        label: Optional[str] = None,
        extra_css: Optional[str] = None,
        bordered: Optional[bool] = False,
    ):
        super().__init__(label=label)
        # Dedent the input text to handle common indentation in triple-quoted strings
        self.text = textwrap.dedent(str(text))  # Ensure text is string
        self.extra_css = extra_css or ""  # Ensure it's a string
        self.bordered = bordered

        logger.info(
            f"Markdown component initialized with {len(self.text)} characters of Markdown text. "
            f"Label: '{self.label}', Bordered: {self.bordered}"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Markdown component to an HTML string.

        The Markdown text is converted to HTML. An optional, HTML-escaped label
        is rendered as a caption. The content is wrapped in `div` elements
        with appropriate classes for styling and JavaScript hooks (e.g., `include_hljs`).

        Returns:
            str: The HTML representation of the rendered Markdown content.
        """
        border_class = "round-bordered" if self.bordered else ""
        # 'include_hljs' signals to JavaScript that code blocks within this Markdown
        # should be processed by Highlight.js.
        wrapper_classes = f"markdown-wrapper include_hljs {border_class}".strip()

        html_parts = [f'<div class="{wrapper_classes}">']

        if self.label:
            escaped_label = html.escape(self.label)
            anchor_id = _generate_anchor_id(self.label)  # Use original label for ID
            html_parts.append(
                f"<report-caption><a href='#{anchor_id}'>{escaped_label}</a></report-caption>"
            )

        # Apply extra_css to an inner div. Ensure it's HTML-attribute-safe.
        escaped_extra_css = html.escape(self.extra_css, quote=True)
        style_attr = f'style="{escaped_extra_css}"' if self.extra_css else ""
        html_parts.append(f"<div {style_attr}>")

        # Convert Markdown to HTML. _gfm_markdown_to_html should produce safe HTML.
        html_parts.append(_gfm_markdown_to_html(self.text))

        html_parts.append("</div>")  # End inner div
        html_parts.append("</div>")  # End markdown-wrapper

        return "".join(html_parts)


##############################


class Heading(Base):
    """
    Displays a large heading within the report.

    The `Heading` component is used to create visually distinct section titles
    within a report, using HTML heading tags (h1-h5).

    Args:
        label (str): The text content of the heading. This text will be
            HTML-escaped before being rendered within the heading tag (e.g., `<h1>`).
            This argument also serves as the `label` for the `Base` class.
        level (int, optional): The HTML heading level to use (1 through 5).
            For example, `level=1` creates an `<h1>` tag, `level=2` creates `<h2>`, etc.
            Defaults to 1.

    Raises:
        ValueError: If the specified `level` is not between 1 and 5 (inclusive),
            or if `label` (the heading text) is empty or not provided.
    """

    def __init__(
        self,
        label: str,  # This is the heading text
        *,
        level: Optional[int] = 1,  # HTML heading level (h1, h2, etc.)
    ):
        if not (isinstance(level, int) and 1 <= level <= 5):
            raise ValueError("Heading level must be an integer between 1 and 5.")
        if not label or not str(label).strip():  # Check if label is empty or only whitespace
            raise ValueError("Heading text (label) cannot be empty.")

        # The label for Base class is the heading text itself.
        # It will be HTML-escaped in to_html.
        super().__init__(label=str(label))
        self.level = level

        logger.info(f"Heading component initialized: Level H{self.level}, Text: '{self.label}'")

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Converts the Heading component to its HTML representation (e.g., `<h1>...</h1>`).
        The heading text (label) is HTML-escaped.
        Includes `<br />` tags before and after the heading for spacing.

        Returns:
            str: The HTML string for the heading.
        """
        # HTML-escape the label (heading text) to ensure safe rendering
        escaped_heading_text = html.escape(self.label)
        return f"<br /><h{self.level}>{escaped_heading_text}</h{self.level}><br />"


##############################


class Separator(Base):
    """
    Inserts a visual separator (horizontal rule) into the report.

    The `Separator` component provides a way to create clear visual
    breaks between sections of a report. It renders as a horizontal
    line, making it easy to distinguish different parts of the content.

    Args:
        label (Optional[str], optional): An optional label for the separator.
            If provided, it is HTML-escaped and rendered as a caption
            (using `<report-caption>`) below the horizontal rule (`<hr>`).
            The caption includes a linkable anchor generated from the label text.
            This can be useful for navigation or providing context for the break.
            Defaults to None, in which case only the `<hr>` (with surrounding `<br>`)
            is rendered.
    """

    def __init__(self, label: Optional[str] = None):
        super().__init__(label=label)
        logger.info(f"Separator component initialized. Label: '{self.label}'")

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Converts the Separator component to its HTML representation.

        Renders as a horizontal rule (`<hr>`). If a `label` is provided,
        it's displayed as an HTML-escaped caption below the rule.
        Includes `<br>` tags for spacing.

        Returns:
            str: The HTML string for the separator.
        """
        if self.label:
            # HTML-escape the label for safe rendering
            escaped_label = html.escape(self.label)
            anchor_id = _generate_anchor_id(self.label)  # Use original label for ID
            # Conventionally, caption might be above or below. Here, it's placed after the <hr>.
            return f"<br/><hr/><report-caption><a href='#{anchor_id}'>{escaped_label}</a></report-caption><br/>"
        else:
            return "<br/><hr/><br/>"


##############################


class Text(Markdown):
    """
    An alias for the `Markdown` component, for displaying rich text.

    Displays Markdown-formatted text. It is a direct alias of the `Markdown`
    component, inheriting all its functionality and parameters.

    This component is useful for embedding rich text content formatted using
    GitHub Flavored Markdown. Refer to the `Markdown` class for detailed
    documentation on arguments and behavior (e.g., `text`, `label`, `extra_css`, `bordered`).
    """

    # No __init__ or other methods needed here as it's a pure alias.
    # Python's inheritance handles everything.
    # The docstring above clarifies its relationship to Markdown.
    pass


##############################


class Select(Base):
    """
    Creates a dropdown select element for user interaction within the report.

    The `Select` component creates a tabbed interface where each tab displays
    the content of a corresponding `Base` component from the `blocks` list.
    The `label` of each `Base` component in `blocks` is used as the title for its tab.
    Clicking a tab reveals its associated content.

    A unique `group_id` is generated for each `Select` instance to ensure that
    JavaScript functions for tab switching work correctly when multiple `Select`
    components are on the same page. Labels used for tab titles and overall
    caption are HTML-escaped.

    Args:
        blocks (list[Base]): A list of `Base`-derived components. Each component's
            `label` attribute (which must be present and non-empty) is used as the
            title for a tab. The component's `to_html()` output is the tab's content.
        label (Optional[str], optional): An optional overall label for the tab group,
            HTML-escaped and displayed above the tabs as a caption with an anchor.
            Inherits from `Base`. Defaults to None.

    Raises:
        ValueError: If any component in `blocks` does not have a `label` attribute,
            or if a label is empty or consists only of whitespace.
    """

    def __init__(self, blocks: list[Base], *, label: Optional[str] = None):
        super().__init__(label=label)  # Overall label for the tab group
        self.blocks = blocks

        # Validate that all blocks have non-empty labels, as they are used for tab titles
        for i, b in enumerate(self.blocks):
            if not hasattr(b, "label") or not b.label or not str(b.label).strip():
                raise ValueError(
                    f"Block at index {i} in Select component must have a non-empty label to be used as a tab title."
                )

        block_labels = [str(b.label) for b in self.blocks]
        logger.info(
            f"Select component initialized with {len(self.blocks)} tabs: "
            f"{', '.join(block_labels)}. Overall label: '{self.label}'"
        )

    def _generate_tab_buttons_html(self, group_id_str: str) -> str:
        """Generates the HTML for the tab buttons. Labels are HTML-escaped."""
        buttons_html_parts = []
        for i, block in enumerate(self.blocks):
            # block.label is guaranteed to exist and be non-empty by __init__
            escaped_block_label = html.escape(str(block.label))
            # For use in JavaScript strings, ensure proper escaping for quotes.
            js_escaped_block_label = html.escape(str(block.label), quote=True)

            default_open_class = "defaultOpen" if i == 0 else ""
            buttons_html_parts.append(
                f'<button class="tablinks {default_open_class}" '
                # Pass the string representation of group_id to JS
                f"onclick=\"openTab(event, '{js_escaped_block_label}', '{group_id_str}')\" "
                f'data-group-id="{group_id_str}">{escaped_block_label}</button>'
            )
        return f'<div class="tab">{"".join(buttons_html_parts)}</div>'

    def _generate_tab_contents_html(self, group_id_str: str) -> str:
        """Generates the HTML for the tab contents. Block labels used as IDs are HTML-escaped."""
        contents_html_parts = []
        for block in self.blocks:
            # block.label is guaranteed by __init__
            # Use a combination of group_id and escaped label for unique ID
            js_escaped_block_label_for_id = html.escape(str(block.label), quote=True)
            tab_content_id = f"tab_{group_id_str}_{_generate_anchor_id(str(block.label))}"  # Use anchor for ID safety

            contents_html_parts.append(
                # Use the unique ID and also data-group-id for JS targeting
                f'<div id="{tab_content_id}" data-group-id="{group_id_str}" '
                f'data-tab-name="{js_escaped_block_label_for_id}" class="tabcontent">'
                f"{block.to_html()}"  # Content from the block
                f"</div>"
            )
        return "".join(contents_html_parts)

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Select (tabbed) component to an HTML string.

        Includes an optional HTML-escaped caption, tab buttons, and tab content panels.
        A unique group ID is used to ensure correct behavior with multiple Select instances.

        Returns:
            str: The HTML representation of the tabbed component.
        """
        caption_html = ""
        if self.label:
            escaped_label = html.escape(self.label)
            anchor_id = _generate_anchor_id(self.label)  # Use original label for ID
            caption_html = (
                f"<report-caption><a href='#{anchor_id}'>{escaped_label}</a></report-caption>"
            )

        # Generate a unique group_id string for this Select instance.
        group_id_str = uuid4().hex[:8]

        tab_buttons_html = self._generate_tab_buttons_html(group_id_str)
        tab_contents_html = self._generate_tab_contents_html(group_id_str)

        return f"{caption_html}{tab_buttons_html}{tab_contents_html}"


##############################


class Accordion(Base):
    """
    Creates an accordion element for organizing and collapsing content sections within a report.

    The `Accordion` component creates a stack of collapsible panels, where each
    panel is effectively a `Collapse` component (using `<details>` and `<summary>`).
    The `label` of each `Base` component in the `blocks` list serves as the title
    (summary) for its respective panel.

    Labels for panels and the optional overall caption are HTML-escaped.

    Args:
        blocks (list[Base]): A list of `Base`-derived components. Each component's
            `label` attribute (must be present and non-empty) is used as the
            title for an accordion panel. The component's `to_html()` output
            forms the content of that panel.
        label (Optional[str], optional): An optional overall label for the accordion,
            HTML-escaped and displayed above the panels as a caption with an anchor.
            Inherits from `Base`. Defaults to None.
        open_first (Optional[bool], optional): If True, the first panel in the
            accordion will be rendered with the `open` attribute, making it
            expanded by default. Defaults to False.

    Raises:
        ValueError: If any component in `blocks` does not have a `label` attribute,
            or if a label is empty or consists only of whitespace.
    """

    def __init__(
        self,
        blocks: list[Base],
        *,
        label: Optional[str] = None,  # Overall label for the accordion group
        open_first: Optional[bool] = False,
    ):
        super().__init__(label=label)
        self.blocks = blocks
        self.open_first = open_first

        # Validate that all blocks have non-empty labels for panel titles
        for i, b in enumerate(self.blocks):
            if not hasattr(b, "label") or not b.label or not str(b.label).strip():
                raise ValueError(
                    f"Block at index {i} in Accordion component must have a non-empty label "
                    "to be used as a panel title."
                )

        block_labels = [str(b.label) for b in self.blocks]
        logger.info(
            f"Accordion component initialized with {len(self.blocks)} panels: "
            f"{', '.join(block_labels)}. Overall label: '{self.label}', Open first: {self.open_first}"
        )

    def _generate_accordion_panels_html(self) -> str:
        """Generates the HTML for the individual accordion panels. Panel labels are HTML-escaped."""
        panels_html_parts = []
        for i, block in enumerate(self.blocks):
            # block.label is guaranteed by __init__
            escaped_panel_label = html.escape(str(block.label))
            # Add 'open' attribute to the first panel if open_first is True
            open_attr = " open" if i == 0 and self.open_first else ""

            panels_html_parts.append(
                f'<details class="accordion"{open_attr}>'  # Added class for potential specific styling
                f"<summary>{escaped_panel_label}</summary>"
                f"{block.to_html()}"  # Content from the block
                f"</details>"
            )
        return "".join(panels_html_parts)

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Accordion component to an HTML string.

        Includes an optional HTML-escaped caption and a series of `<details>`
        elements, one for each block provided.

        Returns:
            str: The HTML representation of the accordion.
        """
        caption_html = ""
        if self.label:
            escaped_caption_label = html.escape(self.label)
            anchor_id = _generate_anchor_id(self.label)  # Use original label for ID
            caption_html = f"<report-caption><a href='#{anchor_id}'>{escaped_caption_label}</a></report-caption>"

        accordion_panels_html = self._generate_accordion_panels_html()

        # Wrap the entire accordion in a div for better layout control and styling
        return f'<div class="accordion-group">{caption_html}{accordion_panels_html}</div>'


##############################


class Unformatted(Base):
    """
    Displays data as text without any specific formatting or structure.

    The `Unformatted` component displays raw text content, preserving whitespace
    and line breaks by wrapping the text in `<pre><code>` HTML tags.
    This is suitable for showing data dumps, simple log outputs, or any text
    that should not be processed as Markdown or another rich format.

    The input `text` is HTML-escaped before being placed inside the `<code>` tag
    to prevent XSS vulnerabilities and ensure correct rendering of special characters.
    An optional `label` (also HTML-escaped) can be displayed as a caption.

    Args:
        text (str): The raw text content to be displayed. This text will be
            HTML-escaped.
        label (Optional[str], optional): An optional label for the unformatted
            text block. If provided, it's HTML-escaped and displayed above the
            text as a caption with an anchor. Inherits from `Base`. Defaults to None.
    """

    def __init__(self, text: str, *, label: Optional[str] = None):
        super().__init__(label=label)
        # Store raw text; it will be escaped in to_html
        self.text = str(text)  # Ensure text is a string
        logger.info(
            f"Unformatted component initialized with {len(self.text)} characters of text. Label: '{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Renders the Unformatted text component to an HTML string.

        The text is HTML-escaped and wrapped in `<pre><code>` tags.
        An optional HTML-escaped label is rendered as a caption.

        Returns:
            str: The HTML representation of the unformatted text block.
        """
        # HTML-escape the raw text to prevent XSS and ensure correct rendering
        escaped_text = html.escape(self.text.strip())
        formatted_text_block = f"<pre><code>{escaped_text}</code></pre>"

        html_parts = []
        if self.label:
            escaped_label = html.escape(self.label)
            anchor_id = _generate_anchor_id(self.label)  # Use original label for ID
            html_parts.append(
                f"<report-caption><a href='#{anchor_id}'>{escaped_label}</a></report-caption>"
            )

        # Wrap the formatted text block in a div, which can be useful for styling or layout.
        html_parts.append(f"<div>{formatted_text_block}</div>")

        return "".join(html_parts)


##############################


class Language(Base):
    """
    Base class for components that display code or text in a specific programming language,
    with syntax highlighting.

    This class is not typically used directly but serves as a base for components
    that display code or text in a specific programming or markup language,
    leveraging syntax highlighting via Highlight.js.

    The text content provided to this component (and its subclasses) will be
    HTML-escaped before rendering to prevent XSS vulnerabilities and ensure
    correct display of special characters within the code block.

    Supported languages for syntax highlighting include: "java", "python", "prolog",
    "shell", "sql", "yaml", "json", and "plaintext".

    Args:
        text (str): The code or text content to be displayed. This content will be
            HTML-escaped prior to rendering in the `to_html` method.
        language (str): The programming language identifier (e.g., "python", "sql", "java").
            This identifier must be one of the supported languages and is used by
            Highlight.js to apply the correct syntax highlighting. The language
            name is case-insensitive and will be converted to lowercase.
        scroll_long_content (Optional[bool], optional): If True, it's intended to make
            very long code blocks scrollable.
            **Note:** As of the current version, this parameter is stored but not actively
            used to change the rendering behavior in `to_html`. The output HTML/CSS
            does not yet implement a scrollable container based on this flag.
            Defaults to False.
        label (Optional[str], optional): An optional label for the code block. If provided,
            it's displayed above the code block with a background color that is
            deterministically generated based on the `language` name. The label text
            will be HTML-escaped in `_create_label_span_html`. Inherits from `Base`.
            Defaults to None.

    Raises:
        ValueError: If `language` is not specified or is not in the list of
            supported languages.
    """

    SUPPORTED_LANGUAGES = [
        "java",
        "python",
        "prolog",
        "shell",
        "sql",
        "yaml",
        "json",
        "plaintext",
    ]

    def __init__(
        self,
        text: str,
        language: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        super().__init__(label=label)
        self.text = str(text)  # Ensure text is string, raw text, will be escaped in to_html
        self.scroll_long_content = scroll_long_content  # Currently not used to alter HTML

        if not language:
            raise ValueError("Language must be specified for the Language component.")

        normalized_language = str(language).lower()  # Ensure language is string and normalized
        if normalized_language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Language '{language}' is not supported. "
                f"Supported languages are: {', '.join(self.SUPPORTED_LANGUAGES)}"
            )
        self.language = normalized_language

        logger.info(
            f"{self.language.capitalize()} component: {len(self.text)} characters, "
            f"label='{self.label}', scroll_long_content={self.scroll_long_content}"
        )

    def _create_label_span_html(self) -> str:
        """
        Helper method to create the HTML for the label span if a label is provided.
        The label's background color is determined by the language. The label text
        is HTML-escaped here.
        """
        if not self.label:
            return ""

        # Generate a color based on the language name for consistent label styling
        label_background, label_text_color = _random_color_generator(self.language)
        # HTML-escape the label text before inserting into HTML
        escaped_label = html.escape(self.label)

        return f"""
            <span class="code-block-label" style="background-color: {label_background}; color:{label_text_color};">
                {escaped_label}
            </span>
        """

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Generates the HTML representation of the language code block.
        The main code `self.text` is HTML-escaped here.
        Includes 'include_hljs' class to signal JavaScript to apply syntax highlighting.
        """
        # HTML-escape the raw text to prevent XSS and ensure correct rendering of code.
        # .strip() removes leading/trailing whitespace which might affect <pre> rendering.
        escaped_text = html.escape(self.text.strip())

        # formatted_text will be wrapped in <pre><code class="language-..."> for Highlight.js
        # Adding newlines around escaped_text for better readability of raw HTML and
        # to ensure block display for some markdown processors if this HTML is embedded.
        formatted_text = f"<pre><code class='language-{self.language} syntax-color'>\n{escaped_text}\n</code></pre>"

        label_span_html = self._create_label_span_html()  # Label is escaped within this method

        # The 'include_hljs' class is a marker for JavaScript to initialize Highlight.js
        # on this element. 'code-block' is for general styling.
        # The scroll_long_content flag is not currently altering the HTML structure or classes.

        return f"""
            <div class="code-block include_hljs">
                {label_span_html}{formatted_text}
            </div>
        """


##############################


class Prolog(Language):
    """
    Displays Prolog code with syntax highlighting.

    Inherits from `Language` for common code block functionality.

    Args:
        code (str): The Prolog code string to be displayed.
            The content will be HTML-escaped by the parent `Language` class's `to_html` method.
        scroll_long_content (Optional[bool], optional): If True, long code blocks
            may be made scrollable (behavior depends on CSS/JS in the template).
            Defaults to False.
        label (Optional[str], optional): An optional label for the code block, displayed
            above it. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        # Pass the raw code; Language base class's to_html method handles escaping.
        super().__init__(code, "prolog", scroll_long_content=scroll_long_content, label=label)


##############################


class Python(Language):
    """
    Displays Python code with syntax highlighting.

    Inherits from `Language` for common code block functionality.
    The input `code` string is automatically unindented using `textwrap.dedent`
    before being passed to the parent constructor. This is useful for cleaning up
    Python code defined in triple-quoted strings.

    Args:
        code (str): The Python code string to be displayed.
            It will be dedented before being passed to the `Language` base class.
            The `Language` base class's `to_html` method handles HTML escaping.
        scroll_long_content (Optional[bool], optional): If True, long code blocks
            may be made scrollable (behavior depends on CSS/JS in the template).
            Defaults to False.
        label (Optional[str], optional): An optional label for the code block, displayed
            above it. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        # Dedent the code before passing to the base class.
        # The Language base class's to_html method will handle HTML escaping.
        super().__init__(
            textwrap.dedent(str(code)),  # Ensure code is string before dedent
            "python",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


class Shell(Language):
    """
    Displays Shell (bash/sh) script code with syntax highlighting.

    Inherits from `Language` for common code block functionality.

    Args:
        code (str): The Shell script code string to be displayed.
            The content will be HTML-escaped by the parent `Language` class's `to_html` method.
        scroll_long_content (Optional[bool], optional): If True, long code blocks
            may be made scrollable (behavior depends on CSS/JS in the template).
            Defaults to False.
        label (Optional[str], optional): An optional label for the code block, displayed
            above it. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        # Pass the raw code; Language base class's to_html method handles escaping.
        super().__init__(code, "shell", scroll_long_content=scroll_long_content, label=label)


# Aliases for Shell


class Sh(Shell):
    """Alias for `Shell`. Displays shell script code with syntax highlighting."""

    pass


class Bash(Shell):
    """Alias for `Shell`. Displays Bash script code with syntax highlighting."""

    pass


##############################


class Java(Language):
    """
    Displays Java code with syntax highlighting.

    Inherits from `Language` for common code block functionality.

    Args:
        code (str): The Java code string to be displayed.
            The content will be HTML-escaped by the parent `Language` class's `to_html` method.
        scroll_long_content (Optional[bool], optional): If True, long code blocks
            may be made scrollable (behavior depends on CSS/JS in the template).
            Defaults to False.
        label (Optional[str], optional): An optional label for the code block, displayed
            above it. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        # Pass the raw code; Language base class's to_html method handles escaping.
        super().__init__(code, "java", scroll_long_content=scroll_long_content, label=label)


##############################


class Sql(Language):
    """
    Displays SQL code with syntax highlighting and optional auto-formatting.

    Inherits from `Language` for common code block functionality. If `prettify`
    is enabled, the SQL code is formatted using a basic heuristic formatter
    (`Sql.format_sql`) before being passed to the parent constructor.

    Args:
        code (str): The SQL query string to be displayed. If `prettify` is True,
            this code will be formatted. The resulting code (formatted or original)
            will then be HTML-escaped by the `Language` base class's `to_html` method.
        scroll_long_content (Optional[bool], optional): If True, long code blocks
            may be made scrollable (behavior depends on CSS/JS in the template).
            Defaults to False.
        prettify (Optional[bool], optional): If True, the SQL query string will be
            auto-formatted. This includes uppercasing keywords (e.g., SELECT, FROM),
            standardizing newlines after commas, and indenting clauses.
            The formatting is heuristic and works best on common SQL structures;
            complex or already heavily formatted queries might not be improved.
            Defaults to False.
        label (Optional[str], optional): An optional label for the code block, displayed
            above it. Defaults to None.
    """

    @staticmethod
    def format_sql(sql: str) -> str:
        """
        Heuristically formats an SQL query string for better readability.

        The formatting includes:
        - Placing commas on new lines followed by a tab (if not inside quotes).
        - Uppercasing reserved words (currently only 'AS').
        - Uppercasing block statements (e.g., SELECT, FROM, WHERE) and placing them
        on new lines, followed by a tab.

        Note: This is a basic formatter and may not correctly format all complex SQL queries,
        especially those with comments or already intricate formatting.
        """
        BLOCK_STATEMENTS = [
            "create.*?table",  # regex for all variants, e.g. CREATE OR REPLACE TABLE
            "create.*?view",  # regex for all variants, e.g. CREATE OR REPLACE VIEW
            "select distinct",
            "select",
            "from",
            "left join",
            "inner join",
            "outer join",
            "right join",
            "union",
            "on",
            "where",
            "group by",
            "order by",
            "asc",
            "desc",
            "limit",
            "offset",
            "insert.*?into",
            "update",
            "set",
            "delete",
            "drop",
            "alter",
            "add",
            "modify",
            "rename",
            "truncate",
            "begin",
            "commit",
            "rollback",
            "grant",
            "revoke",
        ]
        RESERVED_WORDS = ["as"]  # Words to uppercase in place

        # Add newline and tab after commas, but not if comma is inside single or double quotes.
        sql = re.sub(r"(?<!['\"]),\s*(?!['\"])", ",\n\t", sql, flags=re.DOTALL)

        # Uppercase specific reserved words if they are not inside quotes.
        for reserved_word in RESERVED_WORDS:
            sql = re.sub(
                rf"(?<!['\"])\b{reserved_word}\b(?!['\"])",
                reserved_word.upper(),
                sql,
                flags=re.IGNORECASE | re.DOTALL,
            )

        # Format block statements
        original_sql_for_check = sql
        for statement_pattern in BLOCK_STATEMENTS:
            # Using a lambda that captures the current state of 'original_sql_for_check'
            def current_replacer(m, osql=original_sql_for_check):
                return (
                    ""
                    if osql.lower().lstrip().startswith(m.group(1).lower())
                    else "\n" + m.group(1).upper() + "\n\t"
                )

            # Refined pattern to better handle keywords at the start or surrounded by whitespace
            sql = re.sub(
                rf"(?i)(?<!['\"])(?:^|\s+)({statement_pattern})(?:\s+|$)(?!['\"])",
                current_replacer,
                sql,
                flags=re.DOTALL,  # re.IGNORECASE is now part of the pattern string with (?i)
            )
        return sql.strip()

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        prettify: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        processed_code = Sql.format_sql(str(code)) if prettify else str(code)
        super().__init__(
            processed_code,
            "sql",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


class Yaml(Language):
    """
    Displays formatted YAML content within the report.

    The `Yaml` component is designed to embed YAML-formatted data
    directly into the report, presenting it in a structured and
    human-readable way. It's useful for displaying configuration files,
    data structures, or any other information that is naturally
    represented in YAML format.

    Args:
        data (Union[dict, list, str]): The YAML data to be displayed.
            This can be a Python dictionary or list (which will be converted to a YAML string),
            or a string already formatted as YAML. The resulting YAML string will be
            HTML-escaped by the `Language` base class's `to_html` method before rendering.
        scroll_long_content (Optional[bool], optional): If True, long code blocks
            may be made scrollable (behavior depends on CSS/JS in the template).
            Defaults to False.
        label (Optional[str], optional): An optional label for the code block, displayed
            above it. Defaults to None.

    Raises:
        ValueError: If the `data` argument's type is not a dict, list, or str.
        yaml.YAMLError: If `data` is a string that cannot be parsed as valid YAML,
            or if there's an error during YAML serialization.
    """

    def __init__(
        self,
        data: Union[str, dict, list],
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        try:
            if isinstance(data, (dict, list)):
                # Convert Python dict/list to YAML string.
                # sort_keys=False preserves insertion order for dicts (Python 3.7+).
                content = yaml.dump(
                    data, indent=2, Dumper=yaml.SafeDumper, sort_keys=False, width=float("inf")
                )
            elif isinstance(data, str):
                # Ensure the input string is valid YAML, then re-dump for consistent formatting.
                parsed_yaml = yaml.load(data, Loader=yaml.SafeLoader)
                content = yaml.dump(
                    parsed_yaml,
                    indent=2,
                    Dumper=yaml.SafeDumper,
                    sort_keys=False,
                    width=float("inf"),
                )
            else:
                raise ValueError(
                    "Invalid data type for Yaml component. Expected dict, list, or valid YAML string."
                )
        except yaml.YAMLError as e:
            logger.error(f"Error processing YAML data for Yaml component: {e}")
            raise ValueError(f"Invalid YAML data or format: {e}") from e

        # Pass the generated YAML string; Language base class's to_html method handles HTML escaping.
        super().__init__(
            content,
            "yaml",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


class Json(Language):
    """
    Displays formatted JSON content within the report.

    The `Json` component serializes Python dictionaries/lists or parses JSON strings,
    then formats the result as an indented JSON string. String values *within*
    the JSON structure are HTML-escaped during serialization by a custom
    encoder (`_RecursiveHtmlEscapingEncoder`) to prevent XSS vulnerabilities.

    The final JSON string (with internal strings escaped) is then passed to the
    `Language` base class, where the entire block is HTML-escaped again. This
    ensures the JSON structure is preserved for display and safe for embedding.

    Args:
        data (Union[dict, list, str]): The JSON data. Can be a Python dict/list or a
            JSON-formatted string.
        scroll_long_content (Optional[bool], optional): If True, long code blocks
            may be made scrollable (behavior depends on CSS/JS in the template).
            Defaults to False.
        label (Optional[str], optional): An optional label for the code block, displayed
            above it. Defaults to None.

    Raises:
        ValueError: If `data` is not a dict, list, or valid JSON string, or if any
            other error occurs during JSON processing.
    """

    def __init__(
        self,
        data: Union[dict, list, str],
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        try:
            if isinstance(data, str):
                # If input is a string, parse it to Python object structure first.
                # This also validates the JSON string.
                parsed_data = json.loads(data)
            elif isinstance(data, (dict, list)):
                # Already a Python structure, use as is.
                parsed_data = data
            else:
                raise ValueError(
                    "Invalid data type for JSON component. Expected dict, list, or valid JSON string."
                )

            content_json_string = json.dumps(
                parsed_data,
                indent=2,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON string provided to Json component: {e}")
            raise ValueError("Input string is not valid JSON.") from e
        except Exception as e:  # Catch other potential errors (e.g., during custom encoding)
            logger.error(f"Error processing JSON data for Json component: {e}")
            raise ValueError(f"Could not process JSON data: {e}") from e

        # Pass the processed JSON string (with internal strings HTML-escaped) to the Language base class.
        # The base class's to_html() will then HTML-escape this *entire* string again.
        super().__init__(
            content_json_string,
            "json",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


class Plaintext(Language):
    """
    Displays text content with minimal formatting (within `<pre><code>` tags) and
    basic syntax highlighting for "plaintext" (which usually means no specific highlighting
    but respects whitespace).

    Inherits from `Language`. The primary purpose is to render text verbatim,
    preserving whitespace and line breaks, without applying Markdown or other
    complex formatting. The `Language` base class's `to_html` method will
    HTML-escape the input text.

    Args:
        text (str): The text content to be displayed. It will be HTML-escaped by
            the `Language` base class's `to_html` method.
        scroll_long_content (Optional[bool], optional): If True, long code blocks
            may be made scrollable (behavior depends on CSS/JS in the template).
            Defaults to False.
        label (Optional[str], optional): An optional label for the code block, displayed
            above it. Defaults to None.
    """

    def __init__(
        self,
        text: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        # Pass the raw text; Language base class's to_html method handles escaping
        # and uses "plaintext" for the Highlight.js class.
        super().__init__(
            text,
            "plaintext",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


TEMPLATE_DIR = Path(__file__).parent / "templates"


class ReportCreator:
    """
    Generates interactive HTML reports from Python objects and components.

    The `ReportCreator` class is the main entry point for assembling and saving
    an HTML report. It manages overall report properties like title, author,
    description, and theming options for various embedded elements such as
    Plotly charts, code blocks (Highlight.js), and diagrams (Mermaid.js).

    Attributes:
        title (str): The main title of the HTML report.
        description (Optional[str]): Markdown-formatted description for the report.
        author (Optional[str]): The author of the report.
        code_theme (str): Theme name for Highlight.js syntax highlighting.
        diagram_theme (str): Theme name for Mermaid.js diagrams.
        accent_color (str): Accent color for the auto-generated SVG logo.
        footer (Optional[str]): Markdown-formatted text for the report's footer.
        header_str (str): HTML string for the report's header/logo.
        default_colors (list): Original Matplotlib color cycle, restored on exit.

    Args:
        title (str): The title for the report. This will be HTML-escaped.
        description (Optional[str], optional): A short description of the report.
            Supports GitHub Flavored Markdown. Rendered below the title. Defaults to None.
        author (Optional[str], optional): The name of the report's author.
            HTML-escaped. Defaults to None.
        logo (Optional[str | Path], optional): Specifies the logo in the report header.
            - URL (http, https, data:image): Used directly.
            - Local file path: Embedded as base64 data URI.
            - String (not file/URL): Assumed GitHub username for avatar.
            - None (default): Auto-generates SVG icon from `title` and `accent_color`.
        theme (str, optional): Plotly template for charts. "rc" is a custom theme.
            Defaults to "rc".
        code_theme (str, optional): Highlight.js theme for code blocks.
            Defaults to "github-dark".
        diagram_theme (str, optional): Mermaid.js theme for diagrams.
            Defaults to "default".
        accent_color (str, optional): Accent color for auto-generated logo.
            Defaults to "black".
        footer (Optional[str], optional): Text for the report's footer (Markdown supported).
            Defaults to None.

    Raises:
        ValueError: If an invalid `theme` (Plotly template) is specified.
    """

    def __init__(
        self,
        title: str,
        *,
        description: Optional[str] = None,
        author: Optional[str] = None,
        logo: Optional[str | Path] = None,  # Allow Path for logo
        theme: str = "rc",
        code_theme: str = "github-dark",
        diagram_theme: str = "default",
        accent_color: str = "black",
        footer: Optional[str] = None,
    ):
        self.title = str(title)  # Ensure title is string
        self.description = str(description) if description is not None else None
        self.author = str(author) if author is not None else None
        self.code_theme = str(code_theme)
        self.diagram_theme = str(diagram_theme)
        self.accent_color = str(accent_color)
        self.footer = str(footer) if footer is not None else None

        logger.info(
            f"ReportCreator initialized: title='{self.title}', description provided: {bool(self.description)}"
        )

        # Setup plotting template
        if "rc" not in pio.templates:  # Ensure "rc" template is added only once
            pio.templates["rc"] = get_rc_theme()

        # Validate theme
        valid_themes = list(pio.templates.keys())
        if theme not in valid_themes:
            raise ValueError(
                f"Theme '{theme}' not in available themes: {', '.join(valid_themes)}"
            )
        pio.templates.default = theme

        self._create_header(logo)  # Initialize self.header_str

    def _create_header(self, logo: Optional[str | Path]) -> None:
        """
        Creates the HTML string for the report's header, primarily for the logo.
        Logo source is HTML-escaped if it's a URL. Local files are converted to
        data URIs. Auto-generated SVG uses escaped values.

        Args:
            logo (Optional[str | Path]): The logo source, as described in `__init__`.
        """
        logo_style = (
            'style="width: 125px; height: 125px; object-fit: contain;"'  # Consistent style
        )
        self.header_str = ""

        if logo:
            logo_str = str(logo)  # Work with string representation
            if logo_str.startswith(("http://", "https://", "data:image")):
                # Direct URL or data URI - escape it for safety in HTML attribute
                self.header_str = (
                    f'<img src="{html.escape(logo_str, quote=True)}" {logo_style}>'
                )
            else:  # Attempt to treat as Path or GitHub username
                logo_path = Path(logo_str)
                if logo_path.is_file():
                    try:
                        data_uri = _convert_filepath_to_datauri(logo_path)
                        # Data URIs are safe for src attribute, no further HTML escaping needed for the URI itself
                        self.header_str = f'<img src="{data_uri}" {logo_style}>'
                    except Exception as e:
                        logger.warning(
                            f"Could not convert logo file '{logo_path}' to data URI: {e}. Skipping logo."
                        )
                else:  # Not a file, assume GitHub username if it was a string
                    logger.info(f"Assuming '{logo_str}' is a GitHub username for the logo.")
                    # Ensure username is URL-safe for the GitHub URL path
                    gh_avatar_url = f"https://avatars.githubusercontent.com/{html.escape(logo_str, quote=True)}?s=125"
                    self.header_str = f'<img src="{gh_avatar_url}" {logo_style}>'
        else:
            # Auto-generate SVG icon if no logo is provided
            title_for_initials = self.title or "R"
            match = re.findall(r"[A-Z]", title_for_initials)
            icon_text = "".join(match[:2]) if match else title_for_initials[0].upper()

            escaped_accent_color = html.escape(self.accent_color, quote=True)
            text_fill_color = "white"

            width = 125
            cx = cy = r = width / 2
            font_size = int(r * 0.7)
            # Join preferred_fonts with quotes for CSS font-family
            font_family_css = ", ".join([f"'{f}'" for f in preferred_fonts] + ["sans-serif"])

            self.header_str = textwrap.dedent(f"""\
                <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{width}" height="{width}" viewBox="0 0 {width} {width}">
                    <style>
                        .icon_text_style {{
                            font-family: {font_family_css};
                            font-size: {font_size}px;
                            font-weight: bold;
                            text-anchor: middle;
                            dominant-baseline: central;
                        }}
                    </style>
                    <circle cx="{cx}" cy="{cy}" r="{r}" fill="{escaped_accent_color}" />
                    <text class="icon_text_style" x="50%" y="50%" fill="{text_fill_color}">{html.escape(icon_text)}</text>
                </svg>
            """)

    def __enter__(self) -> "ReportCreator":
        """
        Enters a context, saving the original Matplotlib color cycle and applying
        Report Creator's theme colors. This ensures Matplotlib figures generated
        within this context use a consistent color scheme.

        Returns:
            ReportCreator: The instance itself.
        """
        # Store the original Matplotlib color cycle
        self.default_colors = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
        # Apply Report Creator's custom color cycle
        mpl.rcParams["axes.prop_cycle"] = cycler("color", report_creator_colors)
        logger.debug("Entered ReportCreator context: Matplotlib styles updated.")
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
        """
        Exits the context, restoring the original Matplotlib color cycle.
        """
        mpl.rcParams["axes.prop_cycle"] = cycler("color", self.default_colors)
        logger.debug("Exited ReportCreator context: Original Matplotlib styles restored.")

    @_time_it
    def save(self, view: Base, path: str | Path, prettify_html: bool = True) -> None:
        """
        Renders the report content and saves it to an HTML file.

        This method takes the main view component, renders it to HTML, and then
        embeds this HTML body into a Jinja2 template that includes necessary
        headers, styles, and scripts. All textual metadata (title, author,
        description, footer) is HTML-escaped before being passed to the template.

        Args:
            view (Base): The root `Base` component representing the report's content.
            path (str | Path): File path to save the HTML report.
            prettify_html (bool, optional): If True (default), uses BeautifulSoup
                to prettify the HTML output. Requires `beautifulsoup4`. Defaults to True.

        Raises:
            ValueError: If `view` is not an instance of `Base`.
            FileNotFoundError: If the Jinja2 template file cannot be found.
            RuntimeError: If template rendering or component HTML generation fails.
            IOError: If the HTML file cannot be written.
        """
        output_path = Path(path)

        if not isinstance(view, Base):
            raise ValueError(
                f"Expected 'view' to be an instance of a Base component, got {type(view).__name__} instead."
            )

        logger.info("Rendering report content from view component...")
        try:
            body_html = view.to_html()
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Error rendering report view component: {e}\n{error_trace}")
            body_html = (
                f"<h1>Error Rendering Report Content</h1>"
                f"<p>An error occurred while generating the HTML for the report's main view.</p>"
                f"<h2>Traceback:</h2><pre>{html.escape(error_trace)}</pre>"
            )

        try:
            file_loader = FileSystemLoader(str(TEMPLATE_DIR))
            # Explicitly disable autoescaping at Environment level, as we handle it manually
            env = Environment(loader=file_loader, autoescape=False)
            template = env.get_template("default.html")
        except Exception as e:
            logger.error(f"Failed to load report template from '{TEMPLATE_DIR}': {e}")
            raise FileNotFoundError(
                f"Could not load report template 'default.html': {e}"
            ) from e

        include_plotly = "plotly-graph-div" in body_html
        include_datatable = "include_datatable" in body_html
        include_mermaid = "include_mermaid" in body_html
        include_hljs = "include_hljs" in body_html

        logger.info(
            f"Report features detected: Plotly={include_plotly}, DataTable={include_datatable}, "
            f"Mermaid={include_mermaid}, HighlightJS={include_hljs}"
        )

        # Prepare context for Jinja2 template, ensuring all text is HTML-escaped
        # Note: body_html and header_str are already HTML-safe or structured HTML
        template_context = {
            "title": html.escape(self.title or "Report"),
            "description": _gfm_markdown_to_html(self.description) if self.description else "",
            "author": html.escape(self.author.strip())
            if self.author and self.author.strip()
            else "",
            "body": body_html,
            "header_logo": self.header_str,
            "include_plotly": include_plotly,
            "include_datatable": include_datatable,
            "include_mermaid": include_mermaid,
            "include_hljs": include_hljs,
            "code_theme": html.escape(self.code_theme),
            "diagram_theme": html.escape(self.diagram_theme),
            "accent_color": html.escape(self.accent_color),
            "footer": _gfm_markdown_to_html(self.footer).strip() if self.footer else "",
        }

        try:
            final_html_content = template.render(template_context)
        except Exception as e:
            logger.error(f"Failed to render final HTML template: {e}\n{traceback.format_exc()}")
            raise RuntimeError(f"Failed during final HTML template rendering: {e}") from e

        output_to_write = final_html_content
        if prettify_html:
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(final_html_content, "html.parser")
                output_to_write = soup.prettify(formatter="minimal")
            except ImportError:
                logger.warning(
                    "BeautifulSoup not installed (`pip install beautifulsoup4`), saving HTML without prettification."
                )
            except Exception as e:
                logger.warning(f"HTML prettification failed: {e}. Saving raw HTML instead.")

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_to_write, encoding="utf-8")
            file_size = output_path.stat().st_size
            logger.info(
                f"ReportCreator successfully created report at: '{output_path.resolve()}' "
                f'(Size: {humanize.naturalsize(file_size, binary=True)}, Title: "{self.title}")'
            )
        except OSError as e:
            logger.error(f"Failed to write report file to '{output_path}': {e}")
            raise OSError(f"Failed to write report file: {e}") from e
