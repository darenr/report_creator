from typing import Dict, List, Sequence, Tuple, Union

import logging

from .rc_base import Base


class Python(Base):
    def __init__(self, code: str, collapse=False, label=None):
        Base.__init__(self, label=label)
        self.code = code
        self.collapse = collapse
        self.language = "python"
        logging.info(f"Python {len(self.code)} characters")

    def to_html(self):
        if self.label:
            formatted_text = f"<pre><code class='language-{self.language}'>### {self.label}\n\n{self.code.strip()}</code></pre>"
        else:
            formatted_text = f"<pre><code class='language-{self.language}'>{self.code.strip()}</code></pre>"

        if self.collapse:
            return f"<details><summary>{self.label or 'Click to see Code'}</summary>{formatted_text}</details>"
        else:
            return formatted_text