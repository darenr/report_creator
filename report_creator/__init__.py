from report_creator.__version__ import __version__

# Import from new locations
from .base import Base
from .charts import Bar, Box, Histogram, Line, Pie, Radar, Scatter

# Imports from report_creator.py (original location for non-chart components)
from .report_creator import (
    Accordion,
    # Bar, # Moved to .charts
    # Base, # Moved to .base
    Bash,
    Block,
    # Box, # Moved to .charts
    Collapse,
    DataTable,
    Diagram,
    EventMetric,
    Group,
    Heading,
    # Histogram, # Moved to .charts
    Html,
    Image,
    Java,
    Json,
    # Line, # Moved to .charts
    Markdown,
    Metric,
    MetricGroup,
    # Pie, # Moved to .charts
    Plaintext,
    Prolog,
    Python,
    # Radar, # Moved to .charts
    ReportCreator,
    # Scatter, # Moved to .charts
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
    # report_creator_colors, # This is likely from theming, not report_creator.py
)

# It's good practice to import specific variables if they are part of the public API
from .theming import report_creator_colors

# Make loguru logger available for the library.
# The consuming application can then configure handlers if needed.
from loguru import logger

# By default, Loguru adds a handler to stderr.
# If this library should not output logs unless configured by the application,
# you might consider adding:
# logger.remove() # Removes all handlers, including the default stderr one.
# or
# logger.disable("report_creator") # Disables logging for this specific module name.
# For now, we will allow the default behavior, which is to log to stderr.
