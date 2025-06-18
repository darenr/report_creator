# Standard library imports
from abc import ABC, abstractmethod  # Use ABC for abstract base classes
from typing import Any, Optional, Union

# Third-party imports
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

# Loguru for logging
from loguru import logger

# Internal imports
from .base import Base
from .theming import preferred_fonts  # report_creator_colors is not directly used here
from .utilities import (
    _strip_whitespace,  # _generate_anchor_id, _gfm_markdown_to_html not used here
)


class PxBase(Base, ABC):
    """
    Abstract Base Class for Plotly Express chart components.

    This class provides common functionality for chart components built using
    Plotly Express. It handles optional labels (typically used for chart titles)
    and includes static methods to apply consistent styling and keyword argument
    processing to Plotly Figure objects.

    Derived classes must implement the `to_html` method to generate the
    specific chart HTML.

    Args:
        label (Optional[str], optional): An optional label for the chart,
            which is often used as the chart's title. If provided, it can be
            automatically formatted and set as the title by `apply_common_kwargs`.
            Defaults to None.
    """

    def __init__(self, label: Optional[str] = None):
        super().__init__(label=label)

    @abstractmethod
    def to_html(self) -> str:
        """
        Abstract method that must be implemented by derived chart classes.
        It should render the chart component to an HTML string.

        Returns:
            str: The HTML representation of the chart.
        """
        pass

    @staticmethod
    def apply_common_fig_options(fig: go.Figure) -> None:
        """
        Applies common layout options to a Plotly Figure object for consistent styling.

        These options currently include:
        - Setting a preferred font family for the entire figure.
        - Enabling autosize for the figure.
        - Removing the lasso and select tools from the Plotly modebar, as they are
          less commonly used in static reports.
        - Styling x-axis titles with the preferred font.
        - Setting x-axis tick labels to a 90-degree angle for better readability
          if they are long or numerous.

        Args:
            fig (go.Figure): The Plotly Figure object to which the common styling
                options will be applied. The figure is modified in place.
        """
        fig.update_layout(
            font_family=preferred_fonts[0] if preferred_fonts else "sans-serif",
            autosize=True,
            # Remove less commonly used tools from the modebar
            modebar_remove=["lasso2d", "select2d"],
        )
        fig.update_xaxes(
            title_font_family=preferred_fonts[0] if preferred_fonts else "sans-serif",
            tickangle=90,  # Rotates x-axis labels to prevent overlap
        )

    @staticmethod
    def apply_common_kwargs(kwargs: dict[str, Any], label: Optional[str] = None) -> None:
        """
        Applies common keyword arguments to a kwargs dictionary, primarily for
        setting a chart title based on the provided `label`.

        If a `label` is provided and the `kwargs` dictionary does not already
        contain a "title" key, this method will format the `label` (by wrapping
        long text using HTML `<br>` tags) and add it to `kwargs` as "title".
        This ensures that charts have titles derived from their labels unless
        a title is explicitly overridden in `**kwargs`.

        Args:
            kwargs (dict[str, Any]): The dictionary of keyword arguments intended for
                a Plotly Express function. This dictionary is modified in place.
            label (Optional[str], optional): The label for the chart. If provided,
                it's used to generate a title. Defaults to None.
        """

        def _format_title_with_line_breaks(text: str, max_words_per_line: int = 5) -> str:
            """
            Formats a string by inserting HTML <br> tags to wrap lines,
            aiming to break lines after a specified number of words.
            """
            if not text:  # Handle empty or None text
                return ""
            words = str(text).split()  # Ensure text is string
            lines = []
            current_line_words = []
            for word in words:
                current_line_words.append(word)
                if len(current_line_words) >= max_words_per_line:
                    lines.append(" ".join(current_line_words))
                    current_line_words = []
            if current_line_words:  # Add any remaining words
                lines.append(" ".join(current_line_words))
            return "<br>".join(lines)

        if label and "title" not in kwargs:
            kwargs["title"] = _format_title_with_line_breaks(label)


##############################

# Charting Components

##############################


class Bar(PxBase):
    """
    Displays a bar chart using Plotly Express.

    This component generates a bar chart from a Pandas DataFrame.
    It allows specifying the x and y axes, an optional dimension for coloring
    bars (grouping), and a label that is typically used as the chart title.
    Additional keyword arguments (`**kwargs`) are passed directly to the
    `plotly.express.bar` function, allowing for extensive customization.

    Args:
        df (pd.DataFrame): The DataFrame containing the data for the chart.
        x (str): The name of the column in `df` to be used for the x-axis.
        y (str): The name of the column in `df` to be used for the y-axis
            (representing bar heights).
        dimension (Optional[str], optional): The name of the column in `df`
            to be used for color-coding the bars. If provided, this will map
            unique values in the `dimension` column to different colors.
            Defaults to None.
        label (Optional[str], optional): An optional label for the chart,
            which is used to generate the chart title if no 'title' is
            provided in `**kwargs`. Defaults to None.
        **kwargs (Any): Additional keyword arguments
            passed directly to `plotly.express.bar()`. This can include
            arguments like `orientation`, `barmode`, `color_discrete_map`, etc.

    Raises:
        ValueError: If specified `x`, `y`, or `dimension` columns are not in `df`.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        *,
        dimension: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(label=label)
        self.df = df
        self.x_col = x
        self.y_col = y
        self.dimension_col = dimension
        self.kwargs = kwargs

        if self.x_col not in self.df.columns:
            raise ValueError(
                f"X-axis column '{self.x_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
            )
        if self.y_col not in self.df.columns:
            raise ValueError(
                f"Y-axis column '{self.y_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
            )

        if self.dimension_col:
            if self.dimension_col not in self.df.columns:
                raise ValueError(
                    f"Dimension column '{self.dimension_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
                )
            if "color" not in self.kwargs:
                self.kwargs["color"] = self.dimension_col

        PxBase.apply_common_kwargs(self.kwargs, label=self.label)
        logger.info(
            f"Bar chart: x='{self.x_col}', y='{self.y_col}', dimension='{self.dimension_col}', label='{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """Generates the HTML representation of the bar chart."""
        fig = px.bar(self.df, x=self.x_col, y=self.y_col, **self.kwargs)
        PxBase.apply_common_fig_options(fig)
        if "bargap" not in self.kwargs:  # Apply default bargap if not user-specified
            fig.update_layout(bargap=0.1)
        return fig.to_html(
            include_plotlyjs=False,
            full_html=False,
            config={"responsive": True, "displayModeBar": True},
        )


class Line(PxBase):
    """
    Displays a line chart using Plotly Express.

    Plots one or more y-axis variables against an x-axis variable from a DataFrame.
    An optional `dimension` column can color-code and differentiate symbols for lines.
    Defaults to spline lines with markers.

    Args:
        df (pd.DataFrame): DataFrame for the chart.
        x (str): Column name for the x-axis.
        y (Union[str, list[str]]): Column name or list of column names for the y-axis.
        dimension (Optional[str], optional): Column name for color-coding and symbol
            differentiation. Defaults to None.
        label (Optional[str], optional): Chart label, used for title generation.
            Defaults to None.
        **kwargs (Any): Additional arguments for `plotly.express.line()`.

    Raises:
        ValueError: If specified `x`, `y`, or `dimension` columns are not in `df`,
                    or if `y` is not a string or list of strings.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: Union[str, list[str]],
        *,
        dimension: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(label=label)
        self.df = df
        self.x_col = x
        self.y_cols = y
        self.dimension_col = dimension
        self.kwargs = kwargs

        if self.x_col not in self.df.columns:
            raise ValueError(
                f"X-axis column '{self.x_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
            )

        if isinstance(self.y_cols, list):
            for y_col_name in self.y_cols:
                if y_col_name not in self.df.columns:
                    raise ValueError(
                        f"Y-axis column '{y_col_name}' not found in DataFrame columns: {self.df.columns.tolist()}."
                    )
        elif isinstance(self.y_cols, str):
            if self.y_cols not in self.df.columns:
                raise ValueError(
                    f"Y-axis column '{self.y_cols}' not found in DataFrame columns: {self.df.columns.tolist()}."
                )
        else:
            raise ValueError(
                f"Parameter 'y' must be a string or a list of strings, got {type(self.y_cols).__name__}."
            )

        if self.dimension_col:
            if self.dimension_col not in self.df.columns:
                raise ValueError(
                    f"Dimension column '{self.dimension_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
                )
            if "color" not in self.kwargs:
                self.kwargs["color"] = self.dimension_col
            if "symbol" not in self.kwargs:
                self.kwargs["symbol"] = self.dimension_col

        if "line_shape" not in self.kwargs:
            self.kwargs["line_shape"] = "spline"
        if "markers" not in self.kwargs:
            self.kwargs["markers"] = True

        PxBase.apply_common_kwargs(self.kwargs, label=self.label)
        logger.info(
            f"Line chart: x='{self.x_col}', y(s)='{self.y_cols}', dimension='{self.dimension_col}', label='{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """Generates the HTML representation of the line chart."""
        fig = px.line(self.df, x=self.x_col, y=self.y_cols, **self.kwargs)
        PxBase.apply_common_fig_options(fig)
        return fig.to_html(
            include_plotlyjs=False,
            full_html=False,
            config={"responsive": True, "displayModeBar": True},
        )


class Pie(PxBase):
    """
    Displays a pie chart (or donut chart if `hole` is specified) using Plotly Express.

    Visualizes parts of a whole, where `values` determine slice sizes and `names`
    provide slice labels. Defaults to a donut chart appearance (hole=0.4).

    Args:
        df (pd.DataFrame): DataFrame for the chart.
        values (str): Column name for slice values.
        names (str): Column name for slice names/labels.
        label (Optional[str], optional): Chart label, used for title generation.
            Defaults to None.
        **kwargs (Any): Additional arguments for `plotly.express.pie()`.
            Example: `hole=0` for a pie chart, `color_discrete_sequence`.

    Raises:
        ValueError: If specified `values` or `names` columns are not in `df`.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        values: str,
        names: str,
        *,
        label: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(label=label)
        self.df = df
        self.values_col = values
        self.names_col = names
        self.kwargs = kwargs

        if self.values_col not in self.df.columns:
            raise ValueError(
                f"Values column '{self.values_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
            )
        if self.names_col not in self.df.columns:
            raise ValueError(
                f"Names column '{self.names_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
            )

        PxBase.apply_common_kwargs(self.kwargs, label=self.label)
        if "hole" not in self.kwargs:
            self.kwargs["hole"] = 0.4  # Default to donut

        logger.info(
            f"Pie chart: values='{self.values_col}', names='{self.names_col}', label='{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """Generates the HTML representation of the pie chart."""
        fig = px.pie(self.df, values=self.values_col, names=self.names_col, **self.kwargs)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(uniformtext_minsize=10, uniformtext_mode="hide")
        PxBase.apply_common_fig_options(fig)
        return fig.to_html(
            include_plotlyjs=False,
            full_html=False,
            config={"responsive": True, "displayModeBar": True},
        )


class Radar(PxBase):
    """
    Displays a radar chart (spider/star chart) using Plotly's graph objects.

    Each row in the input DataFrame represents a trace (entity), and each column
    an angular axis (category). The DataFrame index names the traces.

    Args:
        df (pd.DataFrame): DataFrame for the chart.
            - Index: Names for radar traces (must be unique, non-null).
            - Columns: Angular axes/categories.
            - Values: Magnitudes for each category per trace.
        label (Optional[str], optional): Chart label, used for title generation.
            Defaults to None.
        lock_minimum_to_zero (Optional[bool], optional): If True, radial axis starts at zero.
            Default False (axis minimum based on data).
        filled (Optional[bool], optional): If True, areas enclosed by traces are filled.
            Defaults to False.
        **kwargs (Any): Additional arguments.
            - `trace_kwargs` (dict): Passed to `go.Scatterpolar` traces.
            - Others used by `PxBase.apply_common_kwargs` (e.g., `title`, `height`).

    Raises:
        ValueError: If `df` is not a Pandas DataFrame, or if its index is invalid
                    (empty, not unique, or contains NaNs).
    """

    def __init__(
        self,
        df: pd.DataFrame,
        *,
        label: Optional[str] = None,
        lock_minimum_to_zero: Optional[bool] = False,
        filled: Optional[bool] = False,
        **kwargs: Any,
    ):
        super().__init__(label=label)

        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input 'df' must be a Pandas DataFrame.")
        if df.index is None or len(df.index) == 0:
            raise ValueError("DataFrame must have a non-empty index for Radar chart traces.")
        if not df.index.is_unique:
            raise ValueError("DataFrame index must be unique for Radar chart traces.")
        if df.index.hasnans:  # Checks for NaNs in the index
            raise ValueError("DataFrame index must not contain NaNs for Radar chart traces.")

        self.df = df
        self.filled = filled
        self.kwargs = kwargs

        self.min_value = (
            0.0 if lock_minimum_to_zero else float(df.min(numeric_only=True).min(skipna=True))
        )
        self.max_value = float(df.max(numeric_only=True).max(skipna=True))

        PxBase.apply_common_kwargs(self.kwargs, label=self.label)
        logger.info(
            f"Radar chart: {len(self.df)} traces, {len(self.df.columns)} categories. "
            f"Radial range: [{self.min_value}, {self.max_value}]. Filled: {self.filled}. Label: '{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """Generates the HTML representation of the radar chart."""
        fig = go.Figure()
        theta_categories = self.df.columns.tolist()
        theta_closed_loop = theta_categories + theta_categories[:1]  # Close the loop

        for trace_name, row_data in self.df.iterrows():
            r_values = row_data.values.tolist()
            r_closed_loop = r_values + r_values[:1]  # Close the loop for r values

            trace_specific_kwargs = self.kwargs.get("trace_kwargs", {})
            fig.add_trace(
                go.Scatterpolar(
                    r=r_closed_loop,
                    theta=theta_closed_loop,
                    fill="toself" if self.filled else None,
                    name=str(trace_name),  # Ensure trace name is string
                    **trace_specific_kwargs,
                )
            )

        PxBase.apply_common_fig_options(fig)
        fig.update_layout(
            polar={"radialaxis": {"visible": True, "range": [self.min_value, self.max_value]}},
            height=self.kwargs.get("height", 600),  # Allow height override
            title=self.kwargs.get("title"),  # Title applied via PxBase
        )
        return fig.to_html(
            include_plotlyjs=False,
            full_html=False,
            config={"responsive": True, "displayModeBar": True},
        )


class Scatter(PxBase):
    """
    Displays a scatter plot using Plotly Express.

    Shows the relationship between two numerical variables (`x` and `y`).
    An optional `dimension` can color-code and differentiate symbols.
    Marginal plots (histogram, box, etc.) can be added.

    Args:
        df (pd.DataFrame): DataFrame for the chart.
        x (str): Column name for the x-axis.
        y (str): Column name for the y-axis.
        dimension (Optional[str], optional): Column name for color-coding and
            symbol differentiation. Defaults to None.
        label (Optional[str], optional): Chart label, used for title generation.
            Defaults to None.
        marginal (Optional[str], optional): Adds marginal plots. Valid options:
            "histogram", "violin", "box", "rug". Defaults to None.
        **kwargs (Any): Additional arguments for `plotly.express.scatter()`.

    Raises:
        ValueError: If specified `x`, `y`, or `dimension` columns are not in `df`,
                    or if `marginal` type is invalid.
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
        **kwargs: Any,
    ):
        super().__init__(label=label)
        self.df = df
        self.x_col = x
        self.y_col = y
        self.dimension_col = dimension
        self.kwargs = kwargs

        if self.x_col not in self.df.columns:
            raise ValueError(
                f"X-axis column '{self.x_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
            )
        if self.y_col not in self.df.columns:
            raise ValueError(
                f"Y-axis column '{self.y_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
            )

        VALID_MARGINALS = ["histogram", "violin", "box", "rug"]
        if marginal:
            if marginal not in VALID_MARGINALS:
                raise ValueError(
                    f"Invalid 'marginal' type '{marginal}'. Must be one of {VALID_MARGINALS}."
                )
            self.kwargs["marginal_x"] = marginal
            self.kwargs["marginal_y"] = marginal

        if self.dimension_col:
            if self.dimension_col not in self.df.columns:
                raise ValueError(
                    f"Dimension column '{self.dimension_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
                )
            if "color" not in self.kwargs:
                self.kwargs["color"] = self.dimension_col
            if "symbol" not in self.kwargs:
                self.kwargs["symbol"] = self.dimension_col

        PxBase.apply_common_kwargs(self.kwargs, label=self.label)
        logger.info(
            f"Scatter plot: x='{self.x_col}', y='{self.y_col}', dimension='{self.dimension_col}', "
            f"marginal='{marginal}', label='{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """Generates the HTML representation of the scatter plot."""
        fig = px.scatter(self.df, x=self.x_col, y=self.y_col, **self.kwargs)
        PxBase.apply_common_fig_options(fig)
        return fig.to_html(
            include_plotlyjs=False,
            full_html=False,
            config={"responsive": True, "displayModeBar": True},
        )


class Box(PxBase):
    """
    Displays a box plot using Plotly Express.

    Shows data distribution. `y` is the variable plotted. `dimension` (as `x`)
    groups data into multiple box plots. For wide-form data, plots can be
    generated for each numerical column if `y` is None.

    Args:
        df (pd.DataFrame): DataFrame for the chart.
        y (Optional[str], optional): Column name for the y-axis (variable for
            distribution). Can be None for wide-form data. Defaults to None.
        dimension (Optional[str], optional): Column name for x-axis grouping (categories).
            If provided, passed as `x` to `px.box`, and also used for `color` if
            `color` is not in `**kwargs`. Defaults to None.
        label (Optional[str], optional): Chart label, used for title generation.
            Defaults to None.
        **kwargs (Any): Additional arguments for `plotly.express.box()`.

    Raises:
        ValueError: If specified `y` or `dimension` columns are not in `df`.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        y: Optional[str] = None,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(label=label)
        self.df = df
        self.y_col = y
        self.dimension_col = dimension
        self.kwargs = kwargs

        if self.y_col and self.y_col not in self.df.columns:
            raise ValueError(
                f"Y-axis column '{self.y_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
            )

        if self.dimension_col:
            if self.dimension_col not in self.df.columns:
                raise ValueError(
                    f"Dimension column '{self.dimension_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
                )
            if "x" not in self.kwargs:
                self.kwargs["x"] = self.dimension_col
            if "color" not in self.kwargs:
                self.kwargs["color"] = self.dimension_col

        PxBase.apply_common_kwargs(self.kwargs, label=self.label)
        logger.info(
            f"Box plot: y='{self.y_col}', dimension (as x)='{self.dimension_col}', label='{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """Generates the HTML representation of the box plot."""
        fig = px.box(self.df, y=self.y_col, **self.kwargs)
        PxBase.apply_common_fig_options(fig)
        if "boxpoints" not in self.kwargs:  # Show outliers by default
            fig.update_traces(boxpoints="outliers")
        return fig.to_html(
            include_plotlyjs=False,
            full_html=False,
            config={"responsive": True, "displayModeBar": True},
        )


class Histogram(PxBase):
    """
    Displays a histogram using Plotly Express.

    Visualizes the distribution of a single numerical variable (`x`).
    An optional `dimension` can color-code bars.

    Args:
        df (pd.DataFrame): DataFrame for the chart.
        x (str): Column name for the x-axis (numerical variable for distribution).
        dimension (Optional[str], optional): Column name for color-coding bars.
            Defaults to None.
        label (Optional[str], optional): Chart label, used for title generation.
            Defaults to None.
        **kwargs (Any): Additional arguments for `plotly.express.histogram()`.

    Raises:
        ValueError: If specified `x` or `dimension` columns are not in `df`.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        dimension: Optional[str] = None,
        *,
        label: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(label=label)
        self.df = df
        self.x_col = x
        self.dimension_col = dimension
        self.kwargs = kwargs

        if self.x_col not in self.df.columns:
            raise ValueError(
                f"X-axis column '{self.x_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
            )

        if self.dimension_col:
            if self.dimension_col not in self.df.columns:
                raise ValueError(
                    f"Dimension column '{self.dimension_col}' not found in DataFrame columns: {self.df.columns.tolist()}."
                )
            if "color" not in self.kwargs:
                self.kwargs["color"] = self.dimension_col

        PxBase.apply_common_kwargs(self.kwargs, label=self.label)
        logger.info(
            f"Histogram: x='{self.x_col}', dimension='{self.dimension_col}', label='{self.label}'"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        """Generates the HTML representation of the histogram."""
        fig = px.histogram(self.df, x=self.x_col, **self.kwargs)
        if "bargap" not in self.kwargs:  # Default bargap for histograms
            fig.update_layout(bargap=0.1)
        PxBase.apply_common_fig_options(fig)
        return fig.to_html(
            include_plotlyjs=False,
            full_html=False,
            config={"responsive": True, "displayModeBar": True},
        )
