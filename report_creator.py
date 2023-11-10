import logging
from string import Template
from typing import Dict, List, Sequence, Tuple, Union

import matplotlib
import pandas as pd
from bs4 import BeautifulSoup as bs
from markdown import markdown
from yaml import Dumper, dump

logging.basicConfig(level=logging.INFO)


class Base:
    def __init__(self, label: str):
        self.label = label

    def to_html(self):
        return ""


class Blocks:
    # vertically stacked compoments
    def __init__(self, *components: Base):
        self.components = components
        logging.info(f"Blocks {len(self.components)} components")

    def to_html(self):
        html = "<block>"

        for component in self.components:
            logging.info(f"adding {type(component)} to block")
            html += "<block_article>"
            html += component.to_html()
            html += "</block_article>"

        html += "</block>"

        return html


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


class Select(Base):
    def __init__(self, *components: Base):
        self.components = components
        logging.info(f"Select {len(self.components)} components")


class BigNumber(Base):
    def __init__(self, heading: str, value: Union[str, int, float], label=None):
        Base.__init__(self, label=label)
        self.heading = heading
        self.value = value
        logging.info(f"BigNumber {self.heading} {self.value}")

    def to_html(self):
        return f"<p style='color: var(--text-muted);'>{self.heading}</p><h1>{self.value}</h1>"


class DataTable(Base):
    def __init__(self, df: pd.DataFrame, label=None):
        Base.__init__(self, label=label)
        self.df = df
        logging.info(f"DataTable {len(self.df)} rows")


class Text(Base):
    def __init__(self, text: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        logging.info(f"Text {len(self.text)} characters")

    def to_html(self):
        html = ""
        for p in self.text.split("\n\n"):
            html += f"<p>{p.strip()}</p>"
        return html


class Markdown(Base):
    def __init__(self, text: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        logging.info(f"Markdown {len(self.text)} characters")

    def to_html(self):
        return markdown(self.text).strip()


class Python(Base):
    def __init__(self, code: str, label=None):
        Base.__init__(self, label=label)
        self.code = code
        self.language = "python"
        logging.info(f"Python {len(self.code)} characters")

    def to_html(self):
        preamble = f"# {self.label}\n\n" if self.label else ""
        return f"<pre><code class='language-{self.language}'>{preamble}{self.code.strip()}</code></pre>"


class Yaml(Base):
    def __init__(self, text: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        self.language = "yaml"
        logging.info(f"Yaml {len(self.text)} characters")

    def to_html(self):
        preamble = f"# {self.label}\n\n" if self.label else ""
        return f"<pre><code class='language-{self.language}'>{preamble}{self.text.strip()}</code></pre>"
        return html


class Plot(Base):
    def __init__(self, fig, label=None):
        Base.__init__(self, label=label)
        self.fig = fig


class ReportCreator:
    def __init__(self, title: str):
        self.title = title

    def save(self, view: Base, path: str, theme: str = "water") -> None:
        logging.info(f"Saving report to {path}, (theme: {theme})")

        if theme not in ["light", "dark"]:
            raise ValueError(f"Unknown theme {theme}, use one of light|dark")

        with open(f"templates/default.html", "r") as f:
            t = Template(f.read())
            with open(path, "w") as f:
                html = t.substitute(
                    title=self.title,
                    theme=theme,
                    highlight=f"stackoverflow-{theme}.min.css",
                    body=view.to_html(),
                )
                soup = bs(html, features="lxml")
                f.write(soup.prettify())


if __name__ == "__main__":
    df = pd.DataFrame(
        [["Daren", 42], ["Yekaterina", 15], ["Andrea", 14]], columns=["Name", "Age"]
    )
    fig = df.plot.bar(x="Name", y="Age")

    report = ReportCreator("My Report")

    view = Blocks(
        Group(
            BigNumber(
                heading="Chances of rain",
                value="84%",
            ),
            BigNumber(heading="Loss", value=0.1),
            BigNumber(heading="Accuracy", value=95),
        ),
        Text("This is a paragraph.\n\nThis is another paragraph."),
        Yaml(
            """
doe: "a deer, a female deer"
ray: "a drop of golden sun"
pi: 3.14159
xmas: true
french-hens: 3
calling-birds:
- huey
- dewey
- louie
- fred
xmas-fifth-day:
calling-birds: four
french-hens: 3
golden-rings: 5
partridges:
    count: 1
    location: "a pear tree"
turtle-doves: two             
        """,
            label="Random Yaml",
        ),
        Python(
            "import pandas as pd\n\ndf = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})",
            label="Some random python",
        ),
        Markdown(
            """
> #### The quarterly results look great!
>
> - Revenue was off the chart.
> - Profits were higher than ever.
>
>  *Everything* is going according to **plan**.                 
        """
        ),
        Plot(fig, label="Chart"),
        DataTable(df, label="Data"),
    )

    report.save(view, "aa.html", theme="dark")
