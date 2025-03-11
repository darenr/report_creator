import base64
import io
import logging
from abc import abstractmethod
from typing import Optional, Union

import matplotlib
import matplotlib.figure
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from ..utilities import (
    _generate_anchor_id,
    _strip_whitespace,
)
from .base import Base

# Configure logging
logger = logging.getLogger("report_creator")


class Widget(Base):
    """
    A container for embedding and rendering external content or interactive widgets.

    The `Widget` component is designed to display objects that can render themselves
    as HTML, such as Pandas DataFrames, Matplotlib figures, and Plotly figures.
    It acts as a bridge between these external objects and the report, enabling
    their seamless integration.

    Args:
        widget (Any): The external widget or object to be embedded within the report.
        label (Optional[str], optional): An optional label or caption for the widget.
            If provided, it will be displayed above the widget in the rendered report.
            Defaults to None.

    Raises:
        ValueError: If the provided widget does not have an `_repr_html_` method.
    """

    def __init__(self, widget: any, *, label: Optional[str] = None):
        super().__init__(label=label)
        if isinstance(widget, go.Figure):
            self.widget = widget
            PxBase.apply_common_fig_options(self.widget)
        elif hasattr(widget, "get_figure"):
            self.widget = widget.get_figure()
        else:
            self.widget = widget

    @_strip_whitespace
    def to_html(self) -> str:
        html_output = "<div class='report-widget'>"

        if self.label:
            anchor_id = _generate_anchor_id(self.label)
            html_output += (
                f"<report-caption><a href='#{anchor_id}'>{self.label}</a></report-caption>"
            )

        if isinstance(self.widget, pd.DataFrame):
            html_output += self.widget.style._repr_html_()
        elif isinstance(self.widget, matplotlib.figure.Figure):
            tmp = io.BytesIO()

            self.widget.set_dpi(300)
            self.widget.set_figwidth(10)
            self.widget.tight_layout()
            self.widget.savefig(tmp, format="png")
            tmp.seek(0)
            b64image = base64.b64encode(tmp.getvalue()).decode("utf-8").replace("\n", "")
            html_output += f'<br/><img src="data:image/png;base64,{b64image}">'
        elif hasattr(self.widget, "_repr_html_"):
            html_output += self.widget._repr_html_()
        elif hasattr(self.widget, "__repr__") or hasattr(self.widget, "__str__"):
            html_output += f"<p>{self.widget}</p>"

        html_output += "</div>"
        return html_output


class PxBase(Base):
    """Base class for Plotly Express chart components."""

    def __init__(self, label: Optional[str] = None):
        super().__init__(label=label)

    @abstractmethod
    def to_html(self) -> str:
        """Each component that derives from PXBase must implement this method"""
        pass

    @staticmethod
    def apply_common_fig_options(fig):
        fig.update_layout(
            font_family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif",
            autosize=True,
            modebar_remove="lasso",
        )
        fig.update_xaxes(
            title_font_family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif",
            tickangle=90,
        )

    @staticmethod
    def apply_common_kwargs(kwargs, label: Optional[str] = None):
        def insert_br_tags(text: str, n: int = 8):
            words = text.split()
            output = []
            current_line = []

            for word in words:
                current_line.append(word)
                if len(current_line) == n:
                    output.append(" ".join(current_line))
                    current_line = []

            if current_line:  # Add any remaining words
                output.append(" ".join(current_line))

            return "<br>".join(output)  # Join the lines with <br> tag

        if label and "title" not in kwargs:
            kwargs["title"] = insert_br_tags(label, n=8)


class Bar(PxBase):
    """
    Displays a bar chart using Plotly Express.

    The `Bar` component renders a bar chart from a Pandas DataFrame.
    It supports grouping by a categorical dimension and provides
    options for customizing the chart's appearance.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `x` and `y` arguments.
        x (str): The name of the column in the DataFrame to be plotted on
            the x-axis. This column typically represents the categories
            or discrete values for the bars.
        y (str): The name of the column in the DataFrame to be plotted on
            the y-axis. This column typically represents the numerical
            values associated with each category.
        dimension (Optional[str], optional): The name of an optional column
            in the DataFrame to be used as a categorical dimension for
            grouping the bars. If provided, the bars will be colored
            according to the unique values in this column. Defaults to None.
        label (Optional[str], optional): An optional label or title for the
            bar chart. Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to
            the `plotly.express.bar` function. This allows for fine-grained
            control over the chart's appearance and behavior.

    Raises:
        AssertionError: If the specified `x` column is not found in the DataFrame.
        AssertionError: If the specified `y` column is not found in the DataFrame.
        AssertionError: If the specified `dimension` column is not found in the DataFrame, when provided.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        *,
        dimension: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        super().__init__(label=label)
        self.df = df
        self.x = x
        self.y = y
        self.kwargs = kwargs

        assert x in df.columns, f"{x} not in df"
        assert y in df.columns, f"{y} not in df"

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["color"] = dimension

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        logger.info(f"Bar: {len(self.df)} rows, {x=}, {y=}, {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        fig = px.bar(self.df, x=self.x, y=self.y, **self.kwargs)

        PxBase.apply_common_fig_options(fig)
        fig.update_layout(bargap=0.1)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


class Line(PxBase):
    """
    Displays a line chart using Plotly Express.

    The `Line` component renders a line chart from a Pandas DataFrame,
    allowing you to visualize trends and relationships between variables
    over a continuous or ordered dimension. It supports plotting multiple
    lines on the same chart and provides options for customizing the
    chart's appearance.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `x` and `y` arguments.
        x (str): The name of the column in the DataFrame to be plotted on
            the x-axis. This column typically represents a continuous or
            ordered dimension (e.g., time, sequence).
        y (Union[str, list[str]]): The name(s) of the column(s) in the
            DataFrame to be plotted on the y-axis. This can be a single
            column name (for a single line) or a list of column names
            (for multiple lines).
        dimension (Optional[str], optional): The name of an optional column
            in the DataFrame to be used as a categorical dimension. If
            provided, the lines will be differentiated by color and symbol
            according to the unique values in this column. Defaults to None.
        label (Optional[str], optional): An optional label or title for the
            line chart. Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.line` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `line_shape`, `markers`, etc.

    Raises:
        AssertionError: If the specified `x` column is not found in the DataFrame.
        AssertionError: If any of the specified `y` column(s) are not found in the DataFrame.
        AssertionError: If the specified `dimension` column is not found in the DataFrame, when provided.
        ValueError: If `y` is not a string or a list of strings.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: Union[str, list[str]],
        *,
        dimension: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        super().__init__(label=label)
        self.df = df
        self.x = x
        self.y = y
        self.kwargs = kwargs

        assert x in df.columns, f"{x} not in df"

        if isinstance(y, list):
            for _ in y:
                assert _ in df.columns, f"{_} not in df"

        elif isinstance(y, str):
            assert y in df.columns, f"{y} not in df"
        else:
            raise ValueError(f"y must be a string or a list of strings, got {type(y)}")

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["symbol"] = dimension
            self.kwargs["color"] = dimension

        if "line_shape" not in self.kwargs:
            self.kwargs["line_shape"] = "linear"

        if "markers" not in self.kwargs:
            self.kwargs["markers"] = True

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        logger.info(f"Line: {len(self.df)} rows, {x=}, {y=}, {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        fig = px.line(self.df, x=self.x, y=self.y, **self.kwargs)

        PxBase.apply_common_fig_options(fig)
        fig.update_layout(bargap=0.1)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


class Pie(PxBase):
    """
    Displays a pie chart using Plotly Express.

    The `Pie` component renders a pie chart from a Pandas DataFrame,
    allowing you to visualize the proportions of different categories
    within a dataset. It provides options for customizing the chart's
    appearance, including the size of the hole in the center (for creating
    donut charts).

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `values` and `names` arguments.
        values (str): The name of the column in the DataFrame representing
            the numerical values that determine the size of each pie slice.
        names (str): The name of the column in the DataFrame representing
            the categories or labels for each pie slice.
        label (Optional[str], optional): An optional label or title for the
            pie chart. Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.pie` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `hole` (for creating donut charts), `color_discrete_sequence`,
            etc.

    Raises:
        AssertionError: If the specified `values` column is not found in the DataFrame.
        AssertionError: If the specified `names` column is not found in the DataFrame.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        values: str,
        names: str,
        *,
        label: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        super().__init__(label=label)
        self.df = df
        self.values = values
        self.names = names
        self.kwargs = kwargs

        assert values in df.columns, f"{values} not in df"
        assert names in df.columns, f"{names} not in df"

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        if "hole" not in self.kwargs:
            self.kwargs["hole"] = 0.3

        logger.info(f"Pie: {len(self.df)} rows, {values=}, {names=}, {label=}")

    def to_html(self) -> str:
        fig = px.pie(
            self.df,
            values=self.values,
            names=self.names,
            **self.kwargs,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(uniformtext_minsize=10, uniformtext_mode="hide")

        PxBase.apply_common_fig_options(fig)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


class Radar(PxBase):
    """
    Displays a radar chart using Plotly Express.

    The `Radar` component renders a radar chart from a Pandas DataFrame.
    Radar charts are useful for visualizing multivariate data and comparing
    multiple quantitative variables across different categories or entities.

    Example:

    +-----------------+-------+-----------+-------+---------------+----------+
    |                 | MMLU  | HumanEval | GSM8K | ARC Challenge | BigBench |
    +=================+=======+===========+=======+===============+==========+
    | Llama 3.1 405B  | 78.2  | 75.1      | 86    | 84.5          | 68       |
    +-----------------+-------+-----------+-------+---------------+----------+
    | Llama 3.2 405B  | 78.5  | 75.3      | 86.2  | 84.8          | 68.3     |
    +-----------------+-------+-----------+-------+---------------+----------+
    | Llama 3.3 405B  | 78.8  | 75.5      | 86.4  | 85.1          | 68.6     |
    +-----------------+-------+-----------+-------+---------------+----------+
    | Llama 3.4 405B  | 79.1  | 75.7      | 86.6  | 85.4          | 68.9     |
    +-----------------+-------+-----------+-------+---------------+----------+

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `r` (values) and `theta` (categories) arguments.
        label (Optional[str], optional): An optional label or title for the
            radar chart. Defaults to None.
        lock_minimum_to_zero (Optional[bool], optional): If True, the minimum
            value of the radar chart's radial axis will be locked to zero,
            ensuring that the chart starts from zero. If False, the minimum
            value will be determined by the minimum value in the DataFrame.
            Defaults to False.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.line_polar` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `line_close` (to close the polygon), `color_discrete_sequence`,
            etc.

    Raises:
        AssertionError: If the specified `r` column is not found in the DataFrame.
        AssertionError: If the specified `theta` column is not found in the DataFrame.
        AssertionError: If the specified `dimension` column is not found in the DataFrame, when provided.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        *,
        label: Optional[str] = None,
        lock_minimum_to_zero: Optional[bool] = False,
        filled: Optional[bool] = False,
        **kwargs: Optional[dict],
    ):
        super().__init__(label=label)
        assert df.index is not None, "DataFrame has no index"
        assert len(df.index) > 0, "DataFrame has no index or is empty"
        assert df.index.is_unique and not df.index.hasnans, "DataFrame index is invalid"
        self.df = df
        self.filled = filled

        self.min_value = 0 if lock_minimum_to_zero else df.min().min()
        self.max_value = df.max().max()
        self.kwargs = kwargs

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        logger.info(
            f"Radar: {len(self.df)} rows, (range: {self.min_value} .. {self.max_value}) {label=}"
        )

    def to_html(self):
        fig = go.Figure()

        theta = self.df.columns.tolist()
        theta += theta[:1]  # Ensure the radar chart is closed

        for index, row in self.df.iterrows():
            r = row.values.tolist()
            r += r[:1]  # Ensure that the first value of r is repeated to close the loop

            fig.add_trace(
                go.Scatterpolar(
                    r=r,
                    theta=theta,
                    fill="toself" if self.filled else None,
                    name=index,
                )
            )

        PxBase.apply_common_fig_options(fig)

        fig.update_layout(
            polar={
                "radialaxis": {
                    "visible": True,
                    "range": [
                        self.min_value,
                        self.max_value,
                    ],
                }
            },
            height=600,
        )

        if self.label:
            fig.update_layout(title=self.label)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


class Scatter(PxBase):
    """
    Displays a scatter plot using Plotly Express.

    The `Scatter` component renders a scatter plot from a Pandas DataFrame,
    allowing you to visualize the relationship between two numerical variables.
    It supports adding a categorical dimension for color-coding or sizing
    the data points, enhancing the visualization of patterns within the data.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `x` and `y` arguments.
        x (str): The name of the column in the DataFrame to be plotted on
            the x-axis. This column typically represents a numerical variable.
        y (str): The name of the column in the DataFrame to be plotted on
            the y-axis. This column typically represents a numerical variable.
        dimension (Optional[str], optional): The name of an optional column
            in the DataFrame to be used as a categorical dimension for
            color-coding or sizing the data points. If provided, the points
            will be colored or sized according to the unique values in this
            column. Defaults to None.
        label (Optional[str], optional): An optional label or title for the
            scatter plot. Defaults to None.
        marginal (Optional[str], optional): An optional argument to specify
            the type of marginal plots to display along the x and y axes.
            This can be one of 'histogram', 'violin', 'box', or 'rug'.
            Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.scatter` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `trendline`, `symbol`, etc.

    Raises:
        AssertionError: If the specified `x` column is not found in the DataFrame.
        AssertionError: If the specified `y` column is not found in the DataFrame.
        AssertionError: If the specified `color` column is not found in the DataFrame, when provided.
        AssertionError: If the specified `size` column is not found in the DataFrame, when provided.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        marginal: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        super().__init__(label=label)
        self.df = df
        self.x = x
        self.y = y
        self.kwargs = kwargs

        assert x in df.columns, f"{x} not in df"
        assert y in df.columns, f"{y} not in df"

        if marginal:
            assert marginal in [
                "histogram",
                "violin",
                "box",
                "rug",
            ], "marginal must be one of ['histogram', 'violin', 'box', 'rug']"
            self.kwargs["marginal_x"] = marginal
            self.kwargs["marginal_y"] = marginal

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["color"] = dimension
            self.kwargs["symbol"] = dimension

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        logger.info(f"Scatter: {len(self.df)} rows, {y=}, {dimension=}, {label=}")

    def to_html(self) -> str:
        """
        Convert the scatter plot to an HTML string.

        Returns:
            str: The HTML representation of the scatter plot.
        """
        fig = px.scatter(
            self.df,
            x=self.x,
            y=self.y,
            **self.kwargs,
        )

        PxBase.apply_common_fig_options(fig)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


class Box(PxBase):
    """
    Displays a box plot using Plotly Express.

    The `Box` component renders a box plot from a Pandas DataFrame,
    allowing you to visualize the distribution of data across different
    categories or groups. Box plots are useful for showing the median,
    quartiles, and potential outliers within each group.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the columns specified by
            the `x` and `y` arguments.
        y (str): The name of the column in the DataFrame to be plotted on
            the y-axis. This column typically represents the numerical
            variable whose distribution is being visualized.
        dimension (Optional[str], optional): The name of an optional column
            in the DataFrame to be used as a categorical dimension for
            grouping the box plots. If provided, the box plots will be
            separated according to the unique values in this column.
            Defaults to None.
        label (Optional[str], optional): An optional label or title for the
            box plot. Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.box` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `notched` boxes, `orientation` etc.

    Raises:
        AssertionError: If the specified `x` column is not found in the DataFrame.
        AssertionError: If the specified `y` column is not found in the DataFrame.
        AssertionError: If the specified `color` column is not found in the DataFrame, when provided.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        y: Optional[str] = None,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        super().__init__(label=label)
        self.df = df
        self.y = y
        self.kwargs = kwargs

        assert y in df.columns, f"{y} not in df"

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["x"] = dimension
            self.kwargs["color"] = dimension

        PxBase.apply_common_kwargs(self.kwargs, label=label)

        logger.info(f"Box: {len(self.df)} rows, {y=}, {dimension=}, {label=}")

    def to_html(self) -> str:
        """
        Convert the box plot to an HTML string.

        Returns:
            str: The HTML representation of the box plot.
        """
        fig = px.box(
            self.df,
            y=self.y,
            **self.kwargs,
        )

        PxBase.apply_common_fig_options(fig)

        fig.update_traces(boxpoints="outliers")

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


class Histogram(PxBase):
    """
    Displays a histogram using Plotly Express.

    The `Histogram` component renders a histogram from a Pandas DataFrame,
    allowing you to visualize the distribution of a numerical variable.
    Histograms are useful for understanding the frequency and range of
    values within a dataset.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be plotted.
            This DataFrame should contain at least the column specified by
            the `x` argument.
        x (str): The name of the column in the DataFrame to be plotted on
            the x-axis. This column represents the numerical variable
            whose distribution is being visualized.
        dimension (Optional[str], optional): The name of an optional column
            in the DataFrame to be used as a categorical dimension for
            splitting the histogram. If provided, multiple histograms will
            be created, one for each unique value of the column. Defaults to None.
        label (Optional[str], optional): An optional label or title for the
            histogram. Defaults to None.
        **kwargs: Additional keyword arguments to be passed directly to the
            `plotly.express.histogram` function. This allows for fine-grained
            control over the chart's appearance and behavior, such as
            `barmode`, `histnorm`, etc.

    Raises:
        AssertionError: If the specified `x` column is not found in the DataFrame.
        AssertionError: If the specified `color` column is not found in the DataFrame, when provided.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        **kwargs: Optional[dict],
    ):
        super().__init__(label=label)
        self.df = df
        self.x = x
        self.kwargs = kwargs

        assert x in df.columns, f"{x} not in df"

        if dimension:
            assert dimension in df.columns, f"{dimension} not in df"
            self.kwargs["color"] = dimension

        PxBase.apply_common_kwargs(kwargs, label=label)

        logger.info(f"Histogram: {len(self.df)} rows, {x=}, {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        fig = px.histogram(self.df, x=self.x, **self.kwargs)
        fig.update_layout(bargap=0.1)

        PxBase.apply_common_fig_options(fig)

        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})
