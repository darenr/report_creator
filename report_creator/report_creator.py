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

logging.basicConfig(level=logging.INFO)


def strip_whitespace(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str):
            return result.strip()
        else:
            return result

    return wrapper


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


class Group:
    # horizontally stacked compoments
    def __init__(self, *components: Base, label=None):
        self.components = components
        self.label = label
        logging.info(f"Group {len(self.components)} components {label=}")

    @strip_whitespace
    def to_html(self):
        html = "<group>"
        if self.label:
            html += f"<report_caption>{self.label}</report_caption>"

        html += "<group-component>"
        for component in self.components:
            html += "<group-article>"
            html += component.to_html()
            html += "</group-article>"

        html += "</group-component>"
        html += "</group>"

        return html


##############################


class Collapse:
    def __init__(self, label: str, *components: Base):
        self.components = components
        self.label = label
        logging.info(f"Collapse {len(self.components)} components")

    @strip_whitespace
    def to_html(self):
        html = f"<details><summary>{self.label}</summary>"

        for component in self.components:
            html += component.to_html()

        html += "</details>"
        return html


##############################


class Statistic(Base):
    def __init__(
        self, heading: str, value: Union[str, int, float], unit=None, label=None
    ):
        Base.__init__(self, label=label)
        self.heading = heading
        self.value = value
        self.unit = unit or ""
        logging.info(f"Statistic {self.heading} {self.value}")

    @strip_whitespace
    def to_html(self):
        return f"""
            <div class="statistic">
                <p>{self.heading}</p>
                <h1>{self.value}{self.unit}</h1>
            </div>
        """


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
            # 'class="fancy_table display compact nowrap" style="width:100%;"'
            'class="fancy_table display  style="width:100%;"'
        )
        self.table_html = styler.to_html()
        logging.info(f"DataTable {len(df)} rows")

    @strip_whitespace
    def to_html(self):
        return f"<div class='dataTables_wrapper'>{self.table_html}</div>"


##############################


class Html(Base):
    def __init__(self, html: str, label=None):
        Base.__init__(self, label=label)
        self.html = html
        logging.info(f"Html {len(self.html)} characters")

    @strip_whitespace
    def to_html(self):
        return self.html


##############################


class Image(Base):
    def __init__(self, img: str, label=None):
        Base.__init__(self, label=label or img)
        self.img = img
        logging.info(f"Image URL {img}, label: {self.label}")

    @strip_whitespace
    def to_html(self):
        return f"""
        <div class="image-block">
            <img src="{self.img}" alt="{self.label}">
        </div>
    """


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
                "markdown_checklist.extension",
            ],
        ).strip()

    @strip_whitespace
    def to_html(self):
        return Markdown.markdown_to_html(self.text)


##############################


class Plot(Base):
    # see https://plotly.com/python/interactive-html-export/
    # for how to make interactive

    def __init__(self, fig, label=None):
        Base.__init__(self, label=label)
        # if not isinstance(fig, matplotlib.figure.Figure, plotly.graph_objs._figure.Figure):
        #     raise ValueError(
        #         f"Expected matplotlib.figure.Figure, got {type(fig)}, try obj.get_figure()"
        #     )
        self.fig = fig
        logging.info(f"Plot")

    @strip_whitespace
    def to_html(self) -> str:
        
        html = "<div class='plot_wrapper'>"
        
        if self.label:
            html += f"<h3 class='block-bordered'>{self.label}</h3>"
        
        if isinstance(self.fig, matplotlib.figure.Figure):
            tmp = io.BytesIO()
            self.fig.set_figwidth(10)
            self.fig.tight_layout()
            self.fig.savefig(tmp, format="png")
            tmp.seek(0)
            b64image = base64.b64encode(tmp.getvalue()).decode("utf-8").replace("\n", "")
            html += f'<br/><img src="data:image/png;base64,{b64image}">'
        else:
            import plotly
            if isinstance(self.fig, plotly.graph_objs._figure.Figure):
                tmp = io.StringIO()
                self.fig.write_html(tmp)
                html += tmp.getvalue()         
            else:
                raise ValueError(f"Expected matplotlib.figure.Figure, got {type(self.fig)}, try obj.get_figure()")
            
        html += "</div>"
        
        return html

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
            return f"<h3>{self.label}</h3>{formatted_text}"
        else:
            return formatted_text


##############################


class Select(Base):
    def __init__(self, *components: Base):
        self.components = components
        for component in self.components:
            if not component.label:
                raise ValueError("All components must have a label to use in a Select")

        logging.info(
            f"Select {len(self.components)} components: {', '.join([c.label for c in self.components])}"
        )

    def to_html(self):
        """
        <div class="tab">
        <button class="tablinks" onclick="openTab(event, 'London')" id="defaultOpen">London</button>
        <button class="tablinks" onclick="openTab(event, 'Paris')">Paris</button>
        <button class="tablinks" onclick="openTab(event, 'Tokyo')">Tokyo</button>
        </div>

        <!-- Tab content -->
        <div id="London" class="tabcontent">
        <h3 class="block-bordered">London</h3>
        <p>London is the capital city of England.</p>
        </div>

        <div id="Paris" class="tabcontent">
        <h3 class="block-bordered">Paris</h3>
        <p>Paris is the capital of France.</p>
        </div>

        <div id="Tokyo" class="tabcontent">
        <h3 class="block-bordered">Tokyo</h3>
        <p>Tokyo is the capital of Japan.</p>
        </div>
        """
        
        # assemble the button bar for the tabs
        html = """<div class="tab">"""
        for i, component in enumerate(self.components):
            logging.info(f"creating tab: {component.label}")    
            extra="id='defaultOpen'" if i==0 else ""
            html += f"""<button class="tablinks" onclick="openTab(event, '{component.label}')" {extra}>{component.label}</button>"""
        html += """</div>"""

        # assemble the tab contents
        for component in self.components:
            html += f"""<div id="{component.label}" class="tabcontent">"""
            html += component.to_html()
            html += """</div>"""

        return html


##############################


class Language(Base):
    def __init__(self, text: str, language: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        self.language = language
        logging.info(f"{language} {len(self.text)} characters")

    @strip_whitespace
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
