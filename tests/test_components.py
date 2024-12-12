import os

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
    assert "<div class='group-content'>" in metric_group.to_html()


def test_event_metric():
    event_metric = rc.EventMetric(sample_df, "Value > 20", "Date", frequency="D")
    html = event_metric.to_html()
    assert "Value > 20" in html
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
    report = rc.ReportCreator(title="Test Report", description="This is a test report.", author="Tester")
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
    assert "<hr>" in separator.to_html()


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
        ("![Image](https://example.com/image.png)", '<img src="https://example.com/image.png" alt="Image" />'),
        # Test lists
        ("- Item 1\n- Item 2\n- Item 3", "<ul>\n<li>Item 1</li>\n<li>Item 2</li>\n<li>Item 3</li>\n</ul>"),
        ("1. Item 1\n2. Item 2\n3. Item 3", "<ol>\n<li>Item 1</li>\n<li>Item 2</li>\n<li>Item 3</li>\n</ol>"),
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
    assert (
        "<div class='codehilite'><pre><code class='language-python'>print('Hello, World!')\n</code></pre></div>"
        in html_output
    )


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
    html = rc.Json({"key": "<python_class>"}).to_html()
    assert "&lt;python_class&gt;" in html


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
    with pytest.raises(AssertionError, match="Theme invalid_theme not in"):
        rc.ReportCreator(title="Test", theme="invalid_theme")


def test_report_creator_save(tmp_path):
    """Test the save method of ReportCreator."""
    # Create a temporary directory for saving the report
    tmp_file = tmp_path / "test_report.html"

    # Initialize the ReportCreator
    report = rc.ReportCreator(
        title="Test Report", description="Test Description", author="Tester", footer="Footer Example"
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
    group = rc.Group(rc.Metric("Metric 1", 100), rc.Metric("Metric 2", 200), label="Metrics Group")

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
    with pytest.raises(ValueError, match="Expected view to be either Block or Group object"):
        report.save("InvalidViewType", "output.html")


def test_report_creator_save_prettify_html(tmp_path):
    """Test saving a report with prettified HTML."""
    tmp_file = tmp_path / "prettified_report.html"

    report = rc.ReportCreator(title="Prettified Report", description="A report with prettified HTML.")

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
