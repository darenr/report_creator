from typing import Dict, List, Sequence, Tuple, Union

import logging

from markdown import markdown

from .rc_base import Base


class Markdown(Base):
    def __init__(self, text: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        logging.info(f"Markdown {len(self.text)} characters")

    def to_html(self):
        return markdown(self.text).strip()
