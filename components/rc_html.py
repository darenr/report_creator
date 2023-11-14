import logging
from typing import Dict, List, Sequence, Tuple, Union

from .rc_base import Base


class Html(Base):
    def __init__(self, html: str, label=None):
        Base.__init__(self, label=label)
        self.html = html
        logging.info(f"Html {len(self.html)} characters")

    def to_html(self):
        return self.html
