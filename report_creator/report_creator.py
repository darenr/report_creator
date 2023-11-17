import base64
import io
import logging
import os
from string import Template
from typing import Dict, List, Sequence, Tuple, Union

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from markdown import markdown

plt.style.use("ggplot")

logging.basicConfig(level=logging.INFO)


class Base:
    def __init__(self, label: str):
        self.label = label

    def to_html(self):
        return ""


##############################


class Blocks:
    # vertically stacked compoments
    def __init__(self, *components: Base):
        self.components = components
        logging.info(f"Blocks {len(self.components)} components")

    def to_html(self):
        html = "<block>"

        for component in self.components:
            html += "<block_article>"
            html += component.to_html()
            html += "</block_article>"

        html += "</block>"

        return html


##############################


class Group:
    # horizontally stacked compoments
    def __init__(self, *components: Base):
        self.components = components
        logging.info(f"Group {len(self.components)} components")

    def to_html(self):
        html = "<group>"

        for component in self.components:
            html += "<group_article>"
            html += component.to_html()
            html += "</group_article>"
            html += "<group_separator></group_separator>"

        html += "</group>"
        return html


##############################


class Collapse:
    def __init__(self, label: str, *components: Base):
        self.components = components
        self.label = label
        logging.info(f"Collapse {len(self.components)} components")

    def to_html(self):
        html = f"<details><summary>{self.label}</summary>"

        for component in self.components:
            html += component.to_html()

        html += "</details>"
        return html


##############################


class BigNumber(Base):
    def __init__(self, heading: str, value: Union[str, int, float], label=None):
        Base.__init__(self, label=label)
        self.heading = heading
        self.value = value
        logging.info(f"BigNumber {self.heading} {self.value}")

    def to_html(self):
        return f"<div class='block-bordered'><p>{self.heading}</p><h1 class='bignumber'>{self.value}</h1></div>"


##############################


class DataTable(Base):
    def __init__(
        self,
        df: pd.DataFrame,
        label=None,
        max_rows: int = -1,
        **kwargs,
    ):
        Base.__init__(self, label=label)

        if max_rows > 0:
            styler = df.head(max_rows).style
        else:
            styler = df.style

        if label:
            styler.set_caption(label)

        styler.hide(axis="index")
        styler.set_table_attributes(
            'class="fancy_table display compact nowrap" style="width:100%;"'
        )
        self.table_html = styler.to_html()
        logging.info(f"DataTable {len(df)} rows")

    def to_html(self):
        return f"<div class='dataTables_wrapper'>{self.table_html}</div>"


##############################


class Html(Base):
    def __init__(self, html: str, label=None):
        Base.__init__(self, label=label)
        self.html = html
        logging.info(f"Html {len(self.html)} characters")

    def to_html(self):
        return self.html


##############################


class Image(Base):
    def __init__(self, img, label=None):
        Base.__init__(self, label=label)
        logging.info(f"Image")


##############################


class Markdown(Base):
    def __init__(self, text: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        logging.info(f"Markdown {len(self.text)} characters")

    @staticmethod
    def markdown_to_html(text):
        return markdown(
            text,
            extensions=[
                "markdown.extensions.fenced_code",
                "markdown.extensions.tables",
                "markdown.extensions.codehilite",
            ],
        ).strip()

    def to_html(self):
        return Markdown.markdown_to_html(self.text).strip()


##############################


class Plot(Base):
    def __init__(self, fig: matplotlib.figure.Figure, label=None):
        Base.__init__(self, label=label)
        if not isinstance(fig, matplotlib.figure.Figure):
            raise ValueError(
                f"Expected matplotlib.figure.Figure, got {type(fig)}, try obj.get_figure()"
            )
        self.fig = fig
        logging.info(f"Plot")

    def to_html(self) -> str:
        tmp = io.BytesIO()
        self.fig.set_figwidth(10)
        self.fig.tight_layout()
        self.fig.savefig(tmp, format="png")
        tmp.seek(0)
        b64image = base64.b64encode(tmp.getvalue()).decode("utf-8").replace("\n", "")
        return f'<img src="data:image/png;base64,{b64image}">'


##############################


class Section(Base):
    def __init__(self, label: str = None):
        Base.__init__(self, label=label)
        logging.info(f"Section")

    def to_html(self):
        if self.label:
            return f"<br/><div><hr/><h2>{self.label}</h2></div>"
        else:
            return f"<br/><div><hr/></div>"


##############################


class Text(Base):
    def __init__(self, text: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        logging.info(f"Text {len(self.text)} characters")

    def to_html(self):
        title = f"title='{self.label}'" if self.label else ""

        formatted_text = "\n\n".join(
            [f"<p {title}>{p.strip()}</p>" for p in self.text.split("\n\n")]
        )

        if self.label:
            return f"<h3>{self.label}</h3>{formatted_text}"
        else:
            return formatted_text


##############################


class Select(Base):
    def __init__(self, *components: Base):
        self.components = components
        logging.info(f"Select {len(self.components)} components")


##############################


class Language(Base):
    def __init__(self, text: str, language: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        self.language = language
        logging.info(f"{language} {len(self.text)} characters")

    def to_html(self):
        if self.label:
            formatted_text = f"<pre><code class='language-{self.language}'>### {self.label}\n\n{self.text.strip()}</code></pre>"
        else:
            formatted_text = f"<pre><code class='language-{self.language}'>{self.code.strip()}</code></pre>"

        return f"<div class='block-bordered'>{formatted_text}</div>"


##############################


class Python(Language):
    def __init__(self, code: str, label=None):
        Language.__init__(self, code, "python", label=label)


class Yaml(Language):
    def __init__(self, data: Union[Dict, List], label=None):
        Language.__init__(
            self,
            yaml.dump(data, sort_keys=True, indent=2),
            "yaml",
            label=label,
        )


##############################


class ReportCreator:
    def __init__(self, title: str):
        self.title = title

    def save(self, view: Base, path: str, format=True) -> None:
        logging.info(f"Saving report to {path}")

        current_path = os.path.dirname(os.path.abspath(__file__))

        with open(f"{current_path}/templates/default.html", "r") as f:
            t = Template(f.read())
            with open(path, "w") as f:
                html = t.substitute(
                    title=self.title,
                    body=view.to_html(),
                )
                if format:
                    from bs4 import BeautifulSoup as bs

                    soup = bs(html, features="lxml")
                    f.write(soup.prettify())
                else:
                    f.write(html)
