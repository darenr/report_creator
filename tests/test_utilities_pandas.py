
import pandas as pd
import pytest
from report_creator.utilities import create_color_value_sensitive_mapping

def test_create_color_value_sensitive_mapping_pandas_defaults():
    values = pd.Series(["Success", "Error occurred", 10, -5, True, False, "Random"])
    colors = create_color_value_sensitive_mapping(values)

    expected_colors = [
        "green",  # Success (string, no error kw)
        "red",    # Error occurred (contains "error")
        "green",  # 10 (positive number)
        "red",    # -5 (negative number)
        "green",  # True (boolean, no specific color set, treated as success)
        "green",  # False (boolean, no specific color set, treated as success)
        "green",  # Random (string, no error kw)
    ]
    assert colors == expected_colors

def test_create_color_value_sensitive_mapping_pandas_custom_colors():
    values = pd.Series(["Success", "Error occurred", 10, -5, True, False])
    colors = create_color_value_sensitive_mapping(
        values,
        error_color="darkred",
        success_color="lightgreen",
        boolean_true_color="blue",
        boolean_false_color="orange"
    )

    expected_colors = [
        "lightgreen", # Success
        "darkred",    # Error
        "lightgreen", # 10
        "darkred",    # -5
        "blue",       # True
        "orange",     # False
    ]
    assert colors == expected_colors

def test_create_color_value_sensitive_mapping_pandas_custom_keywords():
    values = pd.Series(["No problem", "Big Mistake", "Critical Failure"])
    colors = create_color_value_sensitive_mapping(
        values,
        error_keywords=["mistake", "critical"]
    )

    expected_colors = [
        "green", # No problem
        "red",   # Big Mistake
        "red",   # Critical Failure
    ]
    assert colors == expected_colors

def test_create_color_value_sensitive_mapping_pandas_case_insensitive():
    values = pd.Series(["ERROR", "fail", "FAILED", "Exception"])
    colors = create_color_value_sensitive_mapping(values)

    expected_colors = ["red", "red", "red", "red"]
    assert colors == expected_colors

def test_create_color_value_sensitive_mapping_pandas_mixed_types():
    # Including None/NaN/pd.NA
    values = pd.Series([None, 3.14, -0.01, float('nan')])
    colors = create_color_value_sensitive_mapping(values)

    expected_colors = [
        "gray",   # None -> default (object dtype) -> is_str=False, is_num=False, is_bool=False.
                  # Wait, is_num depends on implementation.
                  # pd.isna(None) is True.
                  # is_num check: is_numeric_dtype(object) is False.
                  # fallback map: isinstance(None, (int, float)) is False.
                  # So default_color "gray". Correct.
        "green",  # 3.14 -> success
        "red",    # -0.01 -> error (negative)
        "gray",   # nan -> default (pandas treats NaN as missing/NA, unlike Python where isinstance(nan, float) is True)
    ]
    assert colors == expected_colors

def test_create_color_value_sensitive_mapping_pandas_index():
    values = pd.Index(["Success", "Error"])
    colors = create_color_value_sensitive_mapping(values)
    expected_colors = ["green", "red"]
    assert colors == expected_colors
