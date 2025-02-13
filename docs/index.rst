Report Creator
=============

A powerful Python library for creating beautiful, interactive HTML reports.

.. image:: _static/example_report.png
   :alt: Example Report
   :align: center

Features
--------

- **Interactive Components**: Charts, tables, metrics, and more
- **Flexible Layout**: Vertical and horizontal arrangements
- **Markdown Support**: GitHub-flavored markdown with syntax highlighting
- **Data Visualization**: Built-in plotting using Plotly
- **Responsive Design**: Works on desktop and mobile devices
- **Theme Customization**: Multiple themes and styling options
- **Export Options**: HTML output with optional self-contained mode

Quick Start
----------

Installation
~~~~~~~~~~~

.. code-block:: bash

   pip install report-creator

Basic Usage
~~~~~~~~~~

.. code-block:: python

   from report_creator import ReportCreator, Block, Heading, Markdown, Metric

   # Create a simple report
   with ReportCreator("My First Report") as report:
       view = Block(
           Heading("Sales Dashboard"),
           Markdown("Monthly performance metrics"),
           Group(
               Metric("Revenue", 1500000, unit="$"),
               Metric("Orders", 1234),
               Metric("Growth", 12.5, unit="%")
           )
       )
       report.save(view, "report.html")

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   components
   layouts
   charts
   themes
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/report_creator
   api/components
   api/charts
   api/utilities

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog 