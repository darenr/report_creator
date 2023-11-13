from typing import Dict, List, Sequence, Tuple, Union

import logging

from .rc_base import Base


class Section(Base):
    def __init__(self, label: str=None):
        Base.__init__(self, label=label)
        logging.info(f"Section")

    def to_html(self):
        if self.label:
            return f"<br/><div><hr/><h2>{self.label}</h2></div>"
        else:
            return f"<br/><div><hr/></div>"
