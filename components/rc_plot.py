from typing import Dict, List, Sequence, Tuple, Union

import logging

from .rc_base import Base


class Plot(Base):
    def __init__(self, fig, label=None):
        Base.__init__(self, label=label)
        self.fig = fig
