from loguru import logger

from report_creator.__version__ import __version__

from .base import Base
from .charts import Bar, Box, Histogram, Line, Pie, Radar, Scatter
from .report_creator import (
    Accordion,
    Bash,
    Block,
    Collapse,
    DataTable,
    Diagram,
    EventMetric,
    Group,
    Heading,
    Html,
    Image,
    Java,
    Json,
    Markdown,
    Metric,
    MetricGroup,
    Plaintext,
    Prolog,
    Python,
    ReportCreator,
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
from .theming import report_creator_colors
