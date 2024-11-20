import base64
import io
import json
import logging
import os
import re
import textwrap
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Union
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
    _markdown_to_html,
    _random_light_color_generator,
    _strip_whitespace,
)

logger = logging.getLogger("report_creator")


class Base(ABC):
    """Abstract Base Class for all components

    Args:
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, label: Optional[str] = None):
        self.label = label

    @abstractmethod
    def to_html(self) -> str:
        """Each component that derives from Base must implement this method"""


##############################


class Block(Base):
    """Block is a container for vertically stacked components

    Args:
        components (Base): _description_
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, *components: Base, label: Optional[str] = None):
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
    """Group is a container for horizontally stacked components

    Args:
        components (Base): _description_
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, *components: Base, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.components = components
        logger.info(f"Group: {len(self.components)} components {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        html = "<div>"

        if self.label:
            html += f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</report-caption></a>"

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
        html = f"<details><summary>{self.label}</summary>"

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
            html += f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</report-caption>"

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

    def __init__(self, df: pd.DataFrame, heading: str, value: str, *, label: Optional[str] = None):
        Base.__init__(self, label=label)
        assert heading in df.columns, f"heading {heading} not in df"
        assert value in df.columns, f"value {value} not in df"

        self.g = Group(*[Metric(row[heading], row[value]) for _, row in df.iterrows()], label=label)

        logger.info(f"MetricGroup: {len(df)} metrics")

    @_strip_whitespace
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

    Args:
        df (pd.DataFrame): the data
        condition (str): an expression to evaluate like B==42
        date (str, optional): the date column.
        frequency (str, optional): the frequency to group over. Defaults to "D" (daily)
        color (str, optional): _description_. Defaults to "red".
        heading (Optional[str], optional): _description_. Defaults to None.
        label (Optional[str], optional): _description_. Defaults to None.
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

        description = f"<div class='metric-description'><p>{self.label}</p></div>" if self.label else ""

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
    """Metric is a container for a single metric. It takes a heading and a value.

    Args:
        heading (str): _description_
        value (Union[str, int, float]): _description_
        unit ([type], optional): _description_. Defaults to None.
        float_precision (int, optional): limit the precision (number of decimal digits). Defaults to 3.
        label (Optional[str], optional): _description_. Defaults to None. May be markdown.
        colored (Optional[bool], optional): to use a colorful background or not. Defaults to False.
    """

    def __init__(
        self,
        heading: str,
        value: Union[str, int, float, datetime],
        *,
        unit: Optional[str] = None,
        float_precision: Optional[int] = 3,
        label: Optional[str] = None,
        colored: Optional[bool] = False,
    ):
        Base.__init__(self, label=textwrap.dedent(label) if label else None)
        self.heading = heading
        self.float_precision = float_precision
        self.value = value
        self.unit = unit or ""
        self.colored = colored

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

        description = f"<div class='metric-description'>{_markdown_to_html(self.label)}</div>" if self.label else ""

        if self.colored:
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
        data (Union[pd.DataFrame, List[Dict]]): _description_
        label (Optional[str], optional): _description_. Defaults to None.
        index (bool, optional): _description_. Defaults to False.
        float_precision (int, optional): _description_. Defaults to 3.
    """

    def __init__(
        self,
        data: Union[pd.DataFrame, List[Dict]],
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
    """DataTable is a container for a DataFrame (or table-like list of dictionaries.) with search and sort capabilities.

    Args:
        data (Union[pd.DataFrame, List[Dict]]): _description_
        label (Optional[str], optional): _description_. Defaults to None.
        wrap_text (bool, optional): _description_. Defaults to True.
        index (bool, optional): _description_. Defaults to False.
        max_rows (int, optional): _description_. Defaults to -1.
        float_precision (int, optional): _description_. Defaults to 3.
    """

    def __init__(
        self,
        data: Union[pd.DataFrame, List[Dict]],
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

        styler.set_table_attributes(f'class="{" ".join(data_table_classes)} cellspacing="0" style="width: 100%;"')
        self.table_html = styler.format(escape="html", precision=float_precision).to_html()
        logger.info(f"DataTable: {len(df)} rows")

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
            raise ValueError(f"HTML component with label {self.label}, tags are not closed: {', '.join(errors)}")
        logger.info(f"HTML: {len(self.html)} characters")

    @_strip_whitespace
    def to_html(self) -> str:
        border = "round-bordered" if self.bordered else ""

        html = f"<style>{self.css}</style>" if self.css else ""
        if self.label:
            html += f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</report-caption>"
        html += f'<div class="{border}">' + self.html + "</div>"
        return html


##############################


class Diagram(Base):
    """Diagram is a container for a mermaid js diagram. For examples of the syntax please see https://mermaid.js.org/syntax/examples.html
    Note also that ChatGPT is able to create the diagrams for you simply by describing them in text. The kitchen sink example is an example of this.

    Args:
        src (str): The mermaid source code.
        label (Optional[str], optional): The label for the diagram. Defaults to None.
        extra_css (str, optional): Additional CSS styles to be applied. Defaults to None.
    """

    def __init__(
        self,
        src: str,
        *,
        label: Optional[str] = None,
        extra_css: Optional[str] = None,
    ):
        Base.__init__(self, label=label)

        self.src = src
        self.extra_css = extra_css or ""
        logger.info(f"Diagram: {len(self.src)} characters")

    @_strip_whitespace
    def to_html(self) -> str:
        html = """
            <div class="diagram-block">
                <figure>
        """

        if self.label:
            html += f"<figcaption><report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</report-caption></figcaption>"

        html += f"<div class='mermaid include_mermaid'>{self.src}</div>"

        html += "</figure></div>"

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

        image_markup = (
            f"""<img src="{self.src}" style="{self.rounded_css} {self.extra_css}" alt="{self.label or self.src}">"""
        )
        if self.link_to:
            html += f"""<a href="{self.link_to}" target="_blank">{image_markup}</a>"""
        else:
            html += image_markup

        if self.label:
            html += f"<figcaption><report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</report-caption></figcaption>"

        html += "</figure></div>"

        return html


##############################


class Markdown(Base):
    """Markdown is a container for markdown text. It can also take extra CSS.

    Args:
        text (str): The markdown text to be displayed.
        label (Optional[str], optional): The label for the markdown section. Defaults to None.
        extra_css (str, optional): Additional CSS styles to be applied. Defaults to None.
        bordered (bool, optional): If set to True, the markdown will have a border. Defaults to False.
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
        self.text = text
        self.extra_css = extra_css or ""
        self.bordered = bordered

        logger.info(f"Markdown: {len(self.text)} characters")

    @staticmethod
    def _markdown_to_html(text):
        return _markdown_to_html(text)

    @_strip_whitespace
    def to_html(self) -> str:
        border = "round-bordered" if self.bordered else ""
        html = f"<div class='markdown-wrapper include_hljs {border}'>"
        if self.label:
            html += f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</report-caption>"
        html += f'<div style="{self.extra_css}">'
        html += Markdown._markdown_to_html(self.text)
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
    """Line is a container for a plotly express line chart.

    Args:
        df (pd.DataFrame): The data to be plotted.
        x (str): The column to be plotted on the x-axis.
        y (Union[str, List[str]]): The column(s) to be plotted on the y-axis.
        dimension (Optional[str], optional): The column to be plotted on the dimension axis. Defaults to None.
        label (Optional[str], optional): The label for the bar chart. Defaults to None.
        **kwargs (Optional[Dict], optional): Additional keyword arguments to be passed to the plotly express line chart.

    Raises:
        AssertionError: If the specified columns (x, y, dimension) are not present in the DataFrame.

    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: Union[str, List[str]],
        *,
        dimension: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs: Optional[Dict],
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
        **kwargs (Optional[Dict], optional): Additional keyword arguments for the report. Defaults to None.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        values: str,
        names: str,
        *,
        label: Optional[str] = None,
        **kwargs: Optional[Dict],
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
        **kwargs: Optional[Dict],
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
        kwargs (Optional[Dict]): Additional keyword arguments.

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
        assert level >= 1 and level <= 5, f"heading level ({level}) must be between 1 and 5 (inclusive)"
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
            return f"<br><hr><report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</report-caption>"
        else:
            return "<br><hr>"


##############################


class Text(Markdown): ...


##############################


class Select(Base):
    """Select is a container for a group of components that will shown in tabs. It can also take an outer label.

    Args:
        blocks (List[Base]): _description_
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, blocks: List[Base], *, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.blocks = blocks

        for b in self.blocks:
            if not b.label:
                raise ValueError("All blocks must have a label to use in a Select")

        logger.info(f"Select: {len(self.blocks)} tabs: {', '.join([c.label for c in self.blocks])}")

    @_strip_whitespace
    def to_html(self) -> str:
        html = (
            f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</report-caption>"
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
            return f"""<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</report-caption><div>{formatted_text}</div>"""
        else:
            return f"""<div>{formatted_text}</div>"""


##############################


class Language(Base):
    def __init__(self, text: str, language: str, *, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.text = text
        self.language = language.lower()
        logger.info(f"{language}: {len(self.text)} characters")

        if not self.language:
            assert self.language, "Language must be specified"
        else:
            assert self.language in [
                "java",
                "python",
                "shell",
                "sql",
                "yaml",
                "json",
                "plaintext",
            ], f"Language {self.language} not supported"

    @_strip_whitespace
    @abstractmethod
    def to_html(self) -> str:
        if self.label:
            formatted_text = f"<pre><code class='language-{self.language} syntax-color'>### {self.label}\n\n{self.text.strip()}</code></pre>"
        else:
            formatted_text = (
                f"<pre><code class='language-{self.language} syntax-color'>{self.text.strip()}</code></pre>"
            )

        return f"""<div class="code-block include_hljs">{formatted_text}</div>"""


##############################


class Python(Language):
    """Python is a container for python code. It can also take a label.

    Args:
        code (str): _description_
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, code: str, *, label: Optional[str] = None):
        Language.__init__(self, escape(code), "python", label=label)


##############################


class Shell(Language):
    """Shell is a container for zsh/csh/sh code. It can also take a label.

    Args:
        code (str): _description_
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, code: str, *, label: Optional[str] = None):
        Language.__init__(self, escape(code), "shell", label=label)


##############################


class Java(Language):
    """Java is a container for Java code. It can also take a label.

    Args:
        code (str): _description_
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, code: str, *, label: Optional[str] = None):
        Language.__init__(self, escape(code), "java", label=label)


##############################


class Sql(Language):
    """Sql is a container for SQL code. It can also take a label.

    Args:
        code (str): your SQL code
        prettify (Optional[bool], optional): _description_. Defaults to True.
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
        prettify: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        Language.__init__(self, Sql.format_sql(code) if prettify else code, "sql", label=label)


##############################


class Yaml(Language):
    """Yaml is a container for yaml. It can also take a label.

    Args:
        data (Union[Dict, List]): _description_
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, data: Union[Dict, List], *, label: Optional[str] = None):
        Language.__init__(
            self,
            yaml.dump(data, indent=2, Dumper=yaml.SafeDumper),
            "yaml",
            label=label,
        )


##############################


class Json(Language):
    """Json is a container for JSON data. It can also take a label.

    Args:
        data (Union[Dict, List]): _description_
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, data: Union[Dict, List], *, label: Optional[str] = None):
        Language.__init__(
            self,
            json.dumps(data, indent=2),
            "json",
            label=label,
        )


##############################


class Plaintext(Language):
    """Plaintext is a container for plain text that will styled as code. It can also take a label.

    Args:
        code (str): _description_
        label (Optional[str], optional): _description_. Defaults to None.
    """

    def __init__(self, code: str, *, label: Optional[str] = None):
        Language.__init__(
            self,
            code,
            "plaintext",
            label=label,
        )


##############################


class ReportCreator:
    """
    Initialize a ReportCreator object.

    Args:
        title (str): The title of the report.
        description (str, optional): The description of the report (markdown is ok). Defaults to None.
        author (str, optional): The author of the report. Defaults to None.
        logo (str, optional): A GitHub username to use as the report icon, a url/filepath to an image, or None. Defaults to None,
        which will use an autogenerated icon based on the title.
        theme (str, optional): The theme to use for the report. Defaults to "rc".
        diagram_theme (str, optional): The mermaid theme (https://mermaid.js.org/config/theming.html#available-themes) to use Defaults to "default", options: "neo", "neo-dark", "dark", "neutral", "forest", & "base".
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
        diagram_theme: Optional[str] = "default",
        footer: Optional[str] = None,
    ):
        self.title = title
        self.description = description
        self.author = author
        self.code_theme = "vs"
        self.diagram_theme = diagram_theme
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
                self.header_str = (
                    f"""<img src="https://avatars.githubusercontent.com/{logo}?s=125" style="width: 125px;">"""
                )
        else:
            match = re.findall(r"[A-Z]", self.title)
            icon_text = "".join(match[:2]) if match else self.title[0]
            icon_color, text_color = "black", "white"

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
            raise ValueError(f"Expected view to be either Block or Group object, got {type(view)} instead")

        logger.info(f"Saving report to {path}")

        try:
            body = view.to_html()
        except ValueError:
            body = f"""<pre>{traceback.format_exc()}</pre>"""

        file_loader = FileSystemLoader(f"{os.path.dirname(os.path.abspath(__file__))}/templates")
        template = Environment(loader=file_loader).get_template("default.html")

        include_plotly = "plotly-graph-div" in body
        include_datatable = "include_datatable" in body
        include_mermaid = "include_mermaid" in body
        include_hljs = "include_hljs" in body

        logger.info(f"ReportCreator: {include_plotly=}, {include_datatable=}, {include_mermaid=}, {include_hljs=}")
        logger.info(f"ReportCreator: {self.description=}, {self.author=}")
        with open(path, "w", encoding="utf-8") as f:
            html = template.render(
                title=self.title or "Report",
                description=_markdown_to_html(self.description) if self.description else "",
                author=self.author.strip() if self.author else "",
                body=body,
                header_logo=self.header_str,
                include_plotly=include_plotly,
                include_datatable=include_datatable,
                include_mermaid=include_mermaid,
                include_hljs=include_hljs,
                code_theme=self.code_theme,
                diagram_theme=self.diagram_theme,
                footer=_markdown_to_html(self.footer).strip() if self.footer else None,
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

            logger.info(
                f'ReportCreator created {path}, size: {humanize.naturalsize(len(html), binary=True)}, title: "{self.title}"'
            )
