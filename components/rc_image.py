import base64
import io
import logging
from typing import Dict, List, Sequence, Tuple, Union

from matplotlib import figure

from .rc_base import Base


class Image(Base):
    def __init__(self, img, label=None):
        Base.__init__(self, label=label)
        logging.info(f"Image")
