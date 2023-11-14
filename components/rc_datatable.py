from typing import Dict, List, Sequence, Tuple, Union

import logging

import pandas as pd
import numpy as np

from .rc_base import Base

class DataTable(Base):
    def __init__(self, df: pd.DataFrame, collapse=False, label=None, max_rows: int = -1, **kwargs):
        Base.__init__(self, label=label)
        
        self.collapse = collapse

        if max_rows > 0:
            styler = df.head(max_rows).style
        else:
            styler = df.style
            
        if label:
            styler.set_caption(label)
            
        styler.hide(axis="index")
        styler.set_table_attributes('class="fancy_table display compact nowrap" style="width:100%;"')  
        self.table_html = styler.to_html()
        logging.info(f"DataTable {len(df)} rows")
        
        

    def to_html(self):
        formatted_text = f"<div class='dataTables_wrapper'>{self.table_html}</div>"
        
        if self.collapse:
            if self.label:
                return f"<details><summary>{self.label}</summary>{formatted_text}</details>"
            else:
                return f"<details><summary>Click to see Data Table</summary>{formatted_text}</details>"
            
        else:
            return formatted_text

            
