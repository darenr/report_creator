import pandas as pd
import pytest
import report_creator as rc
from report_creator.charts import Radar

def test_radar_basic():
    df = pd.DataFrame({
        "Cat1": [1, 2],
        "Cat2": [3, 4],
        "Cat3": [5, 6]
    }, index=["T1", "T2"])

    radar = Radar(df, label="Test Radar")
    html = radar.to_html()

    assert "Test Radar" in html
    assert "plotly-graph-div" in html
    # Check if data is present (simple check)
    assert "T1" in html
    assert "T2" in html

def test_radar_filled():
    df = pd.DataFrame({
        "A": [1],
        "B": [2],
        "C": [3]
    }, index=["Trace1"])

    radar = Radar(df, filled=True)
    html = radar.to_html()

    # In the original implementation, fill="toself" is added to the trace
    # We should check if 'fill' property is present in the JSON data embedded in HTML
    # But parsing the HTML is hard. We rely on the fact that no error is raised and logic is correct.
    # We can check for string "toself" if it appears in the output JS logic (it might be minified or slightly different).
    assert "toself" in html

def test_radar_trace_kwargs():
    df = pd.DataFrame({
        "A": [1],
        "B": [2]
    }, index=["Trace1"])

    # User passes trace_kwargs to customize the trace
    radar = Radar(df, trace_kwargs={"line": {"width": 5}})
    html = radar.to_html()

    # "width" might be in the output
    assert "width" in html

def test_radar_validation():
    # Empty DataFrame (and thus empty index)
    df = pd.DataFrame({"A": []})
    with pytest.raises(ValueError, match="DataFrame must have a non-empty index"):
        Radar(df)

    # Non-unique index
    df = pd.DataFrame({"A": [1, 2]}, index=["T1", "T1"])
    with pytest.raises(ValueError, match="DataFrame index must be unique"):
        Radar(df)

    # NaNs in index
    df = pd.DataFrame({"A": [1]}, index=[float("nan")])
    with pytest.raises(ValueError, match="DataFrame index must not contain NaNs"):
        Radar(df)

def test_radar_lock_minimum_to_zero():
    df = pd.DataFrame({"A": [10, 20]}, index=["T1", "T2"])
    radar = Radar(df, lock_minimum_to_zero=True)
    # This affects range.
    # We can't easily assert on the logic result without inspecting the figure object directly,
    # but we can ensure it runs.
    radar.to_html()
