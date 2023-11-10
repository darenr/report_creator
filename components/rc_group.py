from typing import Dict, List, Sequence, Tuple, Union

import logging

from .rc_base import Base


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
