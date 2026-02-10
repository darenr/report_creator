import plotly.graph_objs as go
import pytest

from report_creator.charts import Bar, Box, Histogram, Line, Pie, PxBase, Scatter


def test_bar(sample_df):
    bar = Bar(sample_df, x="Category", y="Value", label="Bar Chart")
    html = bar.to_html()
    assert "Bar Chart" in html
    assert "plotly-graph-div" in html

    # Test with dimension
    bar_dim = Bar(sample_df, x="Category", y="Value", dimension="Metric")
    assert bar_dim.kwargs["color"] == "Metric"

    # Test with dimension and color already in kwargs
    bar_color = Bar(sample_df, x="Category", y="Value", dimension="Metric", color="red")
    assert bar_color.kwargs["color"] == "red"


def test_line(sample_df):
    line = Line(sample_df, x="Date", y="Value", label="Line Chart")
    html = line.to_html()
    assert "Line Chart" in html

    # Test multiple y columns
    line_multi = Line(sample_df, x="Date", y=["Value", "Value"])
    assert line_multi.y_cols == ["Value", "Value"]

    # Test dimension
    line_dim = Line(sample_df, x="Date", y="Value", dimension="Category")
    assert line_dim.kwargs["color"] == "Category"
    assert line_dim.kwargs["symbol"] == "Category"

    # Test with color, symbol, line_shape, markers already in kwargs
    line_custom = Line(
        sample_df,
        x="Date",
        y="Value",
        dimension="Category",
        color="red",
        symbol="circle",
        line_shape="linear",
        markers=False,
    )
    assert line_custom.kwargs["color"] == "red"
    assert line_custom.kwargs["symbol"] == "circle"
    assert line_custom.kwargs["line_shape"] == "linear"
    assert line_custom.kwargs["markers"] is False


def test_pie(sample_df):
    pie = Pie(sample_df, values="Value", names="Metric", label="Pie Chart")
    html = pie.to_html()
    assert "Pie Chart" in html
    assert pie.kwargs["hole"] == 0.4

    # Custom hole
    pie_custom = Pie(sample_df, values="Value", names="Metric", hole=0.1)
    assert pie_custom.kwargs["hole"] == 0.1


def test_pie_validation(sample_df):
    with pytest.raises(ValueError, match="Values column 'Invalid' not found"):
        Pie(sample_df, values="Invalid", names="Metric")
    with pytest.raises(ValueError, match="Names column 'Invalid' not found"):
        Pie(sample_df, values="Value", names="Invalid")


def test_scatter(sample_df):
    scatter = Scatter(sample_df, x="Value", y="Value", label="Scatter Plot")
    html = scatter.to_html()
    assert "Scatter Plot" in html

    # Test marginals
    scatter_marg = Scatter(sample_df, x="Value", y="Value", marginal="histogram")
    assert scatter_marg.kwargs["marginal_x"] == "histogram"
    assert scatter_marg.kwargs["marginal_y"] == "histogram"

    # Test dimension
    scatter_dim = Scatter(sample_df, x="Value", y="Value", dimension="Category")
    assert scatter_dim.kwargs["color"] == "Category"
    assert scatter_dim.kwargs["symbol"] == "Category"

    # Test with color, symbol already in kwargs
    scatter_custom = Scatter(
        sample_df, x="Value", y="Value", dimension="Category", color="blue", symbol="diamond"
    )
    assert scatter_custom.kwargs["color"] == "blue"
    assert scatter_custom.kwargs["symbol"] == "diamond"


def test_scatter_validation(sample_df):
    with pytest.raises(ValueError, match="X-axis column 'Invalid' not found"):
        Scatter(sample_df, x="Invalid", y="Value")
    with pytest.raises(ValueError, match="Y-axis column 'Invalid' not found"):
        Scatter(sample_df, x="Value", y="Invalid")
    with pytest.raises(ValueError, match="Invalid 'marginal' type"):
        Scatter(sample_df, x="Value", y="Value", marginal="invalid")
    with pytest.raises(ValueError, match="Dimension column 'Invalid' not found"):
        Scatter(sample_df, x="Value", y="Value", dimension="Invalid")


def test_box(sample_df):
    box = Box(sample_df, y="Value", label="Box Plot")
    html = box.to_html()
    assert "Box Plot" in html

    # Test dimension
    box_dim = Box(sample_df, y="Value", dimension="Category")
    assert box_dim.kwargs["x"] == "Category"
    assert box_dim.kwargs["color"] == "Category"

    # Test with x, color already in kwargs
    box_custom = Box(sample_df, y="Value", dimension="Category", x="OtherCol", color="green")
    assert box_custom.kwargs["x"] == "OtherCol"
    assert box_custom.kwargs["color"] == "green"


def test_box_validation(sample_df):
    with pytest.raises(ValueError, match="Y-axis column 'Invalid' not found"):
        Box(sample_df, y="Invalid")
    with pytest.raises(ValueError, match="Dimension column 'Invalid' not found"):
        Box(sample_df, y="Value", dimension="Invalid")


def test_histogram(sample_df):
    hist = Histogram(sample_df, x="Value", label="Histogram")
    html = hist.to_html()
    assert "Histogram" in html

    # Test dimension
    hist_dim = Histogram(sample_df, x="Value", dimension="Category")
    assert hist_dim.kwargs["color"] == "Category"

    # Test with color already in kwargs
    hist_custom = Histogram(sample_df, x="Value", dimension="Category", color="purple")
    assert hist_custom.kwargs["color"] == "purple"


def test_histogram_validation(sample_df):
    with pytest.raises(ValueError, match="X-axis column 'Invalid' not found"):
        Histogram(sample_df, x="Invalid")
    with pytest.raises(ValueError, match="Dimension column 'Invalid' not found"):
        Histogram(sample_df, x="Value", dimension="Invalid")


def test_apply_common_fig_options():
    fig = go.Figure()
    PxBase.apply_common_fig_options(fig)
    assert fig.layout.font.family is not None
    assert fig.layout.autosize is True
    assert "lasso2d" in fig.layout.modebar.remove
    assert "select2d" in fig.layout.modebar.remove


def test_apply_common_kwargs_title_formatting():
    kwargs = {}
    label = "This is a very long title that should be wrapped"
    PxBase.apply_common_kwargs(kwargs, label=label)
    assert "<br>" in kwargs["title"]

    kwargs = {}
    label = "Short"
    PxBase.apply_common_kwargs(kwargs, label=label)
    assert kwargs["title"] == "Short"

    kwargs = {"title": "Existing"}
    PxBase.apply_common_kwargs(kwargs, label="Ignore me")
    assert kwargs["title"] == "Existing"

    # Edge cases for title formatting
    kwargs = {}
    PxBase.apply_common_kwargs(kwargs, label="")
    assert "title" not in kwargs

    kwargs = {}
    PxBase.apply_common_kwargs(kwargs, label=None)
    assert "title" not in kwargs

    # Test title formatting with nested function logic if possible
    # We can't call _format_title_with_line_breaks directly but we can test its result
    kwargs = {}
    PxBase.apply_common_kwargs(kwargs, label="word " * 10)
    assert "<br>" in kwargs["title"]
    assert kwargs["title"].count("<br>") == 1  # 10 words, max 5 per line -> 2 lines, 1 <br>


def test_radar_validation_extended(sample_df):
    from report_creator.charts import Radar

    with pytest.raises(ValueError, match="Input 'df' must be a Pandas DataFrame"):
        Radar("not a dataframe")


def test_line_extra_branches(sample_df):
    from report_creator.charts import Line

    # Test line with dimension where color/symbol already there
    l = Line(
        sample_df, x="Date", y="Value", dimension="Category", color="red", symbol="diamond"
    )
    assert l.kwargs["color"] == "red"
    assert l.kwargs["symbol"] == "diamond"


def test_pie_extra_branches(sample_df):
    from report_creator.charts import Pie

    # Test pie with hole already in kwargs
    p = Pie(sample_df, values="Value", names="Metric", hole=0.5)
    assert p.kwargs["hole"] == 0.5


def test_box_extra_branches(sample_df):
    from report_creator.charts import Box

    # Test box with dimension where x/color already there
    b = Box(sample_df, y="Value", dimension="Category", x="CustomX", color="blue")
    assert b.kwargs["x"] == "CustomX"
    assert b.kwargs["color"] == "blue"


def test_histogram_extra_branches(sample_df):
    from report_creator.charts import Histogram

    # Test histogram with dimension where color already there
    h = Histogram(sample_df, x="Value", dimension="Category", color="green")
    assert h.kwargs["color"] == "green"
