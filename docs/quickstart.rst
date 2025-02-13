Quick Start Guide
================

This guide will help you get started with Report Creator quickly.

Installation
-----------

Install using pip:

.. code-block:: bash

   pip install report-creator

Basic Report
-----------

Here's a simple example that creates a report with some common components:

.. code-block:: python

   from report_creator import (
       ReportCreator, Block, Group,
       Heading, Markdown, Metric, DataTable
   )
   import pandas as pd

   # Sample data
   df = pd.DataFrame({
       'Product': ['A', 'B', 'C'],
       'Sales': [100, 200, 150],
       'Growth': [10, 15, -5]
   })

   # Create report
   with ReportCreator("Sales Report", author="John Doe") as report:
       view = Block(
           Heading("Monthly Sales Analysis"),
           Markdown("""
               # Overview
               This report shows our monthly sales performance.
               Key metrics are highlighted below.
           """),
           Group(
               Metric("Total Sales", 450, unit="$"),
               Metric("Average Growth", 6.67, unit="%"),
               Metric("Best Product", "B")
           ),
           Heading("Detailed Data", level=2),
           DataTable(df, label="Sales by Product")
       )
       report.save(view, "sales_report.html")

Layout Components
---------------

Block
~~~~~
Use ``Block`` for vertical layouts:

.. code-block:: python

   Block(
       component1,
       component2,
       component3
   )

Group
~~~~~
Use ``Group`` for horizontal layouts:

.. code-block:: python

   Group(
       component1,
       component2,
       component3
   )

Common Components
---------------

Heading
~~~~~~~
Section headers with optional levels:

.. code-block:: python

   Heading("Main Title", level=1)
   Heading("Subtitle", level=2)

Markdown
~~~~~~~
Rich text with GitHub-flavored markdown:

.. code-block:: python

   Markdown("""
       # Section
       - Point 1
       - Point 2
       
       ```python
       def example():
           return "Hello"
       ```
   """)

Metric
~~~~~~
Key performance indicators:

.. code-block:: python

   Metric("Revenue", 1500000, unit="$")
   Metric("Growth", 12.5, unit="%")
   Metric("Status", "Active", color=True)

DataTable
~~~~~~~~
Interactive tables with search and sort:

.. code-block:: python

   DataTable(
       df,
       label="Sales Data",
       wrap_text=False,
       max_rows=1000
   )

Charts
------

Line Chart
~~~~~~~~~
Time series and trends:

.. code-block:: python

   Line(
       df,
       x="date",
       y="value",
       dimension="category",
       label="Trends"
   )

Bar Chart
~~~~~~~~
Category comparisons:

.. code-block:: python

   Bar(
       df,
       x="product",
       y="sales",
       dimension="region",
       label="Sales by Product"
   )

Customization
------------

Themes
~~~~~~
Choose from built-in themes:

.. code-block:: python

   ReportCreator(
       "My Report",
       theme="dark",
       code_theme="monokai",
       accent_color="#FF5733"
   )

CSS Styling
~~~~~~~~~~
Add custom CSS:

.. code-block:: python

   Markdown(
       "Custom styled text",
       extra_css="color: blue; font-size: 18px;"
   )

Next Steps
---------

- Explore the :doc:`components` documentation for all available components
- Check out :doc:`examples` for more complex report examples
- Learn about :doc:`themes` for customizing the look and feel
- See :doc:`api/report_creator` for detailed API reference 