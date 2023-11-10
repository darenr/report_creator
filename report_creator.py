import logging
from string import Template
from typing import Dict, List, Sequence, Tuple, Union

import matplotlib
import pandas as pd
from markdown import markdown
from yaml import Dumper, dump
from bs4 import BeautifulSoup as bs

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
        return f"<div><h1>{self.heading}</h1><h2>{self.value}</h2></div>"

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
            html += f"<p>{p}</p>"
        return html

class Markdown(Base):
    def __init__(self, text: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        logging.info(f"Markdown {len(self.text)} characters")        
    
    def to_html(self):
        return markdown(self.text)


class Plot(Base):
    def __init__(self, fig, label=None):
        Base.__init__(self, label=label)
        self.fig = fig


class ReportCreator:
    def __init__(self, title: str, template="default"):
        self.title = title
        self.template = template

    def save(self, view: Base, path: str) -> None:
        logging.info(f"Saving report to {path}")
        
        with open(f"templates/{self.template}.html", "r") as f:
            t = Template(f.read())
            with open(path, "w") as f:
                html = t.substitute(title=self.title, body=view.to_html())
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
                heading="Number of percentage points",
                value="84%",
            ),
            BigNumber(heading="Simple Statistic", value=100)
        ),
        Text("This is a paragraph.\n\nThis is another paragraph."),
        Markdown("""
> #### The quarterly results look great!
>
> - Revenue was off the chart.
> - Profits were higher than ever.
>
>  *Everything* is going according to **plan**.                 
        """),
        Plot(fig, label="Chart"),
        DataTable(df, label="Data"),
    )

    report.save(view, "aa.html")
