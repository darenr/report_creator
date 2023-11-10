from typing import Dict, List, Sequence, Tuple, Union

import logging

from .rc_base import Base


class Yaml(Base):
    def __init__(self, text: str, label=None):
        Base.__init__(self, label=label)
        self.text = text
        self.language = "yaml"
        logging.info(f"Yaml {len(self.text)} characters")

    def to_html(self):
        preamble = f"# {self.label}\n\n" if self.label else ""
        return f"<pre><code class='language-{self.language}'>{preamble}{self.text.strip()}</code></pre>"
        return html
