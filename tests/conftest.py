import pandas as pd
import pytest

@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "Date": pd.date_range(start="2023-01-01", periods=5),
            "Value": [10, 20, 30, 40, 50],
            "Metric": ["A", "B", "C", "D", "E"],
            "Category": ["X", "Y", "X", "Y", "X"],
        }
    )
