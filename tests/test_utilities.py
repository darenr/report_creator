
from report_creator.utilities import create_color_value_sensitive_mapping


def test_create_color_value_sensitive_mapping_defaults():
    values = ["Success", "Error occurred", 10, -5, True, False, "Random"]
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

def test_create_color_value_sensitive_mapping_custom_colors():
    values = ["Success", "Error occurred", 10, -5, True, False]
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

def test_create_color_value_sensitive_mapping_custom_keywords():
    values = ["No problem", "Big Mistake", "Critical Failure"]
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

def test_create_color_value_sensitive_mapping_case_insensitive():
    values = ["ERROR", "fail", "FAILED", "Exception"]
    colors = create_color_value_sensitive_mapping(values)

    expected_colors = ["red", "red", "red", "red"]
    assert colors == expected_colors

def test_create_color_value_sensitive_mapping_mixed_types():
    values = [None, 3.14, -0.01, object()]
    colors = create_color_value_sensitive_mapping(values)

    expected_colors = [
        "gray",   # None -> default
        "green",  # 3.14 -> success
        "red",    # -0.01 -> error (negative)
        "gray",   # object() -> default
    ]
    assert colors == expected_colors
