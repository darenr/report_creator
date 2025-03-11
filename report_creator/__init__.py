"""
Report Creator: A library for creating beautiful HTML reports from Python.
"""

from .__version__ import __version__
from .components import (
    Accordion,
    Bar,
    Base,
    Bash,
    Block,
    Box,
    Collapse,
    DataTable,
    Diagram,
    EventMetric,
    Group,
    Heading,
    Histogram,
    Html,
    Image,
    Java,
    Json,
    Line,
    Markdown,
    Metric,
    MetricGroup,
    Pie,
    Plaintext,
    Prolog,
    Python,
    Radar,
    Scatter,
    Select,
    Separator,
    Sh,
    Shell,
    Sql,
    Table,
    Text,
    Unformatted,
    Widget,
    Yaml,
)
from .report_creator import ReportCreator

# Re-export components and other classes, constants
from .theming import report_creator_colors
