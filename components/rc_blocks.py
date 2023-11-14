import logging
from typing import Dict, List, Sequence, Tuple, Union

from .rc_base import Base


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
