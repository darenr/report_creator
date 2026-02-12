import pytest
from report_creator.report_creator import Sql


def test_sql_formatting_select_simple():
    sql = "select * from table where id = 1"
    formatted = Sql.format_sql(sql)
    # The formatter now capitalizes and splits keywords
    assert "SELECT" in formatted
    assert "FROM" in formatted
    assert "WHERE" in formatted
    # Check that it starts with SELECT (no leading newline if start)
    assert formatted.strip().startswith("SELECT")
    # Check for newlines
    assert "\n\t*\nFROM" in formatted or "\nFROM" in formatted

def test_sql_formatting_select_distinct():
    sql = "select distinct name, age from users"
    formatted = Sql.format_sql(sql)
    assert "SELECT DISTINCT" in formatted
    assert formatted.strip().startswith("SELECT DISTINCT")

def test_sql_formatting_nested_query():
    # Note: The formatter expects a space after the parenthesis for keywords.
    sql = "select * from ( select distinct id from t)"
    formatted = Sql.format_sql(sql)
    # Outer SELECT
    assert formatted.strip().startswith("SELECT")
    # Inner SELECT DISTINCT should be present and formatted
    # Note: The current regex implementation might format nested queries with newlines if they match the pattern
    assert "SELECT DISTINCT" in formatted
    assert "FROM" in formatted

def test_sql_formatting_comma_newlines():
    sql = "select a, b, c from t"
    formatted = Sql.format_sql(sql)
    # Commas should be followed by newline and tab
    assert "a,\n\t" in formatted
    assert "b,\n\t" in formatted

def test_sql_formatting_reserved_words():
    sql = "select a as alias from t"
    formatted = Sql.format_sql(sql)
    assert " AS " in formatted
    assert "FROM" in formatted

def test_sql_formatting_case_insensitivity():
    sql = "SELECT * FROM TABLE WHERE ID = 1"
    formatted = Sql.format_sql(sql)
    # Should remain uppercase or be re-uppercased (the formatter uppercases keywords)
    assert "SELECT" in formatted
    assert "FROM" in formatted
    assert "WHERE" in formatted

def test_sql_formatting_quoted_strings():
    # Keywords inside quotes should NOT be formatted
    # Note: Keywords immediately followed by a quote (e.g. select 'val') or preceded by a quote might not be formatted
    # to avoid false positives inside strings.
    sql = "select 'select' as type, \"from\" as source from table"
    formatted = Sql.format_sql(sql)
    # The 'select' inside quotes should remain lowercase 'select'
    assert "'select'" in formatted
    # The "from" inside quotes should remain lowercase "from"
    assert '"from"' in formatted

    # AS should be formatted (uppercase)
    assert " AS " in formatted
    # The final FROM (not quoted) should be formatted because it is not followed by a quote
    assert "\nFROM\n\t" in formatted

def test_sql_formatting_create_table():
    sql = "create table foo as select * from bar"
    formatted = Sql.format_sql(sql)
    assert "CREATE TABLE" in formatted
    assert "AS" in formatted
    assert "SELECT" in formatted

def test_sql_formatting_group_by():
    sql = "select a, count(*) from t group by a order by 2 desc"
    formatted = Sql.format_sql(sql)
    assert "GROUP BY" in formatted
    assert "ORDER BY" in formatted
    assert "DESC" in formatted

def test_sql_formatting_left_join():
    sql = "select * from a left join b on a.id = b.id"
    formatted = Sql.format_sql(sql)
    assert "LEFT JOIN" in formatted
    assert "ON" in formatted

def test_sql_formatting_starts_with_newline():
    # If the SQL starts with whitespace, the formatter should handle it gracefully
    sql = "\n  select * from t"
    formatted = Sql.format_sql(sql)
    assert formatted.strip().startswith("SELECT")
