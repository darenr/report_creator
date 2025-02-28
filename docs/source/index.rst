.. Project documentation master file

.. meta::
    :description lang=en:
        Report creator is a library to create self contained HTML reports from python code for text, code, images, and data visualizations.

Report Creator
==============

|PyPI|_ |Python|_ |GitHub|_

.. |PyPI| image:: https://img.shields.io/pypi/v/report_creator.svg?style=for-the-badge&logo=pypi&logoColor=white
..  _PyPI: https://pypi.org/project/report_creator/
.. |Python| image:: https://img.shields.io/pypi/pyversions/report_creator.svg?style=for-the-badge&logo=pypi&logoColor=white
..  _Python: https://pypi.org/project/report_creator/

.. |GitHub| image:: https://img.shields.io/github/license/darenr/report_creator?style=for-the-badge&logo=pypi&logoColor=white
..  _GitHub: https://github.com/darenr/report_creator

Overview
--------

**Report Creator** is a Python library for generating shareable, self-contained HTML reports. These reports are designed to be:

*   **Self-Contained:** Includes base64-encoded images, ensuring the report is fully portable.
*   **Versatile:** Viewable in any web browser and can be easily printed to PDF.
*   **Comprehensive:** Supports a wide array of components including:

    *   Text and code blocks
    *   Images (local, URLs, or base64)
    *   Data visualizations (powered by Plotly Express)
    *   Tables (static or interactive)
    *   Diagrams (using Mermaid.js)
*   **Customizable:** Markdown support within components or as labels/descriptions for other components.
*   **Flexible Layout:** Components can be arranged horizontally (`rc.Group()`) or vertically (`rc.Block()`).
* **Extendable** By using the `rc.Widget()` class, any python object that implements the `_repr_html_()` method can be included in the report.


Getting Started
---------------

Here's a basic example of how to use Report Creator:

.. code-block:: python3

   import report_creator as rc

   report = rc.ReportCreator(title="My Report")
   report.add_component(rc.Block(
         rc.Heading("Hello World", level=1),
         rc.Markdown("This is a simple report using Report Creator."),
   ))
   report.save("report.html")


See the :doc:`getting_started` section for more details.

A comprehensive example demonstrating all components and their options can be found in the ``kitchen_sink.py`` example file |kitchen_sink_location_source|. The resulting report can be viewed |kitchen_sink_location_output|.

.. |kitchen_sink_location_source| raw:: html

   <a href="https://github.com/darenr/report_creator/blob/main/examples/kitchen_sink.py" target="_blank">kitchen_sink.py</a>

.. |kitchen_sink_location_output| raw:: html

   <a href="https://darenr.github.io/report_creator/" target="_blank">here</a>

Table of Contents
-----------------

.. toctree::
   :caption: Usage
   :titlesonly:
   :maxdepth: 2

   getting_started
   api