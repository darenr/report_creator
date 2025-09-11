import os
from datetime import datetime
from html import escape

import pandas as pd
import pytest

import report_creator as rc

# Sample DataFrame for testing
sample_df = pd.DataFrame(
    {
        "Date": pd.date_range(start="2023-01-01", periods=5),
        "Value": [10, 20, 30, 40, 50],
        "Metric": ["A", "B", "C", "D", "E"],
    }
)


def test_block():
    metric1 = rc.Metric("Test Metric", 123)
    metric2 = rc.Metric("Another Metric", 456)
    block = rc.Block(metric1, metric2)
    assert "<block>" in block.to_html()
    assert "<block-component>" in block.to_html()


def test_group():
    metric1 = rc.Metric("Test Metric", 123)
    metric2 = rc.Metric("Another Metric", 456)
    group = rc.Group(metric1, metric2, label="Test Group")
    assert "Test Group" in group.to_html()
    assert '<div class="group">' in group.to_html()


def test_collapse():
    metric = rc.Metric("Test Metric", 123)
    collapse = rc.Collapse(metric, label="Collapsible Section")
    assert "Collapsible Section" in collapse.to_html()
    assert '<details class="collapse">' in collapse.to_html()


def test_metric():
    metric = rc.Metric("Test Metric", 123, unit="ms")
    html = metric.to_html()
    assert "Test Metric" in html
    assert "123ms" in html


def test_metric_group():
    metric_group = rc.MetricGroup(sample_df, "Metric", "Value", label="Metrics Group")
    assert "Metrics Group" in metric_group.to_html()
    assert '<div class="group-content">' in metric_group.to_html()


def test_event_metric():
    event_metric = rc.EventMetric(sample_df, "Value > 20", "Date", frequency="D")
    html = event_metric.to_html()
    assert escape("Value > 20") in html
    assert "metric" in html


def test_table():
    table = rc.Table(sample_df, label="Test Table")
    html = table.to_html()
    assert "Test Table" in html
    assert "<table" in html


def test_data_table():
    data_table = rc.DataTable(sample_df, label="Data Table Example")
    html = data_table.to_html()
    assert "Data Table Example" in html
    assert "fancy-table" in html


def test_report_creator(tmp_path):
    report = rc.ReportCreator(
        title="Test Report", description="This is a test report.", author="Tester"
    )
    block = rc.Block(rc.Metric("Metric Example", 123))
    report.save(block, f"{tmp_path}/test_report.html", prettify_html=False)
    assert report.title == "Test Report"
    assert report.description == "This is a test report."


def test_heading():
    heading = rc.Heading("Main Heading", level=2)
    assert "<h2>Main Heading</h2>" in heading.to_html()


def test_separator():
    separator = rc.Separator(label="Section Break")
    assert "Section Break" in separator.to_html()
    assert "<hr/>" in separator.to_html()


@pytest.mark.parametrize(
    "text,expected_html",
    [
        # Test simple Markdown with headers
        ("# Heading 1", "<h1>Heading 1</h1>"),
        ("## Heading 2", "<h2>Heading 2</h2>"),
        ("### Heading 3", "<h3>Heading 3</h3>"),
        # Test Markdown with bold and italics
        ("**bold text**", "<strong>bold text</strong>"),
        ("*italic text*", "<em>italic text</em>"),
        # Test links and images
        ("[Link](https://example.com)", '<a href="https://example.com">Link</a>'),
        (
            "![Image](https://example.com/image.png)",
            '<img src="https://example.com/image.png" alt="Image" />',
        ),
        # Test lists
        (
            "- Item 1\n- Item 2\n- Item 3",
            "<ul>\n<li>Item 1</li>\n<li>Item 2</li>\n<li>Item 3</li>\n</ul>",
        ),
        (
            "1. Item 1\n2. Item 2\n3. Item 3",
            "<ol>\n<li>Item 1</li>\n<li>Item 2</li>\n<li>Item 3</li>\n</ol>",
        ),
        # Test mixed Markdown
        (
            "# Heading\nThis is **bold** and *italic*, with [a link](https://example.com).",
            '<h1>Heading</h1>\n<p>This is <strong>bold</strong> and <em>italic</em>, with <a href="https://example.com">a link</a>.</p>',
        ),
    ],
)
def test_markdown_conversion(text, expected_html):
    """Test Markdown to HTML conversion."""
    markdown = rc.Markdown(text)
    html_output = markdown.to_html()
    assert expected_html in html_output


def test_markdown_with_code():
    """Test Markdown with code."""
    markdown = rc.Markdown("```python\nprint('Hello, World!')\n```")
    html_output = markdown.to_html()
    assert "language-python" in html_output


def test_markdown_with_label():
    """Test Markdown with a label."""
    markdown = rc.Markdown("## Markdown with Label", label="Section Label")
    html_output = markdown.to_html()
    assert "Section Label" in html_output
    assert "<h2>Markdown with Label</h2>" in html_output


def test_markdown_with_bordered():
    """Test Markdown with a border."""
    markdown = rc.Markdown("## Markdown with Border", bordered=True)
    html_output = markdown.to_html()
    assert "round-bordered" in html_output
    assert "<h2>Markdown with Border</h2>" in html_output


def test_markdown_with_extra_css():
    """Test Markdown with extra CSS."""
    markdown = rc.Markdown("## Markdown with CSS", extra_css="color: red;")
    html_output = markdown.to_html()
    assert 'style="color: red;"' in html_output
    assert "<h2>Markdown with CSS</h2>" in html_output


def test_markdown_edge_cases():
    """Test edge cases for Markdown."""
    # Empty text
    markdown = rc.Markdown("")
    html_output = markdown.to_html()
    assert "markdown-wrapper include_hljs" in html_output

    # Very long Markdown text
    long_text = "# " + "LongText " * 100
    markdown = rc.Markdown(long_text)
    html_output = markdown.to_html()
    assert "LongText" in html_output


def test_markdown_html_script_injection():
    """Test for potential HTML injection in Markdown."""
    malicious_text = "## Markdown Example\nThis is a Markdown example with a potential XSS vulnerability:\n<script>alert('XSS')</script>\nThe End"
    markdown = rc.Markdown(malicious_text)
    html_output = markdown.to_html()
    assert "<script>" not in html_output
    assert "alert('XSS')" not in html_output
    assert "<h2>Markdown Example</h2>" in html_output
    assert "The End" in html_output


def test_widget():
    widget = rc.Widget(sample_df)
    html = widget.to_html()
    assert "report-widget" in html


def test_line():
    line_chart = rc.Line(sample_df, x="Date", y="Value", label="Line Chart")
    html = line_chart.to_html()
    assert "Line Chart" in html
    assert "plotly-graph-div" in html


def test_json():
    # test for escaped characters
    test_with_escaped_characters = "<script>alert('XSS')</script>"
    html = rc.Json({"key_to_bad_value": test_with_escaped_characters}).to_html()
    assert escape(test_with_escaped_characters) in html


def test_json_string():
    # test for valid json string
    html = rc.Json('{"key": "value"}').to_html()
    assert "key" in html
    assert "value" in html


def test_yaml_dict():
    # Test with a dictionary
    data = {"key1": "value1", "key2": 123, "key3": [1, 2, 3]}
    yaml_component = rc.Yaml(data)
    html = yaml_component.to_html()
    assert "key1" in html
    assert "value1" in html
    assert "key2" in html
    assert "123" in html
    assert "key3" in html


def test_yaml_string():
    # Test with a YAML string
    yaml_string = """
    key1: value1
    key2: 456
    key3:
      - a
      - b
      - c
    """
    yaml_component = rc.Yaml(yaml_string)
    html = yaml_component.to_html()
    assert "key1" in html
    assert "value1" in html
    assert "key2" in html
    assert "456" in html
    assert "key3" in html
    assert "- a" in html
    assert "- b" in html
    assert "- c" in html


def test_report_creator_initialization():
    """Test the initialization of the ReportCreator class."""
    report = rc.ReportCreator(
        title="Test Report",
        description="This is a test description.",
        author="Test Author",
        theme="rc",
        diagram_theme="default",
        accent_color="blue",
        footer="Footer text.",
    )
    assert report.title == "Test Report"
    assert report.description == "This is a test description."
    assert report.author == "Test Author"
    assert report.diagram_theme == "default"
    assert report.accent_color == "blue"
    assert report.footer == "Footer text."


def test_report_creator_invalid_theme():
    """Test ReportCreator raises an error for invalid themes."""
    with pytest.raises(ValueError, match="Theme 'invalid_theme' not in"):
        rc.ReportCreator(title="Test", theme="invalid_theme")


def test_report_creator_save(tmp_path):
    """Test the save method of ReportCreator."""
    # Create a temporary directory for saving the report
    tmp_file = tmp_path / "test_report.html"

    # Initialize the ReportCreator
    report = rc.ReportCreator(
        title="Test Report",
        description="Test Description",
        author="Tester",
        footer="Footer Example",
    )

    # Create a simple Block view
    block = rc.Block(rc.Metric("Test Metric", 123), rc.Metric("Another Metric", 456))

    # Save the report
    report.save(block, str(tmp_file))

    # Verify the file is saved
    assert os.path.exists(tmp_file)
    with open(tmp_file) as f:
        content = f.read()

    # Verify the content
    assert "Test Report" in content
    assert "Test Description" in content
    assert "Test Metric" in content
    assert "123" in content


def test_report_creator_save_with_group(tmp_path):
    """Test saving a report with a Group view."""
    tmp_file = tmp_path / "group_report.html"

    # Initialize the ReportCreator
    report = rc.ReportCreator(title="Group Report Test")

    # Create a Group view
    group = rc.Group(
        rc.Metric("Metric 1", 100), rc.Metric("Metric 2", 200), label="Metrics Group"
    )

    # Save the report
    report.save(group, str(tmp_file))

    # Verify the file is saved
    assert os.path.exists(tmp_file)
    with open(tmp_file) as f:
        content = f.read()

    # Verify the content
    assert "Group Report Test" in content
    assert "Metrics Group" in content
    assert "Metric 1" in content
    assert "100" in content


def test_report_creator_invalid_view():
    """Test save raises an error for invalid view types."""
    report = rc.ReportCreator(title="Invalid View Test")
    with pytest.raises(
        ValueError,
        match="Expected 'view' to be an instance of a Base component, got str instead.",
    ):
        report.save("InvalidViewType", "output.html")


def test_report_creator_save_prettify_html(tmp_path):
    """Test saving a report with prettified HTML."""
    tmp_file = tmp_path / "prettified_report.html"

    report = rc.ReportCreator(
        title="Prettified Report", description="A report with prettified HTML."
    )

    block = rc.Block(rc.Metric("Pretty Metric", 789))

    # Save the report with prettified HTML
    report.save(block, str(tmp_file), prettify_html=True)

    # Verify the file is saved
    assert os.path.exists(tmp_file)
    with open(tmp_file) as f:
        content = f.read()

    # Verify the prettified content
    assert "Pretty Metric" in content
    assert "789" in content
    assert "</html>" in content  # Ensure the HTML is well-formed


def test_report_creator_save_without_prettify_html(tmp_path):
    """Test saving a report without prettified HTML."""
    tmp_file = tmp_path / "non_prettified_report.html"

    report = rc.ReportCreator(title="Non-Prettified Report")

    block = rc.Block(rc.Metric("Simple Metric", 456))

    # Save the report without prettified HTML
    report.save(block, str(tmp_file), prettify_html=False)

    # Verify the file is saved
    assert os.path.exists(tmp_file)
    with open(tmp_file) as f:
        content = f.read()

    # Verify the non-prettified content
    assert "Simple Metric" in content
    assert "456" in content


def test_empty_block():
    """Test Block component with no child components."""
    block = rc.Block()
    html = block.to_html()
    assert "<block>" in html
    assert "</block>" in html
    assert "<block-component>" not in html


def test_empty_group():
    """Test Group component with no child components."""
    group = rc.Group()
    html = group.to_html()
    assert '<div class="group">' in html
    assert "</div>" in html
    assert "<div class='group-content'>" not in html


def test_empty_collapse():
    """Test Collapse component with no child components."""
    collapse = rc.Collapse(label="Empty Collapse")
    html = collapse.to_html()
    assert '<details class="collapse">' in html
    assert "<summary>Empty Collapse</summary>" in html
    assert "</details>" in html


# Sample DataFrame for testing
sample_df = pd.DataFrame(
    {
        "Date": pd.date_range(start="2023-01-01", periods=5),
        "Value": [10, 20, 30, 40, 50],
        "Metric": ["A", "B", "C", "D", "E"],
        "Category": ["X", "Y", "X", "Y", "X"],
    }
)


# --- Metric Component Tests ---
def test_metric_various_values():
    """Test Metric with different value types."""
    assert "123" in rc.Metric("Int", 123).to_html()
    assert "123.457" in rc.Metric("Float", 123.4567).to_html()
    assert "Test" in rc.Metric("String", "Test").to_html()
    assert "2023-01-01" in rc.Metric("Datetime", datetime(2023, 1, 1)).to_html()
    assert "None" in rc.Metric("None", None).to_html()


@pytest.mark.parametrize(
    "value, float_precision, expected",
    [
        (123.456789, 2, "123.46"),
        (123.456789, 0, "123"),
        (123.4, None, "123"),
    ],
)
def test_metric_float_precision(value, float_precision, expected):
    """Test Metric with various float precision."""
    assert expected in rc.Metric("Test", value, float_precision=float_precision).to_html()


def test_metric_with_unit():
    """Test Metric with a unit."""
    assert "123ms" in rc.Metric("Test", 123, unit="ms").to_html()


def test_metric_with_color():
    """Test Metric with color."""
    metric_a = rc.Metric("Test", 123, color=True)
    metric_b = rc.Metric("Test", 123, color=False)
    metric_a_html = metric_a.to_html()
    metric_b_html = metric_b.to_html()
    assert 'style="background-color' in metric_a_html
    assert metric_a_html != metric_b_html


def test_metric_html_label():
    """Test Metric label with html"""
    metric = rc.Metric("Test", 123, label="42")
    assert "42" in metric.to_html()


# --- Table Component Tests ---
def test_table_empty_dataframe():
    """Test Table with an empty DataFrame."""
    table = rc.Table(pd.DataFrame(), label="Empty Table")
    assert "Empty Table" in table.to_html()
    assert "<table" in table.to_html()


def test_table_mixed_data_types():
    """Test Table with mixed data types."""
    df = pd.DataFrame({"A": [1, 2], "B": ["a", "b"], "C": [1.1, 2.2]})
    table = rc.Table(df, label="Mixed Types")
    html = table.to_html()
    assert "Mixed Types" in html
    assert "1.1" in html


def test_table_float_precision():
    """Test Table float precision."""
    df = pd.DataFrame({"A": [1.1111, 2.2222]})
    table = rc.Table(df, label="float precision", float_precision=2)
    html = table.to_html()
    assert "1.11" in html


def test_table_index():
    """Test Table index display."""
    df = pd.DataFrame({"A": [1, 2]})
    table_with_index = rc.Table(df, index=True)
    table_without_index = rc.Table(df, index=False)
    assert table_without_index.to_html().count("</th>") == 1
    assert table_with_index.to_html().count("</th>") == 4


def test_table_with_label():
    table = rc.Table(sample_df, label="Test Table")
    html = table.to_html()
    assert "Test Table" in html


# --- DataTable Component Tests ---
def test_datatable_empty_dataframe():
    """Test DataTable with an empty DataFrame."""
    dt = rc.DataTable(pd.DataFrame(), label="Empty DataTable")
    assert "Empty DataTable" in dt.to_html()
    assert "fancy-table" in dt.to_html()


def test_datatable_mixed_data_types():
    """Test DataTable with mixed data types."""
    df = pd.DataFrame({"A": [1, 2], "B": ["a", "b"], "C": [1.1, 2.2]})
    dt = rc.DataTable(df, label="Mixed Types")
    html = dt.to_html()
    assert "Mixed Types" in html
    assert "1.1" in html


def test_datatable_index():
    """Test DataTable index display."""
    df = pd.DataFrame({"A": [1, 2]})
    dt_with_index = rc.DataTable(df, index=True)
    dt_without_index = rc.DataTable(df, index=False)
    assert dt_without_index.to_html().count("</th>") == 1
    assert dt_with_index.to_html().count("</th>") == 4


def test_datatable_max_rows():
    """Test DataTable max_rows."""
    df = pd.DataFrame({"A": range(10)})
    dt_half = rc.DataTable(df, max_rows=5)
    assert dt_half.to_html().count("</td>") == 5


def test_datatable_wrap_text():
    """Test DataTable wrap_text."""
    df = pd.DataFrame({"A": ["a" * 100, "b"]})
    dt_wrapped = rc.DataTable(df, wrap_text=True)
    dt_nowrapped = rc.DataTable(df, wrap_text=False)
    assert "nowrap" not in dt_wrapped.to_html()
    assert "nowrap" in dt_nowrapped.to_html()


def test_datatable_float_precision():
    """Test DataTable float precision."""
    df = pd.DataFrame({"A": [1.1111, 2.2222]})
    table = rc.DataTable(df, label="float precision", float_precision=2)
    html = table.to_html()
    assert "1.11" in html


def test_datatable_with_label():
    data_table = rc.DataTable(sample_df, label="Data Table Example")
    html = data_table.to_html()
    assert "Data Table Example" in html


# --- Widget Component Tests ---
def test_widget_matplotlib():
    """Test Widget with a Matplotlib figure."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    widget = rc.Widget(fig, label="Matplotlib Widget")
    html = widget.to_html()
    assert "Matplotlib Widget" in html
    assert "<img" in html


def test_widget_plotly():
    """Test Widget with a Plotly figure."""
    import plotly.express as px

    fig = px.line(sample_df, x="Date", y="Value")
    widget = rc.Widget(fig, label="Plotly Widget")
    html = widget.to_html()
    assert "Plotly Widget" in html
    assert "plotly-graph-div" in html


def test_widget_pandas_style():
    """Test Widget with a pandas style"""
    widget = rc.Widget(sample_df.style, label="Plotly Widget")
    html = widget.to_html()
    assert "Plotly Widget" in html
    assert "<th" in html
    assert "<td" in html


def test_widget_with_label():
    widget = rc.Widget(sample_df, label="Test Widget")
    html = widget.to_html()
    assert "Test Widget" in html
    assert "report-widget" in html


# --- HTML Component Tests ---
def test_html_with_css():
    """Test Html with CSS."""
    html = rc.Html("<h1>Test</h1>", css="h1 { color: red; }")
    assert "<style>h1 { color: red; }</style>" in html.to_html()
    assert "<h1>Test</h1>" in html.to_html()


def test_html_with_border():
    """Test Html with border."""
    html_bordered = rc.Html("<div>Test</div>", bordered=True)
    html_nobordered = rc.Html("<div>Test</div>", bordered=False)
    assert "round-bordered" in html_bordered.to_html()
    assert "round-bordered" not in html_nobordered.to_html()


def test_html_with_label():
    """Test Html with label."""
    html_with_label = rc.Html("<div>Test</div>", label="Test Label")
    assert "Test Label" in html_with_label.to_html()


def test_html_unclosed_tags():
    with pytest.raises(ValueError, match="contains unclosed tags"):
        rc.Html("<div>Test")


def test_html_injection():
    html_with_injection = rc.Html("<div><script>alert(1)</script></div>")
    assert "<script>" in html_with_injection.to_html()
    assert "alert(1)" in html_with_injection.to_html()


# --- Diagram Component Tests ---
def test_diagram_pan_and_zoom():
    """Test Diagram pan_and_zoom."""
    diagram_panzoom = rc.Diagram("graph LR\nA-->B", pan_and_zoom=True)
    diagram_nopanzomm = rc.Diagram("graph LR\nA-->B", pan_and_zoom=False)
    assert "mermaid-pan-zoom" in diagram_panzoom.to_html()
    assert "mermaid-pan-zoom" not in diagram_nopanzomm.to_html()


def test_diagram_extra_css():
    """Test Diagram extra_css."""
    diagram = rc.Diagram("graph LR\nA-->B", extra_css="color: red;")
    assert 'style="color: red;"' in diagram.to_html()


def test_diagram_various_types():
    """Test with a few diagram types"""
    rc.Diagram("graph LR\nA-->B").to_html()
    rc.Diagram("sequenceDiagram\nA->>B: Hello").to_html()
    rc.Diagram("gantt\nsection A\nA: 2024-01-01, 2024-01-02").to_html()


def test_diagram_with_label():
    diagram = rc.Diagram("graph LR\nA-->B", label="Test Diagram")
    html = diagram.to_html()
    assert "Test Diagram" in html


# --- Image Component Tests ---
def test_image_base64():
    """Test Image with base64."""
    # Sample base64 encoded string (a 1x1 transparent pixel)
    base64_str = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    image = rc.Image(f"data:image/png;base64,{base64_str}")
    assert f"data:image/png;base64,{base64_str}" in image.to_html()


def test_image_local_filepath(tmp_path):
    """Test Image with local filepath."""
    # Create a dummy image file
    image_path = tmp_path / "test_image.png"
    with open(image_path, "w") as f:
        f.write("dummy image data")
    image = rc.Image(str(image_path), convert_to_base64=True)
    assert "data:image/png;base64" in image.to_html()


def test_image_clickable():
    """Test Image clickable."""
    image = rc.Image("https://via.placeholder.com/150", link_to="https://example.com")
    assert '<a href="https://example.com"' in image.to_html()


def test_image_rounded():
    """Test Image rounded."""
    image_rounded = rc.Image("https://via.placeholder.com/150", rounded=True)
    image_notrounded = rc.Image("https://via.placeholder.com/150", rounded=False)
    assert "border-radius" in image_rounded.to_html()
    assert "border-radius" not in image_notrounded.to_html()


def test_image_extra_css():
    """Test Image extra_css."""
    image = rc.Image("https://via.placeholder.com/150", extra_css="width: 50px;")
    assert "width: 50px;" in image.to_html()


def test_image_with_label():
    image = rc.Image("https://via.placeholder.com/150", label="Test Image")
    html = image.to_html()
    assert "Test Image" in html


def test_markdown_unclosed_tags():
    """Test for potential HTML unclosed tags."""
    unclosed_text = "<h2> Markdown Example\nThis is a Markdown example with a potential XSS vulnerability:\n<b>The End"
    markdown = rc.Markdown(unclosed_text)
    html_output = markdown.to_html()
    assert "<b>" in html_output
    assert "The End" in html_output


# --- Yaml/Json Component Tests ---
def test_json_invalid():
    with pytest.raises(ValueError, match="Input string is not valid JSON"):
        rc.Json("invalid json")
