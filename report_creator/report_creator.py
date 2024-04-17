import base64
import io
import json
import logging
import os
import random
import re
import traceback
from abc import ABC, abstractmethod
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple, Union

import matplotlib
import pandas as pd
import plotly.express as px
import yaml
from jinja2 import Environment, FileSystemLoader
from markupsafe import escape

logging.basicConfig(level=logging.INFO)

import warnings

preferred_fonts = [
    "Helvetica Neue",
    "Roboto",
    "Oracle Sans",
    "sans-serif",
]

preferred_plotly_theme = "plotly_dark"


def check_html_tags_are_closed(html_content: str):
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


def markdown_to_html(text: str) -> str:
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


def random_color_generator(word: str) -> Tuple[str, str]:
    """returns auto selected (background_color, text_color) as tuple

    Args:
        word (str): word to generate color for
    """
    seed = sum([ord(c) for c in word]) % 13
    random.seed(seed)  # must be deterministic
    r = random.randint(10, 245)
    g = random.randint(10, 245)
    b = random.randint(10, 245)

    background_color = f"#{r:02x}{g:02x}{b:02x}"
    text_color = "black" if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.5 else "white"

    return background_color, text_color


def convert_imgurl_to_datauri(imgurl: str) -> str:
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
            html += "<block-article>"
            html += component.to_html()
            html += "</block-article>"

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
        logging.info(f"Collapse {len(self.components)} components, {label=}")

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
        if hasattr(widget, "get_figure"):
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
            df (pd.DataFrame): _description_
            heading (str): _description_
            value (str): _description_
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        assert heading in df.columns, f"heading {heading} not in df"
        assert value in df.columns, f"value {value} not in df"

        self.g = Group(
            *[Metric(row[heading], row[value]) for _, row in df.iterrows()], label=label
        )

        logging.info(f"MetricGroup {len(df)} metrics")

    @strip_whitespace
    def to_html(self) -> str:
        return self.g.to_html()


##############################


class Metric(Base):
    def __init__(
        self,
        heading: str,
        value: Union[str, int, float],
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
        logging.info(f"Metric {self.heading} {self.value}")

    def __str__(self) -> str:
        return f"Metric {self.heading=} {self.value=} {self.unit=} {self.label=}"

    @strip_whitespace
    def to_html(self) -> str:
        if isinstance(self.value, (float)):
            value = round(self.value, self.float_precision)
        else:
            value = self.value

        description = (
            f"<div class='metric-description'>{self.label}</div>" if self.label else ""
        )

        return f"""
            <div class="metric">
                <p>{self.heading}</p>
                <h1>{value}{self.unit}</h1>
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
        logging.info(f"DataTable {len(df)} rows")

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
            html (str): _description_
            css (str, optional): _description_. Defaults to None.
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.html = html
        self.css = css
        status, errors = check_html_tags_are_closed(html)
        if not status:
            raise ValueError(
                f"HTML component with label {self.label}, tags are not closed: {', '.join(errors)}"
            )
        logging.info(f"HTML {len(self.html)} characters")

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
            src (str):  a url where the image can be found, or a base_64 uri
            link_to (str, optional): a url to go to if clicked. Defaults to not clickable.
            label (Optional[str], optional): _description_. Defaults to None.
            extra_css (str, optional): _description_. Defaults to None.
            rounded (bool, optional): if set will clip the image to have rounded off corners
        """
        Base.__init__(self, label=label)
        self.src = src
        self.link_to = link_to
        self.extra_css = extra_css or ""
        self.rounded_css = "border-radius: 1rem;" if rounded else ""
        logging.info(f"Image, label: {self.label}")

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
            text (str): _description_
            label (Optional[str], optional): _description_. Defaults to None.
            extra_css (str, optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.text = text
        self.extra_css = extra_css or ""

        logging.info(f"Markdown {len(self.text)} characters")

    @staticmethod
    def markdown_to_html(text):
        return markdown_to_html(text)

    @strip_whitespace
    def to_html(self) -> str:
        html = "<div class='markdown-wrapper'>"
        if self.label:
            html += f"<report-caption>{self.label}</report-caption>"
        html += f'<div style="{self.extra_css}">'
        html += Markdown.markdown_to_html(self.text)
        html += "</div>"
        html += "</div>"
        return html


##############################


class Plot:
    def __init__(self):
        warnings.warn(
            "rc.Plot(..) is deprecated; use rc.Widget(..), or one of the specific chart types like rc.BarChart(..), rc.HistogramChart(), or rc.PieChart(..)",
            DeprecationWarning,
            stacklevel=2,
        )


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

    def apply_common_fig_options(self, fig):
        fig.update_layout(font_family=preferred_fonts[0])
        fig.update_xaxes(title_font_family=preferred_fonts[0])

        fig.update_layout(font_size=15)
        fig.update_layout(modebar_remove="lasso")
        fig.update_xaxes(tickangle=90)
        fig.update_layout(autosize=True)

    def apply_common_kwargs(self, kwargs, label: Optional[str] = None):
        if "template" not in kwargs:
            kwargs["template"] = preferred_plotly_theme

        if label and "title" not in kwargs:
            kwargs["title"] = label


##############################

# Charting Components


class BarChart(PxBase):
    # https://plotly.com/python/bar-charts/
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
        """BarChart is a container for a plotly express bar chart.

        Args:
            df (pd.DataFrame): The data to be plotted.
            x (str): The column to be plotted on the x-axis.
            y (str): The column to be plotted on the y-axis.
            dimension (Optional[str], optional): The column to be plotted on the dimension axis. Defaults to None.
            label (Optional[str], optional): _description_. Defaults to None.
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

        PxBase.apply_common_kwargs(self, kwargs, label)

        logging.info(f"BarChart {len(self.df)} rows, {x=}, {y=}, {label=}")

    @strip_whitespace
    def to_html(self) -> str:
        fig = px.bar(self.df, x=self.x, y=self.y, **self.kwargs)

        PxBase.apply_common_fig_options(self, fig)
        fig.update_layout(bargap=0.1)

        return fig.to_html(
            include_plotlyjs=False, full_html=False, config={"responsive": True}
        )


##############################


class PieChart(PxBase):
    # https://plotly.com/python/pie-charts/

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

        PxBase.apply_common_kwargs(self, kwargs, label)

        if "hole" not in kwargs:
            self.kwargs["hole"] = 0.3

        logging.info(f"PieChart {len(self.df)} rows, {values=}, {names=}, {label=}")

    def to_html(self) -> str:
        fig = px.pie(
            self.df,
            values=self.values,
            names=self.names,
            **self.kwargs,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(uniformtext_minsize=10, uniformtext_mode="hide")

        PxBase.apply_common_fig_options(self, fig)

        return fig.to_html(
            include_plotlyjs=False, full_html=False, config={"responsive": True}
        )


##############################


class HistogramChart(PxBase):
    # https://plotly.com/python/histograms/
    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        **kwargs: Optional[Dict],
    ):
        """HistogramChart is a container for a plotly express histogram chart.

        Args:
            df (pd.DataFrame): The data to be plotted.
            x (str): The column to be plotted on the x-axis.
            dimension (Optional[str], optional): The column to be plotted on the dimension axis. Defaults to None.
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        self.df = df
        self.x = x
        self.kwargs = kwargs

        assert x in df.columns, f"{x} not in df"

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["color"] = dimension

        PxBase.apply_common_kwargs(self, kwargs, label)

        logging.info(f"HistogramChart {len(self.df)} rows, {x=}, {label=}")

    def to_html(self) -> str:
        fig = px.histogram(self.df, x=self.x, **self.kwargs)
        fig.update_layout(bargap=0.1)

        PxBase.apply_common_fig_options(self, fig)

        return fig.to_html(
            include_plotlyjs=False, full_html=False, config={"responsive": True}
        )


class Heading(Base):
    def __init__(
        self,
        label: str,
        *,
        level: Optional[int] = 1,
    ):
        """Heading is a container for a heading. It can also take a level.

        Args:
            label (str): _description_
            level (int, optional): _description_. Defaults to 1.
        """
        Base.__init__(self, label=label)
        assert (
            level >= 1 and level <= 5
        ), f"heading level ({level}) must be between 1 and 5 (inclusive)"
        assert label, "No heading label provided"
        self.level = level
        logging.info(f"Heading (h{level}): [{label}]")

    @strip_whitespace
    def to_html(self) -> str:
        return f"<br /><h{self.level}>{self.label}</h{self.level}><br />"


##############################


class Separator(Base):
    def __init__(self, label: Optional[str] = None):
        """Separator is a container for a horizontal line. It can also take a label.

        Args:
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Base.__init__(self, label=label)
        logging.info("Separator")

    @strip_whitespace
    def to_html(self) -> str:
        if self.label:
            return f"<br /><hr /><report-caption>{self.label}</report-caption>"
        else:
            return "<b r/><hr />"


##############################


class Text(Base):
    def __init__(
        self, text: str, *, label: Optional[str] = None, extra_css: str = None
    ):
        """Text is a container for raw text. It can also take extra CSS."""
        Base.__init__(self, label=label)
        self.text = text
        self.extra_css = extra_css or ""

        logging.info(f"Text {len(self.text)} characters")

    @strip_whitespace
    def to_html(self) -> str:
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
            f"Select {len(self.blocks)} tabs: {', '.join([c.label for c in self.blocks])}"
        )

    @strip_whitespace
    def to_html(self) -> str:
        html = f"<report-caption>{self.label}</report-caption>" if self.label else ""

        # assemble the button bar for the tabs
        html += """<div class="tab">"""
        for i, block in enumerate(self.blocks):
            extra = "defaultOpen" if i == 0 else ""
            html += f"""<button class="tablinks {extra}" onclick="openTab(event, '{block.label}')">{block.label}</button>"""
        html += """</div>"""

        # assemble the tab contents
        for block in self.blocks:
            html += f"""<div id="{block.label}" class="tabcontent">"""
            html += block.to_html()
            html += """</div>"""

        return html


##############################


class Unformatted(Base):
    def __init__(self, text: str, *, label: Optional[str] = None):
        """Unformatted is a container for any text that should be displayed verbatim with a non-proportional font.

        Args:
            text (str): _description_
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
        """Language is a container for code. It can also take a label.

        Args:
            text (str): _description_
            language (str): _description_
            label (Optional[str], optional): _description_. Defaults to None.
        """

        Base.__init__(self, label=label)
        self.text = text
        self.language = language
        logging.info(f"{language} {len(self.text)} characters")

    @strip_whitespace
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


class Yaml(Language):
    def __init__(self, data: Union[Dict, List], *, label: Optional[str] = None):
        """Yaml is a container for yaml. It can also take a label.

        Args:
            data (Union[Dict, List]): _description_
            label (Optional[str], optional): _description_. Defaults to None.
        """
        Language.__init__(
            self,
            yaml.dump(data, indent=2),
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
    def __init__(self, title: str, *, description: Optional[str] = None):
        """ReportCreator is a container for all components. It can also take a title and description."""
        self.title = title
        self.description = description
        logging.info(f"ReportCreator {self.title}")

        match = re.findall(r"[A-Z]", self.title)
        icon_text = "".join(match[:2]) if match else self.title[0]
        icon_color, text_color = random_color_generator(self.title)

        width = 125

        cx = width / 2
        cy = width / 2
        r = width / 2
        fs = int(r / 15)

        self.svg_str = f"""
            <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{width}" height="{width}">

                <style>
                    .icon_text_style {{
                        font-size: {fs}em;
                        font-family: lucida console, Fira Mono, monospace;
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
        if not isinstance(view, (Block, Group)):
            raise ValueError(
                f"Expected view to be either Block, or Group object, got {type(view)} instead"
            )

        logging.info(f"Saving report to {path}")

        try:
            body = view.to_html()
        except ValueError:
            body = f"""<pre>{traceback.format_exc()}</pre>"""

        file_loader = FileSystemLoader(
            f"{os.path.dirname(os.path.abspath(__file__))}/../templates"
        )
        template = Environment(loader=file_loader).get_template("default.html")

        with open(path, "w") as f:
            html = template.render(
                title=self.title or "Report",
                description=self.description or "",
                body=body,
                header_svg=self.svg_str,
            )
            if prettify_html:
                try:
                    # if beautifulsoup4 is installed we'll use it to prettify the generated html
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(html, features="lxml")
                    f.write(soup.prettify())
                except ImportError:
                    f.write(html)

            else:
                f.write(html)
