import logging
from typing import Optional, Union

import pandas as pd

from ..utilities import (
    _strip_whitespace,
)
from .base import Base
from .charts import Widget

# Configure logging
logger = logging.getLogger("report_creator")


class Table(Widget):
    """
    Displays a Pandas DataFrame or a list of dictionaries as a formatted HTML table.

    The `Table` component provides a straightforward way to render tabular data within a report.
    It supports both Pandas DataFrames and lists of dictionaries as input and
    offers basic styling and formatting options.

    Args:
        data (Union[pd.DataFrame, list[dict]]): The data to be displayed in the table.
            This can be either a Pandas DataFrame or a list of dictionaries, where each
            dictionary represents a row in the table.
        label (Optional[str], optional): An optional label or caption for the table.
            If provided, it will be displayed above the table. Defaults to None.
        index (bool, optional): Whether to display the DataFrame index column in the
            rendered table. If False, the index will be hidden. Defaults to False.
        float_precision (int, optional): The number of decimal places to display for
            floating-point numbers in the table. Defaults to 3.

    Raises:
        ValueError: If the `data` argument is not a Pandas DataFrame or a list of dictionaries.
    """

    def __init__(
        self,
        data: Union[pd.DataFrame, list[dict]],
        *,
        label: Optional[str] = None,
        index: Optional[bool] = False,
        float_precision: Optional[int] = 2,
    ):
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError(f"Expected data to be a list or pd.DataFrame, got {type(data)}")

        s = df.style if index else df.style.hide()
        logger.info(f"Table: {len(df)} rows, {len(df.columns)} columns")
        Widget.__init__(self, s.format(escape="html", precision=float_precision), label=label)


class DataTable(Base):
    """
    Displays a sortable and searchable table from a Pandas DataFrame or a list of dictionaries.

    The `DataTable` component renders tabular data in an interactive HTML table
    with built-in search and sort capabilities. It provides a user-friendly way
    to explore and analyze datasets directly within a report.

    Args:
        data (Union[pd.DataFrame, list[dict]]): The data to be displayed in the table.
            This can be either a Pandas DataFrame or a list of dictionaries, where each
            dictionary represents a row in the table.
        label (Optional[str], optional): An optional label or caption for the table.
            If provided, it will be used as the table's caption. Defaults to None.
        wrap_text (bool, optional): If True, text within table cells will wrap to
            fit the cell width. If False, text will not wrap and may be truncated.
            Defaults to True.
        index (bool, optional): If True, the DataFrame index will be displayed as
            the first column in the table. If False, the index will be hidden.
            Defaults to False.
        max_rows (int, optional): The maximum number of rows to display in the table.
            If set to -1, all rows will be displayed. Defaults to -1.
        float_precision (int, optional): The number of decimal places to display for
            floating-point numbers in the table. Defaults to 3.

    Raises:
        ValueError: If the `data` argument is not a Pandas DataFrame or a list of dictionaries.
    """

    def __init__(
        self,
        data: Union[pd.DataFrame, list[dict]],
        *,
        label: Optional[str] = None,
        wrap_text: bool = True,
        index: Optional[bool] = False,
        max_rows: Optional[int] = -1,
        float_precision: Optional[int] = 2,
    ):
        super().__init__(label=label)

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError(f"Expected data to be a list or pd.DataFrame, got {type(data)}")

        styler = df.head(max_rows).style if max_rows > 0 else df.style

        if label:
            styler.set_caption(label)

        data_table_classes = [
            "fancy-table",
            "display",
            "row-border",
            "hover",
            "responsive",
        ]
        if not wrap_text:
            data_table_classes.append("nowrap")

        if not index:
            styler.hide(axis="index")

        styler.set_table_attributes(
            f'class="{" ".join(data_table_classes)} cellspacing="0" style="width: 100%;"'
        )
        self.table_html = styler.format(escape="html", precision=float_precision).to_html()
        logger.info(f"DataTable: {len(df)} rows, {len(df.columns)} columns")

    @_strip_whitespace
    def to_html(self) -> str:
        return f"<div class='dataTables-wrapper include_datatable'><br/>{self.table_html}</div>"
