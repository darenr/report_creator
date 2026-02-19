
import pytest
from report_creator.report_creator import Html

def test_html_validation_enabled_by_default():
    invalid_html = "<div><p>Unclosed div"
    with pytest.raises(ValueError, match="unclosed tags"):
        Html(invalid_html)

def test_html_validation_disabled():
    invalid_html = "<div><p>Unclosed div"
    # Should not raise ValueError
    html_component = Html(invalid_html, validate_html=False)
    assert html_component.html_str == invalid_html

def test_html_validation_valid_html():
    valid_html = "<div><p>Closed</p></div>"
    html_component = Html(valid_html)
    assert html_component.html_str == valid_html

def test_html_validation_valid_html_disabled():
    valid_html = "<div><p>Closed</p></div>"
    html_component = Html(valid_html, validate_html=False)
    assert html_component.html_str == valid_html
