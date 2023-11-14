import logging
from typing import Dict, List, Sequence, Tuple, Union

from .rc_base import Base


class Yaml(Base):
    def __init__(self, text: str, collapse=False, label=None):
        Base.__init__(self, label=label)
        self.text = text
        self.collapse = collapse
        self.language = "yaml"
        logging.info(f"Yaml {len(self.text)} characters")

    def to_html(self):
        if self.label:
            formatted_text = f"<pre><code class='language-{self.language}'>### {self.label}\n\n{self.text.strip()}</code></pre>"
        else:
            formatted_text = f"<pre><code class='language-{self.language}'>{self.code.strip()}</code></pre>"

        if self.collapse:
            return f"<details><summary>{self.label or 'Click to see Configuration'}</summary>{formatted_text}</details>"
        else:
            return formatted_text
