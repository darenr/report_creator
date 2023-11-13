from typing import Dict, List, Sequence, Tuple, Union

import logging

from .rc_base import Base


class Summary(Base):
    def __init__(self, summary: str, text: str, label=None):
        Base.__init__(self, label=label)
        self.summary = summary
        self.text = text
        logging.info(f"Summary '{summary}' {len(self.text)} characters")

    def to_html(self):
        
        title = f"title='{self.label}'" if self.label else ""
        
        formatted_text = ''.join(
            [f"<p {title}>{p.strip()}</p>" for p in self.text.split("\n\n")]
        )
        return f"<details><summary>{self.summary}</summary>{formatted_text}</details>"
