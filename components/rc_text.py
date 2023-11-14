import logging
from typing import Dict, List, Sequence, Tuple, Union

from .rc_base import Base


class Text(Base):
    def __init__(self, text: str, collapse=False, label=None):
        Base.__init__(self, label=label)
        self.text = text
        self.collapse = collapse
        logging.info(f"Text {len(self.text)} characters")

    def to_html(self):
        title = f"title='{self.label}'" if self.label else ""

        formatted_text = "\n\n".join(
            [f"<p {title}>{p.strip()}</p>" for p in self.text.split("\n\n")]
        )
        if self.collapse:
            if self.label:
                return f"<details><summary>{self.label}</summary>{formatted_text}</details>"
            else:
                return f"<details><summary>Click to see Text</summary>{formatted_text}</details>"
        else:
            if self.label:
                return f"<h3>{self.label}</h3>{formatted_text}"
            else:
                return formatted_text
