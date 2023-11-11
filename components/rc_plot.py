from typing import Dict, List, Sequence, Tuple, Union

import logging
import io
import base64
from matplotlib import figure

from .rc_base import Base


class Plot(Base):
    def __init__(self, fig: figure.Figure, label=None):
        Base.__init__(self, label=label)
        if not isinstance(fig, figure.Figure):
            raise ValueError(f"Expected matplotlib.figure.Figure, got {type(fig)}, try obj.get_figure()")
        self.fig = fig
        logging.info(f"Plot")

    def to_html(self) -> str:
        tmp = io.BytesIO()
        self.fig.savefig(tmp, format='png')
        tmp.seek(0)
        b64image = base64.b64encode(tmp.getvalue()).decode("utf-8").replace("\n", "")
        return f'<img src="data:image/png;base64,{b64image}">'