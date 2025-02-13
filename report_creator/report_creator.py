import base64
import html
import io
import json
import logging
import os
import re
import textwrap
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Union
from uuid import uuid4

import dateutil
import humanize
import matplotlib
import matplotlib as mpl
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import plotly.io as pio
import yaml
from cycler import cycler
from jinja2 import Environment, FileSystemLoader
from markupsafe import escape
from pandas.api.types import is_datetime64_any_dtype as is_datetime

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

logger = logging.getLogger("report_creator")
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)


class Base(ABC):
    """Abstract Base Class for all components

    Args:
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, label: Optional[str] = None) -> None:
        self.label = label

    @abstractmethod
    def to_html(self) -> str:
        """Each component that derives from Base must implement this method"""


##############################


class Block(Base):
    """A vertical container that stacks components from top to bottom.

    Block is one of the primary layout components. It arranges its child components
    vertically with consistent spacing. Use Block when you want components to appear
    one after another down the page.

    Example:
        ```python
        # Create a block with multiple components
        Block(
            Heading("Section 1"),
            Markdown("Some explanatory text"),
            DataTable(df),
            Heading("Section 2"),
            Group(
                Metric("Value 1", 100),
                Metric("Value 2", 200)
            )
        )
        ```

    Args:
        components (Base): One or more report components to stack vertically
        label (Optional[str]): Optional label for the block. Defaults to None.

    Note:
        - Components are rendered in the order they are provided
        - Blocks can be nested inside other Blocks or Groups
        - Use Group instead if you want horizontal layout
    """

    def __init__(self, *components: "Base", label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.components = components
        logger.info(f"Block: {len(self.components)} components")

    @_strip_whitespace
    def to_html(self) -> str:
        html = "<block>"

        for component in self.components:
            html += "<block-component>"
            html += component.to_html()
            html += "</block-component>"

        html += "</block>"

        return html


##############################


class Group(Base):
    """A horizontal container that arranges components side-by-side.

    Group is used to create horizontal layouts where components appear next to each
    other. It automatically handles responsive behavior, wrapping components to new
    rows on smaller screens.

    Example:
        ```python
        # Create a row of metrics
        Group(
            Metric("Revenue", 1500000, unit="$"),
            Metric("Expenses", 1000000, unit="$"),
            Metric("Profit", 500000, unit="$")
        )
        ```

    Args:
        components (Base): One or more components to arrange horizontally
        label (Optional[str]): Optional label for the group. Defaults to None.

    Note:
        - Components are sized equally by default
        - Use Block instead if you want vertical stacking
        - Groups can be nested in Blocks or other Groups
    """

    def __init__(self, *components: Base, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.components = components
        logger.info(f"Group: {len(self.components)} components {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        html = "<div>"

        if self.label:
            html += f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption></a>"

        html += """<div class="group">"""

        for component in self.components:
            html += "<div class='group-content'>"
            html += component.to_html()
            html += "</div>"

        html += "</div>"  # group

        html += "</div>"  # outer block div

        return html


##############################


class Collapse(Base):
    """Collapse is a container for vertically stacked components that can be collapsed

    Args:
        components (Base): _description_
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, *components: Base, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.components = components
        logger.info(f"Collapse: {len(self.components)} components, {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        html = f"""<details class="collapse"><summary>{self.label}</summary>"""

        for component in self.components:
            html += component.to_html()

        html += "</details>"
        return html


##############################


class Widget(Base):
    """Widget is a container for any component that supports the _repr_html_ method (anything written for Jupyter).

    Args:
        widget: A widget that supports the _repr_html_ method.
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, widget, *, label: Optional[str] = None):
        Base.__init__(self, label=label)
        if isinstance(widget, go.Figure):
            self.widget = widget
            PxBase.apply_common_fig_options(self.widget)

        elif hasattr(widget, "get_figure"):
            self.widget = widget.get_figure()
        else:
            self.widget = widget

    @_strip_whitespace
    def to_html(self) -> str:
        html = "<div class='report-widget'>"

        if self.label:
            html += f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption>"

        if isinstance(self.widget, pd.DataFrame):
            html += self.widget.style._repr_html_()
        elif isinstance(self.widget, matplotlib.figure.Figure):
            tmp = io.BytesIO()

            self.widget.set_dpi(300)
            self.widget.set_figwidth(10)
            self.widget.tight_layout()
            self.widget.savefig(tmp, format="png")
            tmp.seek(0)
            b64image = base64.b64encode(tmp.getvalue()).decode("utf-8").replace("\n", "")
            html += f'<br/><img src="data:image/png;base64,{b64image}">'

        else:
            html += self.widget._repr_html_()

        html += "</div>"
        return html


##############################


class MetricGroup(Base):
    """MetricGroup is a container for a group of metrics. It takes a DataFrame with a heading and value column.

    Args:
        df (pd.DataFrame): the DataFrame containing the data.
        heading (str): the column with the metric heading string
        value (str): the column wuth the metric value
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(
        self, df: pd.DataFrame, heading: str, value: str, *, label: Optional[str] = None
    ):
        Base.__init__(self, label=label)
        assert heading in df.columns, f"heading {heading} not in df"
        assert value in df.columns, f"value {value} not in df"

        self.g = Group(
            *[Metric(row[heading], row[value]) for _, row in df.iterrows()], label=label
        )

        logger.info(f"MetricGroup: {len(df)} metrics")

    @_strip_whitespace
    def to_html(self) -> str:
        return self.g.to_html()


##############################


class EventMetric(Base):
    """A specialized metric for tracking and visualizing event data over time.

    EventMetric combines a metric display with a sparkline chart showing the trend.
    Perfect for monitoring system events, user actions, or any time-series data
    that can be counted.

    Example:
        ```python
        # Track successful API calls
        EventMetric(
            df,
            condition="status_code == 200",
            date="timestamp",
            frequency="D",
            color="green",
            heading="Successful Requests"
        )

        # Monitor errors with weekly aggregation
        EventMetric(
            df,
            condition="severity == 'ERROR'",
            date="log_time",
            frequency="W",
            color="red",
            heading="Weekly Errors"
        )
        ```

    Args:
        df (pd.DataFrame): Event data
        condition (str): Python expression to evaluate for each row
        date (str): Column containing timestamps
        frequency (str, optional): Aggregation frequency:
            - "D": Daily
            - "W": Weekly
            - "M": Monthly
            - "H": Hourly
        color (str, optional): Line/fill color. Defaults to "red".
        heading (Optional[str]): Metric title. Defaults to condition text.
        label (Optional[str]): Description text. Defaults to None.

    Note:
        - Automatically converts date strings to timestamps
        - Shows total count and trend visualization
        - Interactive hover shows values
        - Supports pandas frequency strings
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
        Base.__init__(self, label=label)

        assert date in df.columns, f"index column {date} not in df"
        self.df = df
        self.date = date

        self.freq = frequency

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
        dfx = self.df.eval(f"{self.yhat} = {self.condition}")[[self.date, self.yhat]]
        dfx[self.yhat] = dfx[self.yhat].astype(int)
        dfx = dfx.groupby(pd.Grouper(key=self.date, freq=self.freq)).sum().reset_index()

        # For an empty dataframe summing a series doesn't return 0
        agg_value = dfx["_Y_"].apply("sum") if not dfx.empty else 0

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


##############################


class Metric(Base):
    """Displays a single metric/KPI with optional formatting and description.

    Metric is designed to highlight important numbers and statistics. It supports
    various data types and automatic formatting.

    Example:
        ```python
        # Basic metric
        Metric("Revenue", 1500000, unit="$")

        # With description and precision
        Metric(
            "Conversion Rate",
            0.1234,
            unit="%",
            float_precision=2,
            label="Percentage of visitors who made a purchase"
        )

        # With background color
        Metric("Status", "Active", color=True)
        ```

    Args:
        heading (str): The metric name/title
        value (Union[str, int, float, datetime]): The metric value. Supports:
            - Strings (displayed as-is)
            - Integers (formatted with humanize)
            - Floats (rounded based on precision)
            - Datetime (formatted as YYYY-MM-DD)
        unit (Optional[str]): Unit to display after the value. Defaults to None.
        float_precision (Optional[int]): Number of decimal places for floats. Defaults to 3.
        label (Optional[str]): Markdown description text shown below the metric. Defaults to None.
        color (Optional[bool]): Whether to add a random background color. Defaults to False.

    Note:
        - Large numbers are automatically formatted (e.g. 1.5M instead of 1500000)
        - Colors are generated deterministically based on the heading
        - Description text supports markdown formatting
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
        Base.__init__(self, label=textwrap.dedent(label) if label else None)
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


##############################


class Table(Widget):
    """Table is a simple container for a DataFrame (or table-like list of dictionaries.)

    Args:
        data (Union[pd.DataFrame, list[dict]]): _description_
        label (Optional[str], optional): _description_. Defaults to None.
        index (bool, optional): _description_. Defaults to False.
        float_precision (int, optional): _description_. Defaults to 3.
    """

    def __init__(
        self,
        data: Union[pd.DataFrame, list[dict]],
        *,
        label: Optional[str] = None,
        index: Optional[bool] = False,
        float_precision: Optional[int] = 2,
    ):
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError(f"Expected data to be a list or pd.DataFrame, got {type(data)}")

        s = df.style if index else df.style.hide()

        Widget.__init__(self, s.format(escape="html", precision=float_precision), label=label)


##############################


class DataTable(Base):
    """Creates an interactive data table with search, sort and pagination.

    DataTable provides a rich interface for displaying tabular data. It automatically
    handles large datasets with client-side processing.

    Example:
        ```python
        # Basic table
        DataTable(df)

        # Customized table
        DataTable(
            df,
            label="Sales Data",
            wrap_text=False,
            index=False,
            max_rows=1000,
            float_precision=2
        )
        ```

    Args:
        data (Union[pd.DataFrame, list[dict]]): Table data as DataFrame or list of dicts
        label (Optional[str]): Table caption/title. Defaults to None.
        wrap_text (bool): Whether to wrap long text in cells. Defaults to True.
        index (Optional[bool]): Whether to show DataFrame index. Defaults to False.
        max_rows (Optional[int]): Max rows to display (-1 for all). Defaults to -1.
        float_precision (Optional[int]): Decimal places for floats. Defaults to 2.

    Features:
        - Full-text search across all columns
        - Click column headers to sort
        - Page through large datasets
        - Responsive layout with horizontal scrolling
        - Export to CSV/Excel
    """

    def __init__(
        self,
        data: Union[pd.DataFrame, list[dict]],
        *,
        label: Optional[str] = None,
        wrap_text: bool = True,
        index: Optional[bool] = False,
        max_rows: Optional[int] = -1,
        float_precision: Optional[int] = 2,
    ):
        Base.__init__(self, label=label)

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError(f"Expected data to be a list or pd.DataFrame, got {type(data)}")

        styler = df.head(max_rows).style if max_rows > 0 else df.style

        if label:
            styler.set_caption(label)

        data_table_classes = [
            "fancy-table",
            "display",
            "row-border",
            "hover",
            "responsive",
        ]
        if not wrap_text:
            data_table_classes.append("nowrap")

        if not index:
            styler.hide(axis="index")

        styler.set_table_attributes(
            f'class="{" ".join(data_table_classes)} cellspacing="0" style="width: 100%;"'
        )
        self.table_html = styler.format(escape="html", precision=float_precision).to_html()
        logger.info(f"DataTable: {len(df)} rows, {len(df.columns)} columns")

    @_strip_whitespace
    def to_html(self) -> str:
        return f"<div class='dataTables-wrapper include_datatable'><br/>{self.table_html}</div>"


##############################


class Html(Base):
    """Html is a container for raw HTML. It can also include CSS.

    Args:
        html (str): The raw HTML content.
        css (str, optional): The CSS styles to be applied to the HTML. Defaults to None.
        label (Optional[str], optional): The label for the HTML component. Defaults to None.
        bordered (Optional[bool], optional): If set to True, the HTML will have a border. Defaults to False.
    """

    def __init__(
        self,
        html: str,
        *,
        css: Optional[str] = None,
        label: Optional[str] = None,
        bordered: Optional[bool] = False,
    ):
        Base.__init__(self, label=label)
        self.html = html
        self.css = css
        self.bordered = bordered
        status, errors = _check_html_tags_are_closed(html)
        if not status:
            raise ValueError(
                f"HTML component with label {self.label}, tags are not closed: {', '.join(errors)}"
            )
        logger.info(f"HTML: {len(self.html)} characters")

    @_strip_whitespace
    def to_html(self) -> str:
        border = "round-bordered" if self.bordered else ""

        html = f"<style>{self.css}</style>" if self.css else ""
        if self.label:
            html += f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption>"
        html += f'<div class="{border}">' + self.html + "</div>"
        return html


##############################


class Diagram(Base):
    """Creates diagrams using Mermaid.js syntax.

    Diagram enables you to create various types of diagrams using Mermaid's markdown-like
    syntax. Supports flowcharts, sequence diagrams, gantt charts and more.

    Example:
        ```python
        # Simple flowchart
        Diagram('''
            graph TD
                A[Start] --> B{Decision}
                B -->|Yes| C[OK]
                B -->|No| D[Cancel]
        ''')

        # With pan/zoom and custom styling
        Diagram(
            mermaid_code,
            label="System Architecture",
            pan_and_zoom=True,
            extra_css="max-width: 800px;"
        )
        ```

    Args:
        src (str): Mermaid diagram source code
        pan_and_zoom (Optional[bool]): Enable pan/zoom controls. Defaults to True.
        extra_css (Optional[str]): Additional CSS styles. Defaults to None.
        label (Optional[str]): Diagram caption. Defaults to None.

    Supported Diagram Types:
        - Flowchart
        - Sequence Diagram
        - Class Diagram
        - State Diagram
        - Entity Relationship Diagram
        - User Journey
        - Gantt Chart
        - Pie Chart
        - Git Graph

    Note:
        - See https://mermaid.js.org/syntax/flowchart.html for syntax reference
        - Pan: Click and drag
        - Zoom: Shift + mouse wheel
    """

    def __init__(
        self,
        src: str,
        *,
        pan_and_zoom: Optional[bool] = True,
        extra_css: Optional[str] = None,
        label: Optional[str] = None,
    ):
        Base.__init__(self, label=label)

        self.src = src
        self.extra_css = extra_css or ""
        self.pan_and_zoom = pan_and_zoom
        logger.info(f"Diagram: {len(self.src)} characters")

    @_strip_whitespace
    def to_html(self) -> str:
        html = """
            <div class="diagram-block">
                <figure>
        """

        if self.label:
            html += f"<figcaption><report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption></figcaption>"

        html += f"""<pre class='mermaid include_mermaid {"mermaid-pan-zoom" if self.pan_and_zoom else ""}' style="{self.extra_css}">
                        {self.src}
                    </pre>"""

        if self.pan_and_zoom:
            html += "<small>"
            html += "pan (mouse) and zoom (shift+wheel)"
            html += """&nbsp;<a href="#" onclick="event.preventDefault();" class="panzoom-reset">(reset)</a>"""
            html += "</small>"

        html += """
                </figure>
            </div>"""

        return html


##############################


class Image(Base):
    """Image is a container for an image. It can also take a link.

    Args:
        src (str): a URL where the image can be found, or a base_64 URI.
        link_to (str, optional): a URL to go to if clicked. Defaults to not clickable.
        label (Optional[str], optional): a label for the image. Defaults to None.
        extra_css (str, optional): additional CSS styles for the image. Defaults to None.
        rounded (bool, optional): if set to True, the image will have rounded corners. Defaults to True.
        convert_to_base64 (bool, optional): if set to True, the src will be fetched at create time and replaced with a base64 encoded image. Defaults to False.
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
        Base.__init__(self, label=label)
        self.src = src
        self.link_to = link_to
        self.extra_css = extra_css or ""
        self.rounded_css = "border-radius: 0.75rem;" if rounded else ""
        if convert_to_base64:
            try:
                self.src = _convert_imgurl_to_datauri(src)
            except Exception as e:
                logger.error(f"Error converting {src} to base64: {e}")
        logger.info(f"Image: label: {self.label}")

    @_strip_whitespace
    def to_html(self) -> str:
        html = """<div class="image-block"><figure>"""

        image_markup = f"""<img src="{self.src}" style="{self.rounded_css} {self.extra_css}" alt="{self.label or self.src}">"""
        if self.link_to:
            html += f"""<a href="{self.link_to}" target="_blank">{image_markup}</a>"""
        else:
            html += image_markup

        if self.label:
            html += f"<figcaption><report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption></figcaption>"

        html += "</figure></div>"

        return html


##############################


class Markdown(Base):
    """Renders Markdown text with GitHub-flavored syntax support.

    Markdown provides a simple way to add formatted text content to reports.
    Supports standard Markdown plus tables, code blocks, and other GFM features.

    Example:
        ```python
        # Basic text
        Markdown("# Heading\nRegular text with **bold** and *italic*")

        # With code blocks
        Markdown('''
            # Analysis Results

            ## Key Findings
            - Point 1
            - Point 2

            ```python
            def example():
                return "Code with syntax highlighting"
            ```

            | Column 1 | Column 2 |
            |----------|----------|
            | Data 1   | Data 2   |
        ''')

        # With custom styling
        Markdown(
            text="Content here...",
            extra_css="max-width: 800px;",
            bordered=True
        )
        ```

    Args:
        text (str): Markdown-formatted text content
        label (Optional[str]): Section label/title. Defaults to None.
        extra_css (Optional[str]): Additional CSS styles. Defaults to None.
        bordered (Optional[bool]): Add container border. Defaults to False.

    Supported Syntax:
        - Headers (# H1, ## H2, etc.)
        - Lists (ordered and unordered)
        - Links and images
        - Tables
        - Code blocks with syntax highlighting
        - Task lists
        - Strikethrough
        - Emoji shortcodes
        - HTML tags

    Note:
        - Uses GitHub-flavored Markdown parsing
        - Code syntax highlighting via highlight.js
        - Automatically generates anchor links for headers
        - Preserves whitespace in code blocks
    """

    def __init__(
        self,
        text: str,
        *,
        label: Optional[str] = None,
        extra_css: Optional[str] = None,
        bordered: Optional[bool] = False,
    ):
        Base.__init__(self, label=label)
        self.text = textwrap.dedent(text)
        self.extra_css = extra_css or ""
        self.bordered = bordered

        logger.info(f"Markdown: {len(self.text)} characters")

    @_strip_whitespace
    def to_html(self) -> str:
        border = "round-bordered" if self.bordered else ""
        html = f"<div class='markdown-wrapper include_hljs {border}'>"
        if self.label:
            html += f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption>"

        html += f'<div style="{self.extra_css}">' if self.extra_css else "<div>"
        html += _gfm_markdown_to_html(self.text)
        html += "</div>"
        html += "</div>"

        return html


##############################


class PxBase(Base):
    def __init__(self, label: Optional[str] = None):
        Base.__init__(self, label=label)

    @abstractmethod
    def to_html(self) -> str:
        """Each component that derives from PXBase must implement this method"""
        pass

    @staticmethod
    def apply_common_fig_options(fig):
        fig.update_layout(
            font_family=preferred_fonts[0],
            autosize=True,
            modebar_remove="lasso",
        )
        fig.update_xaxes(title_font_family=preferred_fonts[0], tickangle=90)

    @staticmethod
    def apply_common_kwargs(kwargs, label: Optional[str] = None):
        def insert_br_tags(text: str, n: int = 8):
            words = text.split()
            output = []
            current_line = []

            for word in words:
                current_line.append(word)
                if len(current_line) == n:
                    output.append(" ".join(current_line))
                    current_line = []

            if current_line:  # Add any remaining words
                output.append(" ".join(current_line))

            return "<br>".join(output)  # Join the lines with <br> tag

        if label and "title" not in kwargs:
            kwargs["title"] = insert_br_tags(label, n=8)


##############################

# Charting Components

##############################


class Bar(PxBase):
    """Creates interactive bar charts with grouping and stacking options.

    Bar charts effectively show comparisons between categories. Supports vertical
    or horizontal bars, grouping, stacking, and sorting options.

    Example:
        ```python
        # Basic bar chart
        Bar(df, x="category", y="value")

        # Grouped bars
        Bar(
            df,
            x="product",
            y="sales",
            dimension="region",
            label="Sales by Product and Region"
        )

        # Stacked bars with sorting
        Bar(
            df,
            x="month",
            y="revenue",
            dimension="department",
            kwargs={
                "barmode": "stack",
                "category_orders": {"month": df.month.unique()}
            }
        )
        ```

    Args:
        df (pd.DataFrame): The data to plot
        x (str): Column name for categories
        y (str): Column name for values
        dimension (Optional[str]): Column for grouping/coloring bars. Defaults to None.
        label (Optional[str]): Chart title/caption. Defaults to None.
        **kwargs: Additional plotly express bar chart options:
            - barmode: "group" or "stack"
            - orientation: "v" (vertical) or "h" (horizontal)
            - text: Column name for bar labels
            - category_orders: Dict defining category sort order
            - height: Chart height in pixels
            - title: Chart title (auto-generated from label if not specified)

    Note:
        - Automatically sizes bars and gaps
        - Interactive tooltips show values
        - Legend shown when using dimension grouping
        - Responsive layout adapts to container width
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        *,
        dimension: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        Base.__init__(self, label=label)
        self.df = df
        self.x = x
        self.y = y
        self.kwargs = kwargs

        assert x in df.columns, f"{x} not in df"
        assert y in df.columns, f"{y} not in df"

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["color"] = dimension

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        logger.info(f"Bar: {len(self.df)} rows, {x=}, {y=}, {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        fig = px.bar(self.df, x=self.x, y=self.y, **self.kwargs)

        PxBase.apply_common_fig_options(fig)
        fig.update_layout(bargap=0.1)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


##############################


class Line(PxBase):
    """Creates interactive line charts with optional multi-series support.

    Line charts are ideal for showing trends over time or comparing multiple series
    of data. Supports automatic date formatting, hover tooltips, and zooming.

    Example:
        ```python
        # Basic line chart
        Line(df, x="date", y="value")

        # Multiple series
        Line(
            df,
            x="date",
            y=["revenue", "costs", "profit"],
            label="Financial Metrics"
        )

        # With dimension coloring
        Line(
            df,
            x="date",
            y="temperature",
            dimension="location",
            label="Temperature by City"
        )
        ```

    Args:
        df (pd.DataFrame): The data to plot
        x (str): Column name for x-axis (typically dates/time)
        y (Union[str, list[str]]): Column name(s) for y-axis values
        dimension (Optional[str]): Column to use for grouping/coloring. Defaults to None.
        label (Optional[str]): Chart title/caption. Defaults to None.
        **kwargs: Additional plotly express line chart options:
            - line_shape: "linear", "spline", "hv", "vh", "hvh", "vhv"
            - markers: Show point markers (bool)
            - template: Plotly theme template
            - height: Chart height in pixels
            - title: Chart title (auto-generated from label if not specified)

    Note:
        - Automatically handles date formatting on x-axis
        - Interactive zoom and pan enabled by default
        - Hover tooltips show x,y values
        - Legend shown automatically for multiple series
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: Union[str, list[str]],
        *,
        dimension: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        Base.__init__(self, label=label)
        self.df = df
        self.x = x
        self.y = y
        self.kwargs = kwargs

        assert x in df.columns, f"{x} not in df"

        if isinstance(y, list):
            for _ in y:
                assert _ in df.columns, f"{_} not in df"

        elif isinstance(y, str):
            assert y in df.columns, f"{y} not in df"
        else:
            raise ValueError(f"y must be a string or a list of strings, got {type(y)}")

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["symbol"] = dimension
            self.kwargs["color"] = dimension

        if "line_shape" not in self.kwargs:
            self.kwargs["line_shape"] = "linear"

        if "markers" not in self.kwargs:
            self.kwargs["markers"] = True

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        logger.info(f"Line: {len(self.df)} rows, {x=}, {y=}, {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        fig = px.line(self.df, x=self.x, y=self.y, **self.kwargs)

        PxBase.apply_common_fig_options(fig)
        fig.update_layout(bargap=0.1)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


##############################


class Pie(PxBase):
    """Pie is a container for a plotly express pie chart.

    Args:
        df (pd.DataFrame): The input DataFrame containing the data for the report.
        values (str): The column name in the DataFrame representing the values for the pie.
        names (str): The column name in the DataFrame representing the names for the pie.
        label (Optional[str], optional): The label for the pi. Defaults to None.
        **kwargs (Optional[dict], optional): Additional keyword arguments for the report. Defaults to None.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        values: str,
        names: str,
        *,
        label: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        Base.__init__(self, label=label)
        self.df = df
        self.values = values
        self.names = names
        self.kwargs = kwargs

        assert values in df.columns, f"{values} not in df"
        assert names in df.columns, f"{names} not in df"

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        if "hole" not in self.kwargs:
            self.kwargs["hole"] = 0.3

        logger.info(f"Pie: {len(self.df)} rows, {values=}, {names=}, {label=}")

    def to_html(self) -> str:
        fig = px.pie(
            self.df,
            values=self.values,
            names=self.names,
            **self.kwargs,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(uniformtext_minsize=10, uniformtext_mode="hide")

        PxBase.apply_common_fig_options(fig)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


##############################


class Scatter(PxBase):
    """Creates interactive scatter plots with optional dimension grouping.

    Scatter plots are ideal for showing relationships between variables and
    identifying patterns, clusters, and outliers.

    Example:
        ```python
        # Basic scatter plot
        Scatter(df, x="x_value", y="y_value")

        # With dimension coloring and marginals
        Scatter(
            df,
            x="sepal_length",
            y="sepal_width",
            dimension="species",
            marginal="histogram",
            label="Iris Dataset"
        )

        # Custom styling
        Scatter(
            df,
            x="price",
            y="sqft",
            dimension="type",
            kwargs={
                "opacity": 0.7,
                "size": "bedrooms",
                "hover_data": ["address"]
            }
        )
        ```

    Args:
        df (pd.DataFrame): The data to plot
        x (str): Column name for x-axis
        y (str): Column name for y-axis
        dimension (Optional[str]): Column for point coloring/grouping. Defaults to None.
        label (Optional[str]): Plot title/caption. Defaults to None.
        marginal (Optional[str]): Add marginal distributions:
            - "histogram": Frequency histograms
            - "violin": Violin plots
            - "box": Box plots
            - "rug": Rug plots
        Defaults to None.
        **kwargs: Additional plotly express scatter options:
            - size: Column name for point sizes
            - hover_data: List of columns to show in tooltips
            - trendline: Add regression line ("ols", "lowess")
            - opacity: Point transparency (0-1)
            - symbol: Column for point shape variation

    Note:
        - Interactive zoom and pan enabled
        - Hover tooltips show x,y values
        - Legend shown when using dimension
        - Supports large datasets with WebGL rendering
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        marginal: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        Base.__init__(self, label=label)
        self.df = df
        self.x = x
        self.y = y
        self.kwargs = kwargs

        assert x in df.columns, f"{x} not in df"
        assert y in df.columns, f"{y} not in df"

        if marginal:
            assert marginal in [
                "histogram",
                "violin",
                "box",
                "rug",
            ], "marginal must be one of ['histogram', 'violin', 'box', 'rug']"
            self.kwargs["marginal_x"] = marginal
            self.kwargs["marginal_y"] = marginal

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["color"] = dimension
            self.kwargs["symbol"] = dimension

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        logger.info(f"Scatter: {len(self.df)} rows, {y=}, {dimension=}, {label=}")

    def to_html(self) -> str:
        """
        Convert the scatter plot to an HTML string.

        Returns:
            str: The HTML representation of the scatter plot.
        """
        fig = px.scatter(
            self.df,
            x=self.x,
            y=self.y,
            **self.kwargs,
        )

        PxBase.apply_common_fig_options(fig)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


##############################


class Box(PxBase):
    """
    Box plot class for creating scatter plots.

    Args:
        df (pd.DataFrame): The input DataFrame.
        y (str, optional): The column name for the y-axis. Defaults to None.
        dimension (str, optional): The column name for the dimension. Defaults to None.
        label (str, optional): The label for the report. Defaults to None.
        **kwargs (dict, optional): Additional keyword arguments.

    Raises:
        AssertionError: If the y column is not present in the DataFrame.
        AssertionError: If the dimension column is not present in the DataFrame (if specified).
    """

    def __init__(
        self,
        df: pd.DataFrame,
        y: Optional[str] = None,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        Base.__init__(self, label=label)
        self.df = df
        self.y = y
        self.kwargs = kwargs

        assert y in df.columns, f"{y} not in df"

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["x"] = dimension
            self.kwargs["color"] = dimension

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        logger.info(f"Box: {len(self.df)} rows, {y=}, {dimension=}, {label=}")

    def to_html(self) -> str:
        """
        Convert the box plot to an HTML string.

        Returns:
        - str: The HTML string representation of the box plot.

        """
        fig = px.box(
            self.df,
            y=self.y,
            **self.kwargs,
        )

        PxBase.apply_common_fig_options(fig)

        fig.update_traces(boxpoints="outliers")

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


##############################


class Histogram(PxBase):
    """
    A class representing a histogram plot.

    Args:
        df (pd.DataFrame): The input DataFrame.
        x (str): The column name to be used for the histogram.
        dimension (Optional[str], optional): The column name to be used for coloring the histogram bars. Defaults to None.
        label (Optional[str], optional): The label for the histogram. Defaults to None.
        kwargs (Optional[dict]): Additional keyword arguments.

    For more information, refer to the Plotly documentation: https://plotly.com/python/histograms/
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        Base.__init__(self, label=label)
        self.df = df
        self.x = x
        self.kwargs = kwargs

        assert x in df.columns, f"{x} not in df"

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["color"] = dimension

        PxBase.apply_common_kwargs(kwargs, label=label)

        logger.info(f"Histogram: {len(self.df)} rows, {x=}, {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        fig = px.histogram(self.df, x=self.x, **self.kwargs)
        fig.update_layout(bargap=0.1)

        PxBase.apply_common_fig_options(fig)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


class Heading(Base):
    """
    Represents a heading in a report.

    Args:
        label (str): The label or text of the heading.
        level (Optional[int]): The level of the heading, ranging from 1 to 5 (inclusive). Defaults to 1.

    Raises:
        AssertionError: If the heading level is not between 1 and 5 (inclusive).
        AssertionError: If no heading label is provided.

    Attributes:
        level (int): The level of the heading.
    """

    def __init__(
        self,
        label: str,
        *,
        level: Optional[int] = 1,
    ):
        Base.__init__(self, label=label)
        assert level >= 1 and level <= 5, (
            f"heading level ({level}) must be between 1 and 5 (inclusive)"
        )
        assert label, "No heading label provided"
        self.level = level
        logger.info(f"Heading: (h{level}): [{label}]")

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Converts the heading to an HTML string.

        Returns:
            str: The HTML representation of the heading.
        """
        return f"<br /><h{self.level}>{self.label}</h{self.level}><br />"


##############################


class Separator(Base):
    """Separator is a container for a horizontal line. It can also take a label.

    Args:
        label (Optional[str], optional): The label to be displayed above the separator. Defaults to None.
    """

    def __init__(self, label: Optional[str] = None):
        Base.__init__(self, label=label)
        logger.info(f"Separator: {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        """Converts the Separator object to its HTML representation.

        Returns:
            str: The HTML representation of the Separator.
        """
        if self.label:
            return f"<br><hr><report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption>"
        else:
            return "<br><hr>"


##############################


class Text(Markdown): ...


##############################


class Select(Base):
    """Select is a container for a group of components that will shown in tabs. It can also take an outer label.

    Args:
        blocks (list[Base]): _description_
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, blocks: list[Base], *, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.blocks = blocks

        for b in self.blocks:
            if not b.label:
                raise ValueError("All blocks must have a label to use in a Select")

        logger.info(
            f"Select: {len(self.blocks)} tabs: {', '.join([c.label for c in self.blocks])}"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        html = (
            f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption>"
            if self.label
            else ""
        )

        # unique ID for select grouping.
        # Ensures no clashes between different selects with the same block.label set
        # self.label may not be unique
        data_table_index = int(uuid4()) % 10000

        # assemble the button bar for the tabs
        html += """<div class="tab">"""
        for i, block in enumerate(self.blocks):
            extra = "defaultOpen" if i == 0 else ""
            html += f"""<button class="tablinks {extra}" onclick="openTab(event, '{block.label}', {data_table_index})" data-table-index={data_table_index}>{block.label}</button>"""
        html += """</div>"""

        # assemble the tab contents
        for block in self.blocks:
            html += f"""<div id="{block.label}" data-table-index={data_table_index} class="tabcontent">"""
            html += block.to_html()
            html += """</div>"""

        return html


##############################


class Accordion(Base):
    """Accordion is a container for a set of text blocks that can be collapsed.

    Args:
        blocks (list[Base]): _description_
        label (Optional[str], optional): _description_. Defaults to None.
        open_first (bool, optional): _description_. Defaults to False.
    """

    def __init__(
        self,
        blocks: list[Base],
        *,
        label: Optional[str] = None,
        open_first: Optional[bool] = False,
    ):
        Base.__init__(self, label=label)
        self.blocks = blocks
        self.open_first = open_first

        for b in self.blocks:
            if not b.label:
                raise ValueError("All blocks must have a label to use in an Accordion")

        logger.info(
            f"Select: {len(self.blocks)} tabs: {', '.join([c.label for c in self.blocks])}"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        html = (
            f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption>"
            if self.label
            else ""
        )

        # assesmble the accordion
        for i, block in enumerate(self.blocks):
            html += f"""<details {" open " if i == 0 and self.open_first else ""} class="accordion">"""
            html += f"""<summary>{block.label}</summary>"""
            html += block.to_html()
            html += """</details>"""

        return html


##############################


class Unformatted(Base):
    """Unformatted is a container for any text that should be displayed verbatim with a non-proportional font.

    Args:
        text (str): any text that should be displayed verbatim with a non-proportional font.
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, text: str, *, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.text = text

    @_strip_whitespace
    def to_html(self) -> str:
        formatted_text = f"<pre><code>{self.text.strip()}</code></pre>"

        if self.label:
            return f"""<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption><div>{formatted_text}</div>"""
        else:
            return f"""<div>{formatted_text}</div>"""


##############################


class Language(Base):
    def __init__(
        self,
        text: str,
        language: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        Base.__init__(self, label=label)
        self.text = text
        self.language = language.lower()
        self.scroll_long_content = scroll_long_content
        logger.info(f"{language}: {len(self.text)} characters, {scroll_long_content=}")

        if not self.language:
            assert self.language, "Language must be specified"
        else:
            assert self.language in [
                "java",
                "python",
                "prolog",
                "shell",
                "sql",
                "yaml",
                "json",
                "plaintext",
            ], f"Language {self.language} not supported"

    @_strip_whitespace
    @abstractmethod
    def to_html(self) -> str:
        formatted_text = f"<pre><code class='language-{self.language} syntax-color'>\n{self.text.strip()}</code></pre>"
        if self.label:
            label_background, label_text_color = _random_color_generator(self.language)
            label_span = f"""
                <span class="code-block-label" style="background-color: {label_background}; color:{label_text_color};">
                    {self.label}
                </span>
            """
        else:
            label_span = ""
        return f"""
                <div class="code-block include_hljs">
                    {label_span}{formatted_text}
                </div>
        """


##############################


class Prolog(Language):
    """Prolog is a container for prolog code. It can also take a label.

    Args:
        code (str): _description_
        scroll_long_content (Optional[bool], optional): _description_. Defaults to False.
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        Language.__init__(
            self, escape(code), "prolog", scroll_long_content=scroll_long_content, label=label
        )


##############################


class Python(Language):
    """Python is a container for python code. It can also take a label.

    Args:
        code (str): _description_
        scroll_long_content (Optional[bool], optional): _description_. Defaults to False.
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        Language.__init__(
            self, escape(code), "python", scroll_long_content=scroll_long_content, label=label
        )


##############################


class Shell(Language):
    """Shell is a container for zsh/csh/sh code. It can also take a label.

    Args:
        code (str): _description_
        scroll_long_content (Optional[bool], optional): _description_. Defaults to False.
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        Language.__init__(
            self, escape(code), "shell", scroll_long_content=scroll_long_content, label=label
        )


# Alias for Shell


class Sh(Shell): ...


class Bash(Shell): ...


##############################


class Java(Language):
    """Java is a container for Java code. It can also take a label.

    Args:
        code (str): _description_
        scroll_long_content (Optional[bool], optional): _description_. Defaults to False.
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        Language.__init__(
            self, escape(code), "java", scroll_long_content=scroll_long_content, label=label
        )


##############################


class Sql(Language):
    """Sql is a container for SQL code. It can also take a label.

    Args:
        code (str): your SQL code
        scroll_long_content (Optional[bool], optional): _description_. Defaults to False.
        prettify (Optional[bool], optional): _description_. Defaults to False for space-efficiency.
        label (Optional[str], optional): _description_. Defaults to None.
    """

    @staticmethod
    def format_sql(sql: str) -> str:
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
        RESERVED_WORDS = ["as"]

        sql = re.sub(r"(?<!['\"]),\s*(?!['\"])", ",\n\t", sql, flags=re.DOTALL)

        for reserved_word in RESERVED_WORDS:
            sql = re.sub(
                rf"(?<!['\"]){reserved_word}(?!['\"])",
                reserved_word.upper(),
                sql,
                flags=re.DOTALL,
            )

        def format_block_statement(matchobj):
            return f"\n{matchobj.group(0).strip()}\n\t".upper()

        for statement in BLOCK_STATEMENTS:
            sql = re.sub(
                rf"(?<!['\"])^|\s+{statement}\s+|$(?!['\"])",
                format_block_statement,  # add newline before each statement, upper case
                sql,
                flags=re.IGNORECASE | re.DOTALL,
            )
        return sql

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        prettify: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        Language.__init__(
            self,
            Sql.format_sql(code) if prettify else code,
            "sql",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


class Yaml(Language):
    """Yaml is a container for yaml. It can also take a label.

    Args:
        data (Union[dict, list]): _description_
        scroll_long_content (Optional[bool], optional): _description_. Defaults to False.
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(
        self,
        data: Union[dict, list],
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        Language.__init__(
            self,
            yaml.dump(data, indent=2, Dumper=yaml.SafeDumper),
            "yaml",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


class Json(Language):
    """Displays JSON data with syntax highlighting and formatting.

    Json provides a clean way to show structured data in reports with proper
    indentation and color coding.

    Example:
        ```python
        # Basic JSON display
        Json({"key": "value", "nested": {"data": [1, 2, 3]}})

        # With scrolling for large content
        Json(
            large_data_dict,
            scroll_long_content=True,
            label="API Response"
        )
        ```

    Args:
        data (Union[dict, list]): JSON-serializable Python object
        scroll_long_content (Optional[bool]): Enable vertical scrolling for long
            content. Defaults to False.
        label (Optional[str]): Block label/title. Defaults to None.

    Features:
        - Proper indentation (2 spaces)
        - Syntax highlighting
        - HTML escaping of string values
        - Optional scrolling container
        - Copy-to-clipboard button

    Note:
        - Automatically handles nested structures
        - Preserves data types in display
        - Safe HTML encoding of content
    """

    def __init__(
        self,
        data: Union[dict, list],
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        class HTMLEscapingEncoder(json.JSONEncoder):
            def encode(self, obj):
                obj = json.loads(super().encode(obj))  # Ensure JSON structure
                if isinstance(obj, dict):
                    obj = {
                        k: html.escape(v) if isinstance(v, str) else v for k, v in obj.items()
                    }
                return super().encode(obj)

        Language.__init__(
            self,
            json.dumps(data, indent=2, cls=HTMLEscapingEncoder),
            "json",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


class Plaintext(Language):
    """Plaintext is a container for plain text that will styled as "code". It can also take a label.

    Args:
        code (str): _description_
        scroll_long_content (Optional[bool], optional): _description_. Defaults to False.
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        Language.__init__(
            self,
            code,
            "plaintext",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


class ReportCreator:
    """A powerful report generation system that creates interactive HTML reports.

    The ReportCreator class is the main entry point for creating reports. It handles:
    - Report configuration and theming
    - Component rendering and layout
    - Asset management and resource handling
    - HTML generation and export

    Example:
        ```python
        # Create a basic report
        with ReportCreator("My Report", author="John Doe") as report:
            view = Block(
                Heading("Sales Analysis"),
                Markdown("Monthly sales performance analysis"),
                Group(
                    Metric("Total Sales", 150000, unit="$"),
                    Metric("Growth", 12.5, unit="%")
                )
            )
            report.save(view, "sales_report.html")
        ```

    Args:
        title (str): The report title that appears at the top of the page
        description (Optional[str]): Markdown-formatted description text. Defaults to None.
        author (Optional[str]): Report author name. Defaults to None.
        logo (Optional[str]): Can be:
            - GitHub username (will use GitHub avatar)
            - URL to image
            - Path to local image file
            - None (generates icon from title)
        theme (Optional[str]): Report theme name. Must be one of the registered plotly themes.
            Defaults to "rc".
        code_theme (Optional[str]): Syntax highlighting theme. Defaults to "github-dark".
        diagram_theme (Optional[str]): Mermaid diagram theme. Options:
            - "default"
            - "neo"
            - "neo-dark"
            - "dark"
            - "neutral"
            - "forest"
            - "base"
        accent_color (Optional[str]): Primary accent color. Defaults to "black".
        footer (Optional[str]): Markdown-formatted footer text. Defaults to None.

    Raises:
        ValueError: If title is empty or invalid theme specified
    """

    def __init__(
        self,
        title: str,
        *,
        description: Optional[str] = None,
        author: Optional[str] = None,
        logo: Optional[str] = None,
        theme: Optional[str] = "rc",
        code_theme: Optional[str] = "github-dark",
        diagram_theme: Optional[str] = "default",
        accent_color: Optional[str] = "black",
        footer: Optional[str] = None,
    ):
        # Add logger initialization
        self.report_id = str(uuid4())
        self.logger = ReportLogger(self.report_id)

        if not title or not isinstance(title, str):
            self.logger.log("ERROR", "Title must be a non-empty string")
            raise ValueError("Title must be a non-empty string")

        self.title = title
        self.description = description
        self.author = author
        self.code_theme = code_theme
        self.diagram_theme = diagram_theme
        self.accent_color = accent_color
        self.footer = footer

        self.logger.log(
            "INFO", f"Initializing report: {self.title}", description=description, author=author
        )

        pio.templates["rc"] = get_rc_theme()

        assert theme in pio.templates, f"Theme {theme} not in {', '.join(pio.templates.keys())}"
        self.logger.log("INFO", f"Using theme: {theme}")

        pio.templates.default = theme

        if logo:
            if logo.startswith("http") or logo.startswith("data:image"):
                self.header_str = f"""<img src="{logo}" style="width: 125px;">"""
            elif os.path.exists(logo):
                self.header_str = f"""<img src="{_convert_filepath_to_datauri(logo)}" style="width: 125px;">"""
            else:
                self.logger.log("INFO", f"Using GitHub avatar for: {logo}")
                self.header_str = f"""<img src="https://avatars.githubusercontent.com/{logo}?s=125" style="width: 125px;">"""
        else:
            match = re.findall(r"[A-Z]", self.title)
            icon_text = "".join(match[:2]) if match else self.title[0]

            icon_color, text_color = self.accent_color, "white"

            width = 150
            cx = width / 2
            cy = width / 2
            r = width / 2
            fs = int(r / 15)

            self.header_str = textwrap.dedent(f"""
                    <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{width}" height="{width}">

                        <style>
                            .icon_text_style {{
                                font-size: {fs}rem;
                                stroke-width: 1px;
                                font-family: sans-serif;
                                font-weight: bold;
                                text-anchor: middle;
                                dominant-baseline: central;
                            }}

                        </style>

                        <circle cx="{cx}" cy="{cy}" r="{r}" fill="{icon_color}" />
                        <text class="icon_text_style" x="50%" y="50%" fill="{text_color}">{icon_text}</text>
                    </svg>
                """)
            self.logger.log("INFO", "Generated default icon from title")

    def __enter__(self):
        """Save the original color schema"""
        self.logger.log("INFO", "Entering report context")
        self.default_colors = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
        mpl.rcParams["axes.prop_cycle"] = cycler("color", report_creator_colors)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Restore the original color schema"""
        self.logger.log("INFO", "Exiting report context")
        mpl.rcParams["axes.prop_cycle"] = cycler("color", self.default_colors)

        # Log any errors that occurred
        if exc_type:
            self.logger.log("ERROR", f"Error during report generation: {exc_value}")

    @_time_it
    def save(self, view: Base, path: str, prettify_html: Optional[bool] = True) -> None:
        """
        Save the report to a file.

        Args:
            view (Base): The view object representing the report content.
            path (str): The path to save the report file.
            prettify_html (bool, optional): Whether to prettify the generated HTML. Defaults to True.

        Raises:
            ValueError: If the view object is not an instance of Block or Group.

        """
        self.logger.log("INFO", f"Starting report save to: {path}")

        if not isinstance(view, (Block, Group)):
            error_msg = (
                f"Expected view to be either Block or Group object, got {type(view)} instead"
            )
            self.logger.log("ERROR", error_msg)
            raise ValueError(error_msg)

        try:
            body = view.to_html()
            self.logger.log("INFO", "Successfully generated HTML body")
        except Exception as e:
            self.logger.log("ERROR", f"Failed to generate HTML: {str(e)}")
            body = f"""<pre>{traceback.format_exc()}</pre>"""

        file_loader = FileSystemLoader(
            f"{os.path.dirname(os.path.abspath(__file__))}/templates"
        )
        template = Environment(loader=file_loader).get_template("default.html")

        include_plotly = "plotly-graph-div" in body
        include_datatable = "include_datatable" in body
        include_mermaid = "include_mermaid" in body
        include_hljs = "include_hljs" in body

        self.logger.log(
            "INFO",
            "Detected components",
            plotly=include_plotly,
            datatable=include_datatable,
            mermaid=include_mermaid,
            hljs=include_hljs,
        )

        try:
            html = template.render(
                title=self.title or "Report",
                description=_gfm_markdown_to_html(self.description) if self.description else "",
                author=self.author.strip() if self.author else "",
                body=body,
                header_logo=self.header_str,
                include_plotly=include_plotly,
                include_datatable=include_datatable,
                include_mermaid=include_mermaid,
                include_hljs=include_hljs,
                code_theme=self.code_theme,
                diagram_theme=self.diagram_theme,
                accent_color=self.accent_color,
                footer=_gfm_markdown_to_html(self.footer).strip() if self.footer else None,
            )

            if prettify_html:
                try:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(html, "html.parser")
                    html = soup.prettify(formatter="minimal")
                    self.logger.log("INFO", "Applied HTML prettification")
                except ImportError:
                    self.logger.log(
                        "WARNING", "BeautifulSoup not installed, skipping HTML prettification"
                    )

            with open(path, "w", encoding="utf-8") as f:
                f.write(html)

            file_size = len(html)
            self.logger.log(
                "INFO",
                "Successfully saved report",
                path=path,
                size=humanize.naturalsize(file_size, binary=True),
            )

            # Log summary statistics
            summary = self.logger.get_summary()
            self.logger.log(
                "INFO",
                "Report generation complete",
                duration=str(summary["duration"]),
                errors=summary["error_count"],
                warnings=summary["warning_count"],
            )

        except Exception as e:
            self.logger.log("ERROR", f"Failed to save report: {str(e)}")
            raise


class ReportLogger:
    """Enhanced logging for report generation"""

    def __init__(self, report_id: str):
        self.report_id = report_id
        self.start_time = datetime.now()
        self.logs: list[dict] = []

    def log(self, level: str, message: str, **kwargs) -> None:
        self.logs.append(
            {
                "timestamp": datetime.now(),
                "level": level,
                "message": message,
                "report_id": self.report_id,
                **kwargs,
            }
        )

    def get_summary(self) -> dict:
        """Get report generation summary"""
        return {
            "report_id": self.report_id,
            "duration": datetime.now() - self.start_time,
            "error_count": sum(1 for log in self.logs if log["level"] == "ERROR"),
            "warning_count": sum(1 for log in self.logs if log["level"] == "WARNING"),
        }
