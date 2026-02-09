import base64
from unittest.mock import MagicMock
import pytest
import report_creator as rc

def test_d3_component():
    # Mock d3 object
    mock_d3 = MagicMock()
    expected_html = "<html><body><h1>Hello D3</h1></body></html>"
    mock_d3.show.return_value = expected_html
    # Mock config as an attribute, which is common in d3blocks objects
    mock_d3.config = {'figsize': [800, 600]}

    # Instantiate D3 component
    d3_component = rc.D3(mock_d3, label="Test Chart")

    # Verify inheritance
    assert isinstance(d3_component, rc.Base)

    # Call to_html
    html_output = d3_component.to_html()

    # Check if d3.show was called correctly
    mock_d3.show.assert_called_with(return_html=True)

    # Check output contains iframe and base64 encoded html
    expected_b64 = base64.b64encode(expected_html.encode('utf-8')).decode('utf-8')
    assert f'<iframe src="data:text/html;base64,{expected_b64}' in html_output
    assert 'max-width: 800px' in html_output
    assert 'height="600px"' in html_output
    assert 'Test Chart' in html_output

def test_d3_component_error_handling():
    # Mock d3 object that raises exception
    mock_d3 = MagicMock()
    mock_d3.show.side_effect = Exception("D3 Error")

    d3_component = rc.D3(mock_d3)
    html_output = d3_component.to_html()

    assert "Error rendering D3 chart" in html_output
    assert "D3 Error" in html_output
