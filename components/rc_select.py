import logging
from typing import Dict, List, Sequence, Tuple, Union

from .rc_base import Base


class Select(Base):
    def __init__(self, *components: Base):
        self.components = components
        logging.info(f"Select {len(self.components)} components")
