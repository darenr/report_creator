from typing import Dict, List, Sequence, Tuple, Union

import logging


class Base:
    def __init__(self, label: str):
        self.label = label

    def to_html(self):
        return ""
