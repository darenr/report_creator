import logging
from string import Template
from typing import Dict, List, Sequence, Tuple, Union

from bs4 import BeautifulSoup as bs

logging.basicConfig(level=logging.INFO)

from components import *


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
                    code_highlight=f"stackoverflow-{theme}.css",
                    body=view.to_html(),
                )
                soup = bs(html, features="lxml")
                f.write(soup.prettify())
