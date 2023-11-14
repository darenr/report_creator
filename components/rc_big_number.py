import logging
from typing import Dict, List, Sequence, Tuple, Union

from .rc_base import Base


class BigNumber(Base):
    def __init__(self, heading: str, value: Union[str, int, float], label=None):
        Base.__init__(self, label=label)
        self.heading = heading
        self.value = value
        logging.info(f"BigNumber {self.heading} {self.value}")

    def to_html(self):
        return f"<div class='bignumber'><p>{self.heading}</p><h1 class='bignumber'>{self.value}</h1></div>"
