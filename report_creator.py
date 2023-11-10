import logging
from string import Template
from typing import Dict, List, Sequence, Tuple, Union

import matplotlib
import pandas as pd
import numpy as np
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
        return f"<p class='bignumber'>{self.heading}</p><h1 class='bignumber'>{self.value}</h1>"


class DataTable(Base):
    def __init__(self, df: pd.DataFrame, label=None, max_rows=None, hide_index=True):
        Base.__init__(self, label=label)
        self.df = df
        self.max_rows = max_rows
        self.hide_index = hide_index
        logging.info(f"DataTable {len(self.df)} rows")
        
    def to_html(self):
        
        # properties = {"border": "2px solid gray", "color": "green", "font-size": "16px"}
        # styler = self.df.style.set_properties(**properties)
        # if self.label:
        #     styler.set_caption(self.label)
            
        # styler.format(precision=3)  
           
        # if self.hide_index: 
        #     styler.hide()

        # return styler.to_html(max_rows=self.max_rows)
    
        styles = [
        #table properties
        dict(selector=" ", 
             props=[("margin","0"),
                    ("font-family",'"Helvetica", "Arial", sans-serif'),
                    ("border-collapse", "collapse"),
                    ("border","none"),
                       ]),



        #background shading
        dict(selector="tbody tr:nth-child(even)",
             props=[("background-color", "#fff")]),
        dict(selector="tbody tr:nth-child(odd)",
             props=[("background-color", "#eee")]),

        #cell spacing
        dict(selector="td", 
             props=[("padding", ".5em")]),

        #header cell properties
        dict(selector="th", 
             props=[("font-size", "100%"),
                    ("text-align", "center")]),

        dict(selector="caption",
             props=[("color", "var(--text-muted)"),
                    ("padding-bottom", "10px"),
                    ("font-size", "1.5em")]),
        ]

        styler = self.df.style.set_table_styles(styles)
        
        if self.label:
            styler.set_caption(self.label)

        if self.hide_index: 
            styler.hide()

        return styler.to_html(max_rows=self.max_rows)        
    
    


class Text(Base):
    def __init__(self, text: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        logging.info(f"Text {len(self.text)} characters")

    def to_html(self):
        title = f"title='{self.label}'" if self.label else ""

        return '\n\n'.join([f"<p {title}>{p.strip()}</p>" for p in self.text.split("\n\n")])



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
    boring_df = pd.DataFrame(
        [["Daren", 42], ["Yekaterina", 15], ["Andrea", 14]], columns=["Name", "Age"]
    )
    

    
    fig = boring_df.plot.bar(x="Name", y="Age")

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
        Text("""Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, “and what is the use of a book,” thought Alice “without pictures or conversations?”

So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her.

There was nothing so very remarkable in that; nor did Alice think it so very much out of the way to hear the Rabbit say to itself, “Oh dear! Oh dear! I shall be late!” (when she thought it over afterwards, it occurred to her that she ought to have wondered at this, but at the time it all seemed quite natural); but when the Rabbit actually took a watch out of its waistcoat-pocket, and looked at it, and then hurried on, Alice started to her feet, for it flashed across her mind that she had never before seen a rabbit with either a waistcoat-pocket, or a watch to take out of it, and burning with curiosity, she ran across the field after it, and fortunately was just in time to see it pop down a large rabbit-hole under the hedge.
        """, label="Alice in Wonderland"),
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
        DataTable(boring_df, label="Boring data"),
    )

    report.save(view, "aa.html", theme="light")
