from typing import Dict, List, Sequence, Tuple, Union

import logging

from .rc_base import Base


class Text(Base):
    def __init__(self, text: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        logging.info(f"Text {len(self.text)} characters")

    def to_html(self):
        title = f"title='{self.label}'" if self.label else ""

        return "\n\n".join(
            [f"<p {title}>{p.strip()}</p>" for p in self.text.split("\n\n")]
        )
