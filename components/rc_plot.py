from typing import Dict, List, Sequence, Tuple, Union

import logging
import io
import base64
import matplotlib

import matplotlib.pyplot as plt
plt.style.use('ggplot')


from .rc_base import Base


class Plot(Base):
    def __init__(self, fig: matplotlib.figure.Figure, label=None):
        Base.__init__(self, label=label)
        if not isinstance(fig, matplotlib.figure.Figure):
            raise ValueError(f"Expected matplotlib.figure.Figure, got {type(fig)}, try obj.get_figure()")
        self.fig = fig
        logging.info(f"Plot")

    def to_html(self) -> str:
        tmp = io.BytesIO()
        self.fig.set_figwidth(10)
        self.fig.tight_layout()
        self.fig.savefig(tmp, format='png')
        tmp.seek(0)
        b64image = base64.b64encode(tmp.getvalue()).decode("utf-8").replace("\n", "")
        return f'<img src="data:image/png;base64,{b64image}">'