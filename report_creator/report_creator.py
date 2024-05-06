import base64
import io
import json
import logging
import os
import random
import re
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple, Union
from uuid import uuid4

import dateutil
import humanize
import matplotlib
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import yaml
from jinja2 import Environment, FileSystemLoader
from markupsafe import escape
from pandas.api.types import is_datetime64_any_dtype as is_datetime

logging.basicConfig(level=logging.INFO)


preferred_fonts = [
    "Roboto",
    "Helvetica Neue",
    "Oracle Sans",
    "sans-serif",
]

import matplotlib as mpl
from cycler import cycler

report_creator_colors = [
    "#01befe",
    "#ffdd00",
    "#ff7d00",
    "#ff006d",
    "#adff02",
    "#8f00ff",
]

mpl.rcParams["axes.prop_cycle"] = cycler("color", report_creator_colors)

import plotly.io as pio

pio.templates["rc"] = go.layout.Template(
    layout={
        "title": {
            "font": {
                "family": "Roboto",
            }
        },
        "font": {
            "family": "Roboto, Sans-serif",
            "size": 16,
        },
        "colorway": report_creator_colors,
    },
)
pio.templates.default = "rc"
# pio.templates.default = "presentation"


def _check_html_tags_are_closed(html_content: str):
    """Checks if any HTML tags are closed in the given string.

    Args:
        html_content (str): The HTML content to be checked.

    Returns:
        Tuple[bool, Optional[List[str]]]: A tuple containing a boolean value indicating if all tags are closed and a list of tags that are not closed.
    """

    class HTMLValidator(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []  # To keep track of opened tags

        def handle_starttag(self, tag, _):
            self.stack.append(tag)  # Add the tag to the stack when it opens

        def handle_endtag(self, tag):
            if self.stack and self.stack[-1] == tag:
                self.stack.pop()  # Remove the tag from the stack when it closes
            else:
                logging.error(f"Unexpected closing tag {tag} or tag not opened.")

        def validate_html(self, html):
            self.feed(html)
            if self.stack:
                return (False, self.stack)  # Some tags are not closed
            else:
                return (True, None)

    return HTMLValidator().validate_html(html_content)


def _markdown_to_html(text: str) -> str:
    import mistune

    class HighlightRenderer(mistune.HTMLRenderer):
        # need to wrap code/pre inside a div that is styled with codehilite at rendertime
        def block_code(
            self, code, **_
        ):  # **_ gathers unused key-value pairs (to avoid lint warning of unused param(s))
            return (
                "<div class='codehilite'><pre><code>"
                + mistune.escape(code)
                + "</code></pre></div>"
            )

    return mistune.create_markdown(
        renderer=HighlightRenderer(), plugins=["task_lists", "def_list", "math"]
    )(text)


def strip_whitespace(func):
    """
    A decorator that strips leading and trailing whitespace from the result of a function.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function.

    """

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str):
            return result.strip()
        else:
            return result

    return wrapper


def _random_color_generator(word: str) -> Tuple[str, str]:
    """returns auto selected (background_color, text_color) as tuple

    Args:
        word (str): word to generate color for
    """
    random.seed(word.encode())  # must be deterministic
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)

    background_color = f"#{r:02x}{g:02x}{b:02x}"
    text_color = "black" if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.5 else "white"

    return background_color, text_color


def _convert_imgurl_to_datauri(imgurl: str) -> str:
    """convert url to base64 datauri

    Args:
        imgurl (str): url of the image
    """
    from io import BytesIO

    import requests
    from PIL import Image

    response = requests.get(imgurl)
    img = Image.open(BytesIO(response.content))
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    return f"data:image/jpeg;base64,{img_str.decode('utf-8')}"


class Base(ABC):
    def __init__(self, label: Optional[str] = None):
        """Abstract Base Class for all components

        Args:
            label (Optional[str], optional): _description_. Defaults to None.
        """
        self.label = label

    @abstractmethod
    def to_html(self) -> str:
        """Each component that derives from Base must implement this method"""


##############################


class Block(Base):
    def __init__(self, *components: Base, label: Optional[str] = None):
        """Block is a container for vertically stacked components

        Args:
            components (Base): _description_
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.components = components
        logging.info(f"Block: {len(self.components)} components")

    @strip_whitespace
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
    def __init__(self, *components: Base, label: Optional[str] = None):
        """Group is a container for horizontally stacked components

        Args:
            components (Base): _description_
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.components = components
        logging.info(f"Group: {len(self.components)} components {label=}")

    @strip_whitespace
    def to_html(self) -> str:
        html = "<div>"

        if self.label:
            html += f"<report-caption>{self.label}</report-caption>"

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
    def __init__(self, *components: Base, label: Optional[str] = None):
        """Collapse is a container for vertically stacked components that can be collapsed

        Args:
            components (Base): _description_
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.components = components
        logging.info(f"Collapse: {len(self.components)} components, {label=}")

    @strip_whitespace
    def to_html(self) -> str:
        html = f"<details><summary>{self.label}</summary>"

        for component in self.components:
            html += component.to_html()

        html += "</details>"
        return html


##############################


class Widget(Base):
    def __init__(self, widget, *, label: Optional[str] = None):
        """Widget is a container for any component that supports the _repr_html_ method (anything written for Jupyter).

        Args:
            widget: A widget that supports the _repr_html_ method.
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        if isinstance(widget, go.Figure):
            self.widget = widget
            PxBase.apply_common_fig_options(self.widget)

        elif hasattr(widget, "get_figure"):
            self.widget = widget.get_figure()
        else:
            self.widget = widget

    @strip_whitespace
    def to_html(self) -> str:
        html = "<div class='report-widget'>"

        if self.label:
            html += f"<report-caption>{self.label}</report-caption>"

        if isinstance(self.widget, pd.DataFrame):
            html += self.widget.style._repr_html_()
        elif isinstance(self.widget, matplotlib.figure.Figure):
            tmp = io.BytesIO()

            self.widget.set_dpi(300)
            self.widget.set_figwidth(10)
            self.widget.tight_layout()
            self.widget.savefig(tmp, format="png")
            tmp.seek(0)
            b64image = (
                base64.b64encode(tmp.getvalue()).decode("utf-8").replace("\n", "")
            )
            html += f'<br/><img src="data:image/png;base64,{b64image}">'

        else:
            html += self.widget._repr_html_()

        html += "</div>"
        return html


##############################


class MetricGroup(Base):
    def __init__(
        self, df: pd.DataFrame, heading: str, value: str, *, label: Optional[str] = None
    ):
        """MetricGroup is a container for a group of metrics. It takes a DataFrame with a heading and value column.

        Args:
            df (pd.DataFrame): the DataFrame containing the data.
            heading (str): the metric heading string
            value (str): the column wuth the metric value
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        assert heading in df.columns, f"heading {heading} not in df"
        assert value in df.columns, f"value {value} not in df"

        self.g = Group(
            *[Metric(row[heading], row[value]) for _, row in df.iterrows()], label=label
        )

        logging.info(f"MetricGroup: {len(df)} metrics")

    @strip_whitespace
    def to_html(self) -> str:
        return self.g.to_html()


##############################


class EventMetric(Base):
    """A special metric that shows the number of events that match a condition over time. Used or telemetry
    or event tracking. The dataframe must have a column that's datelike. The column specified will be
    converted to a datetime and used to group over. The condition, like "status=200" will be evaluated
    for each row and converted to a 1 for true, or 0 for not true. The sum of these values will be the
    period of frequency (daily, D, weekly, W etc) and plotted as a line chart along with showing the
    count and percentage of the total.

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
        """_summary_

        Args:
            df (pd.DataFrame): the data
            condition (str): an expression to evaluate like B==42
            date (str, optional): the date column.
            frequency (str, optional): the frequency to group over. Defaults to "D" (daily)
            color (str, optional): _description_. Defaults to "red".
            heading (Optional[str], optional): _description_. Defaults to None.
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)

        assert date in df.columns, f"index column {date} not in df"
        self.df = df
        self.date = date

        self.freq = frequency

        if not is_datetime(self.df[date]):
            logging.info(f"EventMetric converting {date} to datetime")
            self.df[date] = self.df[date].apply(dateutil.parser.parse)

        self.condition = condition
        self.color = color
        self.heading = heading or f"{condition}"
        self.yhat = "_Y_"

        logging.info(f"EventMetric: {len(df)} rows, fn: ({condition})")

    @strip_whitespace
    def to_html(self) -> str:
        dfx = self.df.eval(f"{self.yhat} = {self.condition}")[[self.date, self.yhat]]
        dfx[self.yhat] = dfx[self.yhat].astype(int)
        dfx = dfx.groupby(pd.Grouper(key=self.date, freq=self.freq)).sum().reset_index()

        agg_value = dfx["_Y_"].apply("sum")

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
            f"<div class='metric-description'><p>{self.label}</p></div>"
            if self.label
            else ""
        )

        return f"""
            <div class="metric">
                <p>{self.heading}</p>
                <table style="margin-top: 15px;">
                    <tr>
                    <td width=20% style="text-align: center; vertical-align: center;"><h1>{agg_value:d}</h1></td>
                    <td style="vertical-align: bottom;">{fig_html}</td>
                    </tr>
                </table>
                {description}
            </div>
        """


##############################


class Metric(Base):
    def __init__(
        self,
        heading: str,
        value: Union[str, int, float, datetime],
        *,
        unit: Optional[str] = None,
        float_precision: Optional[int] = 3,
        label: Optional[str] = None,
    ):
        """Metric is a container for a single metric. It takes a heading and a value.

        Args:
            heading (str): _description_
            value (Union[str, int, float]): _description_
            unit ([type], optional): _description_. Defaults to None.
            float_precision (int, optional): _description_. Defaults to 3.
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.heading = heading
        self.float_precision = float_precision
        self.value = value
        self.unit = unit or ""
        logging.info(f"Metric: {self.heading} {self.value}")

    def __str__(self) -> str:
        return f"Metric {self.heading=} {self.value=} {self.unit=} {self.label=}"

    @strip_whitespace
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
            f"<div class='metric-description'><p>{self.label}</p></div>"
            if self.label
            else ""
        )

        return f"""
            <div class="metric">
                <p>{self.heading}</p>
                <h1>{value_str}{self.unit}</h1>
                {description}
            </div>
        """


##############################


class Table(Widget):
    def __init__(
        self,
        data: Union[pd.DataFrame, List[Dict]],
        *,
        label: Optional[str] = None,
        index: Optional[bool] = False,
    ):
        """Table is a simple container for a DataFrame (or table-like list of dictionaries.)

        Args:
            data (Union[pd.DataFrame, List[Dict]]): _description_
            label (Optional[str], optional): _description_. Defaults to None.
            index (bool, optional): _description_. Defaults to False.
        """
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError(
                f"Expected data to be a list or pd.DataFrame, got {type(data)}"
            )

        s = df.style if index else df.style.hide()

        Widget.__init__(self, s.format(escape="html"), label=label)


##############################


class DataTable(Base):
    def __init__(
        self,
        data: Union[pd.DataFrame, List[Dict]],
        *,
        label: Optional[str] = None,
        wrap_text: bool = True,
        index: Optional[bool] = False,
        max_rows: Optional[int] = -1,
        float_precision: Optional[int] = 3,
    ):
        """DataTable is a container for a DataFrame (or table-like list of dictionaries.) with search and sort capabilities.

        Args:
            data (Union[pd.DataFrame, List[Dict]]): _description_
            label (Optional[str], optional): _description_. Defaults to None.
            wrap_text (bool, optional): _description_. Defaults to True.
            index (bool, optional): _description_. Defaults to False.
            max_rows (int, optional): _description_. Defaults to -1.
            float_precision (int, optional): _description_. Defaults to 3.
        """
        Base.__init__(self, label=label)

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError(
                f"Expected data to be a list or pd.DataFrame, got {type(data)}"
            )

        styler = df.head(max_rows).style if max_rows > 0 else df.style

        if label:
            styler.set_caption(label)

        data_table_classes = [
            "remove-all-styles",
            "fancy-table",
            "display",
            "row-border",
            "hover",
            "responsive",
        ]
        if not wrap_text:
            data_table_classes.append("nowrap")

        styler.format(precision=float_precision)
        if not index:
            styler.hide(axis="index")
        styler.set_table_attributes(
            f'class="{" ".join(data_table_classes)} cellspacing="0" style="width: 100%;"'
        )
        self.table_html = styler.format(escape="html").to_html()
        logging.info(f"DataTable: {len(df)} rows")

    @strip_whitespace
    def to_html(self) -> str:
        return f"<div class='dataTables-wrapper'><br/>{self.table_html}</div>"


##############################


class Html(Base):
    def __init__(
        self, html: str, *, css: Optional[str] = None, label: Optional[str] = None
    ):
        """Html is a container for raw HTML. It can also take CSS.

        Args:
            html (str): The raw HTML content.
            css (str, optional): The CSS styles to be applied to the HTML. Defaults to None.
            label (Optional[str], optional): The label for the HTML component. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.html = html
        self.css = css
        status, errors = _check_html_tags_are_closed(html)
        if not status:
            raise ValueError(
                f"HTML component with label {self.label}, tags are not closed: {', '.join(errors)}"
            )
        logging.info(f"HTML: {len(self.html)} characters")

    @strip_whitespace
    def to_html(self) -> str:
        html = f"<style>{self.css}</style>" if self.css else ""
        if self.label:
            html += f"<report-caption>{self.label}</report-caption>"
        html += "<div>" + self.html + "</div>"
        return html


##############################


class Image(Base):
    def __init__(
        self,
        src: str,
        *,
        link_to: Optional[str] = None,
        label: Optional[str] = None,
        extra_css: Optional[str] = None,
        rounded: Optional[bool] = True,
    ):
        """Image is a container for an image. It can also take a link.

        Args:
            src (str): a URL where the image can be found, or a base_64 URI.
            link_to (str, optional): a URL to go to if clicked. Defaults to not clickable.
            label (Optional[str], optional): a label for the image. Defaults to None.
            extra_css (str, optional): additional CSS styles for the image. Defaults to None.
            rounded (bool, optional): if set to True, the image will have rounded corners. Defaults to True.
        """
        Base.__init__(self, label=label)
        self.src = src
        self.link_to = link_to
        self.extra_css = extra_css or ""
        self.rounded_css = "border-radius: 1rem;" if rounded else ""
        logging.info(f"Image: label: {self.label}")

    @strip_whitespace
    def to_html(self) -> str:
        html = """<div class="image-block"><figure>"""

        image_markup = f"""<img src="{self.src}" style="{self.rounded_css} {self.extra_css}" alt="{self.label or self.src}">"""
        if self.link_to:
            html += f"""<a href="{self.link_to}" target="_blank">{image_markup}</a>"""
        else:
            html += image_markup

        if self.label:
            html += f"<figcaption><report-caption>{self.label}</report-caption></figcaption>"

        html += "</figure></div>"

        return html


##############################


class Markdown(Base):
    def __init__(
        self, text: str, *, label: Optional[str] = None, extra_css: Optional[str] = None
    ):
        """Markdown is a container for markdown text. It can also take extra CSS.

        Args:
            text (str): The markdown text to be displayed.
            label (Optional[str], optional): The label for the markdown section. Defaults to None.
            extra_css (str, optional): Additional CSS styles to be applied. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.text = text
        self.extra_css = extra_css or ""

        logging.info(f"Markdown: {len(self.text)} characters")

    @staticmethod
    def _markdown_to_html(text):
        return _markdown_to_html(text)

    @strip_whitespace
    def to_html(self) -> str:
        html = "<div class='markdown-wrapper'>"
        if self.label:
            html += f"<report-caption>{self.label}</report-caption>"
        html += f'<div style="{self.extra_css}">'
        html += Markdown._markdown_to_html(self.text)
        html += "</div>"
        html += "</div>"
        return html


##############################


class PxBase(Base):
    def __init__(self, label: Optional[str] = None):
        """PXBase is a container for all Plotly Express components.

        Args:
            label (Optional[str], optional): _description_. Defaults to None.
        """
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
    def apply_common_kwargs(
        kwargs, label: Optional[str] = None, theme: Optional[str] = None
    ):
        if label and "title" not in kwargs:
            kwargs["title"] = label


##############################

# Charting Components

##############################


class Bar(PxBase):
    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        *,
        dimension: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs: Optional[Dict],
    ):
        """Bar is a container for a plotly express bar chart.

        Args:
            df (pd.DataFrame): The data to be plotted.
            x (str): The column to be plotted on the x-axis.
            y (str): The column to be plotted on the y-axis.
            dimension (Optional[str], optional): The column to be plotted on the dimension axis. Defaults to None.
            label (Optional[str], optional): The label for the bar chart. Defaults to None.
            **kwargs (Optional[Dict], optional): Additional keyword arguments to be passed to the plotly express bar chart.

        Raises:
            AssertionError: If the specified columns (x, y, dimension) are not present in the DataFrame.

        """
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

        logging.info(f"Bar: {len(self.df)} rows, {x=}, {y=}, {label=}")

    @strip_whitespace
    def to_html(self) -> str:
        fig = px.bar(self.df, x=self.x, y=self.y, **self.kwargs)

        PxBase.apply_common_fig_options(fig)
        fig.update_layout(bargap=0.1)

        return fig.to_html(
            include_plotlyjs=False, full_html=False, config={"responsive": True}
        )


##############################


class Line(PxBase):
    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        *,
        dimension: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs: Optional[Dict],
    ):
        """Line is a container for a plotly express line chart.

        Args:
            df (pd.DataFrame): The data to be plotted.
            x (str): The column to be plotted on the x-axis.
            y (str|list): The column(s) to be plotted on the y-axis.
            dimension (Optional[str], optional): The column to be plotted on the dimension axis. Defaults to None.
            label (Optional[str], optional): The label for the bar chart. Defaults to None.
            **kwargs (Optional[Dict], optional): Additional keyword arguments to be passed to the plotly express line chart.

        Raises:
            AssertionError: If the specified columns (x, y, dimension) are not present in the DataFrame.

        """
        Base.__init__(self, label=label)
        self.df = df
        self.x = x
        self.y = y
        self.kwargs = kwargs

        assert x in df.columns, f"{x} not in df"

        if isinstance(y, list):
            for y_ in y:
                assert y_ in df.columns, f"{y_} not in df"
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

        logging.info(f"Line: {len(self.df)} rows, {x=}, {y=}, {label=}")

    @strip_whitespace
    def to_html(self) -> str:
        fig = px.line(self.df, x=self.x, y=self.y, **self.kwargs)

        PxBase.apply_common_fig_options(fig)
        fig.update_layout(bargap=0.1)

        return fig.to_html(
            include_plotlyjs=False, full_html=False, config={"responsive": True}
        )


##############################


class Pie(PxBase):
    def __init__(
        self,
        df: pd.DataFrame,
        values: str,
        names: str,
        *,
        label: Optional[str] = None,
        **kwargs: Optional[Dict],
    ):
        """Pie is a container for a plotly express pie chart.

        Args:
            df (pd.DataFrame): The input DataFrame containing the data for the report.
            values (str): The column name in the DataFrame representing the values for the pie.
            names (str): The column name in the DataFrame representing the names for the pie.
            label (Optional[str], optional): The label for the pi. Defaults to None.
            **kwargs (Optional[Dict], optional): Additional keyword arguments for the report. Defaults to None.
        """
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

        logging.info(f"Pie: {len(self.df)} rows, {values=}, {names=}, {label=}")

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

        return fig.to_html(
            include_plotlyjs=False, full_html=False, config={"responsive": True}
        )


##############################


class Scatter(PxBase):
    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        marginal: Optional[str] = None,
        **kwargs: Optional[Dict],
    ):
        """
        Scatter plot class for creating scatter plots.

        Args:
            df (pd.DataFrame): The DataFrame containing the data.
            x (str): The column name for the x-axis data.
            y (str): The column name for the y-axis data.
            dimension (Optional[str], optional): The column name for the dimension data. Defaults to None.
            label (Optional[str], optional): The label for the scatter plot. Defaults to None.
            marginal (Optional[str], optional): The type of marginal plot to add. Must be one of ['histogram', 'violin', 'box', 'rug']. Defaults to None.
            **kwargs (Optional[Dict], optional): Additional keyword arguments to pass to the scatter plot. Defaults to None.
        """
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

        logging.info(f"Scatter: {len(self.df)} rows, {y=}, {dimension=}, {label=}")

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

        return fig.to_html(
            include_plotlyjs=False, full_html=False, config={"responsive": True}
        )


##############################


class Box(PxBase):
    def __init__(
        self,
        df: pd.DataFrame,
        y: Optional[str] = None,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        **kwargs: Optional[Dict],
    ):
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

        logging.info(f"Box: {len(self.df)} rows, {y=}, {dimension=}, {label=}")

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

        return fig.to_html(
            include_plotlyjs=False, full_html=False, config={"responsive": True}
        )


##############################


class Histogram(PxBase):
    """
    A class representing a histogram plot.

    Parameters:
    - df (pd.DataFrame): The input DataFrame containing the data.
    - x (str): The column name in the DataFrame to be plotted on the x-axis.
    - dimension (Optional[str]): The column name in the DataFrame to be used for color dimension (optional).
    - label (Optional[str]): The label for the plot (optional).
    - **kwargs (Optional[Dict]): Additional keyword arguments to be passed to the plotly histogram function.

    Attributes:
    - df (pd.DataFrame): The input DataFrame containing the data.
    - x (str): The column name in the DataFrame to be plotted on the x-axis.
    - kwargs (Optional[Dict]): Additional keyword arguments to be passed to the plotly histogram function.

    Methods:
    - to_html(): Generates the HTML representation of the histogram plot.

    Example usage:
    ```
    df = pd.DataFrame({'values': [1, 2, 3, 4, 5]})
    histogram = Histogram(df, 'values', label='Value Distribution')
    html = histogram.to_html()
    ```

    For more information, refer to the Plotly documentation: https://plotly.com/python/histograms/
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        **kwargs: Optional[Dict],
    ):
        """
        Initialize the Histogram object.

        Args:
            df (pd.DataFrame): The input DataFrame.
            x (str): The column name to be used for the histogram.
            dimension (Optional[str], optional): The column name to be used for coloring the histogram bars. Defaults to None.
            label (Optional[str], optional): The label for the histogram. Defaults to None.
            **kwargs (Optional[Dict]): Additional keyword arguments.

        Raises:
            AssertionError: If `x` or `dimension` is not present in the DataFrame columns.

        """
        Base.__init__(self, label=label)
        self.df = df
        self.x = x
        self.kwargs = kwargs

        assert x in df.columns, f"{x} not in df"

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["color"] = dimension

        PxBase.apply_common_kwargs(kwargs, label=label)

        logging.info(f"Histogram: {len(self.df)} rows, {x=}, {label=}")

    @strip_whitespace
    def to_html(self) -> str:
        fig = px.histogram(self.df, x=self.x, **self.kwargs)
        fig.update_layout(bargap=0.1)

        PxBase.apply_common_fig_options(fig)

        return fig.to_html(
            include_plotlyjs=False, full_html=False, config={"responsive": True}
        )


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
        """
        Initialize a ReportCreator object.

        Args:
            label (str): The heading label for the report.
            level (Optional[int], optional): The heading level for the report. Must be between 1 and 5 (inclusive). Defaults to 1.

        Raises:
            AssertionError: If the heading level is not between 1 and 5 (inclusive).
            AssertionError: If no heading label is provided.
        """
        Base.__init__(self, label=label)
        assert (
            level >= 1 and level <= 5
        ), f"heading level ({level}) must be between 1 and 5 (inclusive)"
        assert label, "No heading label provided"
        self.level = level
        logging.info(f"Heading: (h{level}): [{label}]")

    @strip_whitespace
    def to_html(self) -> str:
        """
        Converts the heading to an HTML string.

        Returns:
            str: The HTML representation of the heading.
        """
        return f"<br /><h{self.level}>{self.label}</h{self.level}><br />"


##############################


class Separator(Base):
    def __init__(self, label: Optional[str] = None):
        """Separator is a container for a horizontal line. It can also take a label.

        Args:
            label (Optional[str], optional): The label to be displayed above the separator. Defaults to None.
        """
        Base.__init__(self, label=label)
        logging.info(f"Separator: {label=}")

    @strip_whitespace
    def to_html(self) -> str:
        """Converts the Separator object to its HTML representation.

        Returns:
            str: The HTML representation of the Separator.
        """
        if self.label:
            return f"<br><hr><report-caption>{self.label}</report-caption>"
        else:
            return "<br><hr>"


##############################


class Text(Base):
    def __init__(
        self, text: str, *, label: Optional[str] = None, extra_css: str = None
    ):
        """
        Initialize a Text object.

        Args:
            text (str): The text content of the report.
            label (str, optional): The label for the report. Defaults to None.
            extra_css (str, optional): Additional CSS styles for the report. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.text = text
        self.extra_css = extra_css or ""

        logging.info(f"Text: {len(self.text)} characters")

    @strip_whitespace
    def to_html(self) -> str:
        """
        Convert the Text object to HTML format.

        Returns:
            str: The Text object converted to HTML format.
        """
        formatted_text = f'<report-text style="{self.extra_css}">'
        formatted_text += "".join(
            [f"<p>{p.strip()}</p>" for p in self.text.split("\n\n")]
        )
        formatted_text += "</report-text>"

        if self.label:
            return f"""<report-caption>{self.label}</report-caption>{formatted_text}"""
        else:
            return formatted_text


##############################


class Select(Base):
    def __init__(self, blocks: List[Base], *, label: Optional[str] = None):
        """Select is a container for a group of components that will shown in tabs. It can also take an outer label.

        Args:
            blocks (List[Base]): _description_
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.blocks = blocks
        for blocks in self.blocks:
            if not blocks.label:
                raise ValueError("All blocks must have a label to use in a Select")

        logging.info(
            f"Select: {len(self.blocks)} tabs: {', '.join([c.label for c in self.blocks])}"
        )

    @strip_whitespace
    def to_html(self) -> str:
        html = f"<report-caption>{self.label}</report-caption>" if self.label else ""

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


class Unformatted(Base):
    def __init__(self, text: str, *, label: Optional[str] = None):
        """Unformatted is a container for any text that should be displayed verbatim with a non-proportional font.

        Args:
            text (str): any text that should be displayed verbatim with a non-proportional font.
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.text = text

    @strip_whitespace
    def to_html(self) -> str:
        formatted_text = f"<pre><code>{self.text.strip()}</code></pre>"

        if self.label:
            return f"""<report-caption>{self.label}</report-caption><div>{formatted_text}</div>"""
        else:
            return f"""<div>{formatted_text}</div>"""


##############################


class Language(Base):
    def __init__(self, text: str, language: str, *, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.text = text
        self.language = language
        logging.info(f"{language}: {len(self.text)} characters")

    @strip_whitespace
    @abstractmethod
    def to_html(self) -> str:
        if self.label:
            formatted_text = f"<pre><code class='language-{self.language} syntax-color'>### {self.label}\n\n{self.text.strip()}</code></pre>"
        else:
            formatted_text = f"<pre><code class='language-{self.language} syntax-color'>{self.text.strip()}</code></pre>"

        return f"""<div class="code-block">{formatted_text}</div>"""


##############################


class Python(Language):
    def __init__(self, code: str, *, label: Optional[str] = None):
        """Python is a container for python code. It can also take a label.

        Args:
            code (str): _description_
            label (Optional[str], optional): _description_. Defaults to None.
        """

        Language.__init__(self, escape(code), "python", label=label)


##############################


class Sql(Language):
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
        prettify: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        """Sql is a container for SQL code. It can also take a label.

        Args:
            code (str): your SQL code
            prettify (Optional[bool], optional): _description_. Defaults to True.
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Language.__init__(
            self, Sql.format_sql(code) if prettify else code, "sql", label=label
        )


##############################


class Yaml(Language):
    def __init__(self, data: Union[Dict, List], *, label: Optional[str] = None):
        """Yaml is a container for yaml. It can also take a label.

        Args:
            data (Union[Dict, List]): _description_
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Language.__init__(
            self,
            yaml.dump(data, indent=2, Dumper=yaml.SafeDumper),
            "yaml",
            label=label,
        )


##############################


class Json(Language):
    def __init__(self, data: Union[Dict, List], *, label: Optional[str] = None):
        """Json is a container for JSON data. It can also take a label.

        Args:
            data (Union[Dict, List]): _description_
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Language.__init__(
            self,
            json.dumps(data, indent=2),
            "json",
            label=label,
        )


##############################


class ReportCreator:
    def __init__(
        self,
        title: str,
        *,
        description: Optional[str] = None,
        author: Optional[str] = None,
        github: Optional[str] = None,
    ):
        """
        Initialize a ReportCreator object.

        Args:
            title (str): The title of the report.
            description (str, optional): The description of the report. Defaults to None.
            author (str, optional): The author of the report. Defaults to None.
            github (str, optional): The GitHub username to use as the report icon. Defaults to None
            which will use an autogenerated icon based on the title.
        """
        self.title = title
        self.description = description
        self.author = author

        logging.info(f"ReportCreator: {self.title} {self.description}")

        if github:
            logging.info(f"GitHub: {github}")
            self.header_str = f"""<img src="https://avatars.githubusercontent.com/{github}?s=125" style="border-radius: 50%;">"""
        else:
            match = re.findall(r"[A-Z]", self.title)
            icon_text = "".join(match[:2]) if match else self.title[0]
            icon_color, text_color = _random_color_generator(self.title)

            width = 125

            cx = width / 2
            cy = width / 2
            r = width / 2
            fs = int(r / 15)

            self.header_str = f"""
                    <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{width}" height="{width}">

                        <style>
                            .icon_text_style {{
                                font-size: {fs}em;
                                font-family: roboto, lucida console, Fira Mono, monospace;
                                text-anchor: middle;
                                stroke-width: 1px;
                                font-weight: bold;
                                alignment-baseline: central;
                            }}

                        </style>

                        <circle cx="{cx}" cy="{cy}" r="{r}" fill="{icon_color}" />
                        <text class="icon_text_style" x="50%" y="50%" fill="{text_color}">{icon_text}</text>
                    </svg>
                """.strip()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def save(self, view: Base, path: str, prettify_html=True) -> None:
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

        logging.info(f"Saving report to {path}")

        try:
            body = view.to_html()
        except ValueError:
            body = f"""<pre>{traceback.format_exc()}</pre>"""

        file_loader = FileSystemLoader(
            f"{os.path.dirname(os.path.abspath(__file__))}/templates"
        )
        template = Environment(loader=file_loader).get_template("default.html")

        with open(path, "w") as f:
            html = template.render(
                title=self.title or "Report",
                description=self.description or "",
                author=self.author or "",
                body=body,
                header_logo=self.header_str,
                include_plotly="plotly-graph-div" in body,
                include_datatables="dataTables-wrapper" in body,
            )
            if prettify_html:
                try:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(html, features="lxml")
                    f.write(soup.prettify())
                except ImportError:
                    f.write(html)

            else:
                f.write(html)
