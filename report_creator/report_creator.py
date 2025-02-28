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
    """
    Abstract Base Class for report components.

    This class serves as the foundation for all visual elements within a report.
    It defines the common interface and behavior expected of all report components.
    Each concrete component, such as a Block, Group, Metric, or Chart, should inherit
    from this class.


    """

    def __init__(self, label: Optional[str] = None):
        self.label = label

    @abstractmethod
    def to_html(self) -> str:
        """Each component that derives from Base must implement this method"""


##############################


class Block(Base):
    """
    A container for vertically stacking report components.

    The `Block` component is fundamental for structuring a report's layout.
    It arranges its child components in a single, vertical column,
    rendering them sequentially from top to bottom. This allows for
    the creation of visually organized sections within a report.

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
    """
    A container for horizontally arranging report components.

    The `Group` component is used to arrange multiple report
    components side-by-side within a horizontal row. It acts as a
    wrapper that renders its child components next to each other,
    allowing you to create layouts with columns or multiple elements
    on the same horizontal line.


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
    """
    A container for creating collapsible sections in a report.

    The `Collapse` component allows you to group a set of report
    components under a single, clickable header. When the header
    is clicked, the content within the `Collapse` is either revealed
    or hidden, allowing for a more compact and organized presentation
    of information. This is useful for hiding less important or
    detailed content that the user may choose to view on demand.

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
    """
    A container for embedding and rendering external content or interactive widgets.

    The `Widget` component is designed to display objects that can render themselves
    as HTML, such as Pandas DataFrames, Matplotlib figures, and Plotly figures.
    It acts as a bridge between these external objects and the report, enabling
    their seamless integration.

    Args:
        widget (Any): The external widget or object to be embedded within the report.
        label (Optional[str], optional): An optional label or caption for the widget.
            If provided, it will be displayed above the widget in the rendered report.
            Defaults to None.

    Raises:
        ValueError: If the provided widget does not have an `_repr_html_` method.

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

        if not hasattr(self.widget, "_repr_html_"):
            raise ValueError("Widget does not have a _repr_html_ method")

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
    """
    Displays a Pandas DataFrame or a list of dictionaries as a formatted HTML table.

    The `Table` component provides a straightforward way to render tabular data within a report.
    It supports both Pandas DataFrames and lists of dictionaries as input and
    offers basic styling and formatting options.

    Args:
        data (Union[pd.DataFrame, list[dict]]): The data to be displayed in the table.
            This can be either a Pandas DataFrame or a list of dictionaries, where each
            dictionary represents a row in the table.
        label (Optional[str], optional): An optional label or caption for the table.
            If provided, it will be displayed above the table. Defaults to None.
        index (bool, optional): Whether to display the DataFrame index column in the
            rendered table. If False, the index will be hidden. Defaults to False.
        float_precision (int, optional): The number of decimal places to display for
            floating-point numbers in the table. Defaults to 3.

    Raises:
        ValueError: If the `data` argument is not a Pandas DataFrame or a list of dictionaries.


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
        logger.info(f"Table: {len(df)} rows, {len(df.columns)} columns")
        Widget.__init__(self, s.format(escape="html", precision=float_precision), label=label)


##############################


class DataTable(Base):
    """
    Displays a sortable and searchable table from a Pandas DataFrame or a list of dictionaries.

    The `DataTable` component renders tabular data in an interactive HTML table
    with built-in search and sort capabilities. It provides a user-friendly way
    to explore and analyze datasets directly within a report.

    Args:
        data (Union[pd.DataFrame, list[dict]]): The data to be displayed in the table.
            This can be either a Pandas DataFrame or a list of dictionaries, where each
            dictionary represents a row in the table.
        label (Optional[str], optional): An optional label or caption for the table.
            If provided, it will be used as the table's caption. Defaults to None.
        wrap_text (bool, optional): If True, text within table cells will wrap to
            fit the cell width. If False, text will not wrap and may be truncated.
            Defaults to True.
        index (bool, optional): If True, the DataFrame index will be displayed as
            the first column in the table. If False, the index will be hidden.
            Defaults to False.
        max_rows (int, optional): The maximum number of rows to display in the table.
            If set to -1, all rows will be displayed. Defaults to -1.
        float_precision (int, optional): The number of decimal places to display for
            floating-point numbers in the table. Defaults to 3.

    Raises:
        ValueError: If the `data` argument is not a Pandas DataFrame or a list of dictionaries.

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
    """
    Embeds raw HTML content, optionally with inline CSS styling, into the report.

    The `Html` component provides a way to include arbitrary HTML markup directly
    within a report. This is useful for embedding custom web elements, adding
    specialized formatting, or integrating content from external sources that
    provide HTML snippets.

    Args:
        html (str): The raw HTML content to be embedded. This can include any
            valid HTML tags and content.
        css (Optional[str], optional): Optional inline CSS styles to be applied
            to the HTML content. If provided, these styles will be wrapped in
            `<style>` tags and inserted before the HTML content. Defaults to None.
        label (Optional[str], optional): An optional label for the HTML component.
            If provided, a caption with a linkable anchor will be displayed above
            the HTML content in the rendered report. Defaults to None.
        bordered (Optional[bool], optional): If True, the HTML content will be
            rendered within a bordered container. Defaults to False.

    Raises:
        ValueError: If the provided HTML content contains unclosed tags.


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
    """
    Renders a diagram using Mermaid.js syntax within the report.

    The `Diagram` component allows you to create and embed diagrams
    directly within your report using the Mermaid.js library. Mermaid
    allows you to define diagrams using a simple text-based syntax,
    which is then rendered visually by the library.

    This component is highly versatile, enabling the creation of various
    diagram types, including flowcharts, sequence diagrams, Gantt charts,
    class diagrams, state diagrams, and more. For detailed syntax
    examples, refer to the Mermaid.js documentation: https://mermaid.js.org/syntax/examples.html.
    ChatGPT is also able to create the diagrams for you simply by describing them in text.

    Args:
        src (str): The Mermaid.js source code defining the diagram.
            This is the text that describes the diagram's structure
            and elements using Mermaid's syntax.
        pan_and_zoom (Optional[bool], optional): Enables panning and zooming
            functionality for the diagram in the rendered report.
            Users can pan by dragging the mouse and zoom using shift + mouse wheel.
            Defaults to True.
        extra_css (Optional[str], optional): Additional inline CSS styles to be
            applied to the diagram. This allows for custom styling beyond
            Mermaid's default appearance. Defaults to None.
        label (Optional[str], optional): An optional label or caption for the
            diagram. If provided, a caption with a linkable anchor will be
            displayed above the diagram. Defaults to None.


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
    """
    Embeds an image within the report, optionally linking it to an external URL.

    The `Image` component allows you to include images in your report,
    either by referencing an external URL or by embedding a base64-encoded
    image directly within the HTML. You can also make the image clickable,
    linking it to another webpage.

    Args:
        src (str): The source of the image. This can be either:
            A URL pointing to an image on the web, a local file path,
            or a base64-encoded image string.
        link_to (Optional[str], optional): An optional URL that the image
            will link to when clicked. If not provided, the image will
            not be clickable. Defaults to None.
        label (Optional[str], optional): An optional label or caption for
            the image. If provided, it will be displayed below the image
            and can be used as a linkable anchor within the report.
            Defaults to None.
        extra_css (Optional[str], optional): Additional inline CSS styles
            to be applied to the image element. This allows for custom
            styling beyond the basic options. Defaults to None.
        rounded (bool, optional): If True, the image will be displayed with
            rounded corners. Defaults to True.
        convert_to_base64 (bool, optional): If True, the `src` will be
            treated as a URL. The image at that URL will be fetched,
            and its content will be embedded in the report as a
            base64-encoded image. This ensures that the image is
            always available, even if the original URL becomes inaccessible.
            Defaults to False.

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
        self.link_to = link_to
        self.extra_css = extra_css or ""
        self.rounded_css = "border-radius: 0.75rem;" if rounded else ""

        if src.startswith("data:image"):
            # Base64 image
            self.src = src
        elif os.path.exists(src):
            # Local file
            self.src = _convert_filepath_to_datauri(src)
        elif convert_to_base64:
            # URL that should be fetched and rendered as base64
            self.src = _convert_imgurl_to_datauri(src)
        else:
            # URL (external image)
            self.src = src

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
    """
    Embeds Markdown-formatted text within the report, with optional styling and borders.

    The `Markdown` component allows you to include rich text content in your report
    using Markdown syntax. It supports Github Falvored Markdown formatting and provides
    options for adding custom CSS styles and borders.

    Args:
        text (str): The Markdown-formatted text to be rendered. This string will be
            processed and displayed as formatted text in the report.
        label (Optional[str], optional): An optional label or heading for the
            Markdown section. If provided, a caption with a linkable anchor will
            be displayed above the Markdown content. Defaults to None.
        extra_css (Optional[str], optional): Additional inline CSS styles to be
            applied to the Markdown content. This allows for custom styling
            beyond the basic Markdown rendering. Defaults to None.
        bordered (bool, optional): If True, the Markdown content will be
            rendered within a bordered container, providing a visual
            separation from surrounding content. Defaults to False.
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
    """
    Displays a bar chart using Plotly Express.

    The `Bar` component renders a bar chart from a Pandas DataFrame.
    It supports grouping by a categorical dimension and provides
    options for customizing the chart's appearance.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `x` and `y` arguments.
        x (str): The name of the column in the DataFrame to be plotted on
            the x-axis. This column typically represents the categories
            or discrete values for the bars.
        y (str): The name of the column in the DataFrame to be plotted on
            the y-axis. This column typically represents the numerical
            values associated with each category.
        dimension (Optional[str], optional): The name of an optional column
            in the DataFrame to be used as a categorical dimension for
            grouping the bars. If provided, the bars will be colored
            according to the unique values in this column. Defaults to None.
        label (Optional[str], optional): An optional label or title for the
            bar chart. Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to
            the `plotly.express.bar` function. This allows for fine-grained
            control over the chart's appearance and behavior.

    Raises:
        AssertionError: If the specified `x` column is not found in the DataFrame.
        AssertionError: If the specified `y` column is not found in the DataFrame.
        AssertionError: If the specified `dimension` column is not found in the DataFrame, when provided.

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
    """
    Displays a line chart using Plotly Express.

    The `Line` component renders a line chart from a Pandas DataFrame,
    allowing you to visualize trends and relationships between variables
    over a continuous or ordered dimension. It supports plotting multiple
    lines on the same chart and provides options for customizing the
    chart's appearance.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `x` and `y` arguments.
        x (str): The name of the column in the DataFrame to be plotted on
            the x-axis. This column typically represents a continuous or
            ordered dimension (e.g., time, sequence).
        y (Union[str, list[str]]): The name(s) of the column(s) in the
            DataFrame to be plotted on the y-axis. This can be a single
            column name (for a single line) or a list of column names
            (for multiple lines).
        dimension (Optional[str], optional): The name of an optional column
            in the DataFrame to be used as a categorical dimension. If
            provided, the lines will be differentiated by color and symbol
            according to the unique values in this column. Defaults to None.
        label (Optional[str], optional): An optional label or title for the
            line chart. Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.line` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `line_shape`, `markers`, etc.

    Raises:
        AssertionError: If the specified `x` column is not found in the DataFrame.
        AssertionError: If any of the specified `y` column(s) are not found in the DataFrame.
        AssertionError: If the specified `dimension` column is not found in the DataFrame, when provided.
        ValueError: If `y` is not a string or a list of strings.

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
    """
    Displays a pie chart using Plotly Express.

    The `Pie` component renders a pie chart from a Pandas DataFrame,
    allowing you to visualize the proportions of different categories
    within a dataset. It provides options for customizing the chart's
    appearance, including the size of the hole in the center (for creating
    donut charts).

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `values` and `names` arguments.
        values (str): The name of the column in the DataFrame representing
            the numerical values that determine the size of each pie slice.
        names (str): The name of the column in the DataFrame representing
            the categories or labels for each pie slice.
        label (Optional[str], optional): An optional label or title for the
            pie chart. Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.pie` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `hole` (for creating donut charts), `color_discrete_sequence`,
            etc.

    Raises:
        AssertionError: If the specified `values` column is not found in the DataFrame.
        AssertionError: If the specified `names` column is not found in the DataFrame.

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


class Radar(PxBase):
    """
    Displays a radar chart using Plotly Express.

    The `Radar` component renders a radar chart from a Pandas DataFrame.
    Radar charts are useful for visualizing multivariate data and comparing
    multiple quantitative variables across different categories or entities.

    Example:

    +-----------------+-------+-----------+-------+---------------+----------+
    |                 | MMLU  | HumanEval | GSM8K | ARC Challenge | BigBench |
    +=================+=======+===========+=======+===============+==========+
    | Llama 3.1 405B  | 78.2  | 75.1      | 86    | 84.5          | 68       |
    +-----------------+-------+-----------+-------+---------------+----------+
    | Llama 3.2 405B  | 78.5  | 75.3      | 86.2  | 84.8          | 68.3     |
    +-----------------+-------+-----------+-------+---------------+----------+
    | Llama 3.3 405B  | 78.8  | 75.5      | 86.4  | 85.1          | 68.6     |
    +-----------------+-------+-----------+-------+---------------+----------+
    | Llama 3.4 405B  | 79.1  | 75.7      | 86.6  | 85.4          | 68.9     |
    +-----------------+-------+-----------+-------+---------------+----------+

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `r` (values) and `theta` (categories) arguments.
        label (Optional[str], optional): An optional label or title for the
            radar chart. Defaults to None.
        lock_minimum_to_zero (Optional[bool], optional): If True, the minimum
            value of the radar chart's radial axis will be locked to zero,
            ensuring that the chart starts from zero. If False, the minimum
            value will be determined by the minimum value in the DataFrame.
            Defaults to False.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.line_polar` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `line_close` (to close the polygon), `color_discrete_sequence`,
            etc.

    Raises:
        AssertionError: If the specified `r` column is not found in the DataFrame.
        AssertionError: If the specified `theta` column is not found in the DataFrame.
        AssertionError: If the specified `dimension` column is not found in the DataFrame, when provided.

    """

    def __init__(
        self,
        df: pd.DataFrame,
        *,
        label: Optional[str] = None,
        lock_minimum_to_zero: Optional[bool] = False,
        filled: Optional[bool] = False,
        **kwargs: Optional[dict],
    ):
        Base.__init__(self, label=label)
        assert df.index is not None, "DataFrame has no index"
        assert len(df.index) > 0, "DataFrame has no index or is empty"
        assert df.index.is_unique and not df.index.hasnans, "DataFrame index is invalid"
        self.df = df
        self.filled = filled

        self.min_value = 0 if lock_minimum_to_zero else df.min().min()
        self.max_value = df.max().max()
        self.kwargs = kwargs

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        logger.info(
            f"Radar: {len(self.df)} rows, (range: {self.min_value} .. {self.max_value}) {label=}"
        )

    def to_html(self):
        fig = go.Figure()

        theta = self.df.columns.tolist()
        theta += theta[:1]  # Ensure the radar chart is closed

        for index, row in self.df.iterrows():
            r = row.values.tolist()
            r += r[:1]  # Ensure that the first value of r is repeated to close the loop

            fig.add_trace(
                go.Scatterpolar(
                    r=r,
                    theta=theta,
                    fill="toself" if self.filled else None,
                    name=index,
                )
            )

        PxBase.apply_common_fig_options(fig)

        fig.update_layout(
            polar={
                "radialaxis": {
                    "visible": True,
                    "range": [
                        self.min_value,
                        self.max_value,
                    ],
                }
            },
            height=600,
        )

        if self.label:
            fig.update_layout(title=self.label)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


##############################


class Scatter(PxBase):
    """
    Displays a scatter plot using Plotly Express.

    The `Scatter` component renders a scatter plot from a Pandas DataFrame,
    allowing you to visualize the relationship between two numerical variables.
    It supports adding a categorical dimension for color-coding or sizing
    the data points, enhancing the visualization of patterns within the data.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `x` and `y` arguments.
        x (str): The name of the column in the DataFrame to be plotted on
            the x-axis. This column typically represents a numerical variable.
        y (str): The name of the column in the DataFrame to be plotted on
            the y-axis. This column typically represents a numerical variable.
        dimension (Optional[str], optional): The name of an optional column
            in the DataFrame to be used as a categorical dimension for
            color-coding or sizing the data points. If provided, the points
            will be colored or sized according to the unique values in this
            column. Defaults to None.
        label (Optional[str], optional): An optional label or title for the
            scatter plot. Defaults to None.
        marginal (Optional[str], optional): An optional argument to specify
            the type of marginal plots to display along the x and y axes.
            This can be one of 'histogram', 'violin', 'box', or 'rug'.
            Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.scatter` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `trendline`, `symbol`, etc.

    Raises:
        AssertionError: If the specified `x` column is not found in the DataFrame.
        AssertionError: If the specified `y` column is not found in the DataFrame.
        AssertionError: If the specified `color` column is not found in the DataFrame, when provided.
        AssertionError: If the specified `size` column is not found in the DataFrame, when provided.

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
    Displays a box plot using Plotly Express.

    The `Box` component renders a box plot from a Pandas DataFrame,
    allowing you to visualize the distribution of data across different
    categories or groups. Box plots are useful for showing the median,
    quartiles, and potential outliers within each group.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `x` and `y` arguments.
        y (str): The name of the column in the DataFrame to be plotted on
            the y-axis. This column typically represents the numerical
            variable whose distribution is being visualized.
        dimension (Optional[str], optional): The name of an optional column
            in the DataFrame to be used as a categorical dimension for
            grouping the box plots. If provided, the box plots will be
            separated according to the unique values in this column.
            Defaults to None.
        label (Optional[str], optional): An optional label or title for the
            box plot. Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.box` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `notched` boxes, `orientation` etc.

    Raises:
        AssertionError: If the specified `x` column is not found in the DataFrame.
        AssertionError: If the specified `y` column is not found in the DataFrame.
        AssertionError: If the specified `color` column is not found in the DataFrame, when provided.


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
            str: The HTML representation of the box plot.

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
    Displays a histogram using Plotly Express.

    The `Histogram` component renders a histogram from a Pandas DataFrame,
    allowing you to visualize the distribution of a numerical variable.
    Histograms are useful for understanding the frequency and range of
    values within a dataset.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the column specified by
            the `x` argument.
        x (str): The name of the column in the DataFrame to be plotted on
            the x-axis. This column represents the numerical variable
            whose distribution is being visualized.
        dimension (Optional[str], optional): The name of an optional column
            in the DataFrame to be used as a categorical dimension for
            splitting the histogram. If provided, multiple histograms will
            be created, one for each unique value of the column. Defaults to None.
        label (Optional[str], optional): An optional label or title for the
            histogram. Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.histogram` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `barmode`, `histnorm`, etc.

    Raises:
        AssertionError: If the specified `x` column is not found in the DataFrame.
        AssertionError: If the specified `color` column is not found in the DataFrame, when provided.

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
    Displays a large heading within the report.

    The `Heading` component is used to create visually distinct
    headings or titles within a report. It provides a way to
    structure content and create clear sections.

    Args:
        text (str): The text content of the heading. This will be
            displayed as a large heading within the report.
        level (int, optional): The HTML heading level to use (h1-h6).
            Lower numbers are larger and more prominent. Defaults to 1 (h1).
        label (Optional[str], optional): An optional label for the
            heading. If provided, a caption with a linkable anchor
            will be generated above the heading. Defaults to None.

    Raises:
        ValueError: If the specified `level` is not between 1 and 6.

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
    """
    Inserts a visual separator (horizontal rule) into the report.

    The `Separator` component provides a way to create clear visual
    breaks between sections of a report. It renders as a horizontal
    line, making it easy to distinguish different parts of the content.

    Args:
        label (Optional[str], optional): An optional label for the separator.
            If provided, a caption with a linkable anchor will be generated
            above the separator line. This can be used for internal
            referencing or to provide a brief description of the break.
            Defaults to None.

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
    """
    Creates a dropdown select element for user interaction within the report.

    The `Select` component allows you to include a dropdown list within your report,
    enabling users to select a single option from a predefined set of choices.
    This can be useful for filtering data, choosing between different views,
    or otherwise controlling the report's behavior.

    Args:
        blocks (list[Base]): A list of `Base` components to be displayed
            within the dropdown. Each component will be associated with
            a separate option in the dropdown list. When the user selects
            an option, the corresponding component will be displayed in
            the report.
        label (Optional[str], optional): An optional label or description
            for the select element. If provided, this label will be displayed
            above the dropdown, helping to explain its purpose to the user.
            Defaults to None.

    Raises:
        ValueError: If the `default_value` is provided but is not present in the `options`.

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
    """
    Creates an accordion element for organizing and collapsing content sections within a report.

    The `Accordion` component allows you to group multiple `Collapse` components
    into a single, vertically stacked accordion. Each `Collapse` acts as an
    expandable/collapsible panel within the accordion. Only one panel can be
    expanded at a time, providing a compact and organized way to present
    multiple sections of content.

    Args:
        blocks (list[Base]): A list of `Base` components to be displayed
            within the accordion. Each component will be associated with
            a separate collapsible panel. When the user expands a panel,
            the corresponding component will be displayed in the report.
        label (Optional[str], optional): An optional label or heading for
            the entire accordion. If provided, a caption with a linkable
            anchor will be generated above the accordion. Defaults to None.

    Raises:
        ValueError: If any of the components do not have a label.

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
    """
    Displays data as text without any specific formatting or structure.

    The `Unformatted` component renders raw text or data directly within
    the report without applying any special HTML formatting or styling.
    This is useful for displaying data that is not intended to be part
    of the main content flow, such as debug output, code snippets, or
    raw data dumps.

    Args:
        text (str): The raw text or data to be displayed as-is within
            the report. This can be any string or data type that you
            want to present without modification.
        label (Optional[str], optional): An optional label for the
            unformatted data. If provided, a caption with a linkable
            anchor will be displayed above the data. Defaults to None.

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
    """
    Base class for components that display code or text in a specific programming language.
    """

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
    """
    Displays the code within the report.

    The `Prolog` component allows you to add Prolog code that will be inserted
    into the report with code formatting applied.

    Args:
        code (str): The Prolog code or text to be displayed.
        label (Optional[str], optional): An optional label for the
            prolog. This label does not appear in the rendered
            report but can be helpful for internal identification
            or debugging purposes. Defaults to None.

    Attributes:
        html (str): The raw HTML content to be inserted.
        label (Optional[str]): The optional label of the prolog.

    Methods:
        to_html() -> str: Generates the HTML representation of the prolog.
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
    """
    Displays the code within the report.

    The `Python` component allows you to add Python code that will be inserted
    into the report with code formatting applied.

    Args:
        code (str): The Prolog code or text to be displayed.
        label (Optional[str], optional): An optional label for the
            prolog. This label does not appear in the rendered
            report but can be helpful for internal identification
            or debugging purposes. Defaults to None.
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
    """
    Displays the code within the report.

    The `Shell` component allows you to add `sh` code that will be inserted
    into the report with code formatting applied.

    Args:
        code (str): The Shell code or text to be displayed.
        label (Optional[str], optional): An optional label for the
            prolog. This label does not appear in the rendered
            report but can be helpful for internal identification
            or debugging purposes. Defaults to None.
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
    """
    Displays the code within the report.

    The `Java` component allows you to add Java code that will be inserted
    into the report with code formatting applied.

    Args:
        code (str): The Prolog code or text to be displayed.
        label (Optional[str], optional): An optional label for the
            prolog. This label does not appear in the rendered
            report but can be helpful for internal identification
            or debugging purposes. Defaults to None.
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
    """
    Displays the code within the report.

    The `Sql` component allows you to add SQL code that will be inserted
    into the report with code formatting applied.

    Args:
        code (str): The SQL query to be rendered
        scroll_long_content (Optional[bool], optional): If True, and the output is long,
            the output will be rendered within a scrollable element. If false it will
            render in place, which may make the report very long. This can be used to
            help manage the length of the report. Defaults to False.
        prettify (Optional[bool], optional): If True, the SQL query will be formatted
            before execution. Defaults to False.
        label (Optional[str], optional): An optional label for the SQL query
            output. If provided, a caption with a linkable anchor will be
            displayed above the output. Defaults to None.

    Raises:
        Exception: If any error occurs during database connection or query execution.

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
    """
    Displays formatted YAML content within the report.

    The `Yaml` component is designed to embed YAML-formatted data
    directly into the report, presenting it in a structured and
    human-readable way. It's useful for displaying configuration files,
    data structures, or any other information that is naturally
    represented in YAML format.

    Args:
        data (Union[dict, list, str]): The YAML data to be displayed.
            This can be either a Python dictionary (which will be
            converted to YAML), a list, or a string containing valid
            YAML content.
        scroll_long_content (Optional[bool], optional): If True, and the output is long,
            the output will be rendered within a scrollable element. If false it will
            render in place, which may make the report very long. This can be used to
            help manage the length of the report. Defaults to False.
        label (Optional[str], optional): An optional label or heading
            for the YAML content. If provided, a caption with a linkable
            anchor will be displayed above the YAML data.
            Defaults to None.

    Raises:
        ValueError: If the data type is not valid for the Yaml component.
        yaml.YAMLError: If the provided YAML data is invalid or cannot be parsed.
    """

    def __init__(
        self,
        data: Union[str, dict, list],
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        if isinstance(data, (dict, list)):
            content = yaml.dump(data, indent=2, Dumper=yaml.SafeDumper)
        elif isinstance(data, str):
            content = yaml.dump(
                yaml.load(data, Loader=yaml.SafeLoader), indent=2, Dumper=yaml.SafeDumper
            )
        else:
            raise ValueError("Invalid data type for Yaml component")

        Language.__init__(
            self,
            content,
            "yaml",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


class Json(Language):
    """
    Displays formatted JSON content within the report.

    The `Json` component is designed to embed JSON-formatted data
    directly into the report, presenting it in a structured and
    human-readable way. It's useful for displaying configuration data,
    API responses, or any other information that is naturally
    represented in JSON format.

    Args:
        data (Union[dict, list, str]): The JSON data to be displayed.
            This can be either a Python dictionary (which will be
            converted to JSON) or a string containing valid JSON content.
        scroll_long_content (bool, optional): If True and the content is long, it will be
            rendered within a scrollable element. If false it will
            render in place, which may make the report very long. This can be used to help
            manage the length of the report. Defaults to False.
        label (Optional[str], optional): An optional label or heading
            for the JSON content. If provided, a caption with a linkable
            anchor will be displayed above the JSON data.
            Defaults to None.


    Methods:
        to_html() -> str: Generates the HTML representation of the formatted JSON content.
    """

    def __init__(
        self,
        data: Union[dict, list, str],
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

        if isinstance(data, (dict, list)):
            content = json.dumps(data, indent=2, cls=HTMLEscapingEncoder)
        elif isinstance(data, str):
            content = json.dumps(json.loads(data), indent=2, cls=HTMLEscapingEncoder)
        else:
            raise ValueError("Invalid data type for JSON component")

        Language.__init__(
            self,
            content,
            "json",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


class Plaintext(Language):
    """
    Displays text content with minimal formatting within the report.

    The `Plaintext` component is used to embed text content into the
    report with basic, pre-defined styling. Unlike the `Markdown`
    component, it does not support Markdown formatting, but it does
    provide a simple way to display blocks of text in a consistent
    and readable way.

    Args:
        text (str): The text content to be displayed. This should be a
            string containing the text you want to include in the report.
        scroll_long_content (bool, optional): If True and the content is long, it will be
            rendered within a scrollable element. If false it will
            render in place, which may make the report very long. This can be used to help
            manage the length of the report. Defaults to False.
        label (Optional[str], optional): An optional label or heading
            for the plaintext content. If provided, a caption with a
            linkable anchor will be displayed above the text.
            Defaults to None.

    """

    def __init__(
        self,
        text: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        Language.__init__(
            self,
            text,
            "plaintext",
            scroll_long_content=scroll_long_content,
            label=label,
        )


##############################


class ReportCreator:
    """
    Generates interactive HTML reports from structured Python data.

    The `ReportCreator` class provides a streamlined interface for constructing
    and rendering comprehensive, visually appealing reports. It supports a wide
    range of components, including text, metrics, tables, charts, and diagrams,
    all customizable through a declarative API.

    Key Features:

    - **Modular Design:** Build reports using a hierarchy of components
      (`Block`, `Group`, `Collapse`, etc.) for clear organization.
    - **Data Visualization:** Easily integrate various chart types
      (`Bar`, `Line`, `Pie`, `Radar`, `Scatter`) powered by Plotly Express.
    - **Tabular Data:** Display and interact with tables using `Table` and
      `DataTable` components.
    - **Markdown & HTML Support:** Incorporate formatted text and raw HTML for
      flexible content rendering.
    - **Diagrams:** Embed `Diagram` components defined using Mermaid.js syntax.
    - **Images:** Add images with captions and optional links using the `Image` component.
    - **Customizable Styling:** Fine-tune the appearance of reports using themes, CSS, and component-specific options.
    - **Interactive Elements:** Includes interactive components like collapsible sections and sortable tables.
    - **Programmatic Report Generation:**  Construct reports entirely through Python code, making it ideal for automated workflows.
    - **Data URI conversion:** Convert local images or urls to datauri for embedded reports.

    Usage:

    1.  Instantiate `ReportCreator` with a report title.
    2.  Assemble the report layout by adding components (e.g., `Block`, `Group`)
        containing other components (e.g., `Metric`, `Chart`, `Table`).
    3.  Generate the HTML report using the `to_html()` method.
    4.  Save the HTML to a file or display it in a web browser.

    Example::

        from report_creator import ReportCreator, Metric, Block

        report = ReportCreator("My Awesome Report")
        report.add_component(Block(Metric("Revenue", 10000, unit="$"),
                                Metric("Customers", 500)))
        html_report = report.to_html()

        with open("my_report.html", "w") as f:
            f.write(html_report)


    Args:
        title (str): The title of the report.
        description (str, optional): The description of the report (markdown is ok). Defaults to None.
        author (str, optional): The author of the report. Defaults to None.
        logo (str, optional): A GitHub username to use as the report icon, a url/filepath to an image, or None. Defaults to None,
        which will use an autogenerated icon based on the title.
        theme (str, optional): The theme to use for the report. Defaults to "rc".
        diagram_theme (str, optional): The mermaid theme (https://mermaid.js.org/config/theming.html#available-themes) to use Defaults to "default", options: "neo", "neo-dark", "dark", "neutral", "forest", & "base".
        accent_color (str, optional): The accent color for the report. Defaults to "black".
        footer (str, optional): The footer text for the report (markdown is ok). Defaults to None.
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
        self.title = title
        self.description = description
        self.author = author
        self.code_theme = code_theme
        self.diagram_theme = diagram_theme
        self.accent_color = accent_color
        self.footer = footer

        logger.info(f"ReportCreator: {self.title=} {self.description=}")

        pio.templates["rc"] = get_rc_theme()

        assert theme in pio.templates, f"Theme {theme} not in {', '.join(pio.templates.keys())}"

        pio.templates.default = theme

        if logo:
            if logo.startswith("http") or logo.startswith("data:image"):
                self.header_str = f"""<img src="{logo}" style="width: 125px;">"""
            elif os.path.exists(logo):
                self.header_str = f"""<img src="{_convert_filepath_to_datauri(logo)}" style="width: 125px;">"""
            else:
                logger.info(f"GitHub: {logo}")
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

    def __enter__(self):
        """Save the original color schema"""
        self.default_colors = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
        mpl.rcParams["axes.prop_cycle"] = cycler("color", report_creator_colors)

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Restore the original color schema"""
        mpl.rcParams["axes.prop_cycle"] = cycler("color", self.default_colors)

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
        if not isinstance(view, (Block, Group)):
            raise ValueError(
                f"Expected view to be either Block or Group object, got {type(view)} instead"
            )

        logger.info(f"Saving report to {path}")

        try:
            body = view.to_html()
        except ValueError:
            body = f"""<pre>{traceback.format_exc()}</pre>"""

        file_loader = FileSystemLoader(
            f"{os.path.dirname(os.path.abspath(__file__))}/templates"
        )
        template = Environment(loader=file_loader).get_template("default.html")

        include_plotly = "plotly-graph-div" in body
        include_datatable = "include_datatable" in body
        include_mermaid = "include_mermaid" in body
        include_hljs = "include_hljs" in body

        logger.info(
            f"ReportCreator: {include_plotly=}, {include_datatable=}, {include_mermaid=}, {include_hljs=}"
        )
        logger.info(f"ReportCreator: {self.description=}, {self.author=} {prettify_html=}")
        with open(path, "w", encoding="utf-8") as f:
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
                    f.write(soup.prettify(formatter="minimal"))
                except ImportError:
                    f.write(html)

            else:
                f.write(html)

            logger.info(
                f'ReportCreator created {path}, size: {humanize.naturalsize(len(html), binary=True)}, title: "{self.title}"'
            )
