import base64
import io
import json
import logging
import os
import traceback
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Sequence, Tuple, Union

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from jinja2 import Environment, FileSystemLoader, Template
from markdown import markdown
from markupsafe import escape

logging.basicConfig(level=logging.INFO)


def markdown_to_html(text: str):
    return markdown(
        text.strip(),
        extensions=[
            "markdown.extensions.fenced_code",
            "markdown.extensions.tables",
            "markdown_checklist.extension",
        ],
    ).strip()


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


class Base(ABC):
    def __init__(self, label: Optional[str] = None):
        self.label = label

    @abstractmethod
    def to_html(self):
        """Each component that derives from Base must implement this method"""


##############################


class Block(Base):
    # vertically stacked compoments
    def __init__(self, *components: Base):
        Base.__init__(self)
        self.components = components
        logging.info(f"Block: {len(self.components)} components")

    @strip_whitespace
    def to_html(self):
        html = "<block>"

        for component in self.components:
            html += "<block-article>"
            html += component.to_html()
            html += "</block-article>"

        html += "</block>"

        return html


##############################


class Group(Base):
    # horizontally stacked compoments
    def __init__(self, *components: Base, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.components = components
        logging.info(f"Group: {len(self.components)} components {label=}")

    @strip_whitespace
    def to_html(self):
        html = "<div>"

        if self.label:
            html += f"<report-caption>{self.label}</report-caption>"

        html += """<div class="group">"""

        for component in self.components:
            html += """
                <div class="group-item">
                    <div class="group-content">"""

            html += component.to_html()

            html += """
                </div>
                    </div>"""

        html += "</div>"

        html += "</div>"
        html += "</div>"

        return html


##############################


class Collapse(Base):
    def __init__(self, *components: Base, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.components = components
        logging.info(f"Collapse {len(self.components)} components, {label=}")

    @strip_whitespace
    def to_html(self):
        html = f"<details><summary>{self.label}</summary>"

        for component in self.components:
            html += component.to_html()

        html += "</details>"
        return html


##############################


class Widget(Base):
    # This component is used to add a widget to the report, a widget is any
    # component that supports the _repr_html_ method, such as a plotly figure,
    # anything written for Jupyter. sklearn Pipelines for example.
    def __init__(self, widget, label: Optional[str] = None):
        Base.__init__(self, label=label)
        if not hasattr(widget, "_repr_html_"):
            raise ValueError(
                f"Expected widget to have a _repr_html_ method, got {type(widget)} instead"
            )
        self.widget = widget

        logging.info(f"Widget {type(self.widget)}")

    @strip_whitespace
    def to_html(self):
        html = "<div class='report-widget'>"

        if self.label:
            html += f"<report-caption>{self.label}</report-caption>"

        html += self.widget._repr_html_()

        html += "</div>"
        return html


##############################


class HTML(Base):
    def __init__(self, html: Optional[str], label=None):
        Base.__init__(self, label=label)
        self.html = html

        logging.info(f"HTML {len(self.html)} bytes")

    @strip_whitespace
    def to_html(self):
        return self.html


##############################


class Metric(Base):
    def __init__(
        self,
        heading: str,
        value: Union[str, int, float],
        unit=None,
        float_precision=3,
        label: Optional[str] = None,
    ):
        Base.__init__(self, label=label)
        self.heading = heading
        self.float_precision = float_precision
        self.value = value
        self.unit = unit or ""
        logging.info(f"Metric {self.heading} {self.value}")

    @strip_whitespace
    def to_html(self):
        if isinstance(self.value, (float)):
            value = round(self.value, self.float_precision)
        else:
            value = self.value

        return f"""
            <div class="metric">
                <p>{self.heading}</p>
                <h1>{value}{self.unit}</h1>
            </div>
        """


##############################


class Table(Widget):
    def __init__(
        self,
        df: pd.DataFrame,
        label: Optional[str] = None,
        max_rows: int = -1,
        float_precision: int = 3,
        **kwargs,
    ):
        Widget.__init__(self, df, label=label)


##############################


class DataTable(Base):
    def __init__(
        self,
        df: pd.DataFrame,
        label: Optional[str] = None,
        max_rows: int = -1,
        float_precision: int = 3,
        **kwargs,
    ):
        Base.__init__(self, label=label)

        if max_rows > 0:
            styler = df.head(max_rows).style
        else:
            styler = df.style

        if label:
            styler.set_caption(label)

        styler.format(precision=float_precision)
        styler.hide(axis="index")
        styler.set_table_attributes(
            'class="remove-all-styles fancy_table display row-border hover responsive nowrap" cellspacing="0" style="width: 100%;"'
        )
        self.table_html = styler.to_html()
        logging.info(f"DataTable {len(df)} rows")

    @strip_whitespace
    def to_html(self):
        return f"<div class='dataTables_wrapper'><br/>{self.table_html}</div>"


##############################


class Html(Base):
    def __init__(self, html: str, css: str = None, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.html = html
        self.css = css
        logging.info(f"HTML {len(self.html)} characters")

    @strip_whitespace
    def to_html(self):
        html = f"<style>{self.css}</style>" if self.css else ""
        if self.label:
            html += f"<report-caption>{self.label}</report-caption>"
        html += self.html
        return html


##############################


class Image(Base):
    def __init__(self, img: str, link: str = None, label: Optional[str] = None):
        Base.__init__(self, label=label or img)
        self.img = img
        self.link = link or img
        logging.info(f"Image URL {img}, label: {self.label}")

    @strip_whitespace
    def to_html(self):
        html = """<div class="image-block"><figure>"""

        html += f"""<a href="{self.link}" target="_blank"><img src="{self.img}" alt="{self.label}"></a>"""
        if self.label:
            html += f"<figcaption><report-caption>{self.label}</report-caption></figcaption>"
        html += "</figure></div>"

        return html


##############################


class Markdown(Base):
    def __init__(self, text: str, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.text = text
        logging.info(f"Markdown {len(self.text)} characters")

    @staticmethod
    def markdown_to_html(text):
        return markdown_to_html(text)

    @strip_whitespace
    def to_html(self):
        html = """<div class='markdown_wrapper'>"""
        if self.label:
            html += f"<report-caption>{self.label}</report-caption>"
        html += Markdown.markdown_to_html(self.text)
        html += "</div>"
        return html


##############################


class Plot(Base):
    # see https://plotly.com/python/interactive-html-export/
    # for how to make interactive

    def __init__(self, fig, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.fig = fig
        if hasattr(fig, "get_figure"):
            self.fig = fig.get_figure()
        logging.info(f"Plot: {type(self.fig)} {self.label=}")

    @strip_whitespace
    def to_html(self) -> str:
        html = "<div class='plot_wrapper'>"

        if self.label:
            html += f"<report-caption>{self.label}</report-caption>"

        if isinstance(self.fig, matplotlib.figure.Figure):
            tmp = io.BytesIO()
            self.fig.set_figwidth(10)
            self.fig.tight_layout()
            self.fig.savefig(tmp, format="png")
            tmp.seek(0)
            b64image = (
                base64.b64encode(tmp.getvalue()).decode("utf-8").replace("\n", "")
            )
            html += f'<br/><img src="data:image/png;base64,{b64image}">'
        else:
            import plotly

            if isinstance(self.fig, plotly.graph_objs._figure.Figure):
                tmp = io.StringIO()
                self.fig.write_html(tmp)
                html += tmp.getvalue()
            else:
                raise ValueError(
                    f"Expected matplotlib.figure.Figure, got {type(self.fig)}, try obj.get_figure()"
                )

        html += "</div>"

        return html


##############################


class Separator(Base):
    def __init__(self, label: Optional[str] = None):
        Base.__init__(self, label=label)
        logging.info(f"Separator")

    @strip_whitespace
    def to_html(self):
        if self.label:
            return f"<br /><hr /><report-caption>{self.label}</report-caption>"
        else:
            return f"<b r/><hr />"


##############################


class Text(Base):
    def __init__(self, text: str, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.text = text
        logging.info(f"Text {len(self.text)} characters")

    @strip_whitespace
    def to_html(self):
        title = f"title='{self.label}'" if self.label else ""

        formatted_text = "\n\n".join(
            [
                f"<p class='indented-text-block'>{p.strip()}</p>"
                for p in self.text.split("\n\n")
            ]
        )

        if self.label:
            return f"""<report-caption>{self.label}</report-caption>{formatted_text}"""
        else:
            return formatted_text


##############################


class Select(Base):
    def __init__(self, blocks: List[Base], label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.blocks = blocks
        for blocks in self.blocks:
            if not blocks.label:
                raise ValueError("All blocks must have a label to use in a Select")

        logging.info(
            f"Select {len(self.blocks)} comblocksponents: {', '.join([c.label for c in self.blocks])}"
        )

    @strip_whitespace
    def to_html(self):
        if self.label:
            html = f"<report-caption>{self.label}</report-caption>"
        else:
            html = ""

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


class Language(Base):
    def __init__(self, text: str, language: str, label: Optional[str] = None):
        Base.__init__(self, label=label)
        self.text = text
        self.language = language
        logging.info(f"{language} {len(self.text)} characters")

    @strip_whitespace
    def to_html(self):
        if self.label:
            formatted_text = f"<pre><code class='language-{self.language}'>### {self.label}\n\n{self.text.strip()}</code></pre>"
        else:
            formatted_text = f"<pre><code class='language-{self.language}'>{self.text.strip()}</code></pre>"

        return f"""<div class="code-block">{formatted_text}</div>"""


##############################


class Python(Language):
    def __init__(self, code: str, label: Optional[str] = None):
        Language.__init__(self, escape(code), "python", label=label)


##############################


class Yaml(Language):
    def __init__(self, data: Union[Dict, List], label: Optional[str] = None):
        Language.__init__(
            self,
            yaml.dump(data, indent=2),
            "yaml",
            label=label,
        )


##############################


class Json(Language):
    def __init__(self, data: Union[Dict, List], label: Optional[str] = None):
        Language.__init__(
            self,
            json.dumps(data, indent=2),
            "json",
            label=label,
        )


##############################


class ReportCreator:
    def __init__(self, title: str, description: Optional[str] = None):
        self.title = title
        self.description = description
        logging.info(f"ReportCreator {self.title}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def save(self, view: Base, path: str, prettify_html=True, mode: str = "light") -> None:
        if not isinstance(view, (Block, Group)):
            raise ValueError(
                f"Expected view to be either Block, or Group object, got {type(view)} instead"
            )

        if mode not in ["light", "dark"]:
            raise ValueError(
                f"Expected mode to be 'light' or 'dark', got {mode} instead"
            )

        logging.info(f"Saving report to {path} [{mode} mode]")

        current_path = os.path.dirname(os.path.abspath(__file__))

        try:
            body = view.to_html()
        except ValueError:
            body = f"""<pre>{traceback.format_exc()}</pre>"""

        file_loader = FileSystemLoader("templates")
        template = Environment(loader=file_loader).get_template("default.html")

        with open(path, "w") as f:
            html = template.render(
                title=self.title or "Report",
                description=self.description or "",
                body=body,
                mode=mode,
            )
            if prettify_html:
                try:
                    # if beautifulsoup4 is installed we'll use it to prettify the generated html
                    from bs4 import BeautifulSoup as bs

                    soup = bs(html, features="lxml")
                    f.write(soup.prettify())
                except ImportError:
                    f.write(html)

            else:
                f.write(html)
