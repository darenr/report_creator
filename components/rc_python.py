from typing import Dict, List, Sequence, Tuple, Union

import logging

from .rc_base import Base


class Python(Base):
    def __init__(self, code: str, label=None):
        Base.__init__(self, label=label)
        self.code = code
        self.language = "python"
        logging.info(f"Python {len(self.code)} characters")

    def to_html(self):
        preamble = f"# {self.label}\n\n" if self.label else ""
        return f"<pre><code class='language-{self.language}'>{preamble}{self.code.strip()}</code></pre>"
